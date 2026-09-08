"""Verify a saved two-stage QA run offline; hashes establish consistency, not authenticity."""

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import _audit_prepared, validate_answer
from structure_aware_retrieval.qa.assessment_plan import (
    _json,
    make_model,
    validate_assessment_bundle,
)
from structure_aware_retrieval.qa.assessment_reporting import summarize_assessment
from structure_aware_retrieval.qa.judging import prepare_judgment, validate_judgment
from structure_aware_retrieval.qa.provider import ModelProviderError, _parse_response

SUCCESS = {"answered", "insufficient_context"}
MAX_FILE_BYTES = 256 * 1024 * 1024


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "Duplicate JSON field")
        result[key] = value
    return result


def _constant(_value):
    raise ValueError("Nonfinite JSON number")


def _read(path: Path, *, lines=False):
    _require(path.stat().st_size <= MAX_FILE_BYTES, "Archive file exceeds verification limit")
    content = path.read_text(encoding="utf-8")

    def parse(text):
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)

    return (
        [parse(line) for line in content.splitlines() if line.strip()] if lines else parse(content)
    )


def _same(left, right, message):
    _require(stable_id(left) == stable_id(right), message)


def _invalid(validator, *args):
    try:
        validator(*args)
    except ValueError:
        return
    raise ValueError("Invalid outcome contains an output that passes validation")


def _provider(result):
    provider = result.get("provider")
    if not provider or provider.get("raw_response") is None:
        return
    try:
        response = _parse_response(provider["raw_response"], provider.get("request_id"))
    except ModelProviderError as error:
        _require(result["status"] == "provider_error", "Failed envelope has successful outcome")
        normalized = dict(error.response_metadata)
    else:
        _require(result["status"] != "provider_error", "Valid envelope has provider-error outcome")
        normalized = asdict(response)
    text = normalized.pop("text")
    _same(provider, normalized, "Provider metadata differs from raw response envelope")
    _same(result["raw_output"], text, "Raw output differs from response envelope")


def _generation(result, prepared):
    for key, value in prepared.items():
        if key != "timing_ms":
            _same(result[key], value, "Generation differs from frozen input")
    for key, value in prepared["timing_ms"].items():
        _same(result["timing_ms"][key], value, "Generation preparation timing mismatch")
    _require(
        result["status"] in SUCCESS | {"invalid_answer", "provider_error"},
        "Unsupported generation outcome",
    )
    evidence = prepared["context"]["evidence"]
    _same(result["model_called"], bool(evidence), "Generation call flag mismatch")
    automatic = _audit_prepared(prepared)
    citation_valid = None
    if result["status"] in SUCCESS:
        answer = validate_answer(_json(result["answer"]), evidence)
        _same(answer["status"], result["status"], "Answer status mismatch")
        if result["model_called"]:
            _same(
                validate_answer(result["raw_output"], evidence),
                answer,
                "Answer differs from raw output",
            )
        else:
            _same(
                answer, {"status": "insufficient_context", "claims": []}, "Invalid local abstention"
            )
            _require(
                result["provider"] is None and result["raw_output"] is None,
                "Local abstention has provider data",
            )
        citation_valid = True if answer["claims"] else None
    else:
        _require(result["answer"] is None, "Failed generation contains an answer")
        if result["status"] == "invalid_answer":
            _invalid(validate_answer, result["raw_output"], evidence)
            citation_valid = False
    _same(
        result["automatic_checks"],
        {**automatic, "citation_ids_valid": citation_valid},
        "Automatic source checks mismatch",
    )
    _same(
        result["answer_fingerprint"],
        stable_id(
            prepared["prompt_fingerprint"],
            result["status"],
            result["answer"],
            result["raw_output"],
            result["provider"]["model"] if result["provider"] else None,
        ),
        "Answer fingerprint mismatch",
    )


def _judging(result, prepared):
    for key, value in prepared.items():
        _same(result[key], value, "Judgment differs from replayed preparation")
    _require(result["model_called"] is True, "Judgment lacks a model call")
    _require(
        result["status"] in {"scored", "invalid_judgment", "provider_error"},
        "Unsupported judgment outcome",
    )
    if result["status"] == "scored":
        _same(
            validate_judgment(result["raw_output"], prepared),
            result["judgment"],
            "Judgment differs from raw output",
        )
    else:
        _require(result["judgment"] is None, "Failed judgment contains scores")
        if result["status"] == "invalid_judgment":
            _invalid(validate_judgment, result["raw_output"], prepared)
    _same(
        result["judgment_fingerprint"],
        stable_id(
            prepared["prepared_fingerprint"],
            result["status"],
            result["judgment"],
            result["raw_output"],
            result["provider"],
        ),
        "Judgment fingerprint mismatch",
    )


