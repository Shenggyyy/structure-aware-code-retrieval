"""Build atomic SQLite snapshots and load them without the source repository."""

import json
import os
import platform
import sqlite3
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path

from structure_aware_retrieval.ingestion import EXCLUDED_DIRECTORIES, scan_repository
from structure_aware_retrieval.models import Chunk, Diagnostic, Symbol, stable_id
from structure_aware_retrieval.parsing import parse_file
from structure_aware_retrieval.tokenization import TOKENIZER_VERSION, tokenize_code

SCHEMA_VERSION = 1
PARSER_VERSION = 1
APPLICATION_ID = 0x53414352
BM25_CONFIG = {"variant": "BM25Plus", "k1": 1.5, "b": 0.75, "delta": 0.0}

SCHEMA = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE files (path TEXT PRIMARY KEY, content_hash TEXT NOT NULL, size_bytes INTEGER NOT NULL);
CREATE TABLE symbols (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL REFERENCES files(path),
    parent_id TEXT REFERENCES symbols(id),
    payload TEXT NOT NULL
);
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL REFERENCES symbols(id),
    payload TEXT NOT NULL,
    tokens TEXT NOT NULL
);
CREATE TABLE imports (symbol_id TEXT NOT NULL REFERENCES symbols(id), payload TEXT NOT NULL);
CREATE INDEX chunks_by_symbol ON chunks(symbol_id);
CREATE INDEX symbols_by_file ON symbols(path);
"""


@dataclass(frozen=True, slots=True)
class LoadedIndex:
    metadata: dict
    symbols: dict[str, Symbol]
    chunks: list[Chunk]
    tokens: list[list[str]]


def _read_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        if connection.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError(f"Not a SACR index: {path}")
    except Exception:
        connection.close()
        raise
    return connection


def _git_provenance(root: Path) -> dict[str, str | bool | None]:
    def git(*arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=10,
        )
        return result.stdout.strip()

    try:
        commit = git("rev-parse", "HEAD")
        dirty = bool(git("status", "--porcelain", "--untracked-files=normal"))
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "dirty": None}


def build_index(
    repository: Path,
    output: Path,
    *,
    max_chunk_lines: int = 80,
    max_file_bytes: int = 1_048_576,
    exclude: tuple[str, ...] = (),
    overwrite: bool = False,
) -> dict:
    """Create a snapshot; an explicit overwrite replaces only an existing SACR index."""
    if max_chunk_lines < 1 or max_file_bytes < 1:
        raise ValueError("Chunk and file size limits must be positive")
    repository = repository.resolve(strict=True)
    if output.is_symlink():
        raise ValueError("Index output must not be a symbolic link")
    output = output.resolve()
    if output.suffix not in {".sqlite", ".sqlite3", ".db"}:
        raise ValueError("Index output must have a .sqlite, .sqlite3, or .db extension")
    if output.exists():
        if not overwrite:
            raise FileExistsError(f"Index already exists: {output}; use --overwrite to rebuild")
        try:
            connection = _read_connection(output)
            connection.close()
        except sqlite3.Error as error:
            raise ValueError(f"Cannot replace a non-SACR database: {output}") from error

    git_provenance = _git_provenance(repository)
    scan = scan_repository(repository, max_file_bytes=max_file_bytes, exclude=exclude)
    config = {
        "schema_version": SCHEMA_VERSION,
        "parser_version": PARSER_VERSION,
        "scanner_version": 1,
        "tokenizer_version": TOKENIZER_VERSION,
        "max_chunk_lines": max_chunk_lines,
        "max_file_bytes": max_file_bytes,
        "exclude": list(exclude),
        "excluded_directories": sorted(EXCLUDED_DIRECTORIES),
        "gitignore_hashes": scan.ignore_hashes,
        "bm25": BM25_CONFIG,
    }
    manifest = [(source.path, source.content_hash) for source in scan.files]
    # Include skipped-file identities/reasons without machine-dependent OS messages.
    snapshot_id = stable_id(
        manifest, config, [(item.path, item.reason) for item in scan.diagnostics]
    )
    diagnostics = list(scan.diagnostics)
    parsed_files = []
    for source in scan.files:
        try:
            parsed_files.append(
                (source, parse_file(source, snapshot_id, max_chunk_lines=max_chunk_lines))
            )
        except (SyntaxError, UnicodeError, LookupError, ValueError, RecursionError) as error:
            diagnostics.append(Diagnostic(source.path, "parse_error", str(error)))

    metadata = {
        "snapshot_id": snapshot_id,
        "repository": str(repository),
        "git": git_provenance,
        "runtime": {
            "python": platform.python_version(),
            "packages": {
                package: version(package)
                for package in ("structure-aware-code-retrieval", "rank-bm25", "pathspec")
            },
        },
        "config": config,
        "manifest": manifest,
        "files_scanned": len(scan.files),
        "files_indexed": len(parsed_files),
        "symbol_count": sum(len(parsed.symbols) for _, parsed in parsed_files),
        "chunk_count": sum(len(parsed.chunks) for _, parsed in parsed_files),
        "import_count": sum(len(parsed.imports) for _, parsed in parsed_files),
        "excluded_entries": scan.excluded_entries,
        "diagnostics": [asdict(item) for item in diagnostics],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent, delete=False
    )
    temporary = Path(handle.name)
    handle.close()
    connection = None
    try:
        connection = sqlite3.connect(temporary)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        connection.executescript(SCHEMA)
        with connection:
            connection.executemany(
                "INSERT INTO metadata VALUES (?, ?)",
                [(key, json.dumps(value, ensure_ascii=True)) for key, value in metadata.items()],
            )
            for source, parsed in parsed_files:
                connection.execute(
                    "INSERT INTO files VALUES (?, ?, ?)",
                    (source.path, source.content_hash, len(source.data)),
                )
                symbols = {symbol.id: symbol for symbol in parsed.symbols}
                connection.executemany(
                    "INSERT INTO symbols VALUES (?, ?, ?, ?)",
                    [
                        (symbol.id, symbol.path, symbol.parent_id, json.dumps(asdict(symbol)))
                        for symbol in parsed.symbols
                    ],
                )
                for chunk in parsed.chunks:
                    symbol = symbols[chunk.symbol_id]
                    content = "\n".join(
                        [chunk.path, symbol.qualified_name, symbol.signature, chunk.text]
                    )
                    connection.execute(
                        "INSERT INTO chunks VALUES (?, ?, ?, ?)",
                        (
                            chunk.id,
                            chunk.symbol_id,
                            json.dumps(asdict(chunk)),
                            json.dumps(tokenize_code(content)),
                        ),
                    )
                connection.executemany(
                    "INSERT INTO imports VALUES (?, ?)",
                    [(item.symbol_id, json.dumps(asdict(item))) for item in parsed.imports],
                )
        connection.close()
        connection = None
        os.replace(temporary, output)
    finally:
        if connection is not None:
            connection.close()
        temporary.unlink(missing_ok=True)
    return metadata


def load_index(path: Path) -> LoadedIndex:
    """Read a supported snapshot without creating files or consulting source code."""
    if not path.is_file():
        raise FileNotFoundError(f"Index not found: {path}; run sacr index first")
    connection = None
    try:
        connection = _read_connection(path)
        if connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            raise ValueError("Unsupported index schema; rebuild with sacr index --overwrite")
        metadata = {
            key: json.loads(value)
            for key, value in connection.execute("SELECT key, value FROM metadata")
        }
        if metadata["config"]["tokenizer_version"] != TOKENIZER_VERSION:
            raise ValueError("Unsupported tokenizer version; rebuild the index")
        if not isinstance(metadata["snapshot_id"], str) or not isinstance(
            metadata["config"]["bm25"], dict
        ):
            raise ValueError("Invalid index metadata; rebuild the index")
        symbols = {
            identifier: Symbol(**json.loads(payload))
            for identifier, payload in connection.execute("SELECT id, payload FROM symbols")
        }
        chunks: list[Chunk] = []
        tokens: list[list[str]] = []
        for payload, token_data in connection.execute(
            "SELECT payload, tokens FROM chunks ORDER BY id"
        ):
            chunk = Chunk(**json.loads(payload))
            if chunk.symbol_id not in symbols:
                raise ValueError("Chunk refers to a missing symbol")
            chunks.append(chunk)
            terms = json.loads(token_data)
            if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
                raise ValueError("Invalid stored tokens; rebuild the index")
            tokens.append(terms)
        return LoadedIndex(metadata, symbols, chunks, tokens)
    except (sqlite3.Error, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid or incomplete SACR index: {path}; rebuild it") from error
    finally:
        if connection is not None:
            connection.close()
