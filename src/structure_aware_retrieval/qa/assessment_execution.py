"""Explicitly approved two-stage QA execution with durable accounting and no retries."""

import hashlib
import math
import shutil
from datetime import UTC, datetime
from pathlib import Path

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import complete_question
from structure_aware_retrieval.qa.assessment_plan import (
    BUNDLE_FILES,
    MAX_ANSWER_BYTES,
    _json,
    estimate_input_tokens,
    implementation_record,
    make_model,
    validate_assessment_bundle,
)
from structure_aware_retrieval.qa.assessment_reporting import (
    render_assessment,
    summarize_assessment,
)
from structure_aware_retrieval.qa.execution import _append, _write
from structure_aware_retrieval.qa.judging import (
    complete_judgment,
    judgment_messages,
    prepare_judgment,
)
from structure_aware_retrieval.qa.provider import AnswerModel, OpenAIModel


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _skipped(reason: str) -> dict:
    return {
        "status": "skipped",
        "reason": reason,
        "model_called": False,
        "judgment": None,
        "provider": None,
        "raw_output": None,
        "latency_ms": None,
        "error": None,
    }


def execute_assessment(
    bundle: Path,
    output: Path,
    *,
    budget_usd: float,
    generation_model_id: str,
    judge_model_id: str,
    approved_plan: str,
    generation_model: AnswerModel | None = None,
    judge_model: AnswerModel | None = None,
) -> dict:
    """Require the exact plan, both model IDs and a combined budget before any call.

    Inject both test doubles or neither. Outputs are never overwritten or resumed.
    The budget checks a projection; it does not impose a provider billing hard cap.
    """
    plan, rows, references, rubric = validate_assessment_bundle(bundle)
    if (
        approved_plan != plan["plan_fingerprint"]
        or generation_model_id != plan["generation"]["model"]
        or judge_model_id != plan["judge"]["model"]
    ):
        raise ValueError("Confirm the exact plan fingerprint and both model IDs before execution")
    if (
        type(budget_usd) not in (int, float)
        or not math.isfinite(budget_usd)
        or budget_usd <= 0
        or budget_usd < plan["estimated_cost"]["combined_usd"]
    ):
        raise ValueError("Approved budget must cover generation plus judging; no calls made")
    if (generation_model is None) != (judge_model is None):
        raise ValueError("Inject both offline models or neither; never mix live and test stages")
    if isinstance(generation_model, OpenAIModel) != isinstance(judge_model, OpenAIModel):
        raise ValueError("Do not mix OpenAI adapters with injected test models")
    configured = {
        "generation": make_model(plan["generation"]),
        "judging": make_model(plan["judge"], rubric),
    }
    for stage, injected in (("generation", generation_model), ("judging", judge_model)):
        if isinstance(injected, OpenAIModel) and (
            injected.request_payload([{"role": "user", "content": "settings"}])
            != configured[stage].request_payload([{"role": "user", "content": "settings"}])
            or injected.api_key_env != configured[stage].api_key_env
            or injected.timeout_seconds != configured[stage].timeout_seconds
        ):
            raise ValueError("Injected API model differs from the frozen assessment settings")
    if output.exists() or output.is_symlink():
        raise FileExistsError("Assessment run output exists; never reuse a paid run directory")
    output.mkdir(parents=True, exist_ok=False)
    frozen = output / "prepared"
    (frozen / "generation").mkdir(parents=True)
    for name in BUNDLE_FILES:
        shutil.copyfile(bundle / "generation" / name, frozen / "generation" / name)
    for name in ("plan.json", "references.json", "rubric.json"):
        shutil.copyfile(bundle / name, frozen / name)
    copied_plan, _, _, _ = validate_assessment_bundle(frozen)
    if copied_plan["plan_fingerprint"] != approved_plan:
        raise ValueError("Assessment inputs changed while archiving the approved plan")
    mode = (
        "openai"
        if generation_model is None or isinstance(generation_model, OpenAIModel)
        else "injected_models"
    )
    approval = {
        "plan_fingerprint": approved_plan,
        "generation_model": generation_model_id,
        "judge_model": judge_model_id,
        "budget_usd": budget_usd,
        "recorded_at": _now(),
        "execution_mode": mode,
        "source": "explicit invocation; not an identity verification",
        "execution_implementation": implementation_record(),
    }
    _write(output / "approval.json", approval)
    records = [
        {
            **{key: row[key] for key in ("id", "strategy", "case_id", "repository")},
            "prepared_timing_ms": row["prepared"]["timing_ms"],
            "generation": None,
            "judging": None,
        }
        for row in rows
    ]
    attempts = []
    state = "running"

    def checkpoint() -> dict:
        summary = summarize_assessment(plan, records, attempts, status=state)
        summary["execution_mode"] = mode
        summary["approved_budget_usd"] = budget_usd
        summary["records_fingerprint"] = stable_id(records)
        summary["attempts_fingerprint"] = stable_id(attempts)
        _write(output / "records.json", records)
        _write(output / "summary.json", summary)
        (output / "report.md").write_text(render_assessment(summary), encoding="utf-8")
        return summary

    checkpoint()
    try:
        with (
            (output / "attempts.jsonl").open("x", encoding="utf-8", newline="\n") as journal,
            (output / "results.jsonl").open("x", encoding="utf-8", newline="\n") as results,
        ):

            def call(stage, row, record, prepared, model):
                messages = prepared["messages"]
                payload = configured[stage].request_payload(messages)
                attempt = {
                    "id": row["id"],
                    "stage": stage,
                    "attempted_at": _now(),
                    "model_call_planned": stage == "judging"
                    or bool(prepared["context"]["evidence"]),
                    "request_payload": payload,
                    "request_payload_sha256": hashlib.sha256(
                        _json(payload).encode("utf-8")
                    ).hexdigest(),
                }
                _append(journal, attempt)
                attempts.append(attempt)
                checkpoint()
                result = (
                    complete_question(prepared, model)
                    if stage == "generation"
                    else complete_judgment(prepared, model)
                )
                result["requested_model"] = payload["model"]
                result["attempted_at"] = attempt["attempted_at"]
                result["request_payload_sha256"] = attempt["request_payload_sha256"]
                _append(results, {"id": row["id"], "stage": stage, "result": result})
                record[stage] = result
                checkpoint()
                return result

            for row, record in zip(rows, records, strict=True):
                result = call(
                    "generation",
                    row,
                    record,
                    row["prepared"],
                    generation_model if generation_model is not None else configured["generation"],
                )
                if result["status"] not in ("answered", "insufficient_context"):
                    record["judging"] = _skipped("invalid_generation")
                    if result["status"] == "provider_error":
                        state = "failed"
                        break
                    checkpoint()
                    continue
                prepared = prepare_judgment(result, references[row["case_id"]], rubric)
                payload = configured["judging"].request_payload(prepared["messages"])
                template = judgment_messages(
                    row["prepared"]["question"],
                    None,
                    row["prepared"]["context"]["evidence"],
                    references[row["case_id"]],
                    rubric,
                )
                allowance = (
                    estimate_input_tokens(configured["judging"].request_payload(template))
                    + MAX_ANSWER_BYTES
                )
                if estimate_input_tokens(payload) > allowance:
                    record["judging"] = _skipped("input_exceeds_approved_estimate")
                    state = "failed"
                    break
                judgment = call(
                    "judging",
                    row,
                    record,
                    prepared,
                    judge_model if judge_model is not None else configured["judging"],
                )
                if judgment["status"] == "provider_error":
                    state = "failed"
                    break
            else:
                state = (
                    "complete"
                    if all(record["judging"]["status"] == "scored" for record in records)
                    else "complete_with_failures"
                )
    except BaseException:
        state = "interrupted"
        raise
    finally:
        summary = checkpoint()
    return summary
