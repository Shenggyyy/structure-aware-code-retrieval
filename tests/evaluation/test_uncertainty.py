import math
import random

import pytest

from structure_aware_retrieval.evaluation.metrics import percentile
from structure_aware_retrieval.evaluation.uncertainty import paired_statistics


def test_query_and_repository_weighting_differ_and_small_samples_withhold_intervals():
    result = paired_statistics({"a": 1, "b": 0, "c": 0}, {"a": "one", "b": "two", "c": "two"})
    assert result["mean_delta"] == pytest.approx(1 / 3)
    assert result["repository_macro_delta"] == 0.5
    assert result["by_repository"]["two"] == {"query_count": 2, "mean_delta": 0}
    assert result["interval"] is None
    assert result["interval_status"] == "insufficient_repositories"
    assert result["query_count"] == 3
    assert paired_statistics({}, {})["mean_delta"] is None


def test_cluster_resampling_matches_weighted_hand_calculation_and_is_order_independent():
    differences = {"a": 1, "b": 1, "c": -1, "d": 0, "e": 0.5, "f": -0.5}
    repos = dict(zip(differences, ["a", "a", "b", "c", "d", "e"], strict=True))
    result = paired_statistics(differences, repos, samples=100, seed=7)
    rng = random.Random(7)
    replicates = []
    # Explicit repository multiplicities independently reconstruct each weighted mean.
    for _ in range(100):
        selected = [rng.randrange(5) for _ in range(5)]
        a, b, c, d, e = [selected.count(i) for i in range(5)]
        replicates.append((2 * a - b + 0.5 * d - 0.5 * e) / (2 * a + b + c + d + e))
    assert result["interval"] == {
        "low": percentile(replicates, 0.025),
        "high": percentile(replicates, 0.975),
    }
    assert result == paired_statistics(
        dict(reversed(list(differences.items()))), repos, samples=100, seed=7
    )
    assert result["mean_delta"] == pytest.approx(1 / 6)
    assert result["repository_macro_delta"] == 0


def test_constant_paired_effect_has_exact_interval():
    result = paired_statistics({str(i): 0.25 for i in range(5)}, {str(i): str(i) for i in range(5)})
    assert result["interval"] == {"low": 0.25, "high": 0.25}


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, True, "1"])
def test_invalid_differences_are_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        paired_statistics({"a": value}, {"a": "one"})


@pytest.mark.parametrize(
    "options",
    [{"samples": True}, {"samples": 99}, {"samples": 20_001}, {"seed": -1}, {"seed": False}],
)
def test_invalid_bootstrap_parameters_are_rejected(options):
    with pytest.raises(ValueError, match="bootstrap"):
        paired_statistics({}, {}, **options)


def test_missing_repository_is_rejected():
    with pytest.raises(ValueError, match="repository"):
        paired_statistics({"a": 1}, {})
