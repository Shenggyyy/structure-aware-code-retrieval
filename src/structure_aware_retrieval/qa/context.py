"""Pack ranked snapshot evidence into an exact UTF-8 byte budget."""

import hashlib
import io
import json

from structure_aware_retrieval.indexing import LoadedIndex
from structure_aware_retrieval.models import Chunk, SearchResult, Symbol, stable_id
from structure_aware_retrieval.qa.citations import validate_source_target

CONTEXT_VERSION = 1
MAX_CONTEXT_BYTES = 1_000_000
SELECTION_POLICY = "input_order_first_symbol_skip_overlaps_complete_line_prefix"


def _serialize(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _validate_chunk(chunk: Chunk, symbol: Symbol, snapshot_id: str) -> list[str]:
    validate_source_target(
        {
            "path": chunk.path,
            "qualified_name": symbol.qualified_name,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
        }
    )
    if chunk.id != stable_id(snapshot_id, chunk.symbol_id, chunk.start_line, chunk.end_line):
        raise ValueError("Chunk does not belong to the index snapshot")
    if (
        symbol.id != chunk.symbol_id
        or chunk.path != symbol.path
        or not symbol.start_line <= chunk.start_line <= chunk.end_line <= symbol.end_line
    ):
        raise ValueError("Invalid canonical chunk/symbol metadata")
    # StringIO follows the parser's physical newline convention. str.splitlines
    # would incorrectly split Unicode separators inside source string literals.
    lines = io.StringIO(chunk.text).readlines()
    if len(lines) != chunk.end_line - chunk.start_line + 1:
        raise ValueError("Canonical chunk text does not match its source line range")
    return lines


def _render(
    chunk: Chunk, symbol: Symbol, lines: list[str], line_count: int, citation_id: str
) -> tuple[dict, str]:
    item = {
        "id": citation_id,
        "path": chunk.path,
        "qualified_name": symbol.qualified_name,
        "start_line": chunk.start_line,
        "end_line": chunk.start_line + line_count - 1,
        "text": "".join(lines[:line_count]),
    }
    return item, _serialize(item)


def pack_context(
    index: LoadedIndex,
    hits: list[SearchResult],
    *,
    max_context_bytes: int = 16_000,
    top_k: int = 10,
) -> dict:
    """Select canonical chunks in input order, with at most one chunk per symbol.

    The first hit claims its symbol even when that chunk cannot fit. A candidate
    overlapping any selected source range is skipped in full. Otherwise keep
    its longest complete-line prefix that fits, then consider lower-ranked hits.
    All hit identities are checked, including hits after the selection limit.
    The budget covers the serialized evidence list, not the full LLM prompt or
    model tokens. No source checkout, model, clock, or network is consulted.
    """
    if type(max_context_bytes) is not int or not 2 <= max_context_bytes <= MAX_CONTEXT_BYTES:
        raise ValueError(f"max_context_bytes must be an integer from 2 to {MAX_CONTEXT_BYTES}")
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    snapshot_id = index.metadata.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("Index snapshot_id is required")
    chunks = {chunk.id: chunk for chunk in index.chunks}
    if len(chunks) != len(index.chunks):
        raise ValueError("Index contains duplicate chunk identities")

    candidates = []
    for hit in hits:
        chunk = chunks.get(hit.chunk_id)
        if chunk is None:
            raise ValueError(f"Unknown or stale chunk ID: {hit.chunk_id}")
        if hit.symbol_id != chunk.symbol_id:
            raise ValueError("Retrieved symbol ID does not match the indexed chunk")
        symbol = index.symbols.get(chunk.symbol_id)
        if symbol is None:
            raise ValueError("Indexed chunk refers to an unknown symbol")
        candidates.append((chunk, symbol, _validate_chunk(chunk, symbol, snapshot_id)))

    evidence: list[dict] = []
    serialized: list[str] = []
    seen_symbols: set[str] = set()
    covered: dict[str, list[tuple[int, int]]] = {}
    used_bytes = 2  # Empty JSON list, including its brackets.
    selection = {
        "input_hits": len(hits),
        "selected": 0,
        "truncated": 0,
        "dropped": 0,
        "duplicate_symbol": 0,
        "overlap": 0,
        "budget": 0,
        "limit": 0,
    }
    for chunk, symbol, lines in candidates:
        if symbol.id in seen_symbols:
            selection["duplicate_symbol"] += 1
            continue
        seen_symbols.add(symbol.id)
        if len(evidence) >= top_k:
            selection["limit"] += 1
            continue
        if any(
            start <= chunk.end_line and chunk.start_line <= end
            for start, end in covered.get(chunk.path, [])
        ):
            selection["overlap"] += 1
            continue

        # Serialized size increases with every complete physical line. Binary
        # search avoids repeatedly serializing the already-selected context.
        low, high = 1, len(lines)
        best: tuple[dict, str] | None = None
        comma_bytes = int(bool(evidence))
        while low <= high:
            count = (low + high) // 2
            item, value = _render(chunk, symbol, lines, count, f"S{len(evidence) + 1}")
            if used_bytes + comma_bytes + len(value.encode("utf-8")) <= max_context_bytes:
                best = item, value
                low = count + 1
            else:
                high = count - 1
        if best is None:
            selection["budget"] += 1
            continue
        item, value = best
        truncated = item["end_line"] < chunk.end_line
        used_bytes += comma_bytes + len(value.encode("utf-8"))
        serialized.append(value)
        covered.setdefault(chunk.path, []).append((item["start_line"], item["end_line"]))
        evidence.append(
            {
                **item,
                "chunk_id": chunk.id,
                "symbol_id": symbol.id,
                "text_sha256": hashlib.sha256(item["text"].encode("utf-8")).hexdigest(),
                "truncated": truncated,
            }
        )
        selection["truncated"] += int(truncated)

    selection["selected"] = len(evidence)
    selection["dropped"] = len(hits) - len(evidence)
    config = {
        "max_context_bytes": max_context_bytes,
        "top_k": top_k,
        "policy": SELECTION_POLICY,
        "serialization": "compact_sorted_json_utf8",
    }
    return {
        "schema_version": CONTEXT_VERSION,
        "snapshot_id": snapshot_id,
        "budget": {
            "max_context_bytes": max_context_bytes,
            "used_context_bytes": used_bytes,
            "unit": "utf8_bytes",
        },
        "config": config,
        "selection": selection,
        "evidence": evidence,
        "context_text": "[" + ",".join(serialized) + "]",
        "context_fingerprint": stable_id(CONTEXT_VERSION, snapshot_id, config, evidence),
    }
