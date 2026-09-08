"""Budgeted one-hop graph support for a frozen baseline chunk ranking."""

import heapq
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from itertools import islice

from structure_aware_retrieval.models import SearchResult
from structure_aware_retrieval.relations import RELATION_TYPES, Relation, RelationGraph
from structure_aware_retrieval.strategies import Retriever, validate_query

EDGE_WEIGHTS = {"containment": 0.2, "import": 0.3, "call": 1.0, "test": 0.8}


@dataclass(frozen=True)
class StructureConfig:
    seed_strategy: str = "hybrid"
    relations: tuple[str, ...] = RELATION_TYPES
    seed_k: int = 5
    max_neighbors: int = 8
    max_expanded: int = 20
    max_edges: int = 64
    alpha: float = 0.5

    def __post_init__(self) -> None:
        if self.seed_strategy not in ("hybrid", "symbol", "bm25"):
            raise ValueError("Structure seed_strategy must be hybrid, symbol or bm25")
        if (
            not isinstance(self.relations, tuple)
            or any(kind not in RELATION_TYPES for kind in self.relations)
            or len(set(self.relations)) != len(self.relations)
        ):
            raise ValueError("Structure relations must be unique known relation types")
        for name in ("seed_k", "max_neighbors", "max_expanded", "max_edges"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 10000:
                raise ValueError(f"{name} must be an integer in [1, 10000]")
        if (
            type(self.alpha) not in (int, float)
            or not math.isfinite(self.alpha)
            or not 0 <= self.alpha <= 1
        ):
            raise ValueError("Structure alpha must be finite and in [0, 1]")

    def describe(self) -> dict:
        return {
            **asdict(self),
            "edge_weights": EDGE_WEIGHTS,
            "heuristic_discount": 0.5,
            "direction": "both",
            "support": "max",
            "rank_constant": 60,
            "score_policy": "base_score * (1 + alpha * max(weight * 61/(60+seed_rank)))",
            "depth": 1,
            "version": 1,
        }


def parse_structure(value: object) -> StructureConfig:
    if not isinstance(value, dict) or set(value) - set(StructureConfig.__dataclass_fields__):
        raise ValueError("Invalid structure configuration fields")
    fields = dict(value)
    if "relations" in fields:
        if not isinstance(fields["relations"], list):
            raise ValueError("Structure relations must be a list")
        fields["relations"] = tuple(fields["relations"])
    return StructureConfig(**fields)


def edge_weight(edge: Relation) -> float:
    return EDGE_WEIGHTS[edge.kind] * (0.5 if edge.confidence == "heuristic" else 1.0)


class StructureRetriever:
    def __init__(self, base: Retriever, graph: RelationGraph, config: StructureConfig) -> None:
        self.index = base.index
        self.base = base
        self.graph_metadata = graph.metadata
        self.config = config
        self.last_stats: dict[str, int] = {}
        self.adjacency = defaultdict(lambda: defaultdict(list))
        for edge in graph.edges:
            if edge.source == edge.target:
                continue
            for source, target, direction in (
                (edge.source, edge.target, "forward"),
                (edge.target, edge.source, "reverse"),
            ):
                self.adjacency[source][edge.kind].append(
                    (-edge_weight(edge), edge.id, target, direction, edge)
                )
        for types in self.adjacency.values():
            for rows in types.values():
                rows.sort(key=lambda row: (row[0], row[1]))

    def search(self, query: str, *, top_k: int = 5) -> list[SearchResult]:
        validate_query(query, top_k)
        ranked = self.base.search(query, top_k=max(1, len(self.index.chunks)))
        self.last_stats = {
            "base_chunks_scored": len(self.index.chunks),
            "seed_symbols": 0,
            "edges_examined": 0,
            "expanded_symbols": 0,
            "edge_cap_seeds": 0,
        }
        if not self.config.relations or self.config.alpha == 0 or not ranked:
            return ranked[:top_k]
        best = {}
        for hit in ranked:
            best.setdefault(hit.symbol_id, hit)
        seeds = list(best)[: self.config.seed_k]
        seed_ids = set(seeds)
        self.last_stats["seed_symbols"] = len(seeds)
        support: dict[str, list[dict]] = {}
        for seed_rank, seed in enumerate(seeds, 1):
            branches = [self.adjacency[seed][kind] for kind in self.config.relations]
            if sum(map(len, branches)) > self.config.max_edges:
                self.last_stats["edge_cap_seeds"] += 1
            candidates = {}
            for negative_weight, edge_id, target, direction, edge in islice(
                heapq.merge(*branches, key=lambda row: (row[0], row[1])), self.config.max_edges
            ):
                self.last_stats["edges_examined"] += 1
                # BM25-only expansion cannot invent evidence for zero-match symbols.
                if target in seed_ids or target not in best or target in candidates:
                    continue
                candidates[target] = {
                    "seed_symbol_id": seed,
                    "seed_rank": seed_rank,
                    "seed_chunk_id": best[seed].chunk_id,
                    "edge_id": edge_id,
                    "edge": asdict(edge),
                    "direction": direction,
                    "weight": -negative_weight,
                    "support": -negative_weight * 61 / (60 + seed_rank),
                }
            selected = sorted(
                candidates,
                key=lambda target: (-candidates[target]["weight"], best[target].rank, target),
            )[: self.config.max_neighbors]
            for target in selected:
                if target not in support and len(support) >= self.config.max_expanded:
                    continue
                support.setdefault(target, []).append(candidates[target])
        self.last_stats["expanded_symbols"] = len(support)
        adjusted = []
        for hit in ranked:
            traces = support.get(hit.symbol_id)
            if traces and best[hit.symbol_id].chunk_id == hit.chunk_id:
                bonus = hit.score * self.config.alpha * max(trace["support"] for trace in traces)
                adjusted.append(
                    replace(
                        hit,
                        score=hit.score + bonus,
                        provenance=traces,
                        components={
                            **hit.components,
                            "base_score": hit.score,
                            "structure_bonus": bonus,
                        },
                    )
                )
            else:
                adjusted.append(hit)
        adjusted.sort(key=lambda hit: (-hit.score, hit.chunk_id))
        return [replace(hit, rank=rank) for rank, hit in enumerate(adjusted[:top_k], 1)]
