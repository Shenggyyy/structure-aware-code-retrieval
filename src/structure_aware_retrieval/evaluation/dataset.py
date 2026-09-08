"""Strict, chunker-independent benchmark records and source-index validation."""

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from structure_aware_retrieval.indexing import LoadedIndex
from structure_aware_retrieval.models import Symbol, stable_id

CATEGORIES = {"symbol", "behavior", "cross_file", "test"}


@dataclass(frozen=True)
class Repository:
    id: str
    url: str
    ref: str
    commit: str
    license: str
    corpus_hash: str


@dataclass(frozen=True)
class Query:
    id: str
    repository: str
    category: str
    text: str
    answerable: bool


@dataclass(frozen=True)
class Target:
    path: str
    qualified_name: str
    start_line: int
    end_line: int

    @property
    def key(self) -> str:
        return stable_id(self.path, self.qualified_name, self.start_line, self.end_line)


@dataclass(frozen=True)
class Judgment:
    query_id: str
    target: Target
    grade: int
    rationale: str


@dataclass(frozen=True)
class Benchmark:
    id: str
    version: str
    split: str
    annotation_status: str
    repositories: tuple[Repository, ...]
    queries: tuple[Query, ...]
    judgments: tuple[Judgment, ...]
    digest: str


def _record(value: object, fields: set[str], context: str) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{context}: expected exactly fields {sorted(fields)}")
    return value


def _string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}: expected a nonblank string")
    return value


def _identifier(value: object, context: str) -> str:
    value = _string(value, context)
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", value):
        raise ValueError(f"{context}: invalid identifier")
    return value


def _relative(value: object, context: str) -> str:
    value = _string(value, context)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value:
        raise ValueError(f"{context}: expected a repository-relative POSIX path")
    if path.as_posix() != value or value == ".":
        raise ValueError(f"{context}: path must be normalized")
    return value


def _json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON at line {error.lineno}") from error


def _jsonl(path: Path) -> list[dict]:
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON") from error
    return records


