import json
from pathlib import Path

import pytest

from structure_aware_retrieval.evaluation.comparison import compare_runs
from structure_aware_retrieval.evaluation.recorded import load_runs, read_jsonl
from structure_aware_retrieval.evaluation.runner import run_experiment


@pytest.fixture
def recorded_pair(experiment: Path) -> list[Path]:
    first, second = experiment.parent / "first", experiment.parent / "second"
    run_experiment(experiment, first)
    experiment.write_text(
        experiment.read_text().replace('strategy = "bm25"', 'strategy = "bm25"\nname = "repeat"')
    )
    run_experiment(experiment, second)
    return [first, second]


def test_paired_categories_exclude_no_answer_and_preserve_known_fingerprints(recorded_pair):
    result = compare_runs(recorded_pair, recorded_pair[0].parent / "comparison")
    metric = result["paired"]["repeat"]["1"]["recall"]
    assert metric["query_count"] == metric["ties"] == 2
    assert metric["by_category"]["behavior"]["query_count"] == 1
    assert metric["by_category"]["symbol"]["mean_delta"] == 0
    assert metric["interval"] is None
    assert result["uncertainty"]["estimand"] == "query_macro_mean_difference"
    assert result["runs"][0]["quality_fingerprint"] == result["runs"][1]["quality_fingerprint"]


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "query_metadata",
        "nan",
        "score",
        "text",
        "missing_rankings",
        "summary",
        "summary_category",
    ],
)
def test_inconsistent_recorded_runs_fail_before_comparison_output(recorded_pair, change):
    run = recorded_pair[1]
    name = "per_query.jsonl"
    if change in {"text", "missing_rankings"}:
        name = "rankings.jsonl"
    if change.startswith("summary"):
        path = run / "summary.json"
        summary = json.loads(path.read_text())
        if change == "summary":
            summary["overall"]["metrics"]["1"]["recall"] = -1
        else:
            summary["by_category"] = {}
        path.write_text(json.dumps(summary))
    else:
        path = run / name
        rows = read_jsonl(path)
        if change == "duplicate":
            rows.append(rows[0])
        elif change == "query_metadata":
            rows[0]["repository"] = "different"
        elif change == "nan":
            rows[0]["metrics"]["1"]["recall"] = float("nan")
        elif change == "score":
            rows[0]["metrics"]["1"]["recall"] = 0.1234
        elif change == "text":
            rows[0]["query"] = "different"
        else:
            rows.pop()
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    output = run.parent / "invalid"
    with pytest.raises(ValueError):
        compare_runs(recorded_pair, output)
    assert not output.exists()


def test_empty_recorded_run_list_is_rejected():
    with pytest.raises(ValueError, match="At least one"):
        load_runs([])


def test_fingerprint_roundtrip_preserves_numeric_k_key_order(experiment: Path):
    experiment.write_text(experiment.read_text().replace("ks = [1, 2, 5]", "ks = [1, 5, 10, 20]"))
    output = experiment.parent / "mixed-digit-ks"
    original = run_experiment(experiment, output)
    assert load_runs([output])[0].summary["quality_fingerprint"] == original["quality_fingerprint"]