def _verify(run: Path) -> dict:
    plan, rows, references, rubric = validate_assessment_bundle(run / "prepared")
    approval = _read(run / "approval.json")
    records = _read(run / "records.json")
    summary = _read(run / "summary.json")
    attempts = _read(run / "attempts.jsonl", lines=True)
    events = _read(run / "results.jsonl", lines=True)
    budget = approval["budget_usd"]
    _require(
        type(budget) in (int, float)
        and math.isfinite(budget)
        and budget >= plan["estimated_cost"]["combined_usd"],
        "Invalid approved budget",
    )
    for key, expected in (
        ("plan_fingerprint", plan["plan_fingerprint"]),
        ("generation_model", plan["generation"]["model"]),
        ("judge_model", plan["judge"]["model"]),
    ):
        _same(approval[key], expected, "Approval differs from frozen plan")
    _require(
        approval["execution_mode"] in {"openai", "injected_models"}, "Unsupported execution mode"
    )
    _require(
        isinstance(records, list) and len(records) == len(rows),
        "Records must retain every planned case",
    )
    models = {
        "generation": make_model(plan["generation"]),
        "judging": make_model(plan["judge"], rubric),
    }
    indexed, expected_events, expected_attempts = {}, [], []
    for attempt in attempts:
        key = attempt["id"], attempt["stage"]
        _require(key not in indexed, "Duplicate attempt")
        indexed[key] = attempt
    stopped = False
    for row, record in zip(rows, records, strict=True):
        for key in ("id", "strategy", "case_id", "repository"):
            _same(record[key], row[key], "Record identity or order mismatch")
        _same(
            record["prepared_timing_ms"],
            row["prepared"]["timing_ms"],
            "Record preparation timing mismatch",
        )
        generation, judging = record["generation"], record["judging"]
        _require(generation is not None or judging is None, "Judgment without generation")
        _require(
            not stopped or (generation is None and judging is None),
            "Results continue after the run stopped",
        )
        if stopped:
            continue
        for stage in ("generation", "judging"):
            result = record[stage]
            key = row["id"], stage
            if stage == "judging":
                if generation is None:
                    _require(judging is None, "Judgment without generation")
                    break
                if generation["status"] not in SUCCESS:
                    _require(
                        judging is not None
                        and judging["status"] == "skipped"
                        and judging["reason"] == "invalid_generation"
                        and judging["model_called"] is False
                        and judging.get("judgment") is None,
                        "Invalid skipped judgment",
                    )
                    stopped = generation["status"] == "provider_error"
                    break
                prepared = prepare_judgment(generation, references[row["case_id"]], rubric)
                if result and result["status"] == "skipped":
                    _require(
                        result["reason"] == "input_exceeds_approved_estimate"
                        and result["model_called"] is False
                        and result.get("judgment") is None,
                        "Invalid skipped judgment",
                    )
                    stopped = True
                    break
            else:
                prepared = row["prepared"]
            attempt = indexed.get(key)
            if result is not None:
                _require(attempt is not None, "Result has no attempt journal entry")
            if attempt is not None:
                expected_attempts.append(key)
                payload = models[stage].request_payload(prepared["messages"])
                digest = hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()
                _same(attempt["request_payload"], payload, "Request differs from frozen payload")
                _same(attempt["request_payload_sha256"], digest, "Request payload hash mismatch")
                _same(
                    attempt["model_call_planned"],
                    stage == "judging" or bool(prepared["context"]["evidence"]),
                    "Attempt call flag mismatch",
                )
                if result is not None:
                    _same(result["request_payload_sha256"], digest, "Result request hash mismatch")
                    _same(result["requested_model"], payload["model"], "Requested model mismatch")
                    _same(result["attempted_at"], attempt["attempted_at"], "Attempt time mismatch")
            if result is None:
                stopped = True
                break
            expected_events.append({"id": row["id"], "stage": stage, "result": result})
            _provider(result)
            if stage == "generation":
                _generation(result, prepared)
            else:
                _judging(result, prepared)
                stopped = result["status"] == "provider_error"
    _same(
        [(a["id"], a["stage"]) for a in attempts],
        expected_attempts,
        "Attempt order or coverage mismatch",
    )
    _same(events, expected_events, "Result journal differs from records")
    status = summary["status"]
    _require(
        status in {"running", "complete", "complete_with_failures", "failed", "interrupted"},
        "Unsupported run status",
    )
    all_scored = all(r["judging"] and r["judging"]["status"] == "scored" for r in records)
    all_finished = all(r["generation"] is not None and r["judging"] is not None for r in records)
    if status == "complete":
        _require(all_scored, "Complete status has missing or invalid outcomes")
    elif status == "complete_with_failures":
        _require(
            all_finished and not all_scored and not stopped,
            "Completed-with-failures status has unfinished or stopped outcomes",
        )
    elif status == "failed":
        _require(
            any(
                (r[s] or {}).get("status") == "provider_error"
                for r in records
                for s in ("generation", "judging")
            )
            or any(
                (r["judging"] or {}).get("reason") == "input_exceeds_approved_estimate"
                for r in records
            ),
            "Failed status has no recorded stop reason",
        )
    expected = summarize_assessment(plan, records, attempts, status=status)
    expected.update(
        execution_mode=approval["execution_mode"],
        approved_budget_usd=budget,
        records_fingerprint=stable_id(records),
        attempts_fingerprint=stable_id(attempts),
    )
    _same(summary, expected, "Summary differs from independently recomputed records")
    return {
        "status": status,
        "planned_cases": len(rows),
        "attempts": len(attempts),
        "recorded_results": len(events),
        "execution_mode": approval["execution_mode"],
        "plan_fingerprint": plan["plan_fingerprint"],
    }


def verify_run(run: Path) -> dict:
    """Read only local archives; construct settings but never inspect keys or issue requests."""
    try:
        return _verify(Path(run))
    except (KeyError, TypeError, AttributeError, RecursionError, UnicodeError) as error:
        raise ValueError("Malformed assessment archive") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify_run(args.run)
    except (OSError, ValueError):
        parser.exit(1, "Assessment archive verification failed; inspect local archive integrity.\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
