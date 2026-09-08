"""Paired repository-cluster bootstrap for the query-macro quality difference."""

import math
import random
import statistics
from collections import defaultdict

from structure_aware_retrieval.evaluation.metrics import percentile

MIN_REPOSITORIES = 5  # Reporting policy, not a guarantee of reliable coverage.


def validate_bootstrap(samples: int, seed: int) -> None:
    if type(samples) is not int or not 100 <= samples <= 20_000:
        raise ValueError("bootstrap samples must be an integer from 100 to 20000")
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise ValueError("bootstrap seed must be an integer from 0 to 2**32 - 1")


def paired_statistics(
    differences: dict[str, float],
    repositories: dict[str, str],
    *,
    samples: int = 2000,
    seed: int = 0,
) -> dict:
    """Resample whole repositories, retaining every query and its paired difference.

    Each replicate is sum(selected cluster sums) / sum(selected cluster sizes).
    This estimates the query-weighted difference; averaging cluster means would
    estimate a different quantity when repositories have unequal query counts.
    """
    validate_bootstrap(samples, seed)
    groups = defaultdict(list)
    for query_id, value in sorted(differences.items()):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("Paired differences must be finite numbers")
        if query_id not in repositories or not isinstance(repositories[query_id], str):
            raise ValueError("Every paired query needs a repository")
        groups[repositories[query_id]].append(value)
    groups = dict(sorted(groups.items()))
    result = {
        "query_count": len(differences),
        "repository_count": len(groups),
        "mean_delta": statistics.mean(differences.values()) if differences else None,
        "repository_macro_delta": statistics.mean(statistics.mean(v) for v in groups.values())
        if groups
        else None,
        "by_repository": {
            repo: {"query_count": len(values), "mean_delta": statistics.mean(values)}
            for repo, values in groups.items()
        },
        "interval": None,
        "interval_status": "insufficient_repositories",
    }
    if len(groups) < MIN_REPOSITORIES:
        return result
    clusters = [(sum(values), len(values)) for values in groups.values()]
    rng = random.Random(seed)
    replicates = []
    for _ in range(samples):
        selected = [clusters[rng.randrange(len(clusters))] for _ in clusters]
        replicates.append(sum(total for total, _ in selected) / sum(n for _, n in selected))
    result["interval"] = {
        "low": percentile(replicates, 0.025),
        "high": percentile(replicates, 0.975),
    }
    result["interval_status"] = "computed"
    return result
