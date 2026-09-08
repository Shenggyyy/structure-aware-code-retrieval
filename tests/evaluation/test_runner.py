import csv
import json
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.evaluation.runner import run_experiment
from structure_aware_retrieval.retrieval import BM25Retriever


def test_repeatable_quality_reports_and_no_answer_separation(experiment: Path) -> None:
    first, second = experiment.parent / "run1", experiment.parent / "run2"
    one = run_experiment(experiment, first)
    two = run_experiment(experiment, second)
    assert one["quality_fingerprint"] == two["quality_fingerprint"]
    assert (first / "rankings.jsonl").read_bytes() == (second / "rankings.jsonl").read_bytes()
    assert one["overall"]["answerable_count"] == 2
    assert one["overall"]["no_answer_count"] == 1
    rows = [json.loads(line) for line in (first / "per_query.jsonl").read_text().splitlines()]
    assert rows[0]["metrics"]["5"]["recall"] == 1
    assert rows[2]["metrics"]["1"]["recall"] is None
    assert all(len(row["latency_ms"]["samples"]) == 2 for row in rows)
    with (first / "metrics.csv").open(newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 9
    assert float(csv_rows[0]["recall"]) == rows[0]["metrics"]["1"]["recall"]
    assert "provisional" in (first / "report.md").read_text()
    rankings = [json.loads(line) for line in (first / "rankings.jsonl").read_text().splitlines()]
    keys = [row["key"] for row in rankings[0]["ranking"]]
    assert len(keys) == len(set(keys))


def test_file_level_uses_max_grade_and_deduplicates(experiment: Path) -> None:
    experiment.write_text(experiment.read_text().replace('unit = "symbol"', 'unit = "file"'))
    output = experiment.parent / "file-run"
    run_experiment(experiment, output)
    rows = [json.loads(line) for line in (output / "per_query.jsonl").read_text().splitlines()]
    assert rows[0]["known_relevant"] == 1
    assert rows[0]["metrics"]["1"]["recall"] == 1


def test_existing_outputs_are_preserved(experiment: Path) -> None:
    output = experiment.parent / "existing"
    output.mkdir()
    (output / "keep").write_text("original")
    with pytest.raises(FileExistsError):
        run_experiment(experiment, output)
    assert (output / "keep").read_text() == "original"


def test_reporting_failure_does_not_publish_partial_run(
    experiment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = experiment.parent / "failed"

    def fail(directory, *args):
        (directory / "partial").write_text("incomplete")
        raise OSError("simulated write failure")

    monkeypatch.setattr("structure_aware_retrieval.evaluation.runner.write_report", fail)
    with pytest.raises(OSError, match="simulated"):
        run_experiment(experiment, output)
    assert not output.exists()
    assert not list(experiment.parent.glob(".sacr-run-*"))


def test_nondeterministic_retrieval_fails(
    experiment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = BM25Retriever.search
    calls = 0

    def unstable(self, query, *, top_k=5):
        nonlocal calls
        calls += 1
        return [replace(hit, score=hit.score + calls) for hit in original(self, query, top_k=top_k)]

    monkeypatch.setattr(BM25Retriever, "search", unstable)
    with pytest.raises(ValueError, match="Nondeterministic"):
        run_experiment(experiment, experiment.parent / "unstable")


def test_cli_evaluation_and_errors(experiment: Path) -> None:
    output = experiment.parent / "cli-run"
    arguments = ["evaluate", "--config", str(experiment), "--output", str(output)]
    result = CliRunner().invoke(app, arguments)
    assert result.exit_code == 0, result.output
    assert "Evaluated 3 queries" in result.output
    assert CliRunner().invoke(app, arguments).exit_code == 1


def test_missing_index_fails_before_creating_run(experiment: Path) -> None:
    (experiment.parent / "index.sqlite").unlink()
    output = experiment.parent / "missing"
    with pytest.raises(FileNotFoundError):
        run_experiment(experiment, output)
    assert not output.exists()
