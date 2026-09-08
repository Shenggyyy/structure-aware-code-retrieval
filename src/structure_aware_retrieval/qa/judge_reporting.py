"""Judge-only reporting over immutable historical answers and new ordinal judgments."""

from collections import Counter
from itertools import combinations

from structure_aware_retrieval.qa.assessment_reporting import (
    DIMENSION_STATES,
    DIMENSIONS,
    _attempt_index,
    _cell,
    _display,
    _distribution,
    _stage,
    _state,
)
from structure_aware_retrieval.qa.execution import SUCCESS_STATUSES


def _indexed(plan: dict, records: list[dict], attempts: list[dict]) -> dict:
    indexed = _attempt_index(records, attempts)
    eligible = plan["request_order"]
    omitted = [row["id"] for row in plan["omitted"]]
    identities = {row["id"] for row in records}
    if (
        plan["source_planned_count"] != len(records)
        or plan["request_count"] != len(eligible)
        or len(set(eligible)) != len(eligible)
        or len(set(omitted)) != len(omitted)
        or set(eligible) & set(omitted)
        or set(eligible) | set(omitted) != identities
        or [row["id"] for row in records if row["id"] in eligible] != eligible
    ):
        raise ValueError("Judge revision records must retain the complete source population")
    for attempt in attempts:
        if (
            attempt["stage"] != "judging"
            or attempt["model_call_planned"] is not True
            or attempt["id"] not in eligible
        ):
            raise ValueError("Only eligible new judge attempts belong in revision accounting")
    for row in records:
        generation, judging = row["generation"], row["judging"]
        valid = bool(generation and generation["status"] in SUCCESS_STATUSES)
        if valid != (row["id"] in eligible):
            raise ValueError("Judge revision eligibility differs from the source generation")
        if row["id"] in omitted and (
            not judging
            or judging["status"] != "skipped"
            or judging.get("reason") != "invalid_source_generation"
            or judging["model_called"]
        ):
            raise ValueError("Omitted source generations must remain explicitly skipped")
        if judging and judging["status"] != "skipped" and (row["id"], "judging") not in indexed:
            raise ValueError("Every new judging result requires its attempt")
    return indexed


def _revision_state(row: dict, dimension: str, attempts: dict) -> tuple[str, int | None]:
    generation = row["generation"]
    if not generation or generation["status"] not in SUCCESS_STATUSES:
        return "invalid_generation", None
    return _state(row, dimension, attempts)


def _metrics(plan: dict, records: list[dict], attempts: dict) -> dict:
    planned = len(records)
    dimensions = {}
    for dimension in DIMENSIONS:
        states = [_revision_state(row, dimension, attempts) for row in records]
        counts = Counter(state for state, score in states)
        scores = [score for state, score in states if state == "scored"]
        dimensions[dimension] = {
            "mean": sum(scores) / len(scores) if scores else None,
            **{f"{state}_count": counts[state] for state in DIMENSION_STATES},
            "planned_case_count": planned,
            "scored_fraction_planned": len(scores) / planned if planned else None,
        }
    automatic = {}
    for field in ("evidence_ids_valid", "paths_valid", "line_ranges_valid", "citation_ids_valid"):
        values = [
            (row["generation"] or {}).get("automatic_checks", {}).get(field) for row in records
        ]
        passed, failed = (
            sum(value is True for value in values),
            sum(value is False for value in values),
        )
        automatic[field] = {
            "valid_count": passed,
            "invalid_count": failed,
            "unavailable_count": planned - passed - failed,
            "checked_count": passed + failed,
            "valid_fraction_checked": passed / (passed + failed) if passed + failed else None,
        }
    generated = [row["generation"] for row in records if row["generation"]]
    statuses = Counter(result["status"] for result in generated)
    valid = sum(statuses[status] for status in SUCCESS_STATUSES)
    eligible = [row for row in records if row["id"] in plan["request_order"]]
    judging = _stage(plan, records, attempts, "judging")
    judging.update(
        eligible_request_count=len(eligible),
        omitted_count=planned - len(eligible),
        latency_ms=_distribution(
            [
                row["judging"].get("latency_ms")
                for row in eligible
                if row["judging"] is not None and row["judging"]["status"] != "skipped"
            ],
            len(eligible),
        ),
    )
    judgments = [
        row["judging"]["judgment"]
        for row in records
        if row["judging"] and row["judging"]["status"] == "scored"
    ]
    decisions = Counter(judgment["abstention"]["decision"] for judgment in judgments)
    return {
        "planned_case_count": planned,
        "source_generation": {
            "historical_only": True,
            "planned_case_count": planned,
            "recorded_count": len(generated),
            "unavailable_count": planned - len(generated),
            "status_counts": dict(sorted(statuses.items())),
            "valid_answer_count": statuses["answered"],
            "valid_answer_fraction_planned": statuses["answered"] / planned if planned else None,
            "valid_generation_count": valid,
            "valid_generation_fraction_planned": valid / planned if planned else None,
            "automatic_checks": automatic,
        },
        "judging": judging,
        "dimensions": dimensions,
        "abstentions": {
            "source_local_count": sum(
                result["status"] == "insufficient_context" and not result["model_called"]
                for result in generated
            ),
            "source_model_count": sum(
                result["status"] == "insufficient_context" and result["model_called"]
                for result in generated
            ),
            "decisions": {
                decision: decisions[decision]
                for decision in ("not_abstained", "appropriate", "unnecessary", "unsure")
            },
            "judged_count": len(judgments),
            "unjudged_count": planned - len(judgments),
            "packed_context_sufficiency": dict(
                sorted(
                    Counter(
                        j["abstention"]["packed_context_sufficiency"] for j in judgments
                    ).items()
                )
            ),
        },
        "reference_status_counts": dict(
            sorted(Counter(j["reference_status"] for j in judgments).items())
        ),
    }


