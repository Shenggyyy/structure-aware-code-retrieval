"""Frozen, explicitly approved five-strategy answers with durable single-use attempts."""

import math
import os
import re
import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import complete_question
from structure_aware_retrieval.qa.assessment_plan import estimate_input_tokens
from structure_aware_retrieval.qa.execution import _usage
from structure_aware_retrieval.qa.provider import AnswerModel, OpenAIModel
from structure_aware_retrieval.workbench.comparison import _now, _save, load_comparison
from structure_aware_retrieval.workbench.storage import (
    read_json,
    safe_path,
    workspace_root,
    write_json,
)

GENERATION_MODEL = "gpt-5.4-mini-2026-03-17"
MAX_CONTEXT_TOKENS = 400_000
SETTINGS = {
    "model": GENERATION_MODEL,
    "max_output_tokens": 1024,
    "reasoning_effort": "none",
    "api_key_env": "OPENAI_API_KEY",
    "timeout_seconds": 60,
}
PRICING = {
    "input_per_million": 0.75,
    "output_per_million": 4.50,
    "source_url": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
    "as_of": "2026-09-09",
}
ESTIMATE_NOTE = (
    "Conservative input proxy: UTF-8 message and schema/settings bytes plus 4096 framing "
    "tokens, with the full output token limit at frozen uncached rates. This is not an "
    "exact tokenizer count, invoice, or billing hard cap. No LLM judge is included."
)
PREPARED_FIELDS = (
    "schema_version",
    "question",
    "context",
    "messages",
    "prompt_version",
    "prompt_fingerprint",
)


def _plan_path(plan_id: str, filename: str = "plan.json") -> str:
    if not isinstance(plan_id, str) or not re.fullmatch(r"[0-9a-f]{32}", plan_id):
        raise ValueError("Generation plan ID must be 32 lowercase hexadecimal characters")
    return f"generation-plans/{plan_id}/{filename}"


def _fingerprint(value: dict) -> str:
    return stable_id({key: item for key, item in value.items() if key != "fingerprint"})


def _prepared(qa: dict) -> dict:
    try:
        result = {key: deepcopy(qa[key]) for key in PREPARED_FIELDS}
        result["timing_ms"] = {
            key: qa["timing_ms"][key] for key in ("retrieval", "context_and_prompt")
        }
        if any(
            type(value) not in (int, float) or not math.isfinite(value) or value < 0
            for value in result["timing_ms"].values()
        ):
            raise ValueError("Invalid prepared retrieval timing")
        # Reuse the complete prompt/source audit without making any model call.
        complete_question(result)
        return result
    except (KeyError, TypeError) as error:
        raise ValueError("Malformed preview QA record") from error


def _details(preview: dict) -> dict:
    if preview.get("mode") != "context_preview" or preview.get("status") not in {
        "preview_complete",
        "partial",
        "failed",
    }:
        raise ValueError("Generation requires a finished context preview")
    question = preview.get("question")
    if (
        not isinstance(question, str)
        or not question.strip()
        or len(question.encode("utf-8")) > 4000
    ):
        raise ValueError("Preview question must be nonblank and within 4000 UTF-8 bytes")
    settings, resources = preview.get("settings"), preview.get("resources")
    if not isinstance(settings, dict) or not isinstance(resources, dict):
        raise ValueError("Preview settings and resource snapshot are required")
    model = OpenAIModel(**SETTINGS)
    strategies = []
    for row in preview["results"]:
        payload = None
        status = "unavailable"
        if row.get("status") in {"preview", "insufficient_context"}:
            prepared = _prepared(row["qa"])
            if prepared["question"] != preview["question"]:
                raise ValueError("Preview question does not match its frozen prompt")
            context = prepared["context"]
            if (
                context["snapshot_id"] != resources.get("snapshot_id")
                or stable_id(context["config"]["top_k"]) != stable_id(settings.get("context_top_k"))
                or stable_id(context["config"]["max_context_bytes"])
                != stable_id(settings.get("max_context_bytes"))
            ):
                raise ValueError("Preview context differs from its resource snapshot or settings")
            if prepared["context"]["evidence"]:
                payload = model.request_payload(prepared["messages"])
                status = "ready"
            else:
                status = "no_evidence"
        input_tokens = estimate_input_tokens(payload) if payload is not None else 0
        output_tokens = SETTINGS["max_output_tokens"] if payload is not None else 0
        if input_tokens + output_tokens > MAX_CONTEXT_TOKENS:
            raise ValueError(
                "Conservative input plus output estimate exceeds the model context window; "
                "create a new preview with a smaller context budget"
            )
        strategies.append(
            {
                "strategy": row["strategy"],
                "status": status,
                "estimated_input_tokens": input_tokens,
                "max_output_tokens": output_tokens,
                "estimated_cost_usd": (
                    input_tokens * PRICING["input_per_million"]
                    + output_tokens * PRICING["output_per_million"]
                )
                / 1_000_000,
                "request_payload": payload,
            }
        )
    return {
        "preview_run_id": preview["run_id"],
        "preview_fingerprint": preview["fingerprint"],
        "repository_id": preview["repository_id"],
        "question": preview["question"],
        "model": GENERATION_MODEL,
        "settings": deepcopy(SETTINGS),
        "pricing": deepcopy(PRICING),
        "request_limit": sum(row["status"] == "ready" for row in strategies),
        "judge_calls": 0,
        "context_window_tokens": MAX_CONTEXT_TOKENS,
        "estimated_cost_usd": sum(row["estimated_cost_usd"] for row in strategies),
        "strategies": strategies,
        "estimate_note": ESTIMATE_NOTE,
        "preview": deepcopy(preview),
    }


