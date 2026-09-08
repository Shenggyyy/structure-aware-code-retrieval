"""Offline revision bundles reuse archived answers without provider or credential access."""

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from runpy import run_path

import pytest

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.assessment_plan import estimate_input_tokens, make_model
from structure_aware_retrieval.qa.judging import load_rubric
from tests.qa.test_assessment import OfflineModel, _read, _rows, _write
from tests.qa.test_assessment import forbid_live_calls as forbid_live_calls  # noqa: F401
from tests.qa.test_assessment import study as study  # noqa: F401
from tests.qa.test_assessment_archive import _run
from tests.qa.test_preparation import qa_experiment as qa_experiment  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/prepare_qa_judge_revision.py"
REVISION = run_path(str(SCRIPT))
prepare_revision = REVISION["prepare_revision"]
check_revision = REVISION["check_revision"]


@pytest.fixture
def revision_config(tmp_path):
    config = tmp_path / "revision.toml"
    content = (ROOT / "configs/qa-judge-revision-m7c.toml").read_text(encoding="utf-8")
    content = content.replace(
        'rubric = "qa-judge-rubric-v2.json"',
        f'rubric = "{(ROOT / "configs/qa-judge-rubric-v2.json").as_posix()}"',
    )
    config.write_text(content, encoding="utf-8")
    return config


def test_revision_freezes_exact_answers_and_cost_without_calls(study, tmp_path, revision_config):
    run = _run(study, tmp_path)
    before = {path: path.read_bytes() for path in run.rglob("*") if path.is_file()}
    output = tmp_path / "revision"
    plan = prepare_revision(run, revision_config, output)
    assert check_revision(output) == plan
    assert plan["api_calls_made"] == 0
    assert plan["execution_authorized"] is False
    assert plan["annotation_status"] == "provisional"
    assert plan["human_reviewed"] is False
    assert plan["request_count"] == plan["source_planned_count"] == 6
    requests = _rows(output / "requests.jsonl")
    records = _read(run / "records.json")
    for request, original in zip(requests, records, strict=True):
        prepared = request["prepared"]
        assert request["id"] == original["id"]
        assert prepared["payload"]["answer"] == original["generation"]["answer"]
        assert prepared["source_context"] == original["generation"]["context"]
        payload = request["request_payload"]
        assert payload["text"]["format"]["schema"] == prepared["output_schema"]
        assert payload["input"] == prepared["messages"]
        content = json.loads(payload["input"][1]["content"])
        assert "strategy" not in content and "judging" not in content
        assert "Offline transport fixture judgment" not in json.dumps(payload)
        assert content["response_contract"]["packed_evidence_ids"]
    estimate = plan["estimated_cost"]
    expected_input = sum(estimate_input_tokens(row["request_payload"]) for row in requests)
    assert estimate["estimated_input_tokens"] == expected_input
    assert estimate["new_generation_calls"] == 0
    assert estimate["maximum_judge_calls"] == 6
    assert estimate["combined_usd"] == pytest.approx(
        (expected_input * 0.75 + 6 * 2048 * 4.5) / 1_000_000
    )
    assert _read(output / "replay.json")["counts"]["validation"] == {"accepted": 6}
    assert before == {path: path.read_bytes() for path in before}
    for name in REVISION["SOURCE_FILES"]:
        assert (run / name).read_bytes() == (output / "source" / name).read_bytes()


def test_revision_replays_errors_without_repairing_sources(study, tmp_path, revision_config):
    judge = OfflineModel("judging", [])

    def bad_ids(payload):
        if payload["answer"]["status"] == "answered":
            result = json.loads(judge.complete([{}, {"content": json.dumps(payload)}]).text)
            result["correctness"]["evidence_ids"] = ["S1"]
            return judge.response(result)
        return None

    run = _run(study, tmp_path, judge_behavior=bad_ids)
    raw = (run / "records.json").read_bytes()
    output = tmp_path / "revision"
    prepare_revision(run, revision_config, output)
    diagnostics = _read(output / "replay.json")
    invalid = [row for row in diagnostics["cases"] if row["source_status"] == "invalid_judgment"]
    assert len(invalid) == 4
    assert all(row["schema"] == row["validation"] == "rejected" for row in invalid)
    assert (run / "records.json").read_bytes() == raw
    assert "Not v2 model results" in diagnostics["policy"]
    assert all("correctness" not in row for row in diagnostics["cases"])


