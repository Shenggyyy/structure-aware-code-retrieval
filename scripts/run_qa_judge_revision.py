"""Execute one explicitly approved, bounded judge-only run over archived answers."""

import argparse
import json
import math
import shutil
import traceback
from copy import deepcopy
from pathlib import Path
from runpy import run_path

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.assessment_execution import _now, _skipped
from structure_aware_retrieval.qa.assessment_plan import implementation_record
from structure_aware_retrieval.qa.execution import _append, _write
from structure_aware_retrieval.qa.judge_reporting import render_revision, summarize_revision
from structure_aware_retrieval.qa.judging import complete_judgment
from structure_aware_retrieval.qa.provider import OpenAIModel

PREPARATION_SCRIPT = Path(__file__).with_name("prepare_qa_judge_revision.py")
PREPARATION = run_path(str(PREPARATION_SCRIPT))
check_revision = PREPARATION["check_revision"]
_model = PREPARATION["_model"]
_hash = PREPARATION["_hash"]
_read = run_path(str(Path(__file__).with_name("verify_qa_assessment.py")))["_read"]
BUNDLE_FILES = (
    *PREPARATION["OUTPUT_FILES"],
    "config.toml",
    "rubric.json",
    *(f"source/{name}" for name in PREPARATION["SOURCE_FILES"]),
)


def execute_revision(
    bundle: Path,
    output: Path,
    *,
    budget_usd: float,
    judge_model_id: str,
    approved_plan: str,
    execute: bool = False,
    model_factory=None,
) -> dict:
    """Freeze exact inputs before calling; inject only offline models for tests.

    Approval is explicit invocation, not identity verification. The projection gate
    is not a billing hard cap. No overwrite, resume, regeneration or retries.
    """
    progress = {
        "output_created": False,
        "phase": "initialize",
        "active_request_id": None,
        "attempted_count": 0,
        "completed_count": 0,
    }
    try:
        return _execute_revision(
            bundle,
            output,
            budget_usd=budget_usd,
            judge_model_id=judge_model_id,
            approved_plan=approved_plan,
            execute=execute,
            model_factory=model_factory,
            progress=progress,
        )
    except BaseException as error:
        _record_interruption(output, error, progress)
        raise


