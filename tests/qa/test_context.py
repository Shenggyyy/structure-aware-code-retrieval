import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from structure_aware_retrieval.indexing import LoadedIndex, build_index, load_index
from structure_aware_retrieval.models import Chunk, SearchResult, Symbol, stable_id
from structure_aware_retrieval.qa.citations import audit_evidence
from structure_aware_retrieval.qa.context import pack_context
from structure_aware_retrieval.retrieval import BM25Retriever


def make_index(*sources: tuple[str, str, int, str], snapshot: str = "snapshot"):
    """A source is (symbol name, path, first physical line, source text)."""
    index = LoadedIndex({"snapshot_id": snapshot}, {}, [], [])
    hits = []
    for name, path, start, text in sources:
        end = start + text.count("\n") - int(text.endswith("\n"))
        symbol_id = stable_id(snapshot, name)
        if symbol_id in index.symbols:
            original = index.symbols[symbol_id]
            symbol = replace(
                original,
                start_line=min(start, original.start_line),
                end_line=max(end, original.end_line),
            )
        else:
            symbol = Symbol(symbol_id, path, name, name, "function", None, start, end, "", None)
        index.symbols[symbol_id] = symbol
        chunk_id = stable_id(snapshot, symbol_id, start, end)
        index.chunks.append(Chunk(chunk_id, symbol_id, path, start, end, text))
        hits.append(
            SearchResult(
                len(hits) + 1, 1.0, chunk_id, symbol_id, path, name, "function", start, end, text
            )
        )
    return index, hits


def llm_fields(item):
    return {
        key: item[key] for key in ("id", "path", "qualified_name", "start_line", "end_line", "text")
    }


def test_exact_serialized_bytes_unicode_escapes_and_stable_fingerprint():
    index, hits = make_index(("emoji", 'src/字".py', 9, 'text = "字😀\\\t"\nreturn text\n'))
    full = pack_context(index, hits)
    limit = len(full["context_text"].encode("utf-8"))
    exact = pack_context(index, hits, max_context_bytes=limit)
    assert exact["evidence"] == full["evidence"]
    assert exact["budget"]["used_context_bytes"] == limit
    assert json.loads(exact["context_text"]) == [llm_fields(exact["evidence"][0])]
    assert "字" in exact["context_text"]
    assert exact == pack_context(index, hits, max_context_bytes=limit)
    assert exact["context_fingerprint"] != full["context_fingerprint"]
    assert exact["evidence"][0]["text_sha256"] == hashlib.sha256(hits[0].text.encode()).hexdigest()
    smaller = pack_context(index, hits, max_context_bytes=limit - 1)
    assert smaller["evidence"][0]["text"] == 'text = "字😀\\\t"\n'
    assert smaller["evidence"][0]["end_line"] == 9
    assert smaller["evidence"][0]["truncated"]
    assert smaller["selection"]["truncated"] == 1
    assert smaller["budget"]["used_context_bytes"] <= limit - 1


def test_unicode_separator_is_not_a_physical_source_line():
    index, hits = make_index(("separator", "a.py", 1, "text = 'a\u2028b\u0085c'\nreturn text"))
    result = pack_context(index, hits)
    assert result["evidence"][0]["end_line"] == 2
    assert result["evidence"][0]["text"] == hits[0].text


def test_canonical_posix_filename_with_colon_is_preserved():
    index, hits = make_index(("valid", "pkg/a:b.py", 1, "return 1\n"))
    context = pack_context(index, hits)
    assert context["evidence"][0]["path"] == "pkg/a:b.py"
    assert audit_evidence(context["evidence"])["paths_valid"] is True


@pytest.mark.parametrize("path", ["C:/absolute.py", "C:relative.py"])
def test_windows_drive_paths_cannot_be_canonical_repository_targets(path):
    index, hits = make_index(("invalid", path, 1, "return 1\n"))
    with pytest.raises(ValueError, match="source path"):
        pack_context(index, hits)


def test_unfittable_first_line_does_not_prevent_lower_ranked_evidence():
    index, hits = make_index(("giant", "big.py", 1, "x" * 1000 + "\n"), ("small", "s.py", 1, "x\n"))
    result = pack_context(index, hits, max_context_bytes=150)
    assert [item["qualified_name"] for item in result["evidence"]] == ["small"]
    assert result["evidence"][0]["id"] == "S1"
    assert result["selection"]["budget"] == 1
    assert result["selection"]["dropped"] == 1


def test_duplicate_symbol_uses_first_hit_even_when_it_cannot_fit():
    index, hits = make_index(("long", "a.py", 1, "x" * 1000 + "\n"), ("long", "a.py", 2, "x\n"))
    result = pack_context(index, hits, max_context_bytes=150)
    assert result["evidence"] == []
    assert result["selection"]["budget"] == 1
    assert result["selection"]["duplicate_symbol"] == 1
    assert result["selection"]["dropped"] == 2


