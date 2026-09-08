import math

import pytest

from structure_aware_retrieval.evaluation.metrics import evaluate_ranking, percentile


def test_hand_calculated_binary_and_graded_metrics() -> None:
    result = evaluate_ranking(
        ["unknown", "support", "direct"], {"direct": 2, "support": 1, "missed": 2}, [1, 2, 3, 5]
    )
    assert result[1]["precision"] == result[1]["mrr"] == 0
    assert result[2]["precision"] == 0.5
    assert result[2]["recall"] == pytest.approx(1 / 3)
    assert result[2]["mrr"] == 0.5
    assert result[3]["ndcg"] == pytest.approx(
        (1 / math.log2(3) + 3 / 2) / (3 + 3 / math.log2(3) + 1 / 2)
    )
    assert result[5]["precision"] == 2 / 5
    assert result[5]["recall"] == 2 / 3
    assert result[5]["returned"] == 3
    assert result[5]["judged_fraction"] == 2 / 3


def test_deduplication_happens_before_cutoff() -> None:
    result = evaluate_ranking(["a", "a", "b"], {"a": 1, "b": 2}, [2])[2]
    assert result["precision"] == result["recall"] == 1
    assert result["returned"] == 2


def test_explicit_zero_is_judged_but_unknown_is_not() -> None:
    result = evaluate_ranking(["negative", "unknown"], {"negative": 0, "positive": 2}, [2])[2]
    assert result["judged_fraction"] == 0.5
    assert result["unjudged"] == 1
    assert result["recall"] == 0


def test_empty_results_and_no_answer_are_distinct() -> None:
    empty = evaluate_ranking([], {"positive": 2}, [5])[5]
    assert [empty[name] for name in ("precision", "recall", "mrr", "ndcg")] == [0, 0, 0, 0]
    no_answer = evaluate_ranking(["negative"], {"negative": 0}, [5])[5]
    assert all(no_answer[name] is None for name in ("precision", "recall", "mrr", "ndcg"))
    assert no_answer["judged_fraction"] == 1


@pytest.mark.parametrize("ks", [[], [0], [1, 1], [-1], [True]])
def test_invalid_cutoffs(ks: list[int]) -> None:
    with pytest.raises(ValueError):
        evaluate_ranking([], {}, ks)


def test_invalid_grade_and_percentiles() -> None:
    with pytest.raises(ValueError):
        evaluate_ranking([], {"a": True}, [1])
    assert percentile([3, 1, 2], 0.5) == 2
    assert percentile([3, 1, 2], 0.95) == pytest.approx(2.9)
    assert percentile([7], 0.95) == 7
    with pytest.raises(ValueError):
        percentile([], 0.5)
