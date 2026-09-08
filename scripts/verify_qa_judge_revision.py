"""Verify a judge-only run offline; internal consistency is not provider authenticity."""

import argparse
import json
import math
from pathlib import Path
from runpy import run_path

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.judge_followup_reporting import (
    render_followup,
    summarize_followup,
)
from structure_aware_retrieval.qa.judge_reporting import render_revision, summarize_revision

HERE = Path(__file__).resolve().parent
PREPARATION = run_path(str(HERE / "prepare_qa_judge_revision.py"))
check_revision = PREPARATION["check_revision"]
LEGACY = run_path(str(HERE / "verify_qa_assessment.py"))
_read, _require, _same = (LEGACY[name] for name in ("_read", "_require", "_same"))


def _verify(run: Path, *, followup: bool = False) -> dict:
    if type(followup) is not bool:
        raise ValueError("Follow-up mode must be an explicit boolean")
    check = (
        run_path(str(HERE / "prepare_qa_judge_followup.py"))["check_followup"]
        if followup
        else check_revision
    )
    plan = check(run / "prepared")
    source_path = "prior/records.json" if followup else "source/records.json"
    source = _read(run / "prepared" / source_path)
    requests = _read(run / "prepared/requests.jsonl", lines=True)
    approval = _read(run / "approval.json")
    records = _read(run / "records.json")
    attempts = _read(run / "attempts.jsonl", lines=True)
    events = _read(run / "results.jsonl", lines=True)
    summary = _read(run / "summary.json")
    budget = approval["budget_usd"]
    _require(
        type(budget) in (int, float)
        and math.isfinite(budget)
        and budget > 0
        and budget >= plan["estimated_cost"]["combined_usd"],
        "Invalid approved budget",
    )
    for key, expected in (
        ("plan_fingerprint", plan["plan_fingerprint"]),
        ("judge_model", plan["judge"]["model"]),
        ("source_run_plan_fingerprint", plan["source_run"]["plan_fingerprint"]),
    ):
        _same(approval[key], expected, "Approval differs from frozen plan")
    mode = approval["execution_mode"]
    _require(mode in {"openai", "injected_models"}, "Unsupported execution mode")
    for field in ("source", "recorded_at"):
        _require(
            isinstance(approval[field], str) and bool(approval[field].strip()),
            "Missing approval provenance",
        )
    _require(
        isinstance(approval["execution_implementation"], dict)
        and bool(approval["execution_implementation"]),
        "Missing execution implementation provenance",
    )
    _require(
        isinstance(records, list) and len(records) == len(source),
        "Records must retain every source case",
    )
    requested = {row["id"]: row for row in requests}
    by_id = {}
    for original, record in zip(source, records, strict=True):
        _same(
            {key: value for key, value in record.items() if key != "judging"},
            {key: value for key, value in original.items() if key != "judging"},
            "Source identity, generation or order changed",
        )
        by_id[record["id"]] = record
        if record["id"] not in requested:
            if followup:
                _same(record, original, "Previously attempted or omitted source record changed")
                continue
            result = record["judging"]
            _require(
                isinstance(result, dict)
                and result["status"] == "skipped"
                and result["reason"] == "invalid_source_generation"
                and result["model_called"] is False
                and result.get("judgment") is None,
                "Invalid omitted-source judgment",
            )
    _require(len(attempts) <= len(requests), "Too many judge attempts")
    _same(
        [(attempt["id"], attempt["stage"]) for attempt in attempts],
        [(row["id"], "judging") for row in requests[: len(attempts)]],
        "Attempts must be a single ordered judge-only prefix",
    )
    expected_events, stopped = [], False
    for index, row in enumerate(requests):
        result = by_id[row["id"]]["judging"]
        if index >= len(attempts):
            _require(result is None, "Result has no attempt journal entry")
            continue
        _require(not stopped, "Attempts continue after a failed or unknown outcome")
        attempt = attempts[index]
        _same(
            attempt["request_payload"],
            row["request_payload"],
            "Request differs from frozen payload",
        )
        digest = row["request_payload_sha256"]
        _same(attempt["request_payload_sha256"], digest, "Request payload hash mismatch")
        _require(attempt["model_call_planned"] is True, "Attempt call flag mismatch")
        _require(
            isinstance(attempt["attempted_at"], str) and bool(attempt["attempted_at"].strip()),
            "Invalid attempt timestamp",
        )
        if result is None:
            stopped = True
            continue
        _same(result["request_payload_sha256"], digest, "Result request hash mismatch")
        _same(result["requested_model"], plan["judge"]["model"], "Requested model mismatch")
        _same(result["judge_requested_model"], plan["judge"]["model"], "Judge model mismatch")
        _same(result["attempted_at"], attempt["attempted_at"], "Attempt time mismatch")
        LEGACY["_provider"](result)
        LEGACY["_judging"](result, row["prepared"])
        if mode == "openai" and result["status"] != "provider_error":
            _require(
                isinstance(result["provider"], dict)
                and isinstance(result["provider"].get("raw_response"), dict),
                "OpenAI results require raw provider response envelopes",
            )
        if mode == "openai":
            configured = PREPARATION["_model"](plan["judge"], row["prepared"])
            _same(
                result["judge_settings"],
                {
                    field: getattr(configured, field)
                    for field in (
                        "max_output_tokens",
                        "timeout_seconds",
                        "schema_name",
                        "reasoning_effort",
                    )
                },
                "Judge metadata differs from frozen settings",
            )
        expected_events.append({"id": row["id"], "stage": "judging", "result": result})
        stopped = result["status"] == "provider_error"
    _same(events, expected_events, "Result journal differs from records")
    status = summary["status"]
    _require(
        status in {"running", "interrupted", "failed", "complete", "complete_with_failures"},
        "Unsupported run status",
    )
    scope = [record for record in records if record["id"] in requested] if followup else records
    all_scored = all(
        record["judging"] and record["judging"]["status"] == "scored" for record in scope
    )
    all_finished = all(record["judging"] is not None for record in scope)
    has_provider_error = any(
        (record["judging"] or {}).get("status") == "provider_error" for record in scope
    )
    if status == "complete":
        _require(all_scored, "Complete status has missing or invalid outcomes")
    elif status == "complete_with_failures":
        _require(
            all_finished and not all_scored and not stopped,
            "Completed-with-failures status has unfinished or stopped outcomes",
        )
    elif status == "failed":
        _require(has_provider_error, "Failed status has no provider failure")
    expected = (
        summarize_followup(
            plan,
            _read(run / "prepared/prior/prepared/plan.json"),
            source,
            _read(run / "prepared/prior/attempts.jsonl", lines=True),
            records,
            attempts,
            status=status,
        )
        if followup
        else summarize_revision(plan, records, attempts, status=status)
    )
    expected.update(
        execution_mode=mode,
        approved_budget_usd=budget,
        records_fingerprint=stable_id(records),
        attempts_fingerprint=stable_id(attempts),
    )
    _same(summary, expected, "Summary differs from independently recomputed records")
    _same(
        (run / "report.md").read_text(encoding="utf-8"),
        (render_followup if followup else render_revision)(summary),
        "Report differs from recomputed summary",
    )
    return {
        "status": status,
        "source_planned_cases": len(source),
        "judge_requests": len(requests),
        "attempts": len(attempts),
        "recorded_results": len(events),
        "execution_mode": mode,
        "plan_fingerprint": plan["plan_fingerprint"],
        "new_generation_calls": 0,
    }


def verify_run(run: Path, *, followup: bool = False) -> dict:
    """Read only archived inputs and outputs, without credentials or provider requests."""
    try:
        return _verify(Path(run), followup=followup)
    except (KeyError, TypeError, AttributeError, RecursionError, UnicodeError) as error:
        raise ValueError("Malformed judge revision archive") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument(
        "--followup", action="store_true", help="Verify a follow-up run and its prior"
    )
    args = parser.parse_args()
    try:
        result = verify_run(args.run, followup=args.followup)
    except (OSError, ValueError):
        parser.exit(
            1, "Judge revision archive verification failed; inspect local archive integrity.\n"
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