def load_benchmark(path: Path) -> Benchmark:
    manifest = _record(
        _json(path),
        {
            "schema_version",
            "id",
            "version",
            "split",
            "annotation_status",
            "repositories",
            "queries_file",
            "qrels_file",
        },
        "benchmark",
    )
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("Unsupported benchmark schema_version")
    for key in ("id", "version"):
        _identifier(manifest[key], key)
    if _string(manifest["split"], "split") not in {"dev", "test"}:
        raise ValueError("split must be dev or test")
    if _string(manifest["annotation_status"], "annotation_status") not in {
        "provisional",
        "human_reviewed",
    }:
        raise ValueError("annotation_status must be provisional or human_reviewed")
    if not isinstance(manifest["repositories"], list) or not manifest["repositories"]:
        raise ValueError("repositories must be a nonempty list")
    repositories = []
    for item in manifest["repositories"]:
        item = _record(item, {"id", "url", "ref", "commit", "license", "corpus_hash"}, "repository")
        _identifier(item["id"], "repository id")
        for key in ("url", "ref", "license"):
            _string(item[key], key)
        if not item["url"].startswith("https://"):
            raise ValueError("Repository URL must use HTTPS")
        for key, length in (("commit", 40), ("corpus_hash", 64)):
            if not re.fullmatch(rf"[0-9a-f]{{{length}}}", _string(item[key], key)):
                raise ValueError(f"Invalid repository {key}")
        repositories.append(Repository(**item))
    repository_ids = {item.id for item in repositories}
    if len(repository_ids) != len(repositories):
        raise ValueError("Duplicate repository id")

    def resource(key: str) -> Path:
        relative = _relative(manifest[key], key)
        target = (path.parent / relative).resolve()
        if not target.is_relative_to(path.parent.resolve()):
            raise ValueError(f"{key}: resource must stay within the benchmark directory")
        return target

    query_data = _jsonl(resource("queries_file"))
    judgment_data = _jsonl(resource("qrels_file"))
    queries = []
    for item in query_data:
        item = _record(item, {"id", "repository", "category", "text", "answerable"}, "query")
        _identifier(item["id"], "query id")
        if _string(item["repository"], "query repository") not in repository_ids:
            raise ValueError(f"Unknown query repository: {item['repository']}")
        if _string(item["category"], "category") not in CATEGORIES:
            raise ValueError("Unknown query category")
        _string(item["text"], "query text")
        if type(item["answerable"]) is not bool:
            raise ValueError("answerable must be a boolean")
        queries.append(Query(**item))
    query_ids = {item.id for item in queries}
    if not queries or len(query_ids) != len(queries):
        raise ValueError("Queries must be nonempty and have unique IDs")
    judgments = []
    seen = set()
    for item in judgment_data:
        item = _record(item, {"query_id", "target", "grade", "rationale"}, "judgment")
        if _string(item["query_id"], "judgment query_id") not in query_ids:
            raise ValueError(f"Unknown judgment query: {item['query_id']}")
        if type(item["grade"]) is not int or item["grade"] not in {0, 1, 2}:
            raise ValueError("Relevance grade must be 0, 1, or 2")
        _string(item["rationale"], "rationale")
        target = _record(
            item["target"], {"path", "qualified_name", "start_line", "end_line"}, "target"
        )
        _relative(target["path"], "target path")
        _string(target["qualified_name"], "qualified_name")
        if any(type(target[key]) is not int for key in ("start_line", "end_line")):
            raise ValueError("Target line numbers must be integers")
        if target["start_line"] < 1 or target["end_line"] < target["start_line"]:
            raise ValueError("Invalid target line range")
        locator = Target(**target)
        pair = (item["query_id"], locator.key)
        if pair in seen:
            raise ValueError("Duplicate query/target judgment")
        seen.add(pair)
        judgments.append(Judgment(item["query_id"], locator, item["grade"], item["rationale"]))
    for query in queries:
        has_relevant = any(item.query_id == query.id and item.grade > 0 for item in judgments)
        if has_relevant != query.answerable:
            raise ValueError(f"Answerability and positive judgments disagree for {query.id}")
    return Benchmark(
        manifest["id"],
        manifest["version"],
        manifest["split"],
        manifest["annotation_status"],
        tuple(repositories),
        tuple(queries),
        tuple(judgments),
        stable_id(manifest, query_data, judgment_data),
    )


def symbol_target(symbol: Symbol) -> Target:
    return Target(symbol.path, symbol.qualified_name, symbol.start_line, symbol.end_line)


def corpus_hash(index: LoadedIndex) -> str:
    """Bind labels to selected source bytes and ignore rules, independent of chunking."""
    return stable_id(index.metadata["manifest"], index.metadata["config"]["gitignore_hashes"])


def validate_index(benchmark: Benchmark, repository: Repository, index: LoadedIndex) -> None:
    if index.metadata["git"] != {"commit": repository.commit, "dirty": False}:
        raise ValueError(f"{repository.id}: index must come from the pinned, clean Git checkout")
    if corpus_hash(index) != repository.corpus_hash:
        raise ValueError(
            f"{repository.id}: corpus hash mismatch; check source bytes and file selection"
        )
    if any(item["reason"] != "link_skipped" for item in index.metadata["diagnostics"]):
        raise ValueError(f"{repository.id}: index contains skipped-source diagnostics")
    searchable = {chunk.symbol_id for chunk in index.chunks}
    targets = {symbol_target(symbol).key: symbol.id for symbol in index.symbols.values()}
    queries = {item.id for item in benchmark.queries if item.repository == repository.id}
    for judgment in benchmark.judgments:
        if judgment.query_id in queries:
            symbol_id = targets.get(judgment.target.key)
            if symbol_id not in searchable:
                raise ValueError(
                    f"{judgment.query_id}: target is absent or has no searchable chunks: "
                    f"{judgment.target}"
                )
