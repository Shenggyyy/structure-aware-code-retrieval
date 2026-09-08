"""Report ordinal LLM assessments, coverage and observed costs without invented totals."""

from collections import Counter
from itertools import combinations

from structure_aware_retrieval.qa.answering import _markdown
from structure_aware_retrieval.qa.execution import SUCCESS_STATUSES, TOKEN_FIELDS, _number, _usage

DIMENSIONS = ("correctness", "completeness", "citation_support")
JUDGE_STATUSES = ("scored", "invalid_judgment", "provider_error", "skipped")
DIMENSION_STATES = (
    "scored",
    "unsure",
    "not_applicable",
    "invalid_generation",
    "invalid_judgment",
    "not_run",
    "unknown_outcome",
)


def _attempt_index(records: list[dict], attempts: list[dict]) -> dict:
    identities, pairs, repositories = set(), set(), {}
    for row in records:
        pair = row["strategy"], row["case_id"]
        if row["id"] in identities or pair in pairs:
            raise ValueError("Duplicate assessment identity or strategy/case pair")
        if repositories.setdefault(row["case_id"], row["repository"]) != row["repository"]:
            raise ValueError("Assessment case repository differs across strategies")
        identities.add(row["id"])
        pairs.add(pair)
        for stage in ("generation", "judging"):
            result = row[stage]
            if result is not None and type(result.get("model_called")) is not bool:
                raise ValueError("Assessment result must record whether the model was called")
        judge = row["judging"]
        if judge is not None and judge["status"] not in JUDGE_STATUSES:
            raise ValueError("Unknown judging outcome")
        if judge and judge["status"] == "scored":
            if not row["generation"] or row["generation"]["status"] not in SUCCESS_STATUSES:
                raise ValueError("A scored judgment requires a valid generation")
            for dimension in DIMENSIONS:
                value = judge["judgment"][dimension]
                state, score = value["status"], value["score"]
                if (
                    state not in ("scored", "unsure", "not_applicable")
                    or (state == "scored" and (type(score) is not int or not 0 <= score <= 3))
                    or (state != "scored" and score is not None)
                ):
                    raise ValueError("Invalid ordinal judgment status or score")
    indexed = {}
    for attempt in attempts:
        key = attempt["id"], attempt["stage"]
        if (
            attempt["id"] not in identities
            or attempt["stage"] not in ("generation", "judging")
            or type(attempt["model_call_planned"]) is not bool
            or key in indexed
        ):
            raise ValueError("Invalid or duplicate assessment attempt")
        indexed[key] = attempt
    return indexed


def _distribution(values: list, planned: int) -> dict:
    observed = [value for value in values if _number(value)]
    return {
        "count": len(observed),
        "planned_case_count": planned,
        "missing_count": planned - len(observed),
        "mean": sum(observed) / len(observed) if observed else None,
        "observed_total": sum(observed),
        "total": sum(observed) if len(observed) == planned else None,
    }


def _stage(plan: dict, records: list[dict], attempts: dict, stage: str) -> dict:
    results = [row[stage] for row in records if row[stage] is not None]
    unknown = [row for row in records if row[stage] is None and (row["id"], stage) in attempts]
    possible_calls = sum(attempts[row["id"], stage]["model_call_planned"] for row in unknown)
    config = plan["generation" if stage == "generation" else "judge"]
    usage = _usage([{"result": result} for result in results], possible_calls, config["pricing"])
    subtotals = usage["observed_token_subtotals"]
    usage["observed_cost_subtotal_usd_at_frozen_uncached_rates"] = (
        subtotals["input_tokens"] * config["pricing"]["input_per_million"]
        + subtotals["output_tokens"] * config["pricing"]["output_per_million"]
    ) / 1_000_000
    statuses = Counter(result["status"] for result in results)
    completed = sum(
        statuses[state] for state in (SUCCESS_STATUSES if stage == "generation" else ("scored",))
    )
    failures = sum(
        statuses[state]
        for state in (
            ("invalid_answer", "provider_error")
            if stage == "generation"
            else ("invalid_judgment", "provider_error")
        )
    )
    timings = [
        (row[stage].get("timing_ms") or {}).get("generation_and_validation")
        if stage == "generation"
        else row[stage].get("latency_ms")
        for row in records
        if row[stage] is not None and row[stage]["status"] != "skipped"
    ]
    return {
        "requested_model": config["model"],
        "pricing": config["pricing"],
        "planned_case_count": len(records),
        "attempted_count": sum((row["id"], stage) in attempts for row in records),
        "recorded_count": len(results),
        "completed_count": completed,
        "failed_count": failures,
        "skipped_count": statuses["skipped"],
        "unknown_outcome_count": len(unknown),
        "not_run_count": len(records) - len(results) - len(unknown),
        "model_calls_observed": sum(result["model_called"] for result in results),
        "model_calls_with_unknown_outcome": possible_calls,
        "status_counts": dict(sorted(statuses.items())),
        "reported_models": dict(
            sorted(
                Counter(
                    result["provider"]["model"]
                    for result in results
                    if result.get("provider") and result["provider"].get("model")
                ).items()
            )
        ),
        "latency_ms": _distribution(timings, len(records)),
        **usage,
    }


