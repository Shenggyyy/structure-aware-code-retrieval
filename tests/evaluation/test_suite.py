import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.evaluation.dataset import load_benchmark
from structure_aware_retrieval.evaluation.recorded import read_jsonl
from structure_aware_retrieval.evaluation.suite import audit_suite
from structure_aware_retrieval.models import stable_id


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


@pytest.fixture
def suite_path(experiment: Path) -> Path:
    root = experiment.parent
    entries = []
    for role in ("dev", "test", "public"):
        folder = root / role
        shutil.copytree(root / "benchmark", folder / "benchmark")
        shutil.copyfile(root / "index.sqlite", folder / "index.sqlite")
        shutil.copyfile(experiment, folder / "experiment.toml")
        manifest = json.loads((folder / "benchmark/benchmark.json").read_text())
        manifest["id"] = role
        manifest["split"] = "dev" if role == "dev" else "test"
        manifest["repositories"][0]["url"] = f"https://example.invalid/{role}.git"
        write_json(folder / "benchmark/benchmark.json", manifest)
        for name, key in (("queries", "id"), ("qrels", "query_id")):
            rows = read_jsonl(folder / f"benchmark/{name}.jsonl")
            for row in rows:
                row[key] = f"{role}-{row[key]}"
                if name == "queries":
                    row["text"] = f"{role}: {row['text']}"
            write_jsonl(folder / f"benchmark/{name}.jsonl", rows)
        benchmark = load_benchmark(folder / "benchmark/benchmark.json")
        provenance = [{"query_id": q.id, "family": f"{role}:{q.id}"} for q in benchmark.queries]
        write_jsonl(folder / "benchmark/provenance.jsonl", provenance)
        entries.append(
            {
                "role": role,
                "config": f"{role}/experiment.toml",
                "benchmark_digest": benchmark.digest,
                "provenance_digest": stable_id(provenance),
            }
        )
    suite = root / "suite.json"
    write_json(
        suite,
        {
            "schema_version": 1,
            "id": "fixture-suite",
            "primary_k": 1,
            "primary_metrics": ["recall", "ndcg"],
            "members": entries,
        },
    )
    return suite


def test_suite_audit_checks_sources_without_running_retrieval(suite_path, monkeypatch):
    monkeypatch.setattr(
        "structure_aware_retrieval.evaluation.runner.run_experiment",
        lambda *a: pytest.fail("retrieval must not run"),
    )
    output = suite_path.parent / "audit"
    result = audit_suite(suite_path, output)
    assert result["repository_count"] == 3
    assert result["query_count"] == 9
    assert result["retrieval_executed"] is False
    assert result["review_complete"] is False
    assert result["members"][0]["no_answer_count"] == 1
    assert result == audit_suite(suite_path, suite_path.parent / "repeat")
    with pytest.raises(FileExistsError):
        audit_suite(suite_path, output)
    cli = CliRunner().invoke(
        app,
        [
            "audit-suite",
            "--suite",
            str(suite_path),
            "--output",
            str(suite_path.parent / "cli-audit"),
        ],
    )
    assert cli.exit_code == 0, cli.output


@pytest.mark.parametrize(
    "change", ["overlap", "digest", "provenance", "split", "duplicate_text", "role", "primary_k"]
)
def test_split_leakage_and_changed_freezes_fail(suite_path, change):
    suite = json.loads(suite_path.read_text())
    root = suite_path.parent
    entry = suite["members"][1]
    manifest_path = root / "test/benchmark/benchmark.json"
    manifest = json.loads(manifest_path.read_text())
    if change == "overlap":
        manifest["repositories"][0]["url"] = "https://example.invalid/dev.git/"
        write_json(manifest_path, manifest)
        entry["benchmark_digest"] = load_benchmark(manifest_path).digest
    elif change == "digest":
        entry["benchmark_digest"] = "0" * 64
    elif change == "provenance":
        entry["provenance_digest"] = "0" * 64
    elif change == "split":
        manifest["split"] = "dev"
        write_json(manifest_path, manifest)
        entry["benchmark_digest"] = load_benchmark(manifest_path).digest
    elif change == "duplicate_text":
        path = root / "test/benchmark/queries.jsonl"
        rows = read_jsonl(path)
        rows[0]["text"] = (
            "  " + read_jsonl(root / "dev/benchmark/queries.jsonl")[0]["text"].upper() + "  "
        )
        write_jsonl(path, rows)
        entry["benchmark_digest"] = load_benchmark(manifest_path).digest
    elif change == "role":
        entry["role"] = "dev"
    else:
        suite["primary_k"] = 20
    write_json(suite_path, suite)
    with pytest.raises(ValueError):
        audit_suite(suite_path, root / "invalid")
    assert not (root / "invalid").exists()
