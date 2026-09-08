"""Replay judge-only archives with injected models; never contact a provider."""

import json
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from runpy import run_path

import pytest

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.judge_reporting import render_revision, summarize_revision
from structure_aware_retrieval.qa.provider import _parse_response
from tests.qa.test_assessment import OfflineModel, _read, _rows, _write
from tests.qa.test_assessment import forbid_live_calls as forbid_live_calls  # noqa: F401
from tests.qa.test_assessment import study as study  # noqa: F401
from tests.qa.test_assessment_archive import _rewrite, _run
from tests.qa.test_judge_revision import prepare_revision
from tests.qa.test_judge_revision import revision_config as revision_config  # noqa: F401
from tests.qa.test_preparation import qa_experiment as qa_experiment  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = ROOT / "scripts/verify_qa_judge_revision.py"
verify_run = run_path(str(VERIFY_SCRIPT))["verify_run"]
execute_revision = run_path(str(ROOT / "scripts/run_qa_judge_revision.py"))["execute_revision"]


def _revision_run(study, tmp_path, revision_config, *, behavior=None, source_behavior=None):
    source = _run(study, tmp_path, generation_behavior=source_behavior, raw_envelope=True)
    bundle, output = tmp_path / "revision", tmp_path / "revision-run"
    plan = prepare_revision(source, revision_config, bundle)

    def factory(settings, prepared):
        class Model(OfflineModel):
            def complete(self, messages):
                response = super().complete(messages)
                value = json.loads(response.text)
                if value.get("rubric_id") == "repository-qa-judge-rubric-v1":
                    value["rubric_id"] = "repository-qa-judge-rubric-v2"
                return _parse_response(
                    {
                        "id": response.response_id,
                        "model": self.model,
                        "status": "completed",
                        "output": [
                            {
                                "type": "message",
                                "role": "assistant",
                                "status": "completed",
                                "content": [{"type": "output_text", "text": json.dumps(value)}],
                            }
                        ],
                        "usage": {
                            "input_tokens": 200,
                            "output_tokens": 20,
                            "total_tokens": 220,
                            "input_tokens_details": {"cached_tokens": 0},
                            "output_tokens_details": {"reasoning_tokens": 0},
                        },
                    },
                    response.request_id,
                )

        model = Model("judging", [], behavior=behavior)
        model.model = settings["model"]
        model.output_schema = deepcopy(prepared["output_schema"])
        return model

    execute_revision(
        bundle,
        output,
        budget_usd=max(0.01, plan["estimated_cost"]["combined_usd"]),
        judge_model_id=plan["judge"]["model"],
        approved_plan=plan["plan_fingerprint"],
        execute=True,
        model_factory=factory,
    )
    return output


def _republish(run, records, *, status=None):
    """Refresh unsigned journals/reports to exercise independent semantic verification."""
    _write(run / "records.json", records)
    by_id = {record["id"]: record for record in records}
    events = _rows(run / "results.jsonl")
    for event in events:
        if event["id"] in by_id:
            event["result"] = by_id[event["id"]]["judging"]
    _rewrite(run / "results.jsonl", events)
    old = _read(run / "summary.json")
    attempts = _rows(run / "attempts.jsonl")
    summary = summarize_revision(
        _read(run / "prepared/plan.json"), records, attempts, status=status or old["status"]
    )
    summary.update(
        execution_mode=old["execution_mode"],
        approved_budget_usd=old["approved_budget_usd"],
        records_fingerprint=stable_id(records),
        attempts_fingerprint=stable_id(attempts),
    )
    _write(run / "summary.json", summary)
    (run / "report.md").write_text(render_revision(summary), encoding="utf-8")


def _refresh_judgment(result):
    result["judgment_fingerprint"] = stable_id(
        result["prepared_fingerprint"],
        result["status"],
        result["judgment"],
        result["raw_output"],
        result["provider"],
    )


def test_verifier_preserves_source_answers_and_replays_without_calls(
    study, tmp_path, revision_config
):
    run = _revision_run(study, tmp_path, revision_config)
    before = {path: path.read_bytes() for path in run.rglob("*") if path.is_file()}
    result = verify_run(run)
    assert result["status"] == "complete"
    assert result["source_planned_cases"] == result["judge_requests"] == 6
    assert result["attempts"] == result["recorded_results"] == 6
    assert result["new_generation_calls"] == 0
    assert result["execution_mode"] == "injected_models"
    source = _read(run / "prepared/source/records.json")
    for old, new in zip(source, _read(run / "records.json"), strict=True):
        assert old["generation"] == new["generation"]
        assert new["judging"]["rubric"]["rubric_version"] == 2
        assert new["judging"]["provider"]["raw_response"]
    assert before == {path: path.read_bytes() for path in before}


