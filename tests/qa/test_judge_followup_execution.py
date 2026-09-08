"""Follow-up execution stays within new scope and retains prior unknown outcomes."""

import json
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from runpy import run_path
from types import SimpleNamespace

import pytest

from structure_aware_retrieval.qa.provider import ModelProviderError
from tests.qa.test_assessment import OfflineModel, _read, _rows, _write
from tests.qa.test_assessment import forbid_live_calls as forbid_live_calls  # noqa: F401
from tests.qa.test_assessment import study as study  # noqa: F401
from tests.qa.test_judge_followup import partial_revision as partial_revision  # noqa: F401
from tests.qa.test_judge_revision import revision_config as revision_config  # noqa: F401
from tests.qa.test_judge_revision_execution import RevisionModel, execute_revision
from tests.qa.test_judge_revision_execution import revision as revision  # noqa: F401
from tests.qa.test_preparation import qa_experiment as qa_experiment  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
PREPARE = ROOT / "scripts/prepare_qa_judge_followup.py"
VERIFY = ROOT / "scripts/verify_qa_judge_revision.py"
RUNTIME = ROOT / "scripts/run_qa_judge_revision.py"
prepare_followup = run_path(str(PREPARE))["prepare_followup"]
verify_run = run_path(str(VERIFY))["verify_run"]


@pytest.fixture
def followup(partial_revision, tmp_path):
    bundle = tmp_path / "followup-bundle"
    plan = prepare_followup(partial_revision.run, bundle)
    return SimpleNamespace(bundle=bundle, plan=plan, prior=partial_revision.run)


def run_followup(batch, output, calls, *, behavior=None, **overrides):
    return execute_revision(
        batch.bundle,
        output,
        **{
            "budget_usd": batch.plan["estimated_cost"]["combined_usd"],
            "judge_model_id": batch.plan["judge"]["model"],
            "approved_plan": batch.plan["plan_fingerprint"],
            "execute": True,
            "followup": True,
            "model_factory": lambda settings, prepared: RevisionModel(
                settings, prepared, calls, behavior=behavior
            ),
            **overrides,
        },
    )


def test_completed_new_scope_keeps_unknown_prior_and_separates_costs(followup, tmp_path):
    original = {path: path.read_bytes() for path in followup.prior.rglob("*") if path.is_file()}
    output, calls = tmp_path / "new-run", []
    result = run_followup(followup, output, calls)
    assert result["status"] == "complete"
    assert result["cumulative"]["status"] == "incomplete"
    assert len(calls) == len(_rows(output / "attempts.jsonl")) == 3
    assert len(_rows(output / "results.jsonl")) == 3
    records, previous = _read(output / "records.json"), _read(followup.prior / "records.json")
    assert len(records) == 6
    assert records[:3] == previous[:3]
    assert [row["id"] for row in _rows(output / "attempts.jsonl")] == followup.plan["request_order"]
    assert result["new_judging"]["tokens"]["input_tokens"] == 600
    assert result["prior_judging"]["observed_token_subtotals"]["input_tokens"] == 400
    assert result["overall"]["judging"]["observed_token_subtotals"]["input_tokens"] == 1000
    assert result["new_judging"]["cost_usd_at_frozen_uncached_rates"] == pytest.approx(0.00072)
    assert result["overall"]["judging"]["cost_usd_at_frozen_uncached_rates"] is None
    assert result["overall"]["judging"]["completed_count"] == 5
    assert result["overall"]["judging"]["unknown_outcome_count"] == 1
    assert verify_run(output, followup=True)["status"] == "complete"
    assert original == {path: path.read_bytes() for path in original}
    assert "Offline" in (output / "report.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "overrides",
    [
        {"execute": False},
        {"approved_plan": "unapproved-fingerprint"},
        {"judge_model_id": "another-model"},
        {"budget_usd": 0.000001},
        {"budget_usd": float("nan")},
        {"followup": False},
    ],
)
def test_followup_approval_and_mode_fail_before_output_or_calls(followup, tmp_path, overrides):
    output, calls = tmp_path / "rejected", []
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        run_followup(followup, output, calls, **overrides)
    assert calls == []
    assert not output.exists()


