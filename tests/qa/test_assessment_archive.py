"""Saved-run verification uses deterministic test doubles and no external services."""

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from scripts.verify_qa_assessment import verify_run
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.assessment_reporting import summarize_assessment
from structure_aware_retrieval.qa.provider import ModelProviderError, _parse_response
from tests.qa.test_assessment import (
    OfflineModel,
    _execute,
    _read,
    _rows,
    _write,
)
from tests.qa.test_assessment import (
    forbid_live_calls as forbid_live_calls,  # noqa: F401
)
from tests.qa.test_assessment import (
    study as study,  # noqa: F401
)
from tests.qa.test_preparation import qa_experiment as qa_experiment  # noqa: F401


def _run(study, tmp_path, *, generation_behavior=None, judge_behavior=None, raw_envelope=False):
    class ArchiveModel(OfflineModel):
        def complete(self, messages):
            response = super().complete(messages)
            if not raw_envelope:
                return replace(response, raw_response=None)
            return _parse_response(
                {
                    "id": response.response_id,
                    "model": response.model,
                    "status": "completed",
                    "output": [
                        {
                            "type": "message",
                            "role": "assistant",
                            "status": "completed",
                            "content": [{"type": "output_text", "text": response.text}],
                        }
                    ],
                    "usage": {
                        "input_tokens": response.usage["input_tokens"],
                        "output_tokens": response.usage["output_tokens"],
                        "total_tokens": response.usage["total_tokens"],
                        "input_tokens_details": {"cached_tokens": 0},
                        "output_tokens_details": {"reasoning_tokens": 0},
                    },
                },
                response.request_id,
            )

    output = tmp_path / "run"
    _execute(
        study,
        output,
        ArchiveModel("generation", [], behavior=generation_behavior),
        ArchiveModel("judging", [], behavior=judge_behavior),
    )
    return output


def _rewrite(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _republish(run, records):
    """Refresh unsigned summaries/journals so semantic replay is actually exercised."""
    _write(run / "records.json", records)
    old_events = _rows(run / "results.jsonl")
    by_id = {row["id"]: row for row in records}
    for event in old_events:
        event["result"] = by_id[event["id"]][event["stage"]]
    _rewrite(run / "results.jsonl", old_events)
    old_summary = _read(run / "summary.json")
    summary = summarize_assessment(
        _read(run / "prepared/plan.json"),
        records,
        _rows(run / "attempts.jsonl"),
        status=old_summary["status"],
    )
    summary.update(
        {
            key: old_summary[key]
            for key in (
                "execution_mode",
                "approved_budget_usd",
                "attempts_fingerprint",
            )
        }
    )
    summary["records_fingerprint"] = stable_id(records)
    _write(run / "summary.json", summary)


def test_saved_run_verifies_all_cases_without_calls_or_mutation(study, tmp_path):
    run = _run(study, tmp_path)
    before = {path: path.read_bytes() for path in run.rglob("*") if path.is_file()}
    result = verify_run(run)
    assert result["status"] == "complete"
    assert result["planned_cases"] == 6
    assert result["attempts"] == result["recorded_results"] == 12
    assert result["execution_mode"] == "injected_models"
    assert before == {path: path.read_bytes() for path in before}


def test_raw_provider_envelopes_are_replayed_offline(study, tmp_path):
    run = _run(study, tmp_path, raw_envelope=True)
    assert verify_run(run)["status"] == "complete"
    assert _read(run / "records.json")[0]["generation"]["provider"]["raw_response"]


@pytest.mark.parametrize("stage", ["generation", "judging"])
def test_envelope_detects_altered_usage_with_refreshed_journals_and_summary(study, tmp_path, stage):
    run = _run(study, tmp_path, raw_envelope=True)
    records = _read(run / "records.json")
    result = records[0][stage]
    result["provider"]["usage"]["input_tokens"] += 1
    result["provider"]["usage"]["total_tokens"] += 1
    if stage == "judging":
        result["judgment_fingerprint"] = stable_id(
            result["prepared_fingerprint"],
            result["status"],
            result["judgment"],
            result["raw_output"],
            result["provider"],
        )
    _republish(run, records)
    with pytest.raises(ValueError, match="raw response envelope"):
        verify_run(run)


def test_provider_error_replays_partial_envelope_and_known_usage(study, tmp_path):
    def incomplete(_payload):
        return _parse_response(
            {
                "id": "resp-partial",
                "model": "offline-assessment-judge",
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "status": "incomplete",
                        "content": [{"type": "output_text", "text": "{partial"}],
                    }
                ],
            },
            "req-partial",
        )

    run = _run(study, tmp_path, judge_behavior=incomplete)
    assert verify_run(run)["status"] == "failed"
    result = _read(run / "records.json")[0]["judging"]
    assert result["raw_output"] == "{partial"
    assert result["provider"]["usage"]["input_tokens"] == 100