def create_generation_plan(workspace: Path, preview_run_id: str) -> dict:
    """Freeze exact evidence and payloads offline; this never reads an API key."""
    root = workspace_root(workspace, create=True)
    preview = load_comparison(root, preview_run_id)
    plan = {
        "schema_version": 1,
        "kind": "five_strategy_generation_plan",
        "plan_id": uuid4().hex,
        "created_at": _now(),
        **_details(preview),
    }
    plan["fingerprint"] = _fingerprint(plan)
    safe_path(root, _plan_path(plan["plan_id"])).parent.mkdir(parents=True, exist_ok=False)
    write_json(root, _plan_path(plan["plan_id"]), plan)
    return plan


def load_generation_plan(workspace: Path, plan_id: str) -> dict:
    """Validate saved settings, estimates and source bindings before use."""
    plan = read_json(workspace, _plan_path(plan_id))
    try:
        if (
            plan["schema_version"] != 1
            or plan["kind"] != "five_strategy_generation_plan"
            or plan["plan_id"] != plan_id
            or plan["fingerprint"] != _fingerprint(plan)
            or plan["preview"]["fingerprint"] != _fingerprint(plan["preview"])
        ):
            raise ValueError("Generation plan identity or checksum mismatch")
        # Recompute instead of trusting even a rehashed low-cost or altered-model plan.
        expected = _details(plan["preview"])
        if any(stable_id(plan.get(key)) != stable_id(value) for key, value in expected.items()):
            raise ValueError("Generation plan configuration or estimate mismatch")
        original = load_comparison(workspace, plan["preview_run_id"])
        if original["fingerprint"] != plan["preview_fingerprint"]:
            raise ValueError("The preview changed after the generation plan was frozen")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed generation plan") from error
    return plan


def validate_generation_approval(
    workspace: Path,
    plan_id: str,
    *,
    budget_usd: float,
    confirmed_model: str,
    model: AnswerModel | None = None,
) -> dict:
    """Read-only preflight; execution still atomically claims this plan afterwards."""
    plan = load_generation_plan(workspace, plan_id)
    if confirmed_model != plan["model"]:
        raise ValueError("Confirm the exact model recorded in this generation plan")
    if (
        type(budget_usd) not in (int, float)
        or not math.isfinite(budget_usd)
        or budget_usd <= 0
        or budget_usd < plan["estimated_cost_usd"]
    ):
        raise ValueError("Budget must be finite, positive, and cover the full plan estimate")
    if safe_path(workspace, _plan_path(plan_id, "execution")).exists():
        raise FileExistsError("This generation plan was already consumed; it will not be retried")
    if model is None and plan["request_limit"]:
        key = os.environ.get(SETTINGS["api_key_env"])
        if not key:
            raise ValueError("Set OPENAI_API_KEY in the server environment before generation")
        if not re.fullmatch(r"[!-~]+", key):
            raise ValueError("The configured API key contains invalid characters")
    return plan


def _acquire_lock(path: Path):
    """Process lock released by the OS on exit; permanent claim is never deleted."""
    handle = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            if not handle.read(1):
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        handle.close()
        raise
    return handle


def _summary(record: dict) -> None:
    rows = record["results"]
    returned = [row for row in rows if row["execution"]["state"] == "returned"]
    unknown = sum(row["execution"]["state"] in {"started", "outcome_unknown"} for row in rows)
    calls = len(returned) + unknown
    usage = _usage(
        [{"result": row["qa"]} for row in returned], unknown, record["generation"]["pricing"]
    )
    record["api_calls"] = calls if record["mode"] == "model_generation" else 0
    record["generation"]["summary"] = {
        "calls_started": calls,
        "responses_received": len(returned),
        "outcome_unknown": unknown,
        "not_run": sum(row["execution"]["state"] in {"pending", "not_run"} for row in rows),
        "usage": usage,
        "call_note": "Started attempts are persisted before sending; an interrupted attempt may "
        "have been billed even when its response is unknown. "
        "Injected test models make no API calls.",
    }


def _interrupt(record: dict) -> None:
    for row in record["results"]:
        state = row["execution"]["state"]
        if state in {"started", "pending"}:
            row["execution"]["state"] = "outcome_unknown" if state == "started" else "not_run"
            row["status"] = row["execution"]["state"]
            row["error"] = {
                "type": "InterruptedExecution",
                "message": "No automatic retry. The started request may have been processed."
                if state == "started"
                else "Generation was stopped before this strategy was called.",
            }
    record["status"] = "interrupted"
    record["finished_at"] = _now()
    _summary(record)


def load_generation_execution(workspace: Path, plan_id: str) -> dict | None:
    """Locate only the child explicitly bound to this consumed plan."""
    claim_path = _plan_path(plan_id, "execution/claim.json")
    if not safe_path(workspace, claim_path).exists():
        return None
    claim = read_json(workspace, claim_path)
    if claim.get("plan_id") != plan_id or claim.get("fingerprint") != _fingerprint(claim):
        raise ValueError("Generation execution claim checksum mismatch")
    run_id = claim.get("run_id")
    if not isinstance(run_id, str) or not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise ValueError("Generation execution has an invalid child ID")
    if not safe_path(workspace, f"runs/{run_id}/run.json").exists():
        return None
    record = load_comparison(workspace, run_id)
    generation = record.get("generation", {})
    if (
        generation.get("plan_id") != plan_id
        or generation.get("plan_fingerprint") != claim.get("plan_fingerprint")
        or record.get("mode") not in {"model_generation", "offline_test"}
        or not all(isinstance(row.get("execution"), dict) for row in record["results"])
    ):
        raise ValueError("Generation execution does not match the consumed plan")
    return record


def recover_generation(workspace: Path) -> None:
    """Reconcile only abandoned linked executions; never send or repeat requests."""
    directory = safe_path(workspace, "generation-plans")
    if not directory.exists():
        return
    for folder in directory.iterdir():
        if not re.fullmatch(r"[0-9a-f]{32}", folder.name):
            continue
        try:
            lock_path = safe_path(workspace, _plan_path(folder.name, "execution/active.lock"))
            if not lock_path.exists():
                continue
            with _acquire_lock(lock_path):
                record = load_generation_execution(workspace, folder.name)
                if record is not None and record["status"] == "running":
                    _interrupt(record)
                    _save(workspace, record)
        except (OSError, ValueError, KeyError, TypeError):
            # Active or corrupt records stay intact and can be inspected through history.
            continue


class _JournaledModel:
    def __init__(self, model: AnswerModel, row: dict, save: Callable):
        self.model = model
        self.row = row
        self.save = save

    def complete(self, messages):
        self.row["execution"].update(state="started", started_at=_now())
        self.row["status"] = "running"
        self.row["cost"]["model_calls"] = 1
        self.save(notify=False)
        started = time.perf_counter()
        try:
            return self.model.complete(messages)
        finally:
            self.row["timing_ms"]["generation"] = (time.perf_counter() - started) * 1000


def execute_generation_plan(
    workspace: Path,
    plan_id: str,
    *,
    budget_usd: float,
    confirmed_model: str,
    model: AnswerModel | None = None,
    on_progress: Callable[[dict], None] | None = None,
) -> dict:
    """Consume one approved plan once; each request is journaled before transmission."""
    root = workspace_root(workspace)
    plan = validate_generation_approval(
        root, plan_id, budget_usd=budget_usd, confirmed_model=confirmed_model, model=model
    )
    execution = safe_path(root, _plan_path(plan_id, "execution"))
    try:
        execution.mkdir(exist_ok=False)
    except FileExistsError:
        raise FileExistsError(
            "This generation plan was already consumed; no retry was made"
        ) from None
    with _acquire_lock(safe_path(root, _plan_path(plan_id, "execution/active.lock"))):
        record = deepcopy(plan["preview"])
        record.update(
            run_id=uuid4().hex,
            parent_preview_run_id=plan["preview_run_id"],
            mode="model_generation" if model is None else "offline_test",
            status="running",
            created_at=_now(),
            finished_at=None,
            elapsed_ms=None,
            generation={
                "plan_id": plan_id,
                "plan_fingerprint": plan["fingerprint"],
                "preview_fingerprint": plan["preview_fingerprint"],
                "settings": deepcopy(plan["settings"]),
                "pricing": deepcopy(plan["pricing"]),
                "budget_usd": budget_usd,
                "estimated_cost_usd": plan["estimated_cost_usd"],
                "request_limit": plan["request_limit"],
                "judge_calls": 0,
                "retrieval_reused": True,
                "execution_mode": "openai" if model is None else "injected_model",
            },
        )
        record["settings"].update(
            generation_enabled=True,
            answer_model=plan["model"],
            max_output_tokens=plan["settings"]["max_output_tokens"],
            reasoning_effort=plan["settings"]["reasoning_effort"],
        )
        for row, planned in zip(record["results"], plan["strategies"], strict=True):
            state = {
                "ready": "pending",
                "no_evidence": "not_required",
                "unavailable": "retrieval_failed",
            }[planned["status"]]
            row["execution"] = {"state": state, "started_at": None, "finished_at": None}
            row["cost"]["plan_estimated_usd"] = planned["estimated_cost_usd"]
            if state == "pending":
                row["status"] = "pending"
        claim = {
            "plan_id": plan_id,
            "plan_fingerprint": plan["fingerprint"],
            "run_id": record["run_id"],
            "created_at": _now(),
        }
        claim["fingerprint"] = _fingerprint(claim)
        write_json(root, _plan_path(plan_id, "execution/claim.json"), claim)
        actual_model = model if model is not None else OpenAIModel(**plan["settings"])
        started = time.perf_counter()

        def save(*, notify: bool = True) -> None:
            _summary(record)
            _save(root, record)
            if notify and on_progress is not None:
                on_progress(deepcopy(record))

        try:
            save()
            for row in record["results"]:
                if row["execution"]["state"] != "pending":
                    continue
                prepared = _prepared(row["qa"])
                row["status"] = "running"
                save()
                qa = complete_question(prepared, _JournaledModel(actual_model, row, save))
                generation_ms = row["timing_ms"]["generation"]
                row["qa"] = qa
                row["status"] = qa["status"]
                row["error"] = (
                    {"type": "GenerationError", "message": qa["error"]} if qa["error"] else None
                )
                row["execution"].update(state="returned", finished_at=_now())
                provider = qa.get("provider") or {}
                # HTTP/transport errors without a provider response cannot prove the outcome.
                if qa["status"] == "provider_error" and provider.get("raw_response") is None:
                    row["execution"]["state"] = "outcome_unknown"
                    row["status"] = "outcome_unknown"
                usage = _usage([{"result": qa}], 0, plan["pricing"])
                tokens = usage["tokens"]
                row["tokens"] = {
                    "input": tokens["input_tokens"],
                    "output": tokens["output_tokens"],
                    "total": tokens["total_tokens"],
                    "cached": tokens["cached_tokens"],
                    "reasoning": tokens["reasoning_tokens"],
                }
                row["cost"]["estimated_usd"] = usage["cost_usd_at_frozen_uncached_rates"]
                row["cost"]["note"] = usage["cost_note"]
                row["timing_ms"]["generation"] = generation_ms
                row["timing_ms"]["automatic_validation"] = max(
                    0, qa["timing_ms"]["generation_and_validation"] - (generation_ms or 0)
                )
                row["timing_ms"]["strategy_total"] = sum(
                    value
                    for key, value in row["timing_ms"].items()
                    if key != "strategy_total" and value is not None
                )
                save()
                if row["status"] == "outcome_unknown":
                    _interrupt(record)
                    break
            else:
                record["status"] = (
                    "generation_complete"
                    if all(
                        row["status"] in {"answered", "insufficient_context"}
                        for row in record["results"]
                    )
                    else "partial"
                )
        except BaseException:
            _interrupt(record)
            record["elapsed_ms"] = (time.perf_counter() - started) * 1000
            save(notify=False)
            raise
        record["finished_at"] = _now()
        record["elapsed_ms"] = (time.perf_counter() - started) * 1000
        save()
        return record
