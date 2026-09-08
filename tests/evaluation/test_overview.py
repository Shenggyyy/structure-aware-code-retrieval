import json
import subprocess
import sys
from pathlib import Path

import pytest

from structure_aware_retrieval.evaluation.overview import (
    build_overview,
    render_overview,
    write_overview,
)
from structure_aware_retrieval.evaluation.runner import run_experiment
from structure_aware_retrieval.models import stable_id


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def save_plan(root: Path, plan: dict) -> None:
    plan["plan_digest"] = stable_id({k: v for k, v in plan.items() if k != "plan_digest"})
    dump(root / "plan.json", plan)
    suite = json.loads((root / "suite-results.json").read_text())
    suite["plan_digest"] = plan["plan_digest"]
    dump(root / "suite-results.json", suite)


@pytest.fixture
def saved_suite(experiment: Path) -> Path:
    root = experiment.parent / "suite"
    workers, settings = [], {}
    for name in ("bm25", "repeat"):
        config = experiment.parent / f"{name}.toml"
        # name belongs to the experiment section, before [indexes].
        config.write_text(
            experiment.read_text().replace("[indexes]", f'name = "{name}"\n[indexes]')
        )
        summary = run_experiment(config, root / "runs" / "dev" / name)
        settings[name] = {
            key: summary["config"][key]
            for key in ("name", "strategy", "unit", "ks", "warmup_queries", "repeats", "seed")
        }
        workers.append(
            {
                "role": "dev",
                "name": name,
                "kind": "experiment",
                "details": {"quality_fingerprint": summary["quality_fingerprint"]},
            }
        )
    plan = {
        "schema_version": 1,
        "roles": ["dev"],
        "strategy_order": ["bm25", "repeat"],
        "strategy_settings": settings,
        "primary_k": 2,
        "result_status": "provisional",
        "review_complete": False,
        "members": [
            {
                "role": "dev",
                "benchmark_id": summary["benchmark"]["id"],
                "benchmark_digest": summary["benchmark"]["digest"],
                "annotation_status": summary["benchmark"]["annotation_status"],
                "query_count": 3,
                "repositories": [
                    {"id": repo, "snapshot_id": index["snapshot_id"]}
                    for repo, index in summary["indexes"].items()
                ],
            }
        ],
    }
    dump(
        root / "suite-results.json",
        {
            "schema_version": 1,
            "complete": True,
            "result_status": "provisional",
            "review_complete": False,
            "runs": workers,
        },
    )
    save_plan(root, plan)
    return root


def test_saved_evidence_generates_identical_location_independent_outputs(saved_suite, monkeypatch):
    def no_retrieval(*args, **kwargs):
        pytest.fail("Saved overview must not rerun retrieval")

    monkeypatch.setattr(
        "structure_aware_retrieval.evaluation.runner.create_retriever", no_retrieval
    )
    first = build_overview(saved_suite)
    assert first == build_overview(saved_suite)
    assert first["scope"] == {
        "roles": 1,
        "strategies_per_role": 2,
        "validated_runs": 2,
        "queries": 3,
        "repositories": 1,
    }
    assert str(saved_suite) not in json.dumps(first)
    # Two answerable queries contribute recalls 1/2 and 1; the scope control is excluded.
    assert first["runs"][0]["metrics"]["recall"] == pytest.approx(0.75)
    rendered = render_overview(first)
    assert "## dev" in rendered and "Recall@2" in rendered
    assert "outside the validated quality fingerprints" in rendered
    outputs = [saved_suite.parent / name for name in ("overview-one", "overview-two")]
    for output in outputs:
        write_overview(first, output)
    for name in ("summary.json", "report.md"):
        assert (outputs[0] / name).read_bytes() == (outputs[1] / name).read_bytes()
    with pytest.raises(FileExistsError):
        write_overview(first, outputs[0])


@pytest.mark.parametrize("change", ["hash", "query_count", "snapshot", "benchmark", "settings"])
def test_changed_plan_or_binding_is_rejected(saved_suite, change):
    plan = json.loads((saved_suite / "plan.json").read_text())
    if change == "hash":
        plan["primary_k"] = 999
        dump(saved_suite / "plan.json", plan)
    else:
        member = plan["members"][0]
        if change == "query_count":
            member["query_count"] += 1
        elif change == "snapshot":
            member["repositories"][0]["snapshot_id"] = "changed"
        elif change == "benchmark":
            member["benchmark_digest"] = "changed"
        else:
            plan["strategy_settings"]["repeat"]["repeats"] += 1
        save_plan(saved_suite, plan)
    with pytest.raises(ValueError):
        build_overview(saved_suite)