@pytest.mark.parametrize("mutation", ["score", "usage", "request", "omit", "order", "summary"])
def test_archive_rejects_tampered_evidence(study, tmp_path, mutation):
    run = _run(study, tmp_path)
    records = _read(run / "records.json")
    if mutation in {"score", "usage", "omit", "order"}:
        if mutation == "score":
            selected = next(r for r in records if r["generation"]["status"] == "answered")
            selected["judging"]["judgment"]["correctness"]["score"] = 1
        elif mutation == "usage":
            records[0]["generation"]["provider"]["usage"]["input_tokens"] += 1
        elif mutation == "omit":
            records.pop()
        else:
            records.reverse()
        _write(run / "records.json", records)
    elif mutation == "request":
        attempts = _rows(run / "attempts.jsonl")
        attempts[0]["request_payload"]["max_output_tokens"] += 1
        _rewrite(run / "attempts.jsonl", attempts)
    else:
        summary = _read(run / "summary.json")
        summary["overall"]["combined_usage"]["tokens"]["input_tokens"] += 1
        _write(run / "summary.json", summary)
    with pytest.raises(ValueError):
        verify_run(run)


def test_replay_rejects_changed_score_even_with_updated_unsigned_hashes(study, tmp_path):
    run = _run(study, tmp_path)
    records = _read(run / "records.json")
    selected = next(r["judging"] for r in records if r["generation"]["status"] == "answered")
    selected["judgment"]["correctness"]["score"] = 1
    selected["judgment_fingerprint"] = stable_id(
        selected["prepared_fingerprint"],
        selected["status"],
        selected["judgment"],
        selected["raw_output"],
        selected["provider"],
    )
    _republish(run, records)
    with pytest.raises(ValueError, match="raw output"):
        verify_run(run)


def test_complete_with_invalid_judgments_is_verifiable(study, tmp_path):
    broken = OfflineModel("judging", []).response({"malformed": "offline fixture"})
    run = _run(study, tmp_path, judge_behavior=lambda _: broken)
    assert verify_run(run)["status"] == "complete_with_failures"
    records = _read(run / "records.json")
    records[0]["judging"]["judgment"] = {"correctness": {"score": 3}}
    _write(run / "records.json", records)
    with pytest.raises(ValueError, match="contains scores"):
        verify_run(run)


def test_invalid_generation_and_skipped_judgments_are_verifiable(study, tmp_path):
    broken = OfflineModel("generation", []).response({"malformed": "offline fixture"})
    run = _run(study, tmp_path, generation_behavior=lambda _: broken)
    result = verify_run(run)
    assert result["status"] == "complete_with_failures"
    assert result["attempts"] == result["recorded_results"] == 6


def test_provider_failure_retains_unrun_cases_and_unknown_cost(study, tmp_path):
    def failed(_payload):
        raise ModelProviderError("Offline provider failure")

    run = _run(study, tmp_path, judge_behavior=failed)
    result = verify_run(run)
    assert result["status"] == "failed"
    assert result["recorded_results"] == 2
    assert (
        _read(run / "summary.json")["overall"]["combined_usage"][
            "cost_usd_at_frozen_uncached_rates"
        ]
        is None
    )


def test_interrupted_judge_attempt_is_preserved_without_result(study, tmp_path):
    def interrupted(_payload):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        _run(study, tmp_path, judge_behavior=interrupted)
    result = verify_run(tmp_path / "run")
    assert result["status"] == "interrupted"
    assert result["attempts"] == 2
    assert result["recorded_results"] == 1


@pytest.mark.parametrize("mutation", ["budget", "model", "plan"])
def test_approval_must_bind_both_models_budget_and_plan(study, tmp_path, mutation):
    run = _run(study, tmp_path)
    approval = deepcopy(_read(run / "approval.json"))
    if mutation == "budget":
        approval["budget_usd"] = 0
    elif mutation == "model":
        approval["judge_model"] = "other"
    else:
        approval["plan_fingerprint"] = "0" * 64
    _write(run / "approval.json", approval)
    with pytest.raises(ValueError):
        verify_run(run)
