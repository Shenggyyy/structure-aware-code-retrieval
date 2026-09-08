from dataclasses import replace

import pytest

from structure_aware_retrieval.indexing import LoadedIndex
from structure_aware_retrieval.models import Chunk, SearchResult, Symbol
from structure_aware_retrieval.relations import Relation, RelationGraph
from structure_aware_retrieval.structure import StructureConfig, StructureRetriever, parse_structure


class RankedFixture:
    def __init__(self):
        self.index = LoadedIndex({}, {}, [], [])
        self.hits = []
        for n, key in enumerate("abcdef", 1):
            self.index.symbols[key] = Symbol(
                key, f"{key}.py", key, key, "function", None, 1, 1, "", None
            )
            self.index.chunks.append(Chunk(key, key, f"{key}.py", 1, 1, key))
            self.hits.append(
                SearchResult(
                    n, 1 - (n - 1) * 0.1, key, key, f"{key}.py", key, "function", 1, 1, key
                )
            )

    def search(self, query, *, top_k=5):
        return self.hits[:top_k]


def edge(source, target, kind="call", confidence="static"):
    return Relation(source, target, kind, confidence, f"{source}.py", 1, target)


def test_no_edges_and_zero_alpha_are_exact_controls():
    base = RankedFixture()
    graph = RelationGraph({}, (edge("a", "d"),), ())
    for config in (StructureConfig(relations=()), StructureConfig(alpha=0)):
        retriever = StructureRetriever(base, graph, config)
        assert retriever.search("query", top_k=6) == base.hits
        assert retriever.last_stats["expanded_symbols"] == 0


def test_one_hop_max_support_reverse_edges_and_trace():
    base = RankedFixture()
    graph = RelationGraph({}, (edge("a", "d"), edge("a", "d", "import"), edge("d", "f")), ())
    retriever = StructureRetriever(base, graph, StructureConfig(seed_k=1))
    hits = retriever.search("query", top_k=6)
    promoted = next(hit for hit in hits if hit.symbol_id == "d")
    assert promoted.score == pytest.approx(0.7 * 1.5)
    assert promoted.rank == 1
    assert len(promoted.provenance) == 1
    trace = promoted.provenance[0]
    assert trace["seed_symbol_id"] == trace["seed_chunk_id"] == "a"
    assert trace["edge_id"] == edge("a", "d").id
    assert next(hit for hit in hits if hit.symbol_id == "f").score == 0.5
    reverse = StructureRetriever(
        base, RelationGraph({}, (edge("d", "a"),), ()), StructureConfig(seed_k=1)
    )
    assert reverse.search("query")[0].provenance[0]["direction"] == "reverse"


def test_budgets_and_relation_ablation_bound_work():
    base = RankedFixture()
    graph = RelationGraph({}, tuple(edge("a", target) for target in "bcdef"), ())
    retriever = StructureRetriever(
        base, graph, StructureConfig(seed_k=1, max_edges=3, max_neighbors=2, max_expanded=1)
    )
    retriever.search("query", top_k=6)
    assert retriever.last_stats["edges_examined"] == 3
    assert retriever.last_stats["expanded_symbols"] == 1
    assert retriever.last_stats["edge_cap_seeds"] == 1
    ablated = StructureRetriever(base, graph, StructureConfig(relations=("import",)))
    assert ablated.search("query", top_k=6) == base.hits


def test_duplicate_chunks_seed_once_and_boost_only_best_evidence():
    base = RankedFixture()
    base.hits.insert(1, replace(base.hits[0], chunk_id="a2", score=0.95))
    base.index.chunks.append(Chunk("a2", "a", "a.py", 1, 1, "a"))
    base.hits.append(replace(base.hits[4], chunk_id="d2", score=0.1))
    base.index.chunks.append(Chunk("d2", "d", "d.py", 1, 1, "d"))
    graph = RelationGraph({}, (edge("a", "d"), edge("b", "d")), ())
    retriever = StructureRetriever(base, graph, StructureConfig(seed_k=2))
    hits = retriever.search("query", top_k=8)
    promoted = [hit for hit in hits if hit.provenance]
    assert len(promoted) == 1
    assert len(promoted[0].provenance) == 2
    assert promoted[0].score == pytest.approx(1.05)  # max support, not sum of two seeds
    assert retriever.last_stats["seed_symbols"] == 2


@pytest.mark.parametrize(
    "values",
    [
        {"alpha": float("nan")},
        {"alpha": -1},
        {"max_edges": 0},
        {"seed_k": True},
        {"relations": ["call", "call"]},
        {"relations": ["unknown"]},
        {"seed_strategy": "structure"},
        {"unknown": 1},
    ],
)
def test_invalid_policy_rejected(values):
    with pytest.raises(ValueError):
        parse_structure(values)
