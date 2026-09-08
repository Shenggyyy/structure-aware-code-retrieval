"""Follow-up preparation freezes only never-journaled requests, without live access."""

import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from runpy import run_path
from types import SimpleNamespace

import pytest

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.assessment_plan import estimate_input_tokens
from structure_aware_retrieval.qa.provider import ModelProviderError
from tests.qa.test_assessment import OfflineModel, _read, _rows, _write
from tests.qa.test_assessment import forbid_live_calls as forbid_live_calls  # noqa: F401
from tests.qa.test_assessment import study as study  # noqa: F401
from tests.qa.test_judge_revision import revision_config as revision_config  # noqa: F401
from tests.qa.test_judge_revision_execution import revision as revision  # noqa: F401
from tests.qa.test_judge_revision_execution import run_revision
from tests.qa.test_preparation import qa_experiment as qa_experiment  # noqa: F401

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/prepare_qa_judge_followup.py"
FOLLOWUP = run_path(str(SCRIPT))
prepare_followup = FOLLOWUP["prepare_followup"]
check_followup = FOLLOWUP["check_followup"]
bundle_files = FOLLOWUP["bundle_files"]


@pytest.fixture
def partial_revision(revision, tmp_path):
    run, calls = tmp_path / "partial-revision", []

    def interrupted(_messages):
        if len(calls) == 3:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_revision(revision, run, calls, behavior=interrupted)
    return SimpleNamespace(run=run, calls=calls, revision=revision)


def _rehash(plan, path):
    plan.pop("plan_fingerprint", None)
    plan["plan_fingerprint"] = stable_id(plan)
    _write(path, plan)


def _snapshot(folder):
    return {
        path.relative_to(folder): path.read_bytes() for path in folder.rglob("*") if path.is_file()
    }


def test_followup_freezes_exact_remaining_requests_and_preserves_source(partial_revision, tmp_path):
    prior = partial_revision.run
    before = _snapshot(prior)
    output = tmp_path / "followup"
    plan = prepare_followup(prior, output)
    assert check_followup(output) == plan
    assert plan["kind"] == "qa_judge_followup_plan"
    assert plan["api_calls_made"] == 0
    assert plan["execution_authorized"] is False
    assert plan["human_reviewed"] is False
    assert plan["annotation_status"] == "provisional"
    assert plan["request_count"] == 3
    assert plan["source_planned_count"] == 6
    assert plan["prior_run"]["attempts"] == 3
    assert plan["prior_run"]["recorded_results"] == 2
    parent_plan = _read(prior / "prepared/plan.json")
    for key in (
        "judge",
        "source_run",
        "source_generation_model",
        "source_records_fingerprint",
        "rubric_id",
        "rubric_fingerprint",
        "rubric_file_sha256",
        "omitted",
    ):
        assert plan[key] == parent_plan[key]
    original = _rows(prior / "prepared/requests.jsonl")
    requests = _rows(output / "requests.jsonl")
    assert requests == original[3:]
    assert plan["request_order"] == [row["id"] for row in original[3:]]
    assert plan["requests_fingerprint"] == stable_id(requests)
    for name, digest in plan["prior_files_sha256"].items():
        assert (output / "prior" / name).read_bytes() == before[Path(name)]
        assert digest == hashlib.sha256(before[Path(name)]).hexdigest()
    assert _snapshot(prior) == before
    assert len(partial_revision.calls) == 3


def test_unknown_outcome_is_excluded_even_though_its_result_is_none(partial_revision, tmp_path):
    plan = prepare_followup(partial_revision.run, tmp_path / "followup")
    records = _read(partial_revision.run / "records.json")
    excluded = plan["excluded_prior_attempts"]
    assert [row["status"] for row in excluded] == ["scored", "scored", "unknown_outcome"]
    assert [row["id"] for row in excluded] == [row["id"] for row in records[:3]]
    assert records[2]["judging"] is None and records[3]["judging"] is None
    assert records[2]["id"] not in plan["request_order"]
    assert records[3]["id"] in plan["request_order"]


