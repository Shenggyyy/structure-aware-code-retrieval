"""Report a disjoint follow-up batch without erasing its parent's missing outcomes."""

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.assessment_reporting import (
    DIMENSION_STATES,
    DIMENSIONS,
    _attempt_index,
    _cell,
    _display,
    _stage,
)
from structure_aware_retrieval.qa.judge_reporting import _indexed, summarize_revision


def _validate(
    plan: dict,
    prior_plan: dict,
    prior_records: list[dict],
    prior_attempts: list[dict],
    records: list[dict],
    attempts: list[dict],
) -> None:
    _indexed(prior_plan, prior_records, prior_attempts)
    shared = (
        "source_run",
        "source_records_fingerprint",
        "source_generation_model",
        "judge",
        "annotation_status",
        "rubric_id",
        "source_planned_count",
        "omitted",
    )
    if (
        plan["kind"] != "qa_judge_followup_plan"
        or prior_plan["kind"] != "qa_judge_revision_plan"
        or any(plan[field] != prior_plan[field] for field in shared)
    ):
        raise ValueError("Follow-up must retain its parent's source and judge configuration")
    if plan["prior_records_fingerprint"] != stable_id(prior_records) or plan[
        "prior_attempts_fingerprint"
    ] != stable_id(prior_attempts):
        raise ValueError("Prior records and attempts differ from the frozen follow-up plan")
    prior_ids = [attempt["id"] for attempt in prior_attempts]
    prior_set = set(prior_ids)
    if prior_ids != prior_plan["request_order"][: len(prior_ids)]:
        raise ValueError("Prior attempts must be an ordered prefix of their frozen plan")
    remaining = [identity for identity in prior_plan["request_order"] if identity not in prior_set]
    if plan["request_order"] != remaining or plan["request_count"] != len(remaining):
        raise ValueError("Follow-up must contain exactly the previously unattempted requests")
    by_id = {row["id"]: row for row in prior_records}
    excluded = [
        {
            **{
                field: by_id[identity][field]
                for field in ("id", "case_id", "strategy", "repository")
            },
            "status": (by_id[identity]["judging"] or {}).get("status", "unknown_outcome"),
        }
        for identity in prior_ids
    ]
    if plan["excluded_prior_attempts"] != excluded:
        raise ValueError("Excluded prior attempt identities and outcomes must remain exact")
    if [row["id"] for row in records] != [row["id"] for row in prior_records]:
        raise ValueError("Follow-up records must retain the complete ordered source population")
    for old, new in zip(prior_records, records, strict=True):
        if old["id"] not in remaining:
            if old != new:
                raise ValueError("Prior judging results and unknown outcomes are immutable")
        elif old["judging"] is not None or {
            key: value for key, value in old.items() if key != "judging"
        } != {key: value for key, value in new.items() if key != "judging"}:
            raise ValueError("Follow-up may only fill judging for previously unattempted records")
    if [attempt["id"] for attempt in attempts] != remaining[: len(attempts)]:
        raise ValueError("New attempts must be an ordered prefix disjoint from prior attempts")
    _indexed(prior_plan, records, prior_attempts + attempts)


def _scoped_stage(plan: dict, records: list[dict], attempts: list[dict]) -> dict:
    indexed = _attempt_index(records, attempts)
    stage = _stage(plan, records, indexed, "judging")
    stage["per_strategy"] = {
        name: _stage(plan, [row for row in records if row["strategy"] == name], indexed, "judging")
        for name in sorted({row["strategy"] for row in records})
    }
    return stage


def summarize_followup(
    plan: dict,
    prior_plan: dict,
    prior_records: list[dict],
    prior_attempts: list[dict],
    records: list[dict],
    attempts: list[dict],
    *,
    status: str,
) -> dict:
    """Separate batch accounting from cumulative ordinal scores on the entire source cohort."""
    _validate(plan, prior_plan, prior_records, prior_attempts, records, attempts)
    prior_ids = {attempt["id"] for attempt in prior_attempts}
    remaining = set(plan["request_order"])
    prior_judging = _scoped_stage(
        prior_plan, [row for row in prior_records if row["id"] in prior_ids], prior_attempts
    )
    new_judging = _scoped_stage(plan, [row for row in records if row["id"] in remaining], attempts)
    cumulative = summarize_revision(prior_plan, records, prior_attempts + attempts, status=status)
    judging = cumulative["overall"]["judging"]
    cumulative_status = (
        "incomplete"
        if judging["unknown_outcome_count"] or judging["not_run_count"]
        else "complete_with_failures"
        if judging["failed_count"] or judging["omitted_count"]
        else "complete"
    )
    return {
        "schema_version": 1,
        "kind": "qa_judge_followup_summary",
        "plan_fingerprint": plan["plan_fingerprint"],
        "prior_plan_fingerprint": prior_plan["plan_fingerprint"],
        "source_records_fingerprint": plan["source_records_fingerprint"],
        "source_generation_model": plan["source_generation_model"],
        "rubric_id": plan["rubric_id"],
        "status": status,
        "cumulative_status": cumulative_status,
        "prior_execution_mode": plan["prior_run"]["execution_mode"],
        "new_generation_calls": 0,
        "annotation_status": plan["annotation_status"],
        "evaluation_kind": "llm_assisted_ordinal",
        "human_reviewed": False,
        "estimated_cost": plan["estimated_cost"],
        "prior_judging": prior_judging,
        "new_judging": new_judging,
        "cumulative": {
            "status": cumulative_status,
            "overall": cumulative["overall"],
            "per_strategy": cumulative["per_strategy"],
            "paired_comparisons": cumulative["paired_comparisons"],
            "judging": judging,
        },
        **{key: cumulative[key] for key in ("overall", "per_strategy", "paired_comparisons")},
        "policy": {
            "scores": cumulative["policy"]["scores"],
            "references": cumulative["policy"]["references"],
            "source": "Historical answers and automatic citation ID/path/line checks are "
            "retained unchanged. Automatic checks do not establish semantic support. "
            "Original v1 judge scores and generation costs are excluded.",
            "scope": "The new batch contains only previously unattempted requests. Prior "
            "judgments and unknown outcomes are retained without retry or replacement. "
            "Batch completion does not establish complete source-cohort coverage.",
            "provenance": "Cumulative scores combine the preserved parent and new batch. "
            "Read both execution modes: injected-model fixtures, including fixtures mixed "
            "with historical live results, do not establish a cumulative live evaluation.",
            "unknown_outcomes": cumulative["policy"]["unknown_outcomes"],
            "cost": "Prior judging covers only prior attempts; new judging covers only the "
            "follow-up request population. Cumulative usage counts each attempt once. "
            "Historical generation costs are never included. Known subtotals omit missing "
            "components; any missing usage keeps the corresponding cumulative totals unknown. "
            "Costs are projections at frozen uncached rates, not invoices or budget guarantees.",
            "timing": "Latency is judge-call plus validation time. Prior latency uses prior "
            "attempts as its denominator; new latency uses follow-up requests; cumulative "
            "latency uses all eligible source requests. Missing outcomes stay missing. "
            "No combined generation latency or wall-clock service latency is inferred.",
            "pairing": cumulative["policy"]["pairing"],
        },
    }


