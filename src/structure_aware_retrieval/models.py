"""Snapshot-scoped source objects shared by parsing, indexing, and retrieval."""

import hashlib
import json
from dataclasses import dataclass, field


def stable_id(*parts: object) -> str:
    """Hash explicit JSON components, independent of checkout location."""
    value = json.dumps(parts, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Diagnostic:
    path: str
    reason: str
    message: str


@dataclass(frozen=True, slots=True)
class SourceFile:
    path: str
    content_hash: str
    data: bytes


@dataclass(frozen=True, slots=True)
class Symbol:
    id: str
    path: str
    name: str
    qualified_name: str
    kind: str
    parent_id: str | None
    start_line: int
    end_line: int
    signature: str
    docstring: str | None


@dataclass(frozen=True, slots=True)
class Chunk:
    id: str
    symbol_id: str
    path: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True, slots=True)
class ImportReference:
    symbol_id: str
    module: str
    name: str | None
    alias: str | None
    level: int
    line: int


@dataclass(frozen=True, slots=True)
class ParsedFile:
    symbols: list[Symbol]
    chunks: list[Chunk]
    imports: list[ImportReference]


@dataclass(frozen=True, slots=True)
class SearchResult:
    rank: int
    score: float
    chunk_id: str
    symbol_id: str
    path: str
    qualified_name: str
    kind: str
    start_line: int
    end_line: int
    text: str
    components: dict[str, float] = field(default_factory=dict)
    provenance: list[dict] = field(default_factory=list)
