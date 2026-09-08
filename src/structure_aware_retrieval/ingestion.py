"""Deterministic filesystem scanning without importing target code."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from pathspec import GitIgnoreSpec

from structure_aware_retrieval.models import Diagnostic, SourceFile

EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "__pycache__",
        ".cache",
        ".pytest_cache",
        ".ruff_cache",
        ".idea",
        ".vscode",
        "node_modules",
        "build",
        "dist",
        "artifacts",
    }
)


@dataclass(frozen=True, slots=True)
class ScanResult:
    files: list[SourceFile]
    diagnostics: list[Diagnostic]
    excluded_entries: int
    ignore_hashes: dict[str, str]


def scan_repository(
    root: Path, *, max_file_bytes: int = 1_048_576, exclude: tuple[str, ...] = ()
) -> ScanResult:
    """Apply nested .gitignore files and additional root-relative ignore patterns.

    Built-in exclusions and links cannot be re-included. Like Git, ignored
    directories are pruned; a child cannot be re-included beneath an ignored parent.
    """
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"Repository must be a directory: {root}")
    if max_file_bytes < 1:
        raise ValueError("max_file_bytes must be positive")
    files: list[SourceFile] = []
    diagnostics: list[Diagnostic] = []
    excluded_entries = 0
    ignore_hashes: dict[str, str] = {}
    additional = GitIgnoreSpec.from_lines(exclude)

    def walk(directory: Path, inherited: list[tuple[Path, GitIgnoreSpec]]) -> None:
        nonlocal excluded_entries
        specs = list(inherited)
        ignore_file = directory / ".gitignore"
        if ignore_file.is_file() and not ignore_file.is_symlink():
            try:
                rules = ignore_file.read_bytes()
                ignore_hashes[ignore_file.relative_to(root).as_posix()] = hashlib.sha256(
                    rules
                ).hexdigest()
                specs.append(
                    (
                        directory,
                        GitIgnoreSpec.from_lines(rules.decode("utf-8-sig").splitlines()),
                    )
                )
            except (OSError, UnicodeError, ValueError) as error:
                raise ValueError(f"Cannot read ignore rules at {ignore_file}: {error}") from error

        try:
            with os.scandir(directory) as entries:
                children = sorted(entries, key=lambda entry: entry.name)
        except OSError as error:
            # An unreadable directory could hide arbitrary source; do not publish
            # a seemingly complete replacement index in that case.
            raise ValueError(f"Cannot scan directory {directory}: {error}") from error

        for entry in children:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            try:
                if path.is_symlink() or path.is_junction():
                    diagnostics.append(
                        Diagnostic(relative, "link_skipped", "Links are not followed")
                    )
                    continue
                is_directory = entry.is_dir(follow_symlinks=False)
                if is_directory and entry.name in EXCLUDED_DIRECTORIES:
                    excluded_entries += 1
                    continue
                suffix = "/" if is_directory else ""
                ignored = False
                for base, spec in specs:
                    match = spec.check_file(path.relative_to(base).as_posix() + suffix)
                    if match.include is not None:
                        ignored = match.include
                if ignored or additional.match_file(relative + suffix):
                    excluded_entries += 1
                    continue
                if is_directory:
                    walk(path, specs)
                elif entry.is_file(follow_symlinks=False) and path.suffix == ".py":
                    if entry.stat(follow_symlinks=False).st_size > max_file_bytes:
                        diagnostics.append(
                            Diagnostic(relative, "too_large", f"Exceeds {max_file_bytes} bytes")
                        )
                        continue
                    with path.open("rb") as handle:
                        data = handle.read(max_file_bytes + 1)
                    if len(data) > max_file_bytes:
                        diagnostics.append(
                            Diagnostic(relative, "too_large", f"Exceeds {max_file_bytes} bytes")
                        )
                        continue
                    files.append(SourceFile(relative, hashlib.sha256(data).hexdigest(), data))
            except OSError as error:
                diagnostics.append(Diagnostic(relative, "read_error", str(error)))

    walk(root, [])
    return ScanResult(files, diagnostics, excluded_entries, ignore_hashes)
