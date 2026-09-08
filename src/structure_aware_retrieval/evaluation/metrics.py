"""Pure ranking metrics with explicit duplicate and incomplete-judgment policies."""

import math
from collections.abc import Mapping, Sequence

QUALITY_METRICS = ("precision", "recall", "mrr", "ndcg")


def validate_ks(ks: Sequence[int]) -> tuple[int, ...]:
    if not ks or any(type(k) is not int or k < 1 for k in ks) or len(set(ks)) != len(ks):
        raise ValueError("K values must be unique positive integers")
    return tuple(sorted(ks))


def evaluate_ranking(
    ranking: Sequence[str], judgments: Mapping[str, int], ks: Sequence[int]
) -> dict[int, dict[str, float | int | None]]:
    ks = validate_ks(ks)
    if any(type(grade) is not int or grade not in {0, 1, 2} for grade in judgments.values()):
        raise ValueError("Relevance grades must be 0, 1, or 2")
    unique = list(dict.fromkeys(ranking))
    relevant = sum(grade > 0 for grade in judgments.values())
    ideal = sorted(judgments.values(), reverse=True)
    results = {}
    for k in ks:
        retrieved = unique[:k]
        grades = [judgments.get(key, 0) for key in retrieved]
        hits = sum(grade > 0 for grade in grades)
        first = next((rank for rank, grade in enumerate(grades, 1) if grade > 0), None)
        dcg = sum((2**grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(grades, 1))
        idcg = sum((2**grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(ideal[:k], 1))
        judged = sum(key in judgments for key in retrieved)
        results[k] = {
            "precision": hits / k if relevant else None,
            "recall": hits / relevant if relevant else None,
            "mrr": (1 / first if first else 0.0) if relevant else None,
            "ndcg": dcg / idcg if idcg else None,
            "returned": len(retrieved),
            "unjudged": len(retrieved) - judged,
            "judged_fraction": judged / len(retrieved) if retrieved else 0.0,
        }
    return results


def percentile(values: Sequence[float], fraction: float) -> float:
    """Linearly interpolate between sorted samples; no platform-specific estimator."""
    if not values or not 0 <= fraction <= 1:
        raise ValueError("A nonempty sample and a fraction in [0, 1] are required")
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