def test_cost_estimates_only_new_requests_with_frozen_pricing(partial_revision, tmp_path):
    output = tmp_path / "followup"
    plan = prepare_followup(partial_revision.run, output)
    rows = _rows(output / "requests.jsonl")
    inputs = [estimate_input_tokens(row["request_payload"]) for row in rows]
    estimate = plan["estimated_cost"]
    pricing = plan["judge"]["pricing"]
    outputs = 3 * plan["judge"]["max_output_tokens"]
    assert estimate["new_generation_calls"] == 0
    assert estimate["maximum_judge_calls"] == 3
    assert estimate["estimated_input_tokens"] == sum(inputs)
    assert estimate["maximum_input_tokens_per_call"] == max(inputs)
    assert estimate["maximum_output_tokens"] == outputs
    assert estimate["prior_generation_cost_included"] is False
    assert estimate["prior_judging_cost_included"] is False
    assert estimate["billing_guarantee"] is False
    assert estimate["combined_usd"] == pytest.approx(
        (sum(inputs) * pricing["input_per_million"] + outputs * pricing["output_per_million"])
        / 1_000_000
    )


def test_provider_failure_is_excluded_without_retry(revision, tmp_path):
    prior, calls = tmp_path / "failed-revision", []

    def failure(_messages):
        raise ModelProviderError("Offline transport fixture failure")

    run_revision(revision, prior, calls, behavior=failure)
    plan = prepare_followup(prior, tmp_path / "followup")
    assert plan["prior_run"]["status"] == "failed"
    assert plan["request_count"] == 5
    assert plan["excluded_prior_attempts"][0]["status"] == "provider_error"
    assert plan["excluded_prior_attempts"][0]["id"] not in plan["request_order"]
    assert "interruption.json" not in plan["prior_files_sha256"]
    assert len(calls) == 1


def test_invalid_judgment_is_excluded_before_unknown_outcome(revision, tmp_path):
    prior, calls = tmp_path / "invalid-revision", []

    def invalid_then_stop(_messages):
        if len(calls) == 2:
            raise KeyboardInterrupt
        return replace(OfflineModel("judging", []).response({"broken": True}), raw_response=None)

    with pytest.raises(KeyboardInterrupt):
        run_revision(revision, prior, calls, behavior=invalid_then_stop)
    plan = prepare_followup(prior, tmp_path / "followup")
    assert [row["status"] for row in plan["excluded_prior_attempts"]] == [
        "invalid_judgment",
        "unknown_outcome",
    ]
    assert plan["request_count"] == 4
    assert len(calls) == 2


@pytest.mark.parametrize("status", ["running", "complete", "complete_with_failures"])
def test_nonterminal_or_completed_parent_is_rejected(partial_revision, tmp_path, status):
    summary = _read(partial_revision.run / "summary.json")
    summary["status"] = status
    _write(partial_revision.run / "summary.json", summary)
    output = tmp_path / "followup"
    with pytest.raises(ValueError, match="interrupted or failed"):
        prepare_followup(partial_revision.run, output)
    assert not output.exists()


def test_followup_cannot_be_its_own_parent(partial_revision, tmp_path):
    output = tmp_path / "followup"
    plan = prepare_followup(partial_revision.run, output)
    nested = tmp_path / "nested-parent"
    (nested / "prepared").mkdir(parents=True)
    _write(nested / "prepared/plan.json", plan)
    with pytest.raises(ValueError, match="not another follow-up"):
        prepare_followup(nested, tmp_path / "nested-followup")


def test_all_journaled_requests_leave_nothing_eligible(revision, tmp_path):
    prior, calls = tmp_path / "exhausted-revision", []

    def final_interruption(_messages):
        if len(calls) == 6:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_revision(revision, prior, calls, behavior=final_interruption)
    output = tmp_path / "followup"
    with pytest.raises(ValueError, match="No never-attempted"):
        prepare_followup(prior, output)
    assert not output.exists()
    assert len(calls) == 6