def test_verifier_cli_works_outside_checkout_in_isolated_python(study, tmp_path, revision_config):
    run = _revision_run(study, tmp_path, revision_config)
    result = subprocess.run(
        [sys.executable, "-I", str(VERIFY_SCRIPT), "--run", str(run)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == verify_run(run)


def test_invalid_outputs_continue_and_are_never_published_as_scores(
    study, tmp_path, revision_config
):
    broken = OfflineModel("judging", []).response({"malformed": "offline test"})
    run = _revision_run(study, tmp_path, revision_config, behavior=lambda _: broken)
    verified = verify_run(run)
    assert verified["status"] == "complete_with_failures"
    assert verified["attempts"] == 6
    records = _read(run / "records.json")
    assert all(row["judging"]["judgment"] is None for row in records)
    records[0]["judging"]["judgment"] = {"correctness": {"score": 3}}
    _refresh_judgment(records[0]["judging"])
    _republish(run, records)
    with pytest.raises(ValueError, match="contains scores"):
        verify_run(run)


def test_partial_provider_response_is_replayed_and_stops_further_calls(
    study, tmp_path, revision_config
):
    def incomplete(_):
        return _parse_response(
            {
                "id": "resp-partial",
                "model": "gpt-5.4-mini-2026-03-17",
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "output": [],
                "usage": {"input_tokens": 200, "output_tokens": 20, "total_tokens": 220},
            },
            "req-partial",
        )

    run = _revision_run(study, tmp_path, revision_config, behavior=incomplete)
    result = verify_run(run)
    assert result["status"] == "failed"
    assert result["attempts"] == result["recorded_results"] == 1
    records = _read(run / "records.json")
    assert records[0]["judging"]["provider"]["usage"]["input_tokens"] == 200
    assert all(row["judging"] is None for row in records[1:])


def test_unknown_interruption_keeps_one_unresolved_attempt(study, tmp_path, revision_config):
    def interrupt(_):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        _revision_run(study, tmp_path, revision_config, behavior=interrupt)
    result = verify_run(tmp_path / "revision-run")
    assert result["status"] == "interrupted"
    assert result["attempts"] == 1
    assert result["recorded_results"] == 0


def test_omitted_invalid_source_answers_retain_all_case_denominators(
    study, tmp_path, revision_config
):
    invalid = replace(OfflineModel("generation", []).response({"invalid": True}), raw_response=None)
    run = _revision_run(study, tmp_path, revision_config, source_behavior=lambda _: invalid)
    result = verify_run(run)
    assert result["source_planned_cases"] == 6
    assert result["judge_requests"] == result["attempts"] == 0
    assert result["status"] == "complete_with_failures"


@pytest.mark.parametrize(
    "mutation", ["generation", "score", "usage", "request", "order", "summary", "report"]
)
def test_verifier_rejects_tampering_even_with_updated_unsigned_metadata(
    study, tmp_path, revision_config, mutation
):
    run = _revision_run(study, tmp_path, revision_config)
    records = _read(run / "records.json")
    if mutation in {"generation", "score", "usage"}:
        result = records[0]["judging"]
        if mutation == "generation":
            records[0]["generation"]["answer"]["claims"][0]["text"] = "Changed source answer"
        elif mutation == "score":
            result["judgment"]["correctness"]["score"] = 1
            _refresh_judgment(result)
        else:
            result["provider"]["usage"]["input_tokens"] += 1
            result["provider"]["usage"]["total_tokens"] += 1
            _refresh_judgment(result)
        _republish(run, records)
    elif mutation in {"request", "order"}:
        attempts = _rows(run / "attempts.jsonl")
        if mutation == "request":
            attempts[0]["request_payload"]["max_output_tokens"] += 1
        else:
            attempts.reverse()
        _rewrite(run / "attempts.jsonl", attempts)
        _republish(run, records)
    elif mutation == "report":
        (run / "report.md").write_text("Fabricated results\n", encoding="utf-8")
    else:
        summary = _read(run / "summary.json")
        summary["records_fingerprint"] = "0" * 64
        _write(run / "summary.json", summary)
    with pytest.raises(ValueError):
        verify_run(run)


@pytest.mark.parametrize("mutation", ["budget", "model", "plan", "source", "mode"])
def test_approval_binds_source_plan_model_budget_and_execution_mode(
    study, tmp_path, revision_config, mutation
):
    run = _revision_run(study, tmp_path, revision_config)
    approval = _read(run / "approval.json")
    key, value = {
        "budget": ("budget_usd", 0),
        "model": ("judge_model", "another-model"),
        "plan": ("plan_fingerprint", "0" * 64),
        "source": ("source_run_plan_fingerprint", "0" * 64),
        "mode": ("execution_mode", "openai"),
    }[mutation]
    approval[key] = value
    _write(run / "approval.json", approval)
    with pytest.raises(ValueError):
        verify_run(run)


def test_calls_cannot_follow_an_unknown_attempt(study, tmp_path, revision_config):
    def interrupt(_):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        _revision_run(study, tmp_path, revision_config, behavior=interrupt)
    run = tmp_path / "revision-run"
    attempts = _rows(run / "attempts.jsonl")
    request = _rows(run / "prepared/requests.jsonl")[1]
    attempts.append(
        {
            **deepcopy(attempts[0]),
            **{key: request[key] for key in ("id", "request_payload", "request_payload_sha256")},
        }
    )
    _rewrite(run / "attempts.jsonl", attempts)
    _republish(run, _read(run / "records.json"))
    with pytest.raises(ValueError, match="after a failed or unknown"):
        verify_run(run)


def test_completed_status_cannot_hide_an_unknown_outcome(study, tmp_path, revision_config):
    def interrupt(_):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        _revision_run(study, tmp_path, revision_config, behavior=interrupt)
    run = tmp_path / "revision-run"
    _republish(run, _read(run / "records.json"), status="complete")
    with pytest.raises(ValueError, match="missing or invalid"):
        verify_run(run)