def _state(row: dict, dimension: str, attempts: dict) -> tuple[str, int | None]:
    generation, judging = row["generation"], row["judging"]
    if generation is None:
        return ("unknown_outcome" if (row["id"], "generation") in attempts else "not_run"), None
    if generation["status"] == "preview":
        return "not_run", None
    if generation["status"] not in SUCCESS_STATUSES:
        return "invalid_generation", None
    if judging is None:
        return ("unknown_outcome" if (row["id"], "judging") in attempts else "not_run"), None
    if judging["status"] == "skipped":
        return "not_run", None
    if judging["status"] != "scored":
        return "invalid_judgment", None
    judgment = judging["judgment"][dimension]
    return judgment["status"], judgment["score"]


def _combined(stages: dict) -> dict:
    return {
        "tokens": {
            field: None
            if any(stage["tokens"][field] is None for stage in stages.values())
            else sum(stage["tokens"][field] for stage in stages.values())
            for field in TOKEN_FIELDS
        },
        "observed_token_subtotals": {
            field: sum(stage["observed_token_subtotals"][field] for stage in stages.values())
            for field in TOKEN_FIELDS
        },
        "calls_missing_token_counts": {
            field: sum(stage["calls_missing_token_counts"][field] for stage in stages.values())
            for field in TOKEN_FIELDS
        },
        "cost_usd_at_frozen_uncached_rates": None
        if any(stage["cost_usd_at_frozen_uncached_rates"] is None for stage in stages.values())
        else sum(stage["cost_usd_at_frozen_uncached_rates"] for stage in stages.values()),
        "observed_cost_subtotal_usd_at_frozen_uncached_rates": sum(
            stage["observed_cost_subtotal_usd_at_frozen_uncached_rates"]
            for stage in stages.values()
        ),
    }


def _metrics(plan: dict, records: list[dict], attempts: dict) -> dict:
    planned = len(records)
    dimensions = {}
    for dimension in DIMENSIONS:
        states = [_state(row, dimension, attempts) for row in records]
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
        passed, failed = sum(v is True for v in values), sum(v is False for v in values)
        automatic[field] = {
            "valid_count": passed,
            "invalid_count": failed,
            "unavailable_count": planned - passed - failed,
            "checked_count": passed + failed,
            "valid_fraction_checked": passed / (passed + failed) if passed + failed else None,
        }
    generated = [row["generation"] for row in records if row["generation"]]
    answered = sum(result["status"] == "answered" for result in generated)
    valid = sum(result["status"] in SUCCESS_STATUSES for result in generated)
    judgments = [
        row["judging"]["judgment"]
        for row in records
        if row["judging"] and row["judging"]["status"] == "scored"
    ]
    decisions = Counter(j["abstention"]["decision"] for j in judgments)
    local = sum(r["status"] == "insufficient_context" and not r["model_called"] for r in generated)
    model = sum(r["status"] == "insufficient_context" and r["model_called"] for r in generated)
    stages = {stage: _stage(plan, records, attempts, stage) for stage in ("generation", "judging")}
    preparation = [
        row.get("prepared_timing_ms") or (row["generation"] or {}).get("timing_ms", {})
        for row in records
    ]
    end_to_end = []
    for row, timing in zip(records, preparation, strict=True):
        generation, judging = row["generation"], row["judging"]
        parts = [
            timing.get("retrieval"),
            timing.get("context_and_prompt"),
            (generation or {}).get("timing_ms", {}).get("generation_and_validation"),
            (judging or {}).get("latency_ms"),
        ]
        # No judgment (including skipped judging) is not a measured two-stage evaluation.
        if judging and judging["status"] != "skipped" and all(_number(v) for v in parts):
            end_to_end.append(sum(parts))
    return {
        "planned_case_count": planned,
        "valid_answer_count": answered,
        "valid_answer_fraction_planned": answered / planned if planned else None,
        "valid_generation_count": valid,
        "valid_generation_fraction_planned": valid / planned if planned else None,
        "dimensions": dimensions,
        "automatic_checks": automatic,
        "abstentions": {
            "local_count": local,
            "model_count": model,
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
        "stages": stages,
        "combined_usage": _combined(stages),
        "preparation_latency_ms": {
            key: _distribution([v.get(key) for v in preparation], planned)
            for key in ("retrieval", "context_and_prompt")
        },
        "end_to_end_latency_ms": _distribution(end_to_end, planned),
    }


def summarize_assessment(
    plan: dict, records: list[dict], attempts: list[dict], *, status: str
) -> dict:
    """Summarize all planned cases; missing attempts/results remain explicitly unknown."""
    indexed = _attempt_index(records, attempts)
    strategies = sorted({row["strategy"] for row in records})
    per_strategy = {
        name: _metrics(plan, [row for row in records if row["strategy"] == name], indexed)
        for name in strategies
    }
    scored = {name: {dimension: {} for dimension in DIMENSIONS} for name in strategies}
    for row in records:
        for dimension in DIMENSIONS:
            state, score = _state(row, dimension, indexed)
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
                    "wins": sum(v > 0 for v in differences),
                    "ties": differences.count(0),
                    "losses": sum(v < 0 for v in differences),
                }
            )
    return {
        "schema_version": 1,
        "plan_fingerprint": plan["plan_fingerprint"],
        "status": status,
        "annotation_status": plan["annotation_status"],
        "evaluation_kind": "llm_assisted_ordinal",
        "human_reviewed": False,
        "estimated_cost": plan["estimated_cost"],
        "overall": _metrics(plan, records, indexed),
        "per_strategy": per_strategy,
        "paired_comparisons": paired,
        "policy": {
            "scores": "Ordinal 0-3 model assessments, not accuracy, probabilities or human review. "
            "Means condition on scored cases; all planned cases remain in coverage denominators.",
            "unknown_outcomes": "An attempt without its result has unknown outcome; if a model "
            "call was planned, usage and cost totals remain unavailable.",
            "cost": "Frozen uncached-rate projections from observed usage, not invoices. "
            "Observed subtotals omit missing components and are not full totals.",
            "timing": "Preparation is measured offline retrieval plus context/prompt packing. "
            "End-to-end sums those preparation times and observed generation/validation and "
            "judging times for the same case; excludes model/index loading, run orchestration, "
            "reporting and time between stages. It is not wall-clock service latency.",
            "pairing": "Candidate minus baseline on shared scored case IDs for each pair and "
            "dimension; differing conditional means are not treated as matched samples.",
        },
    }


