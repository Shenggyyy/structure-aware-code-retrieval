"""Hand-calculated synthetic assessment results; no model, network or human labels."""

from copy import deepcopy

import pytest

from structure_aware_retrieval.qa.assessment_reporting import (
    DIMENSIONS,
    render_assessment,
    summarize_assessment,
)


def usage(input_tokens=100, output_tokens=20):
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cached_tokens": 0,
        "reasoning_tokens": 0,
    }


def generation(status="answered", *, local=False):
    return {
        "status": status,
        "model_called": not local,
        "provider": None if local else {"model": "fake-generator", "usage": usage()},
        "timing_ms": {
            "retrieval": 2,
            "context_and_prompt": 3,
            "generation_and_validation": 1 if local else 10,
        },
        "automatic_checks": {
            "evidence_ids_valid": None if local else True,
            "paths_valid": None if local else True,
            "line_ranges_valid": None if local else True,
            "citation_ids_valid": True
            if status == "answered"
            else (False if status == "invalid_answer" else None),
        },
    }


def judgment(scores=(3, 1, 2), *, abstained=False):
    dimensions = {
        dimension: {
            "status": "scored" if type(score) is int else score,
            "score": score if type(score) is int else None,
        }
        for dimension, score in zip(DIMENSIONS, scores, strict=True)
    }
    return {
        "status": "scored",
        "model_called": True,
        "provider": {"model": "fake-judge", "usage": usage(50, 10)},
        "latency_ms": 20,
        "judgment": {
            **dimensions,
            "reference_status": "usable",
            "abstention": {
                "decision": "appropriate" if abstained else "not_abstained",
                "packed_context_sufficiency": "insufficient" if abstained else "sufficient",
            },
        },
    }


def row(strategy, case_id, gen, judge):
    return {
        "id": f"{strategy}-{case_id}",
        "strategy": strategy,
        "case_id": case_id,
        "repository": "synthetic",
        "generation": gen,
        "judging": judge,
        "prepared_timing_ms": {"retrieval": 2, "context_and_prompt": 3},
    }


def attempts(records):
    return [
        {"id": r["id"], "stage": stage, "model_call_planned": r[stage]["model_called"]}
        for r in records
        for stage in ("generation", "judging")
        if r[stage] is not None and r[stage]["status"] != "skipped"
    ]


@pytest.fixture
def plan():
    return {
        "plan_fingerprint": "synthetic-plan",
        "annotation_status": "provisional",
        "generation": {
            "model": "fake-generator",
            "pricing": {"input_per_million": 1, "output_per_million": 2, "as_of": "2026-09-08"},
        },
        "judge": {
            "model": "fake-judge",
            "pricing": {"input_per_million": 3, "output_per_million": 4, "as_of": "2026-09-08"},
        },
        "estimated_cost": {
            "generation": {"estimated_cost_usd": 0.01},
            "judging": {"estimated_cost_usd": 0.02},
            "combined_usd": 0.03,
        },
    }


@pytest.fixture
def records():
    return [
        row("baseline", "one", generation(), judgment()),
        row(
            "baseline",
            "two",
            generation("insufficient_context", local=True),
            judgment(("not_applicable", 0, "not_applicable"), abstained=True),
        ),
        row("candidate", "one", generation(), judgment((1, 3, 3))),
        row("candidate", "two", generation(), judgment(("unsure", 2, 2))),
    ]


def test_ordinal_means_coverage_and_comparisons_use_shared_scored_cases(plan, records):
    before = deepcopy(records)
    summary = summarize_assessment(plan, records, attempts(records), status="complete")
    base, candidate = (summary["per_strategy"][key] for key in ("baseline", "candidate"))
    assert base["valid_answer_count"] == 1 and base["valid_generation_count"] == 2
    assert base["valid_answer_fraction_planned"] == 0.5
    assert base["dimensions"]["correctness"]["mean"] == 3
    assert base["dimensions"]["correctness"]["not_applicable_count"] == 1
    assert candidate["dimensions"]["correctness"]["unsure_count"] == 1
    assert candidate["dimensions"]["correctness"]["scored_fraction_planned"] == 0.5
    comparisons = {p["dimension"]: p for p in summary["paired_comparisons"]}
    assert comparisons["correctness"]["shared_scored_case_ids"] == ["one"]
    assert comparisons["correctness"]["mean_delta"] == -2
    assert comparisons["correctness"]["losses"] == 1
    assert comparisons["completeness"]["shared_scored_case_ids"] == ["one", "two"]
    assert comparisons["completeness"]["mean_delta"] == 2
    assert comparisons["citation_support"]["mean_delta"] == 1
    assert base["abstentions"]["local_count"] == 1
    assert base["abstentions"]["model_count"] == 0
    assert base["abstentions"]["decisions"]["appropriate"] == 1
    assert records == before


