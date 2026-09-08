"""A lexical baseline over persisted code chunks."""

from pathlib import Path

from rank_bm25 import BM25Plus

from structure_aware_retrieval.indexing import BM25_CONFIG, LoadedIndex, load_index
from structure_aware_retrieval.models import SearchResult
from structure_aware_retrieval.tokenization import tokenize_code


class BM25Retriever:
    """Reconstruct term statistics once per load, then reuse them across queries.

    BM25Plus with delta=0 uses positive IDF even in tiny corpora, while nonmatching
    documents receive zero. This variant and its parameters are recorded explicitly.
    """

    def __init__(self, index: LoadedIndex) -> None:
        self.index = index
        if index.metadata["config"]["bm25"] != BM25_CONFIG:
            raise ValueError("Unsupported BM25 configuration; rebuild the index")
        self.model = (
            BM25Plus(index.tokens, k1=BM25_CONFIG["k1"], b=BM25_CONFIG["b"], delta=0.0)
            if index.tokens and any(index.tokens)
            else None
        )

    @classmethod
    def from_path(cls, path: Path) -> "BM25Retriever":
        return cls(load_index(path))

    def search(self, query: str, *, top_k: int = 5) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if not query.strip():
            raise ValueError("Query must not be blank")
        # Repeated words or expansions do not accidentally boost query weights.
        query_tokens = list(dict.fromkeys(tokenize_code(query)))
        if not query_tokens or self.model is None:
            return []
        scores = self.model.get_scores(query_tokens)
        candidates = sorted(
            (index for index, score in enumerate(scores) if score > 0),
            key=lambda index: (-float(scores[index]), self.index.chunks[index].id),
        )[:top_k]
        results = []
        for rank, position in enumerate(candidates, start=1):
            chunk = self.index.chunks[position]
            symbol = self.index.symbols[chunk.symbol_id]
            results.append(
                SearchResult(
                    rank,
                    float(scores[position]),
                    chunk.id,
                    symbol.id,
                    chunk.path,
                    symbol.qualified_name,
                    symbol.kind,
                    chunk.start_line,
                    chunk.end_line,
                    chunk.text,
                )
            )
        return results