def test_invalid_generations_are_omitted_and_keep_planned_denominator(
    study, tmp_path, revision_config
):
    model = OfflineModel("generation", [])
    run = _run(
        study,
        tmp_path,
        generation_behavior=lambda _: model.response({"status": "answered", "claims": []}),
    )
    output = tmp_path / "revision"
    plan = prepare_revision(run, revision_config, output)
    assert plan["source_planned_count"] == len(plan["omitted"]) == 6
    assert plan["request_count"] == plan["estimated_cost"]["combined_usd"] == 0
    assert check_revision(output) == plan


@pytest.mark.parametrize("name", ["requests.jsonl", "replay.json", "README.md", "config.toml"])
def test_revision_checker_rejects_changed_outputs(study, tmp_path, revision_config, name):
    output = tmp_path / "revision"
    prepare_revision(_run(study, tmp_path), revision_config, output)
    path = output / name
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        check_revision(output)


def test_checker_retains_creation_provenance_on_another_host(
    study, tmp_path, revision_config, monkeypatch
):
    output = tmp_path / "revision"
    plan = prepare_revision(_run(study, tmp_path), revision_config, output)
    monkeypatch.setitem(
        prepare_revision.__globals__["_build"].__globals__,
        "implementation_record",
        lambda: {"python": "different", "platform": "another host"},
    )
    assert check_revision(output) == plan
    changed = deepcopy(plan)
    changed["implementation"]["python"] = "changed"
    _write(output / "plan.json", changed)
    with pytest.raises(ValueError, match="fingerprint"):
        check_revision(output)


def test_checker_recomputes_payload_even_with_updated_plan_hash(study, tmp_path, revision_config):
    output = tmp_path / "revision"
    plan = prepare_revision(_run(study, tmp_path), revision_config, output)
    rows = _rows(output / "requests.jsonl")
    rows[0]["request_payload"]["max_output_tokens"] = 8192
    (output / "requests.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    plan["requests_fingerprint"] = stable_id(rows)
    del plan["plan_fingerprint"]
    plan["plan_fingerprint"] = stable_id(plan)
    _write(output / "plan.json", plan)
    with pytest.raises(ValueError, match="differs"):
        check_revision(output)


def test_changed_source_is_rejected_and_existing_output_is_preserved(
    study, tmp_path, revision_config
):
    run = _run(study, tmp_path)
    output = tmp_path / "revision"
    prepare_revision(run, revision_config, output)
    saved = (output / "plan.json").read_bytes()
    with pytest.raises(FileExistsError):
        prepare_revision(run, revision_config, output)
    assert (output / "plan.json").read_bytes() == saved
    records = _read(output / "source/records.json")
    records[0]["generation"]["answer"]["claims"][0]["text"] = "Changed answer"
    _write(output / "source/records.json", records)
    with pytest.raises(ValueError):
        check_revision(output)


def test_revision_cli_imports_outside_checkout_and_exposes_no_execution(
    study, tmp_path, revision_config
):
    run = _run(study, tmp_path)
    output = tmp_path / "revision"
    for arguments in (
        ["prepare", "--run", str(run), "--config", str(revision_config), "--output", str(output)],
        ["check", "--bundle", str(output)],
    ):
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), *arguments],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["api_calls_made"] == 0
    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "execute"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_combined_runner_rejects_v2_static_schema(study):
    rubric = load_rubric(ROOT / "configs/qa-judge-rubric-v2.json")
    with pytest.raises(ValueError, match="combined runner supports rubric v1 only"):
        make_model(study.plan["judge"], rubric)
