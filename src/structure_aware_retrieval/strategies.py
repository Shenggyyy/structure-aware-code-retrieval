"""Shared retrieval contract, exact dense search, RRF, and explicit symbol features."""

import re
from dataclasses import replace
from pathlib import Path
from typing import Protocol

import numpy as np

from structure_aware_retrieval.embeddings import Encoder, load_vectors, validate_vectors
from structure_aware_retrieval.indexing import LoadedIndex
from structure_aware_retrieval.models import SearchResult, Symbol
from structure_aware_retrieval.retrieval import BM25Retriever
from structure_aware_retrieval.tokenization import tokenize_code

STRATEGIES = ("bm25", "dense", "hybrid", "symbol")
RRF_K = 60
SYMBOL_WEIGHTS = {"qualified": 4.0, "name": 2.0, "name_tokens": 1.0, "signature": 0.5, "path": 0.5}


class Retriever(Protocol):
    index: LoadedIndex

    def search(self, query: str, *, top_k: int = 5) -> list[SearchResult]: ...


def validate_query(query: str, top_k: int) -> None:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if not query.strip():
        raise ValueError("Query must not be blank")


def result_at(
    index: LoadedIndex, position: int, rank: int, score: float, components: dict
) -> SearchResult:
    chunk = index.chunks[position]
    symbol = index.symbols[chunk.symbol_id]
    return SearchResult(
        rank,
        score,
        chunk.id,
        symbol.id,
        chunk.path,
        symbol.qualified_name,
        symbol.kind,
        chunk.start_line,
        chunk.end_line,
        chunk.text,
        components,
    )


class DenseRetriever:
    def __init__(self, index: LoadedIndex, encoder: Encoder, vectors: Path) -> None:
        self.index = index
        self.encoder = encoder
        self.vectors, self.vector_metadata = load_vectors(vectors, index, encoder.spec)

    def search(self, query: str, *, top_k: int = 5) -> list[SearchResult]:
        validate_query(query, top_k)
        if not self.index.chunks or not tokenize_code(query):
            return []
        vector = self.encoder.encode([query])
        validate_vectors(vector, 1, self.encoder.spec["dimensions"])
        # Avoid implicit BLAS thread pools; score every normalized row in float32.
        scores = np.einsum("ij,j->i", self.vectors, vector[0], optimize=False)
        # Cosine can be negative. Dense has no calibrated relevance/abstention threshold.
        positions = sorted(
            range(len(scores)), key=lambda i: (-float(scores[i]), self.index.chunks[i].id)
        )[:top_k]
        return [
            result_at(self.index, i, rank, float(scores[i]), {"cosine": float(scores[i])})
            for rank, i in enumerate(positions, 1)
        ]


def reciprocal_rank_fusion(
    branches: dict[str, list[SearchResult]], top_k: int
) -> list[SearchResult]:
    """Equal-weight RRF over unique chunks, using one-based ranks and stable ties."""
    hits = {}
    components: dict[str, dict[str, float]] = {}
    for name, ranking in branches.items():
        seen = set()
        for hit in ranking:
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            hits[hit.chunk_id] = hit
            values = components.setdefault(hit.chunk_id, {})
            values[f"{name}_rank"] = float(len(seen))
            values[f"{name}_score"] = hit.score
            values[f"{name}_rrf"] = 1.0 / (RRF_K + len(seen))
    scores = {
        key: sum(v for k, v in values.items() if k.endswith("_rrf"))
        for key, values in components.items()
    }
    ordered = sorted(hits, key=lambda key: (-scores[key], key))[:top_k]
    return [
        replace(hits[key], rank=rank, score=scores[key], components=components[key])
        for rank, key in enumerate(ordered, 1)
    ]


def symbol_features(symbol: Symbol, query: str) -> dict[str, float]:
    identifiers = set(re.findall(r"\w+(?:\.\w+)*", query.casefold()))
    words = set(tokenize_code(query))
    qualified = symbol.qualified_name.casefold()

    def overlap(text: str) -> float:
        tokens = set(tokenize_code(text))
        return len(tokens & words) / len(tokens) if tokens else 0.0

    return {
        "qualified": float(
            any(
                "." in name and (qualified == name or qualified.endswith("." + name))
                for name in identifiers
            )
        ),
        "name": float(
            symbol.name.casefold() in {part for name in identifiers for part in name.split(".")}
        ),
        "name_tokens": overlap(symbol.name),
        "signature": overlap(symbol.signature),
        "path": overlap(symbol.path),
    }


class FusionRetriever:
    def __init__(
        self, index: LoadedIndex, dense: DenseRetriever, *, symbol_aware: bool = False
    ) -> None:
        self.index = index
        self.bm25 = BM25Retriever(index)
        self.dense = dense
        self.symbol_aware = symbol_aware

    def search(self, query: str, *, top_k: int = 5) -> list[SearchResult]:
        validate_query(query, top_k)
        depth = max(1, len(self.index.chunks))
        branches = {
            "bm25": self.bm25.search(query, top_k=depth),
            "dense": self.dense.search(query, top_k=depth),
        }
        if self.symbol_aware:
            features = {
                key: symbol_features(symbol, query) for key, symbol in self.index.symbols.items()
            }
            scores = {
                key: sum(SYMBOL_WEIGHTS[name] * value for name, value in row.items())
                for key, row in features.items()
            }
            positions = sorted(
                (i for i, chunk in enumerate(self.index.chunks) if scores[chunk.symbol_id] > 0),
                key=lambda i: (-scores[self.index.chunks[i].symbol_id], self.index.chunks[i].id),
            )
            branches["symbol"] = [
                result_at(self.index, i, rank, scores[self.index.chunks[i].symbol_id], {})
                for rank, i in enumerate(positions, 1)
            ]
        return reciprocal_rank_fusion(branches, top_k)


def create_retriever(
    strategy: str,
    index: LoadedIndex,
    *,
    encoder: Encoder | None = None,
    vectors: Path | None = None,
) -> Retriever:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")
    if strategy == "bm25":
        return BM25Retriever(index)
    if encoder is None or vectors is None:
        raise ValueError("Dense, hybrid and symbol strategies require a model and vector file")
    dense = DenseRetriever(index, encoder, vectors)
    if strategy == "dense":
        return dense
    return FusionRetriever(index, dense, symbol_aware=strategy == "symbol")