def test_existing_followup_output_cannot_be_overwritten(followup, tmp_path):
    output, calls = tmp_path / "new-run", []
    run_followup(followup, output, calls)
    before = (output / "attempts.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        run_followup(followup, output, calls)
    assert len(calls) == 3
    assert (output / "attempts.jsonl").read_bytes() == before


def test_new_interruption_retains_two_unknown_outcomes_without_retry(followup, tmp_path):
    output, calls = tmp_path / "interrupted", []

    def interrupt(_messages):
        raise RuntimeError("private-provider-detail")

    with pytest.raises(RuntimeError):
        run_followup(followup, output, calls, behavior=interrupt)
    summary = _read(output / "summary.json")
    assert len(calls) == 1
    assert summary["status"] == "interrupted"
    assert summary["new_judging"]["unknown_outcome_count"] == 1
    assert summary["prior_judging"]["unknown_outcome_count"] == 1
    assert summary["overall"]["judging"]["unknown_outcome_count"] == 2
    assert summary["overall"]["judging"]["not_run_count"] == 2
    diagnostic = _read(output / "interruption.json")
    assert diagnostic["active_request_id"] == followup.plan["request_order"][0]
    assert diagnostic["attempted_count"] == 1
    assert "private-provider-detail" not in json.dumps(diagnostic)
    assert verify_run(output, followup=True)["status"] == "interrupted"


def test_provider_error_stops_only_new_scope_and_preserves_parent(followup, tmp_path):
    output, calls = tmp_path / "failed", []

    def failed(_messages):
        raise ModelProviderError("transport_error")

    result = run_followup(followup, output, calls, behavior=failed)
    assert result["status"] == "failed"
    assert len(calls) == 1
    assert result["new_judging"]["failed_count"] == 1
    assert result["new_judging"]["unknown_outcome_count"] == 0
    assert result["prior_judging"]["unknown_outcome_count"] == 1
    assert verify_run(output, followup=True)["status"] == "failed"


def test_invalid_judgment_is_preserved_while_other_new_requests_finish(followup, tmp_path):
    output, calls = tmp_path / "invalid", []

    def invalid_once(_messages):
        return (
            replace(
                OfflineModel("judging", []).response({}),
                model=followup.plan["judge"]["model"],
                raw_response=None,
            )
            if len(calls) == 1
            else None
        )

    result = run_followup(followup, output, calls, behavior=invalid_once)
    assert result["status"] == "complete_with_failures"
    assert len(calls) == 3
    assert result["new_judging"]["failed_count"] == 1
    assert result["prior_judging"]["unknown_outcome_count"] == 1
    assert verify_run(output, followup=True)["status"] == "complete_with_failures"


@pytest.mark.parametrize(
    "mutation", ["historical_score", "historical_unknown", "new_order", "cost"]
)
def test_verifier_rejects_changed_inherited_evidence_or_new_accounting(
    followup, tmp_path, mutation
):
    output = tmp_path / "tampered"
    run_followup(followup, output, [])
    if mutation in {"historical_score", "historical_unknown"}:
        records = _read(output / "records.json")
        if mutation == "historical_score":
            records[0]["judging"]["raw_output"] = "Changed prior evidence"
        else:
            records[2]["judging"] = deepcopy(records[0]["judging"])
        _write(output / "records.json", records)
    elif mutation == "new_order":
        attempts = _rows(output / "attempts.jsonl")
        attempts[0], attempts[1] = attempts[1], attempts[0]
        (output / "attempts.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in attempts), encoding="utf-8"
        )
    else:
        summary = _read(output / "summary.json")
        summary["new_judging"]["cost_usd_at_frozen_uncached_rates"] = 0
        _write(output / "summary.json", summary)
    with pytest.raises(ValueError):
        verify_run(output, followup=True)


def test_followup_cli_verifier_works_outside_checkout_and_without_credentials(followup, tmp_path):
    output = tmp_path / "cli-run"
    run_followup(followup, output, [])
    verified = subprocess.run(
        [sys.executable, "-I", str(VERIFY), "--followup", "--run", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
        check=False,
    )
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["attempts"] == 3
    rejected = subprocess.run(
        [
            sys.executable,
            "-I",
            str(RUNTIME),
            "--followup",
            "--bundle",
            str(followup.bundle),
            "--output",
            str(tmp_path / "unapproved-cli"),
            "--judge-model",
            followup.plan["judge"]["model"],
            "--approved-plan",
            followup.plan["plan_fingerprint"],
            "--budget-usd",
            "1",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
        check=False,
    )
    assert rejected.returncode == 1
    assert not (tmp_path / "unapproved-cli").exists()