def _record_interruption(output, error, progress):
    """Best-effort metadata only; exception text and traceback source are excluded."""
    try:
        if not progress["output_created"]:
            return
        locations = [
            {
                "file": Path(frame.f_code.co_filename).name,
                "function": frame.f_code.co_name,
                "line": line,
            }
            for frame, line in traceback.walk_tb(error.__traceback__)
        ][-8:]
        diagnostic = {
            "schema_version": 1,
            "status": "interrupted",
            "exception_type": type(error).__name__,
            "phase": progress["phase"],
            "active_request_id": progress["active_request_id"],
            "attempted_count": progress["attempted_count"],
            "completed_count": progress["completed_count"],
            "traceback_locations": locations,
        }
        for attribute in ("errno", "winerror"):
            value = getattr(error, attribute, None)
            if type(value) is int:
                diagnostic[attribute] = value
        # Avoid the checkpoint writer so a failure there can still be diagnosed.
        (output / "interruption.json").write_text(
            json.dumps(diagnostic, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except BaseException:
        # Diagnostics must never replace the original execution exception.
        pass


def _execute_revision(
    bundle,
    output,
    *,
    budget_usd,
    judge_model_id,
    approved_plan,
    execute,
    model_factory,
    progress,
):
    if execute is not True:
        raise ValueError("Explicit --execute approval is required; no calls made")
    plan = check_revision(bundle)
    if approved_plan != plan["plan_fingerprint"] or judge_model_id != plan["judge"]["model"]:
        raise ValueError("Confirm the exact revision plan fingerprint and judge model")
    if (
        type(budget_usd) not in (int, float)
        or not math.isfinite(budget_usd)
        or budget_usd <= 0
        or budget_usd < plan["estimated_cost"]["combined_usd"]
    ):
        raise ValueError("Approved budget must cover the full judge-only projection; no calls made")
    if output.exists() or output.is_symlink():
        raise FileExistsError("Judge run output exists; use a new directory")
    output.mkdir(parents=True, exist_ok=False)
    progress["output_created"] = True
    frozen = output / "prepared"
    for name in BUNDLE_FILES:
        target = frozen / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(bundle / name, target)
    copied_plan = check_revision(frozen)
    if copied_plan != plan:
        raise ValueError("Revision inputs changed while archiving the approved plan")
    # All subsequent reads and calls use the validated copy, not the caller's bundle.
    rows = _read(frozen / "requests.jsonl", lines=True)
    models = []
    for row in rows:
        configured = _model(plan["judge"], row["prepared"])
        if configured.request_payload(row["prepared"]["messages"]) != row["request_payload"]:
            raise ValueError("Frozen request differs from the configured per-answer model")
        if model_factory is None:
            model = configured
        else:
            model = model_factory(deepcopy(plan["judge"]), deepcopy(row["prepared"]))
            if isinstance(model, OpenAIModel):
                raise ValueError(
                    "Injected factories must supply offline models, never OpenAI adapters"
                )
            if getattr(model, "model", None) != judge_model_id or not callable(
                getattr(model, "complete", None)
            ):
                raise ValueError(
                    "Offline model must match the frozen judge ID and implement complete"
                )
            if (
                hasattr(model, "output_schema")
                and model.output_schema != row["prepared"]["output_schema"]
            ):
                raise ValueError("Offline model must use the exact per-answer output schema")
        models.append(model)
    mode = "openai" if model_factory is None else "injected_models"
    approval = {
        "plan_fingerprint": approved_plan,
        "judge_model": judge_model_id,
        "source_run_plan_fingerprint": plan["source_run"]["plan_fingerprint"],
        "budget_usd": budget_usd,
        "recorded_at": _now(),
        "execution_mode": mode,
        "source": "explicit invocation; not an identity verification",
        "execution_implementation": {
            **implementation_record(),
            "runner_script_sha256": _hash(Path(__file__)),
            "preparation_script_sha256": _hash(PREPARATION_SCRIPT),
        },
    }
    _write(output / "approval.json", approval)
    records = _read(frozen / "source/records.json")
    eligible = {row["id"] for row in rows}
    for record in records:
        record["judging"] = (
            None if record["id"] in eligible else _skipped("invalid_source_generation")
        )
    by_id = {row["id"]: row for row in records}
    attempts = []
    state = "running"

    def checkpoint():
        summary = summarize_revision(plan, records, attempts, status=state)
        summary.update(
            execution_mode=mode,
            approved_budget_usd=budget_usd,
            records_fingerprint=stable_id(records),
            attempts_fingerprint=stable_id(attempts),
        )
        _write(output / "records.json", records)
        _write(output / "summary.json", summary)
        (output / "report.md").write_text(render_revision(summary), encoding="utf-8", newline="\n")
        return summary

    try:
        with (
            (output / "attempts.jsonl").open("x", encoding="utf-8", newline="\n") as journal,
            (output / "results.jsonl").open("x", encoding="utf-8", newline="\n") as results,
        ):
            checkpoint()
            for row, model in zip(rows, models, strict=True):
                progress["active_request_id"] = row["id"]
                attempt = {
                    "id": row["id"],
                    "stage": "judging",
                    "attempted_at": _now(),
                    "model_call_planned": True,
                    "request_payload": row["request_payload"],
                    "request_payload_sha256": row["request_payload_sha256"],
                }
                progress["phase"] = "attempt_journal"
                _append(journal, attempt)
                attempts.append(attempt)
                progress["attempted_count"] = len(attempts)
                progress["phase"] = "precall_checkpoint"
                checkpoint()
                progress["phase"] = "model_call"
                result = complete_judgment(deepcopy(row["prepared"]), model)
                result.update(
                    requested_model=judge_model_id,
                    attempted_at=attempt["attempted_at"],
                    request_payload_sha256=attempt["request_payload_sha256"],
                )
                progress["phase"] = "result_journal"
                _append(results, {"id": row["id"], "stage": "judging", "result": result})
                by_id[row["id"]]["judging"] = result
                progress["completed_count"] += 1
                progress["phase"] = "result_checkpoint"
                checkpoint()
                progress["active_request_id"] = None
                if result["status"] == "provider_error":
                    state = "failed"
                    break
            else:
                state = (
                    "complete"
                    if all(r["judging"]["status"] == "scored" for r in records)
                    else "complete_with_failures"
                )
    except BaseException:
        state = "interrupted"
        # Preserve both the original exception and its phase if this write fails too.
        try:
            checkpoint()
        except BaseException:
            pass
        raise
    progress["phase"] = "final_checkpoint"
    try:
        summary = checkpoint()
    except BaseException:
        state = "interrupted"
        raise
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--judge-model", required=True)
    parser.add_argument("--approved-plan", required=True)
    parser.add_argument("--budget-usd", required=True, type=float)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        summary = execute_revision(
            args.bundle,
            args.output,
            budget_usd=args.budget_usd,
            judge_model_id=args.judge_model,
            approved_plan=args.approved_plan,
            execute=args.execute,
        )
    except BaseException as error:
        parser.exit(
            130 if isinstance(error, KeyboardInterrupt) else 1,
            f"Judge-only execution failed ({type(error).__name__}); "
            "inspect interruption.json when present and local plan/run records.\n",
        )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "execution_mode": summary["execution_mode"],
                "plan_fingerprint": summary["plan_fingerprint"],
                "summary": str(args.output / "summary.json"),
            },
            sort_keys=True,
        )
    )
    return 0 if summary["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