@pytest.mark.parametrize(
    "name", ["requests.jsonl", "README.md", "prior/results.jsonl", "prior/interruption.json"]
)
def test_changed_outputs_and_historical_files_are_rejected(partial_revision, tmp_path, name):
    output = tmp_path / "followup"
    prepare_followup(partial_revision.run, output)
    path = output / name
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        check_followup(output)


def test_rehashed_plan_cannot_add_the_unknown_attempt(partial_revision, tmp_path):
    output = tmp_path / "followup"
    plan = prepare_followup(partial_revision.run, output)
    requests = _rows(output / "requests.jsonl")
    unknown = _rows(output / "prior/prepared/requests.jsonl")[2]
    requests.insert(0, unknown)
    (output / "requests.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in requests), encoding="utf-8"
    )
    plan["request_order"] = [row["id"] for row in requests]
    plan["request_count"] = len(requests)
    plan["requests_fingerprint"] = stable_id(requests)
    plan["excluded_prior_attempts"].pop()
    _rehash(plan, output / "plan.json")
    with pytest.raises(ValueError, match="differs"):
        check_followup(output)


def test_static_file_inventory_does_not_trust_manifest_paths(partial_revision, tmp_path):
    output = tmp_path / "followup"
    plan = prepare_followup(partial_revision.run, output)
    names = bundle_files(output)
    assert names == (*FOLLOWUP["BUNDLE_FILES"], "prior/interruption.json")
    (output / "unrelated.txt").write_text("unrelated", encoding="utf-8")
    plan["prior_files_sha256"]["../../outside.txt"] = "0" * 64
    _rehash(plan, output / "plan.json")
    assert bundle_files(output) == names
    assert all(".." not in Path(name).parts and not Path(name).is_absolute() for name in names)
    with pytest.raises(ValueError, match="differs"):
        check_followup(output)


def test_existing_output_is_preserved(partial_revision, tmp_path):
    output = tmp_path / "followup"
    prepare_followup(partial_revision.run, output)
    before = _snapshot(output)
    with pytest.raises(FileExistsError):
        prepare_followup(partial_revision.run, output)
    assert _snapshot(output) == before


def test_parent_change_after_freezing_does_not_change_bundle(partial_revision, tmp_path):
    output = tmp_path / "followup"
    plan = prepare_followup(partial_revision.run, output)
    (partial_revision.run / "records.json").write_text("changed outside bundle", encoding="utf-8")
    assert check_followup(output) == plan


def test_source_change_during_copy_is_rejected(partial_revision, tmp_path, monkeypatch):
    copyfile = FOLLOWUP["shutil"].copyfile

    def changed(source, target):
        result = copyfile(source, target)
        if target == target.parents[1] / "prepared/requests.jsonl":
            target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        return result

    monkeypatch.setattr(FOLLOWUP["shutil"], "copyfile", changed)
    output = tmp_path / "followup"
    with pytest.raises(ValueError, match="differs"):
        prepare_followup(partial_revision.run, output)
    assert not output.exists()


def test_creation_metadata_is_preserved_on_another_host(partial_revision, tmp_path, monkeypatch):
    output = tmp_path / "followup"
    plan = prepare_followup(partial_revision.run, output)
    monkeypatch.setitem(
        FOLLOWUP["_build"].__globals__, "implementation_record", lambda: {"platform": "other"}
    )
    assert check_followup(output) == plan
    changed = deepcopy(plan)
    changed["implementation"]["platform"] = "tampered"
    _write(output / "plan.json", changed)
    with pytest.raises(ValueError, match="fingerprint"):
        check_followup(output)


def test_cli_runs_outside_checkout_without_credentials_and_has_no_execute(
    partial_revision, tmp_path
):
    output = tmp_path / "followup"
    environment = {name: value for name, value in os.environ.items() if name != "OPENAI_API_KEY"}
    for arguments in (
        ["prepare", "--run", str(partial_revision.run), "--output", str(output)],
        ["check", "--bundle", str(output)],
    ):
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), *arguments],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["api_calls_made"] == 0
        assert json.loads(result.stdout)["request_count"] == 3
    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "execute"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr
