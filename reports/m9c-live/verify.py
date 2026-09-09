"""Offline audit of the one approved M9c live run. Never executes a model or plan."""

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from structure_aware_retrieval.qa.answering import complete_question, validate_answer
from structure_aware_retrieval.qa.provider import _parse_response
from structure_aware_retrieval.workbench.comparison import load_comparison
from structure_aware_retrieval.workbench.generation import (
    PREPARED_FIELDS,
    load_generation_execution,
    load_generation_plan,
    validate_generation_approval,
)

PLAN_ID = "e74fbce9735446779c6917e42059da57"
PLAN_FINGERPRINT = "aaca5e28861cfa28179cbcdbea8b6574e9a6db72169299d3744f96ff803dd7f4"
MODEL = "gpt-5.4-mini-2026-03-17"
BUDGET = 0.10
TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cached_tokens",
    "reasoning_tokens",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same_number(left, right):
    return (
        left is right if left is None or right is None else math.isclose(left, right, abs_tol=1e-12)
    )


def audit(workspace: Path) -> dict:
    """Verify saved provenance and accounting without changing workspace files."""
    plan = load_generation_plan(workspace, PLAN_ID)
    require(plan["fingerprint"] == PLAN_FINGERPRINT, "Approved plan fingerprint changed")
    require(plan["model"] == MODEL, "Approved model changed")
    require(plan["request_limit"] == 5 and plan["judge_calls"] == 0, "Approved scope changed")
    require(plan["estimated_cost_usd"] <= BUDGET, "Plan estimate exceeds approved budget")
    original = load_comparison(workspace, plan["preview_run_id"])
    require(original == plan["preview"], "Original preview changed")
    run = load_generation_execution(workspace, PLAN_ID)
    require(run is not None and run["status"] != "running", "A terminal saved run is required")

    require(run["mode"] == "model_generation", "Run is not a real generation archive")
    require(run["parent_preview_run_id"] == plan["preview_run_id"], "Wrong parent preview")
    require(run["resources"] == original["resources"], "Source resources changed")
    require(run["question"] == original["question"], "Question changed")
    require(run["generation"]["plan_fingerprint"] == PLAN_FINGERPRINT, "Run/plan binding mismatch")
    require(run["generation"]["budget_usd"] == BUDGET, "Wrong approved budget recorded")
    require(run["generation"]["settings"] == plan["settings"], "Generation settings changed")
    require(run["generation"]["pricing"] == plan["pricing"], "Frozen pricing changed")
    require(run["generation"]["request_limit"] == 5, "Generation request limit changed")
    require(run["generation"]["judge_calls"] == 0, "Unexpected judge calls")
    require(run["benchmark_metrics"] is None, "Unlabeled question has benchmark metrics")
    require(run["relevance_labels"] == "unlabeled", "Unexpected relevance label status")
    require(run["settings"]["answer_model"] == MODEL, "Wrong shared answering model")
    require(run["settings"]["max_output_tokens"] == 1024, "Wrong output budget")

    returned, unknown, not_run = [], 0, 0
    rows = []
    for current, prior, proposal in zip(
        run["results"], original["results"], plan["strategies"], strict=True
    ):
        strategy = current["strategy"]
        require(strategy == prior["strategy"] == proposal["strategy"], "Strategy ordering changed")
        for field in ("hits", "ranked_candidates", "structure_stats"):
            require(
                current[field] == prior[field], f"{strategy}: saved retrieval/provenance changed"
            )
        for field in ("resource_load", "retrieval", "context_and_prompt"):
            require(
                current["timing_ms"][field] == prior["timing_ms"][field],
                f"{strategy}: retrieval timing changed",
            )
        qa = current["qa"]
        for field in PREPARED_FIELDS:
            require(qa[field] == prior["qa"][field], f"{strategy}: frozen QA inputs changed")
        require(
            qa["messages"] == proposal["request_payload"]["input"], f"{strategy}: payload mismatch"
        )
        prepared = {key: qa[key] for key in PREPARED_FIELDS}
        prepared["timing_ms"] = {
            key: qa["timing_ms"][key] for key in ("retrieval", "context_and_prompt")
        }
        source_audit = complete_question(prepared, model=None)
        require(source_audit["model_called"] is False, "Source audit unexpectedly called a model")
        for field in ("paths_valid", "line_ranges_valid", "evidence_ids_valid"):
            require(
                source_audit["automatic_checks"][field] == qa["automatic_checks"][field],
                f"{strategy}: invalid source checks",
            )
        require(qa["llm_assessment"]["status"] == "not_run", "Unexpected semantic assessment")
        require(qa["evaluation"]["answer_correctness"] is None, "Unexpected correctness score")
        require(qa["evaluation"]["citation_support"] is None, "Unexpected semantic citation score")
        require(current["cost"]["billed_usd"] is None, "Estimated charge represented as invoice")
        require(
            same_number(current["cost"]["plan_estimated_usd"], proposal["estimated_cost_usd"]),
            "Per-strategy estimate changed",
        )

        state = current["execution"]["state"]
        provider = qa.get("provider") or {}
        if state == "returned":
            returned.append(current)
            require(
                qa["model_called"] is True, f"{strategy}: returned response without model attempt"
            )
            require(current["cost"]["model_calls"] == 1, f"{strategy}: incorrect call count")
            raw = provider.get("raw_response")
            require(isinstance(raw, dict), f"{strategy}: raw response missing")
            require(
                provider.get("request_id") and provider.get("response_id"),
                f"{strategy}: provider IDs missing",
            )
            require(
                provider["model"] == MODEL,
                f"{strategy}: provider model differs from approved snapshot",
            )
            if current["status"] in {"answered", "insufficient_context", "invalid_answer"}:
                reparsed = asdict(_parse_response(raw, provider["request_id"]))
                require(
                    reparsed.pop("text") == qa["raw_output"],
                    f"{strategy}: raw answer extraction mismatch",
                )
                require(reparsed == provider, f"{strategy}: provider archive mismatch")
            if current["status"] in {"answered", "insufficient_context"}:
                validated = validate_answer(qa["raw_output"], qa["context"]["evidence"])
                require(
                    validated == qa["answer"], f"{strategy}: answer/citation validation mismatch"
                )
            for short, field in (
                ("input", "input_tokens"),
                ("output", "output_tokens"),
                ("total", "total_tokens"),
                ("cached", "cached_tokens"),
                ("reasoning", "reasoning_tokens"),
            ):
                require(
                    current["tokens"][short] == provider["usage"].get(field),
                    f"{strategy}: token metadata mismatch",
                )
            usage = provider["usage"]
            input_tokens, output_tokens = usage.get("input_tokens"), usage.get("output_tokens")
            cost = (
                None
                if input_tokens is None or output_tokens is None
                else (
                    input_tokens * plan["pricing"]["input_per_million"]
                    + output_tokens * plan["pricing"]["output_per_million"]
                )
                / 1_000_000
            )
            require(
                same_number(current["cost"]["estimated_usd"], cost),
                f"{strategy}: usage cost mismatch",
            )
        elif state == "outcome_unknown":
            unknown += 1
        elif state == "not_run":
            not_run += 1
        else:
            raise ValueError(f"Unexpected terminal execution state: {state}")
        rows.append(
            {
                "strategy": strategy,
                "status": current["status"],
                "execution_state": state,
                "tokens": current["tokens"],
                "estimated_cost_usd": current["cost"]["estimated_usd"],
                "generation_ms": current["timing_ms"]["generation"],
                "citation_ids_valid": qa["automatic_checks"]["citation_ids_valid"],
                "provider_model": provider.get("model"),
                "raw_response_saved": bool(provider.get("raw_response")),
            }
        )

    summary = run["generation"]["summary"]
    require(
        summary["calls_started"] == len(returned) + unknown == run["api_calls"] <= 5,
        "Started call accounting mismatch",
    )
    require(summary["responses_received"] == len(returned), "Response count mismatch")
    require(
        summary["outcome_unknown"] == unknown and summary["not_run"] == not_run,
        "Unknown/unstarted counts mismatch",
    )
    for field in TOKEN_FIELDS:
        values = [row["qa"]["provider"]["usage"].get(field) for row in returned]
        missing = unknown + sum(type(value) is not int or value < 0 for value in values)
        observed = sum(value for value in values if type(value) is int and value >= 0)
        require(
            summary["usage"]["observed_token_subtotals"][field] == observed,
            "Observed subtotal mismatch",
        )
        require(
            summary["usage"]["calls_missing_token_counts"][field] == missing,
            "Unknown token count mismatch",
        )
        require(
            summary["usage"]["tokens"][field] == (None if missing else observed),
            "Aggregate token mismatch",
        )
    totals = summary["usage"]["tokens"]
    projected = (
        None
        if totals["input_tokens"] is None or totals["output_tokens"] is None
        else (
            totals["input_tokens"] * plan["pricing"]["input_per_million"]
            + totals["output_tokens"] * plan["pricing"]["output_per_million"]
        )
        / 1_000_000
    )
    require(
        same_number(summary["usage"]["cost_usd_at_frozen_uncached_rates"], projected),
        "Aggregate cost mismatch",
    )
    try:
        validate_generation_approval(workspace, PLAN_ID, budget_usd=BUDGET, confirmed_model=MODEL)
    except FileExistsError:
        pass
    else:
        raise ValueError("Consumed plan unexpectedly passed read-only repeat-execution preflight")

    report = {
        "audit_status": "passed",
        "scope": "offline integrity, citation identity, accounting; no semantic grading",
        "plan_id": PLAN_ID,
        "run_id": run["run_id"],
        "run_status": run["status"],
        "source_commit": run["resources"]["source"]["commit"],
        "model": MODEL,
        "api_calls": run["api_calls"],
        "judge_calls": 0,
        "approved_budget_usd": BUDGET,
        "plan_estimated_cost_usd": plan["estimated_cost_usd"],
        "usage": summary["usage"],
        "results": rows,
        "original_preview_fingerprint": original["fingerprint"],
        "run_file_sha256": hashlib.sha256(
            (workspace / "runs" / run["run_id"] / "run.json").read_bytes()
        ).hexdigest(),
        "limitations": [
            "No semantic answer correctness measured",
            "Frozen uncached-rate usage projection is not an invoice",
            "One question is a workflow validation, not a strategy benchmark",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace", type=Path, required=True, help="Extracted saved-run workspace"
    )
    parser.add_argument(
        "--output", type=Path, help="Optional report file outside the saved workspace"
    )
    args = parser.parse_args()
    if args.output is not None and args.output.resolve().is_relative_to(args.workspace.resolve()):
        parser.error("--output must stay outside the saved workspace; verification is read-only")
    try:
        report = audit(args.workspace)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Archive verification failed: {error}\n")
    text = json.dumps(report, indent=2) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