def _cell(value: object) -> str:
    return "unknown" if value is None else _markdown(" ".join(str(value).split()))


def _display(value: float | None) -> str:
    return "unknown" if value is None else f"{value:.4f}"


def render_assessment(summary: dict) -> str:
    """Render fixed tables; escape names instead of allowing records to inject Markdown."""
    lines = [
        "# LLM-Assisted QA Assessment",
        "",
        f"Status: {_cell(summary['status'])}. Labels: {_cell(summary['annotation_status'])}.",
        "",
        summary["policy"]["scores"],
        "Human calibration is optional and has not been established.",
        "Automatic citation checks establish identity/location, not semantic support.",
        "",
        "| Strategy | Valid answers / planned | Dimension | Mean (0-3) | Scored | Unsure | N/A "
        "| Invalid generation | Invalid judgment | Not run | Unknown outcome |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, metrics in summary["per_strategy"].items():
        for dimension in DIMENSIONS:
            values = metrics["dimensions"][dimension]
            counts = " | ".join(str(values[f"{state}_count"]) for state in DIMENSION_STATES)
            lines.append(
                f"| {_cell(name)} | {metrics['valid_answer_count']} "
                f"/ {metrics['planned_case_count']} "
                f"| {dimension} | {_display(values['mean'])} | {counts} |"
            )
    lines.extend(
        [
            "",
            "## Observed usage and cost",
            "",
            summary["policy"]["cost"],
            "",
            "| Stage | Observed calls | Calls with unknown outcome | Input tokens "
            "| Output tokens | Cost USD | Known cost subtotal USD |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    overall = summary["overall"]
    for stage, metrics in overall["stages"].items():
        lines.append(
            f"| {stage} | {metrics['model_calls_observed']} "
            f"| {metrics['model_calls_with_unknown_outcome']} "
            f"| {_cell(metrics['tokens']['input_tokens'])} "
            f"| {_cell(metrics['tokens']['output_tokens'])} "
            f"| {_display(metrics['cost_usd_at_frozen_uncached_rates'])} "
            f"| {_display(metrics['observed_cost_subtotal_usd_at_frozen_uncached_rates'])} |"
        )
    combined = overall["combined_usage"]
    lines.extend(
        [
            "",
            f"Combined cost USD: {_display(combined['cost_usd_at_frozen_uncached_rates'])}; "
            "known subtotal: "
            + _display(combined["observed_cost_subtotal_usd_at_frozen_uncached_rates"])
            + ". Missing usage is unknown, not zero.",
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
            "Exact paired case IDs, automatic-check counts, abstentions, reference-status counts, "
            "per-strategy usage and timing coverage are retained in summary.json.",
            "Individual reference issues and raw judgments are retained in records.json "
            "and results.jsonl.",
            "",
            "## Timing boundary",
            "",
            summary["policy"]["timing"],
            "",
            "No new benchmark labels or human-review claims are created by this report.",
            "",
        ]
    )
    return "\n".join(lines)