def test_preserve_input_order_deduplicate_symbols_and_count_selection_limit():
    index, hits = make_index(
        ("a", "a.py", 1, "a\n"),
        ("a", "a.py", 2, "b\n"),
        ("c", "c.py", 1, "c\n"),
        ("d", "d.py", 1, "d\n"),
    )
    result = pack_context(index, [hits[2], hits[1], hits[0], hits[3]], top_k=2)
    assert [item["qualified_name"] for item in result["evidence"]] == ["c", "a"]
    assert [item["id"] for item in result["evidence"]] == ["S1", "S2"]
    assert result["evidence"][1]["start_line"] == 2
    assert result["selection"] == {
        "input_hits": 4,
        "selected": 2,
        "truncated": 0,
        "dropped": 2,
        "duplicate_symbol": 1,
        "overlap": 0,
        "budget": 0,
        "limit": 1,
    }


def test_overlapping_ranges_are_skipped_but_adjacent_or_different_paths_are_retained():
    index, hits = make_index(
        ("a", "same.py", 2, "a\nb\n"),
        ("b", "same.py", 1, "c\nd\n"),
        ("c", "same.py", 4, "e\n"),
        ("d", "different.py", 2, "f\n"),
    )
    result = pack_context(index, hits)
    assert [item["qualified_name"] for item in result["evidence"]] == ["a", "c", "d"]
    assert result["selection"]["overlap"] == 1


def test_hit_display_metadata_cannot_override_canonical_evidence():
    index, hits = make_index(("canonical", "src/real.py", 3, "return 42\n"))
    forged = replace(
        hits[0], path="secret.txt", qualified_name="forged", start_line=99, end_line=99, text="fake"
    )
    result = pack_context(index, [forged])
    item = result["evidence"][0]
    assert item["path"] == "src/real.py"
    assert item["qualified_name"] == "canonical"
    assert item["start_line"] == item["end_line"] == 3
    assert item["text"] == "return 42\n"


def test_unknown_stale_and_mismatched_identities_rejected_even_after_limit():
    index, hits = make_index(("a", "a.py", 1, "a\n"))
    _, stale_hits = make_index(("a", "a.py", 1, "a\n"), snapshot="old")
    for invalid in [replace(hits[0], chunk_id="unknown"), stale_hits[0]]:
        with pytest.raises(ValueError, match="Unknown or stale"):
            pack_context(index, [hits[0], invalid], top_k=1)
    with pytest.raises(ValueError, match="symbol ID"):
        pack_context(index, [replace(hits[0], symbol_id="wrong")])
    with pytest.raises(ValueError, match="snapshot"):
        pack_context(replace(index, metadata={"snapshot_id": "wrong"}), hits)


@pytest.mark.parametrize("budget", [True, 0, 1, -1, 1_000_001, 2.0, "200"])
def test_invalid_budget_is_rejected(budget):
    index, hits = make_index()
    with pytest.raises(ValueError, match="max_context_bytes"):
        pack_context(index, hits, max_context_bytes=budget)


@pytest.mark.parametrize("limit", [True, 0, -1, 1.0])
def test_invalid_selection_limit_is_rejected(limit):
    index, hits = make_index()
    with pytest.raises(ValueError, match="top_k"):
        pack_context(index, hits, top_k=limit)


def test_empty_evidence_and_minimum_budget():
    index, hits = make_index(("a", "a.py", 1, "a\n"))
    for candidates in [[], hits]:
        result = pack_context(index, candidates, max_context_bytes=2)
        assert result["context_text"] == "[]"
        assert result["budget"]["used_context_bytes"] == 2
        assert result["evidence"] == []
    with pytest.raises(ValueError, match="snapshot_id"):
        pack_context(replace(index, metadata={}), [])


def test_corrupt_canonical_index_metadata_is_rejected():
    index, hits = make_index(("a", "a.py", 1, "a\n"))
    with pytest.raises(ValueError, match="duplicate chunk"):
        pack_context(replace(index, chunks=index.chunks * 2), hits)
    with pytest.raises(ValueError, match="unknown symbol"):
        pack_context(replace(index, symbols={}), hits)
    chunk = index.chunks[0]
    with pytest.raises(ValueError, match="metadata"):
        pack_context(replace(index, chunks=[replace(chunk, path="different.py")]), hits)
    with pytest.raises(ValueError, match="source line range"):
        pack_context(replace(index, chunks=[replace(chunk, text="a\nb\n")]), hits)


def test_uses_saved_source_after_checkout_changes(sample_repository: Path, tmp_path: Path):
    database = tmp_path / "index.sqlite"
    build_index(sample_repository, database)
    index = load_index(database)
    hits = BM25Retriever(index).search("calculate_checksum", top_k=4)
    expected = pack_context(index, hits)
    for path in sample_repository.glob("*.py"):
        path.write_text("# changed\n", encoding="utf-8")
    assert pack_context(load_index(database), hits) == expected
    assert "calculate_checksum" in expected["context_text"]