def test_stage_prices_known_tokens_and_latency_boundaries_are_separate(plan, records):
    metrics = summarize_assessment(plan, records, attempts(records), status="complete")["overall"]
    gen, judge = metrics["stages"]["generation"], metrics["stages"]["judging"]
    assert gen["model_calls_observed"] == 3 and judge["model_calls_observed"] == 4
    assert gen["cost_usd_at_frozen_uncached_rates"] == pytest.approx(0.00042)
    assert judge["cost_usd_at_frozen_uncached_rates"] == pytest.approx(0.00076)
    assert metrics["combined_usage"]["cost_usd_at_frozen_uncached_rates"] == pytest.approx(0.00118)
    assert metrics["combined_usage"]["tokens"] == usage(500, 100)
    assert metrics["preparation_latency_ms"]["retrieval"]["total"] == 8
    assert metrics["end_to_end_latency_ms"]["mean"] == pytest.approx(32.75)
    assert gen["latency_ms"]["mean"] == 7.75
    assert metrics["automatic_checks"]["citation_ids_valid"]["checked_count"] == 3
    assert metrics["automatic_checks"]["paths_valid"]["unavailable_count"] == 1


def test_failures_unrun_and_unknown_outcomes_preserve_every_denominator(plan, records):
    invalid = judgment()
    invalid.update(status="invalid_judgment", judgment=None, provider=None)
    selected = records[:2] + [
        row(
            "baseline",
            "bad-generation",
            generation("invalid_answer"),
            {"status": "skipped", "model_called": False, "latency_ms": None},
        ),
        row("baseline", "bad-judge", generation(), invalid),
        row("baseline", "not-run", None, None),
        row("baseline", "unknown-generation", None, None),
        row("baseline", "unknown-judge", generation(), None),
    ]
    journal = attempts(selected) + [
        {"id": "baseline-unknown-generation", "stage": "generation", "model_call_planned": True},
        {"id": "baseline-unknown-judge", "stage": "judging", "model_call_planned": True},
    ]
    metrics = summarize_assessment(plan, selected, journal, status="interrupted")["overall"]
    correct = metrics["dimensions"]["correctness"]
    assert [
        correct[f"{s}_count"]
        for s in (
            "scored",
            "not_applicable",
            "invalid_generation",
            "invalid_judgment",
            "not_run",
            "unknown_outcome",
        )
    ] == [1, 1, 1, 1, 1, 2]
    assert correct["planned_case_count"] == 7 and correct["mean"] == 3
    assert metrics["stages"]["generation"]["unknown_outcome_count"] == 1
    assert metrics["stages"]["generation"]["not_run_count"] == 1
    assert metrics["stages"]["judging"]["calls_missing_token_counts"]["input_tokens"] == 2
    combined = metrics["combined_usage"]
    assert all(value is None for value in combined["tokens"].values())
    assert combined["cost_usd_at_frozen_uncached_rates"] is None
    assert combined["observed_cost_subtotal_usd_at_frozen_uncached_rates"] > 0
    assert combined["observed_token_subtotals"]["input_tokens"] == 500
    assert metrics["preparation_latency_ms"]["retrieval"]["count"] == 7
    assert metrics["end_to_end_latency_ms"]["count"] == 3
    assert metrics["end_to_end_latency_ms"]["total"] is None


def test_unbilled_local_interruption_keeps_zero_cost_but_unknown_semantics(plan):
    records = [row("one", "local", None, None)]
    journal = [{"id": "one-local", "stage": "generation", "model_call_planned": False}]
    summary = summarize_assessment(plan, records, journal, status="interrupted")
    metrics = summary["overall"]
    assert metrics["dimensions"]["correctness"]["mean"] is None
    assert metrics["dimensions"]["correctness"]["unknown_outcome_count"] == 1
    assert metrics["combined_usage"]["cost_usd_at_frozen_uncached_rates"] == 0
    assert metrics["stages"]["generation"]["model_calls_with_unknown_outcome"] == 0
    assert summary["paired_comparisons"] == []


@pytest.mark.parametrize(
    "mutation", ["bool_score", "out_of_range", "unsure_score", "invalid_generation"]
)
def test_malformed_scored_results_cannot_be_published(plan, records, mutation):
    if mutation == "invalid_generation":
        records[0]["generation"]["status"] = "invalid_answer"
    else:
        value = records[0]["judging"]["judgment"]["correctness"]
        value.update(
            {"score": True}
            if mutation == "bool_score"
            else {"score": 4}
            if mutation == "out_of_range"
            else {"status": "unsure"}
        )
    with pytest.raises(ValueError):
        summarize_assessment(plan, records, attempts(records), status="complete")


@pytest.mark.parametrize("mutation", ["record", "attempt", "unknown_attempt"])
def test_duplicate_or_unbound_attempts_do_not_double_count_costs(plan, records, mutation):
    journal = attempts(records)
    if mutation == "record":
        records.append(deepcopy(records[0]))
    elif mutation == "attempt":
        journal.append(deepcopy(journal[0]))
    else:
        journal[0]["id"] = "unknown-id"
    with pytest.raises(ValueError):
        summarize_assessment(plan, records, journal, status="complete")


def test_markdown_names_are_escaped_and_pending_means_are_not_perfect(plan):
    records = [row("name|<script>\n# heading", "one", None, None)]
    summary = summarize_assessment(plan, records, [], status="pending")
    report = render_assessment(summary)
    assert "name\\|&lt;script&gt; \\# heading" in report
    assert "<script>" not in report and "\n# heading" not in report
    assert "not accuracy" in report and "Labels: provisional" in report
    assert "| correctness | unknown | 0 | 0 | 0 | 0 | 0 | 1 | 0 |" in report
    assert summary["overall"]["dimensions"]["correctness"]["mean"] is None
    assert summary["human_reviewed"] is False