def render_followup(summary: dict) -> str:
    """Render separate batch and cumulative outcomes with coverage and provenance boundaries."""
    mode = summary.get("execution_mode", "unspecified")
    prior_mode = summary["prior_execution_mode"]
    lines = [
        "# Follow-Up LLM-Assisted QA Assessment",
        "",
        f"New batch status: {_cell(summary['status'])}. "
        f"Cumulative cohort status: {_cell(summary['cumulative_status'])}.",
        f"Labels: {_cell(summary['annotation_status'])}. New generation calls: 0.",
        f"New execution mode: {_cell(mode)}. Prior execution mode: {_cell(prior_mode)}.",
    ]
    if "injected_models" in (mode, prior_mode):
        lines.append(
            "Offline injected-model fixture results are present; this report does not "
            "establish a cumulative live evaluation."
        )
    elif mode != "openai" or prior_mode != "openai":
        lines.append("Execution provenance does not establish a cumulative live evaluation.")
    lines.extend(
        [
            "",
            *[summary["policy"][key] for key in ("scope", "scores", "source", "references")],
            "",
            "## Prior, new and cumulative judging",
            "",
            summary["policy"]["cost"],
            summary["policy"]["unknown_outcomes"],
            "",
            "| Scope | Cases | Attempts | Scored judgments | Failed | Unknown | Not run "
            "| Input tokens | Output tokens | Cost USD | Known cost subtotal USD |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, judge in (
        ("Prior attempts", summary["prior_judging"]),
        ("New batch", summary["new_judging"]),
        ("Cumulative source cohort", summary["cumulative"]["judging"]),
    ):
        lines.append(
            f"| {name} | {judge['planned_case_count']} | {judge['attempted_count']} "
            f"| {judge['completed_count']} | {judge['failed_count']} "
            f"| {judge['unknown_outcome_count']} | {judge['not_run_count']} "
            f"| {_cell(judge['tokens']['input_tokens'])} "
            f"| {_cell(judge['tokens']['output_tokens'])} "
            f"| {_display(judge['cost_usd_at_frozen_uncached_rates'])} "
            f"| {_display(judge['observed_cost_subtotal_usd_at_frozen_uncached_rates'])} |"
        )
    lines.extend(
        [
            "",
            "## Cumulative ordinal scores and coverage",
            "",
            summary["policy"]["provenance"],
            "",
            "| Strategy | Source cases | Dimension | Mean (0-3) | Scored | Unsure | N/A "
            "| Invalid source | Invalid judgment | Not run | Unknown outcome |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, metrics in summary["per_strategy"].items():
        for dimension in DIMENSIONS:
            values = metrics["dimensions"][dimension]
            counts = " | ".join(str(values[f"{state}_count"]) for state in DIMENSION_STATES)
            lines.append(
                f"| {_cell(name)} | {metrics['planned_case_count']} | {dimension} "
                f"| {_display(values['mean'])} | {counts} |"
            )
    lines.extend(
        [
            "",
            "## Matched comparisons",
            "",
            summary["policy"]["pairing"],
            "",
            "| Baseline | Candidate | Dimension | Paired cases | Mean delta |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for pair in summary["paired_comparisons"]:
        lines.append(
            f"| {_cell(pair['baseline'])} | {_cell(pair['candidate'])} "
            f"| {pair['dimension']} | {pair['paired_count']} | {_display(pair['mean_delta'])} |"
        )
    lines.extend(
        [
            "",
            "## Timing and retained evidence",
            "",
            summary["policy"]["timing"],
            "Per-scope latency, token subtotals, missing counts and exact shared case IDs are "
            "in summary.json. Parent judgments remain preserved; new raw results are in "
            "results.jsonl. No human-review or true-accuracy claim is made.",
            "",
        ]
    )
    return "\n".join(lines)