def summarize_revision(
    plan: dict, records: list[dict], attempts: list[dict], *, status: str
) -> dict:
    """Retain all source denominators while accounting only for new judge attempts."""
    indexed = _indexed(plan, records, attempts)
    strategies = sorted({row["strategy"] for row in records})
    per_strategy = {
        name: _metrics(plan, [row for row in records if row["strategy"] == name], indexed)
        for name in strategies
    }
    scored = {name: {dimension: {} for dimension in DIMENSIONS} for name in strategies}
    for row in records:
        for dimension in DIMENSIONS:
            state, score = _revision_state(row, dimension, indexed)
            if state == "scored":
                scored[row["strategy"]][dimension][row["case_id"]] = score
    paired = []
    for baseline, candidate in combinations(strategies, 2):
        for dimension in DIMENSIONS:
            left, right = scored[baseline][dimension], scored[candidate][dimension]
            shared = sorted(left.keys() & right.keys())
            differences = [right[key] - left[key] for key in shared]
            paired.append(
                {
                    "baseline": baseline,
                    "candidate": candidate,
                    "dimension": dimension,
                    "shared_scored_case_ids": shared,
                    "paired_count": len(shared),
                    "baseline_mean": sum(left[key] for key in shared) / len(shared)
                    if shared
                    else None,
                    "candidate_mean": sum(right[key] for key in shared) / len(shared)
                    if shared
                    else None,
                    "mean_delta": sum(differences) / len(shared) if shared else None,
                    "wins": sum(value > 0 for value in differences),
                    "ties": differences.count(0),
                    "losses": sum(value < 0 for value in differences),
                }
            )
    return {
        "schema_version": 1,
        "kind": "qa_judge_revision_summary",
        "plan_fingerprint": plan["plan_fingerprint"],
        "source_records_fingerprint": plan["source_records_fingerprint"],
        "source_generation_model": plan["source_generation_model"],
        "rubric_id": plan["rubric_id"],
        "status": status,
        "new_generation_calls": 0,
        "annotation_status": plan["annotation_status"],
        "evaluation_kind": "llm_assisted_ordinal",
        "human_reviewed": False,
        "estimated_cost": plan["estimated_cost"],
        "overall": _metrics(plan, records, indexed),
        "per_strategy": per_strategy,
        "paired_comparisons": paired,
        "policy": {
            "scores": "Ordinal 0-3 model assessments, not accuracy, probabilities or human review. "
            "Means condition on scored cases; all source cases remain in coverage denominators.",
            "source": "Answers, automatic identity/path/line checks and source abstentions are "
            "historical observations. Their consistency is revalidated against the frozen "
            "archive; this run generates no new answers or retrieval evidence. Historical "
            "judge scores are excluded. Automatic checks do not establish semantic support.",
            "references": "Reference labels remain provisional; judging may flag them as "
            "inadequate or conflicting. Shared generation/judging models can introduce "
            "correlated errors. "
            "Human calibration remains an optional extension and has not been established.",
            "unknown_outcomes": "An attempt without its result has unknown outcome and may be "
            "billed. Missing usage keeps token/cost totals unavailable; subtotals remain explicit. "
            "Omitted invalid source generations are distinct from eligible requests not yet run.",
            "cost": "Only new judge calls are counted. Frozen uncached-rate projections from "
            "observed usage are not invoices. Known subtotals omit missing components. "
            "Historical generation and judging costs are excluded.",
            "timing": "Only new judging latency is reported, with eligible judge requests as its "
            "coverage denominator. Historical retrieval/generation latency is excluded; no new "
            "combined end-to-end or wall-clock service latency is inferred.",
            "pairing": "Candidate minus baseline on shared scored case IDs for each pair and "
            "dimension. Conditional means with different coverage are not matched comparisons. "
            "These are within-revision comparisons, not v1 versus v2 causal estimates.",
        },
    }


