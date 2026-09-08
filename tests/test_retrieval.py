import math

import pytest

from structure_aware_retrieval.indexing import BM25_CONFIG, LoadedIndex
from structure_aware_retrieval.models import Chunk, Symbol
from structure_aware_retrieval.retrieval import BM25Retriever
from structure_aware_retrieval.tokenization import tokenize_code


def retriever_for(documents: dict[str, list[str]]) -> BM25Retriever:
    symbols = {
        key: Symbol(key, f"{key}.py", key, key, "module", None, 1, 1, "", None) for key in documents
    }
    chunks = [
        Chunk(key, key, f"{key}.py", 1, 1, " ".join(tokens)) for key, tokens in documents.items()
    ]
    return BM25Retriever(
        LoadedIndex({"config": {"bm25": BM25_CONFIG}}, symbols, chunks, list(documents.values()))
    )


def test_identifiers_preserve_full_names_and_components() -> None:
    assert tokenize_code("getHTTPResponse send_request café snake_case") == [
        "gethttpresponse",
        "get",
        "http",
        "response",
        "send_request",
        "send",
        "request",
        "café",
        "snake_case",
        "snake",
        "case",
    ]
    assert tokenize_code("timeout timeout") == ["timeout", "timeout"]
    assert tokenize_code("!?()") == []


def test_bm25_scores_match_hand_calculation_and_nonmatches_are_absent() -> None:
    retriever = retriever_for(
        {"a": ["rare", "rare"], "b": ["other", "other"], "c": ["rare", "other"]}
    )
    results = retriever.search("rare")
    assert [item.chunk_id for item in results] == ["a", "c"]
    # N=3, df=2, every length=2: IDF=ln(4/2), TF saturation for tf=2 is 5/3.5.
    assert results[0].score == pytest.approx(math.log(2) * 5 / 3.5)
    assert results[1].score == pytest.approx(math.log(2))
    assert retriever.search("unseen") == []


def test_ties_use_ids_and_query_repetition_does_not_change_scores() -> None:
    retriever = retriever_for({"b": ["match"], "a": ["match"]})
    assert [item.chunk_id for item in retriever.search("match")] == ["a", "b"]
    assert retriever.search("match match") == retriever.search("match")
    assert len(retriever.search("match", top_k=1)) == 1


def test_one_document_empty_corpus_and_invalid_queries() -> None:
    retriever = retriever_for({"a": ["match"]})
    assert retriever.search("match")[0].score > 0
    assert retriever.search("???") == []
    assert retriever_for({}).search("match") == []
    with pytest.raises(ValueError, match="blank"):
        retriever.search("   ")
    with pytest.raises(ValueError, match="positive"):
        retriever.search("match", top_k=0)
