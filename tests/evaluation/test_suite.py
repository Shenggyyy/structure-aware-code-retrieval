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


@pytest.fixture
def matrix_root(suite_path):
    from structure_aware_retrieval.evaluation.experiments import TEMPLATES, write_config

    root = suite_path.parent
    suite = json.loads(suite_path.read_text())
    for member in suite["members"]:
        member["config"] = str(root / member["config"])
    (root / "benchmarks").mkdir()
    write_json(root / "benchmarks/suite-v1.json", suite)
    (root / "uv.lock").write_text("fixture lock")
    # Real fixed strategy settings, synthetic input paths; no model needed to freeze.
    import tomllib

    repository = Path(__file__).resolve().parents[2]
    for name in TEMPLATES:
        data = tomllib.loads((repository / f"configs/{name}.toml").read_text())
        data["benchmark"] = str(root / "dev/benchmark/benchmark.json")
        for field in ("indexes", "vectors", "graphs"):
            if field in data:
                data[field] = {"fixture": str(root / "dev/index.sqlite")}
        write_config(root / f"configs/{name}.toml", data)
    return root


def test_matrix_freeze_preserves_all_settings_and_is_destination_independent(matrix_root):
    from structure_aware_retrieval.evaluation.config import load_config
    from structure_aware_retrieval.evaluation.experiments import TEMPLATES, freeze_experiments

    output = matrix_root / "frozen"
    with pytest.raises(ValueError, match="allow-provisional"):
        freeze_experiments(matrix_root, output)
    assert not output.exists()
    plan = freeze_experiments(matrix_root, output, allow_provisional=True)
    assert plan["result_status"] == "provisional"
    assert not plan["review_complete"]
    assert plan == freeze_experiments(matrix_root, matrix_root / "again", allow_provisional=True)
    assert len(list((output / "configs").rglob("*.toml"))) == 45
    for role in plan["roles"]:
        for name in TEMPLATES:
            actual = load_config(output / f"configs/{role}/{name}.toml")
            original = load_config(matrix_root / f"configs/{name}.toml")
            assert actual.structure == original.structure
            assert (actual.strategy, actual.ks, actual.seed, actual.repeats) == (
                original.strategy,
                original.ks,
                original.seed,
                original.repeats,
            )
            assert actual.benchmark == matrix_root / role / "benchmark/benchmark.json"
            assert actual.indexes["fixture"] == output / f"artifacts/{role}/indexes/fixture.sqlite"
    with pytest.raises(FileExistsError):
        freeze_experiments(matrix_root, output, allow_provisional=True)


def test_matrix_worker_failure_never_publishes_completion(matrix_root, monkeypatch):
    from structure_aware_retrieval.evaluation.experiments import run_suite

    def fail(*args):
        raise RuntimeError("worker failed")

    monkeypatch.setattr("structure_aware_retrieval.evaluation.experiments.profile_job", fail)
    output = matrix_root / "failed-matrix"
    with pytest.raises(RuntimeError, match="worker failed"):
        run_suite(matrix_root, output, allow_provisional=True)
    assert (output / "plan.json").is_file()
    assert not (output / "suite-results.json").exists()


@pytest.mark.parametrize("change_code", [False, True])
def test_matrix_isolates_roles_and_checks_freeze_before_queries(
    matrix_root, monkeypatch, change_code
):
    from structure_aware_retrieval.evaluation import experiments
    from structure_aware_retrieval.evaluation.config import load_config

    jobs, comparisons = [], []
    provenance = experiments.analysis_provenance()

    def worker(job, directory):
        jobs.append(job)
        if job["kind"] == "experiment":
            config = load_config(Path(job["config"]))
            assert config.benchmark.parent.parent.name == Path(job["output"]).parent.name
            assert job["benchmark_digest"] == load_benchmark(config.benchmark).digest
            assert len(job["config_sha256"]) == 64
        return {
            "kind": job["kind"],
            "operation_seconds": 1,
            "peak_memory": {"bytes": 1024},
            "details": {"artifact_bytes": 2048},
        }

    def compare(runs, output):
        assert len({path.parent for path in runs}) == 1
        comparisons.append([path.name for path in runs])
        output.mkdir(parents=True)
        write_json(
            output / "comparison.json",
            {
                "runs": [
                    {
                        "strategy": path.name,
                        "overall": {
                            "metrics": {"10": {"recall": 0.5, "ndcg": 0.4, "mrr": 0.3}},
                            "latency_ms": {"p50": 2.0, "p95": 3.0},
                        },
                    }
                    for path in runs
                ],
            },
        )

    monkeypatch.setattr(experiments, "profile_job", worker)
    monkeypatch.setattr(experiments, "compare_runs", compare)
    if change_code:
        monkeypatch.setattr(
            experiments, "analysis_provenance", lambda: {"changed": True} if jobs else provenance
        )
    output = matrix_root / "matrix"
    if change_code:
        with pytest.raises(ValueError, match="Implementation changed"):
            experiments.run_suite(matrix_root, output, allow_provisional=True)
        assert len(jobs) == 9  # Three build operations on each of three fixture repositories.
        assert not (output / "suite-results.json").exists()
        return
    result = experiments.run_suite(matrix_root, output, allow_provisional=True)
    assert len(result["runs"]) == 45
    assert len(result["builds"]) == 9
    assert result["complete"] and not result["review_complete"]
    assert result["result_status"] == "provisional"
    assert [names[0] for names in comparisons] == ["hybrid-seed", "structure-full"] * 3
    text = (output / "report.md").read_text()
    assert all(f"## {role}" in text for role in ("dev", "test", "public"))
    assert "not original RepoQA" in text