def render_revision(summary: dict) -> str:
    """Render a judge-only report with explicit historical and new-observation boundaries."""
    mode = summary.get("execution_mode", "unspecified")
    lines = [
        "# Judge-Only LLM-Assisted QA Assessment",
        "",
        f"Status: {_cell(summary['status'])}. Labels: {_cell(summary['annotation_status'])}.",
        f"Execution mode: {_cell(mode)}. New generation calls: 0.",
    ]
    if mode == "injected_models":
        lines.append(
            "Offline injected-model fixture results; no live model evaluation is established."
        )
    elif mode != "openai":
        lines.append(
            "Execution provenance is unspecified; this report does not establish a live run."
        )
    lines.extend(
        [
            "",
            summary["policy"]["scores"],
            summary["policy"]["source"],
            summary["policy"]["references"],
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
    judge = summary["overall"]["judging"]
    lines.extend(
        [
            "",
            "## New judging usage and cost",
            "",
            summary["policy"]["cost"],
            summary["policy"]["unknown_outcomes"],
            f"Eligible requests: {judge['eligible_request_count']}; omitted source cases: "
            f"{judge['omitted_count']}; not run: {judge['not_run_count']}; "
            f"unknown outcomes: {judge['unknown_outcome_count']}.",
            "",
            "| Observed calls | Calls with unknown outcome | Input tokens | Output tokens "
            "| Cost USD | Known cost subtotal USD |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
            f"| {judge['model_calls_observed']} | {judge['model_calls_with_unknown_outcome']} "
            f"| {_cell(judge['tokens']['input_tokens'])} "
            f"| {_cell(judge['tokens']['output_tokens'])} "
            f"| {_display(judge['cost_usd_at_frozen_uncached_rates'])} "
            f"| {_display(judge['observed_cost_subtotal_usd_at_frozen_uncached_rates'])} |",
            "",
            "## Matched comparisons",
            "",
            summary["policy"]["pairing"],
            "",
            "| Baseline | Candidate | Dimension | Paired cases | Mean delta |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in summary["paired_comparisons"]:
        lines.append(
            f"| {_cell(row['baseline'])} | {_cell(row['candidate'])} | {row['dimension']} "
            f"| {row['paired_count']} | {_display(row['mean_delta'])} |"
        )
    lines.extend(
        [
            "",
            "## Timing boundary and retained evidence",
            "",
            summary["policy"]["timing"],
            "Exact paired case IDs, historical automatic-check coverage, abstentions, new "
            "reference-status counts and per-strategy judge usage/latency are in summary.json. "
            "Individual reference issues and raw judgments remain in records.json "
            "and results.jsonl.",
            "No new benchmark labels or human-review claims are created by this report.",
            "",
        ]
    )
    return "\n".join(lines)