@pytest.mark.parametrize("change", ["revision", "missing"])
def test_encoder_metadata_is_bound_to_frozen_model(saved_suite, change):
    # Synthetic metadata exercises binding without downloading or running an encoder.
    plan = json.loads((saved_suite / "plan.json").read_text())
    plan["model"] = {"id": "fixture-encoder", "revision": "frozen-revision"}
    plan["strategy_settings"]["repeat"]["strategy"] = "dense"
    save_plan(saved_suite, plan)
    path = saved_suite / "runs" / "dev" / "repeat" / "summary.json"
    summary = json.loads(path.read_text())
    summary["config"]["strategy"] = "dense"
    summary["config"]["encoder"] = {**plan["model"], "packages": {"fixture": "1.0"}}
    dump(path, summary)
    assert build_overview(saved_suite)["scope"]["validated_runs"] == 2
    if change == "revision":
        summary["config"]["encoder"]["revision"] = "different-revision"
    else:
        del summary["config"]["encoder"]
    dump(path, summary)
    with pytest.raises(ValueError, match="frozen plan/worker"):
        build_overview(saved_suite)


def test_bm25_seeded_structure_remains_model_free(saved_suite):
    plan = json.loads((saved_suite / "plan.json").read_text())
    settings = plan["strategy_settings"]["repeat"]
    settings.update(strategy="structure", structure={"seed_strategy": "bm25"})
    save_plan(saved_suite, plan)
    path = saved_suite / "runs" / "dev" / "repeat" / "summary.json"
    summary = json.loads(path.read_text())
    summary["config"].update(strategy="structure", structure={"seed_strategy": "bm25"})
    dump(path, summary)
    assert build_overview(saved_suite)["scope"]["validated_runs"] == 2


@pytest.mark.parametrize("change", ["missing", "duplicate", "extra", "incomplete", "fingerprint"])
def test_incomplete_or_unbound_worker_matrix_is_rejected(saved_suite, change):
    path = saved_suite / "suite-results.json"
    suite = json.loads(path.read_text())
    if change == "missing":
        suite["runs"].pop()
    elif change == "duplicate":
        suite["runs"].append(suite["runs"][0])
    elif change == "extra":
        suite["runs"].append({**suite["runs"][0], "name": "unexpected"})
    elif change == "incomplete":
        suite["complete"] = False
    else:
        suite["runs"][0]["details"]["quality_fingerprint"] = "changed"
    dump(path, suite)
    with pytest.raises(ValueError):
        build_overview(saved_suite)


def test_changed_quality_and_extra_run_directories_are_rejected(saved_suite):
    extra = saved_suite / "runs" / "dev" / "unexpected"
    extra.mkdir()
    with pytest.raises(ValueError, match="directories"):
        build_overview(saved_suite)
    extra.rmdir()
    path = saved_suite / "runs" / "dev" / "bm25" / "summary.json"
    summary = json.loads(path.read_text())
    summary["overall"]["metrics"]["2"]["recall"] = 0.12345
    dump(path, summary)
    with pytest.raises(ValueError, match="Summary quality"):
        build_overview(saved_suite)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "1"])
def test_invalid_recorded_latency_is_not_presented(saved_suite, value):
    path = saved_suite / "runs" / "dev" / "bm25" / "summary.json"
    summary = json.loads(path.read_text())
    summary["overall"]["latency_ms"]["p50"] = value
    dump(path, summary)
    with pytest.raises(ValueError, match="latency"):
        build_overview(saved_suite)


def test_check_accepts_checkout_line_endings_but_never_repairs_stale_files(saved_suite):
    summary, output = build_overview(saved_suite), saved_suite.parent / "overview"
    with pytest.raises(ValueError, match="missing or stale"):
        write_overview(summary, output, check=True)
    assert not output.exists()
    write_overview(summary, output)
    for name in ("summary.json", "report.md"):
        path = output / name
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
    write_overview(summary, output, check=True)
    assert before == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
    stale = output / "report.md"
    stale.write_text("Stale results\n")
    with pytest.raises(ValueError, match="missing or stale"):
        write_overview(summary, output, check=True)
    assert stale.read_text() == "Stale results\n"


def test_cli_reports_stale_output_with_nonzero_exit(saved_suite):
    script = Path(__file__).resolve().parents[2] / "scripts" / "summarize_results.py"
    output = saved_suite.parent / "cli-overview"
    command = [sys.executable, str(script), "--results", str(saved_suite), "--output", str(output)]
    created = subprocess.run(command, capture_output=True, text=True, check=False)
    assert created.returncode == 0, created.stderr
    assert "2 validated saved runs" in created.stdout
    checked = subprocess.run([*command, "--check"], capture_output=True, text=True, check=False)
    assert checked.returncode == 0, checked.stderr
    (output / "summary.json").write_text("{}\n")
    stale = subprocess.run([*command, "--check"], capture_output=True, text=True, check=False)
    assert stale.returncode != 0
    assert "missing or stale" in stale.stderr
    assert (output / "summary.json").read_text() == "{}\n"
