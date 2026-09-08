"""Deterministic synthetic vectors test mechanics, never real embedding quality."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.embeddings import build_vectors, canonical_texts, load_vectors
from structure_aware_retrieval.indexing import BM25_CONFIG, LoadedIndex
from structure_aware_retrieval.models import Chunk, Symbol
from structure_aware_retrieval.strategies import (
    DenseRetriever,
    create_retriever,
    reciprocal_rank_fusion,
    symbol_features,
)
from structure_aware_retrieval.tokenization import tokenize_code


class FakeEncoder:
    spec = {"id": "synthetic", "dimensions": 2, "max_seq_length": 4, "revision": "fixture"}

    def encode(self, texts: list[str]) -> np.ndarray:
        values = [[1, 0] if "alpha" in text else [0, 1] for text in texts]
        return np.asarray(values, dtype=np.float32).reshape(-1, 2)

    def token_lengths(self, texts: list[str]) -> list[int]:
        return [len(text.split()) for text in texts]


@pytest.fixture
def vector_fixture(tmp_path: Path):
    symbols = {
        key: Symbol(key, "client.py", key, f"client.{key}", "function", None, n, n, key, None)
        for n, key in enumerate(("beta", "alpha", "alphabet"), 1)
    }
    chunks = [Chunk(key, key, "client.py", n, n, key) for n, key in enumerate(symbols, 1)]
    index = LoadedIndex(
        {"snapshot_id": "test", "config": {"bm25": BM25_CONFIG}}, symbols, chunks, []
    )
    index.tokens.extend(tokenize_code(text) for text in canonical_texts(index))
    encoder = FakeEncoder()
    path = tmp_path / "vectors.npz"
    build_vectors(index, encoder, path)
    return index, encoder, path


def test_exact_cosine_order_ties_negative_scores_and_input_validation(vector_fixture):
    index, encoder, path = vector_fixture
    dense = DenseRetriever(index, encoder, path)
    assert [hit.chunk_id for hit in dense.search("alpha")] == ["alpha", "alphabet", "beta"]
    assert [hit.score for hit in dense.search("alpha")] == [1, 1, 0]
    assert dense.search("beta", top_k=1)[0].chunk_id == "beta"
    assert dense.search("!!!") == []
    with pytest.raises(ValueError, match="blank"):
        dense.search(" ")
    with pytest.raises(ValueError, match="positive"):
        dense.search("alpha", top_k=0)
    encoder.encode = lambda texts: np.array([[-1, 0]], dtype=np.float32)
    assert [hit.score for hit in dense.search("alpha")] == [0, -1, -1]


def test_vector_roundtrip_binding_corruption_and_no_overwrite(vector_fixture):
    index, encoder, path = vector_fixture
    vectors, metadata = load_vectors(path, index, encoder.spec)
    assert vectors.shape == (3, 2)
    assert metadata["documents"] == 3
    assert metadata["truncated_documents"] == 0
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        build_vectors(index, encoder, path)
    assert path.read_bytes() == original
    with pytest.raises(ValueError, match="cache mismatch"):
        load_vectors(path, index, {**encoder.spec, "revision": "different"})
    changed = replace(index, chunks=list(reversed(index.chunks)))
    with pytest.raises(ValueError, match="cache mismatch"):
        load_vectors(path, changed, encoder.spec)
    changed = replace(index, chunks=[replace(index.chunks[0], text="changed"), *index.chunks[1:]])
    with pytest.raises(ValueError, match="cache mismatch"):
        load_vectors(path, changed, encoder.spec)
    vectors[0] = [1, 0]
    np.savez(
        path, vectors=vectors, metadata=np.frombuffer(json.dumps(metadata).encode(), dtype=np.uint8)
    )
    with pytest.raises(ValueError, match="checksum"):
        load_vectors(path, index, encoder.spec)


@pytest.mark.parametrize("case", ["nan", "zero", "shape", "dtype"])
def test_bad_encoder_outputs_never_publish(vector_fixture, tmp_path: Path, case: str):
    index, encoder, _ = vector_fixture
    values = encoder.encode(canonical_texts(index))
    if case == "nan":
        values[0, 0] = np.nan
    elif case == "zero":
        values[0] = 0
    elif case == "shape":
        values = values[:1]
    else:
        values = values.astype(np.float64)
    encoder.encode = lambda texts: values
    output = tmp_path / "bad.npz"
    with pytest.raises(ValueError):
        build_vectors(index, encoder, output)
    assert not output.exists()


def test_empty_vectors_and_publication_failure_cleanup(vector_fixture, tmp_path: Path, monkeypatch):
    index, encoder, _ = vector_fixture
    empty = replace(index, chunks=[], tokens=[])
    output = tmp_path / "empty.npz"
    build_vectors(empty, encoder, output)
    assert DenseRetriever(empty, encoder, output).search("alpha") == []

    def fail(*args):
        raise OSError("simulated publish failure")

    monkeypatch.setattr("structure_aware_retrieval.embeddings.os.link", fail)
    before = set(tmp_path.iterdir())
    with pytest.raises(OSError, match="simulated"):
        build_vectors(index, encoder, tmp_path / "failed.npz")
    assert set(tmp_path.iterdir()) == before


def test_rrf_hand_calculation_and_duplicate_votes(vector_fixture):
    index, encoder, path = vector_fixture
    hits = DenseRetriever(index, encoder, path).search("alpha")
    a, b = hits[:2]
    fused = reciprocal_rank_fusion({"one": [a, a, b], "two": [b, a]}, 5)
    assert [hit.chunk_id for hit in fused] == ["alpha", "alphabet"]
    assert fused[0].score == pytest.approx(1 / 61 + 1 / 62)
    assert fused[1].score == fused[0].score
    assert fused[0].components["two_rank"] == 2


def test_symbol_features_match_boundaries_qualified_suffix_and_fields():
    symbol = Symbol(
        "a",
        "src/client.py",
        "send_request",
        "src.client.Client.send_request",
        "method",
        None,
        1,
        4,
        "send_request(self, timeout)",
        None,
    )
    features = symbol_features(symbol, "Client.send_request timeout client")
    assert features["qualified"] == features["name"] == features["name_tokens"] == 1
    assert features["signature"] > 0
    assert features["path"] > 0
    assert symbol_features(symbol, "send_request_extra")["name"] == 0
    assert symbol_features(symbol, "OtherClient.send_request")["qualified"] == 0


@pytest.mark.parametrize("strategy", ["bm25", "dense", "hybrid", "symbol"])
def test_shared_contract_and_stable_full_ranking(vector_fixture, strategy):
    index, encoder, path = vector_fixture
    retriever = create_retriever(strategy, index, encoder=encoder, vectors=path)
    results = retriever.search("alpha")
    assert results == retriever.search("alpha")
    assert len({hit.chunk_id for hit in results}) == len(results)
    assert all(hit.path == "client.py" and hit.start_line >= 1 for hit in results)
    assert retriever.search("alpha", top_k=1) == results[:1]
    if strategy in ("hybrid", "symbol"):
        assert "dense_rrf" in results[0].components
    if strategy == "symbol":
        assert "symbol_rrf" in results[0].components


def test_cli_rejects_missing_vectors_and_unknown_strategy_before_model_load():
    for args in (["--strategy", "dense"], ["--strategy", "invalid"]):
        result = CliRunner().invoke(app, ["search", "alpha", *args])
        assert result.exit_code == 1
        assert "Traceback" not in result.output
