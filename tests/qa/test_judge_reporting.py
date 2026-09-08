"""Hand-calculated judge-only reports; no model calls or asserted human labels."""

from copy import deepcopy

import pytest

from structure_aware_retrieval.qa.assessment_execution import _skipped
from structure_aware_retrieval.qa.execution import SUCCESS_STATUSES
from structure_aware_retrieval.qa.judge_reporting import render_revision, summarize_revision
from tests.qa.test_assessment_reporting import generation, judgment, row, usage


def revision_plan(records):
    eligible = [
        value["id"]
        for value in records
        if value["generation"] and value["generation"]["status"] in SUCCESS_STATUSES
    ]
    return {
        "plan_fingerprint": "synthetic-revision-plan",
        "source_records_fingerprint": "synthetic-source-records",
        "source_generation_model": "fake-historical-generator",
        "annotation_status": "provisional",
        "rubric_id": "repository-qa-judge-rubric-v2",
        "judge": {
            "model": "fake-judge",
            "pricing": {"input_per_million": 3, "output_per_million": 4, "as_of": "2026-09-08"},
        },
        "source_planned_count": len(records),
        "request_count": len(eligible),
        "request_order": eligible,
        "omitted": [{"id": value["id"]} for value in records if value["id"] not in eligible],
        "estimated_cost": {"new_generation_calls": 0, "combined_usd": 0.02},
    }


def judge_attempts(records):
    return [
        {"id": value["id"], "stage": "judging", "model_call_planned": True}
        for value in records
        if value["judging"] and value["judging"]["status"] != "skipped"
    ]


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


def test_new_usage_excludes_all_historical_generation_costs_and_timings(records):
    plan, journal = revision_plan(records), judge_attempts(records)
    expected = summarize_revision(plan, records, journal, status="complete")
    for value in records:
        value["generation"]["provider"] = {"usage": usage(10**12, 10**11)}
        value["generation"]["timing_ms"] = {"generation_and_validation": 10**12}
        value["prepared_timing_ms"] = {"retrieval": 10**12, "context_and_prompt": 10**12}
    summary = summarize_revision(plan, records, journal, status="complete")
    assert summary == expected
    assert summary["source_records_fingerprint"] == plan["source_records_fingerprint"]
    assert summary["new_generation_calls"] == 0
    judge = summary["overall"]["judging"]
    assert judge["model_calls_observed"] == 4
    assert judge["tokens"] == usage(200, 40)
    assert judge["cost_usd_at_frozen_uncached_rates"] == pytest.approx(0.00076)
    assert judge["latency_ms"] == {
        "count": 4,
        "planned_case_count": 4,
        "missing_count": 0,
        "mean": 20,
        "observed_total": 80,
        "total": 80,
    }
    assert "combined_usage" not in summary["overall"]
    assert "end_to_end_latency_ms" not in summary["overall"]
    assert "stages" not in summary["overall"]


def test_paired_comparisons_only_use_shared_scored_cases_and_keep_ordinal_states(records):
    original = deepcopy(records)
    summary = summarize_revision(
        revision_plan(records), records, judge_attempts(records), status="complete"
    )
    assert records == original
    base, candidate = (summary["per_strategy"][key] for key in ("baseline", "candidate"))
    assert base["dimensions"]["correctness"]["mean"] == 3
    assert base["dimensions"]["correctness"]["not_applicable_count"] == 1
    assert candidate["dimensions"]["correctness"]["unsure_count"] == 1
    assert candidate["dimensions"]["correctness"]["scored_fraction_planned"] == 0.5
    comparisons = {value["dimension"]: value for value in summary["paired_comparisons"]}
    assert comparisons["correctness"]["shared_scored_case_ids"] == ["one"]
    assert comparisons["correctness"]["mean_delta"] == -2
    assert comparisons["correctness"]["losses"] == 1
    assert comparisons["completeness"]["paired_count"] == 2
    assert comparisons["completeness"]["mean_delta"] == 2
    assert base["source_generation"]["valid_answer_count"] == 1
    assert base["source_generation"]["valid_generation_count"] == 2
    assert base["abstentions"]["source_local_count"] == 1
    assert base["abstentions"]["decisions"]["appropriate"] == 1
    automatic = summary["overall"]["source_generation"]["automatic_checks"]
    assert automatic["paths_valid"]["checked_count"] == 3
    assert automatic["paths_valid"]["unavailable_count"] == 1
    assert automatic["citation_ids_valid"]["valid_count"] == 3


def test_omitted_unknown_invalid_and_unrun_are_distinct_without_losing_denominators():
    invalid = judgment()
    invalid.update(status="invalid_judgment", judgment=None)
    records = [
        row("one", "scored", generation(), judgment()),
        row("one", "invalid", generation(), invalid),
        row("one", "unknown", generation(), None),
        row("one", "not-run", generation(), None),
        row("one", "missing-source", None, _skipped("invalid_source_generation")),
        row(
            "one",
            "invalid-source",
            generation("invalid_answer"),
            _skipped("invalid_source_generation"),
        ),
    ]
    journal = judge_attempts(records) + [
        {"id": "one-unknown", "stage": "judging", "model_call_planned": True}
    ]
    summary = summarize_revision(revision_plan(records), records, journal, status="interrupted")
    overall = summary["overall"]
    dimension = overall["dimensions"]["correctness"]
    assert dimension["planned_case_count"] == 6
    assert dimension["scored_fraction_planned"] == pytest.approx(1 / 6)
    assert dimension["invalid_generation_count"] == 2
    assert dimension["invalid_judgment_count"] == 1
    assert dimension["unknown_outcome_count"] == 1
    assert dimension["not_run_count"] == 1
    assert dimension["mean"] == 3
    judge = overall["judging"]
    assert judge["planned_case_count"] == 6
    assert judge["eligible_request_count"] == 4
    assert judge["omitted_count"] == judge["skipped_count"] == 2
    assert judge["unknown_outcome_count"] == judge["not_run_count"] == 1
    assert all(value is None for value in judge["tokens"].values())
    assert judge["cost_usd_at_frozen_uncached_rates"] is None
    assert judge["observed_token_subtotals"] == usage(100, 20)
    assert judge["observed_cost_subtotal_usd_at_frozen_uncached_rates"] == pytest.approx(0.00038)
    assert judge["latency_ms"]["planned_case_count"] == 4
    assert judge["latency_ms"]["count"] == 2
    assert judge["latency_ms"]["total"] is None
    assert overall["source_generation"]["unavailable_count"] == 1
    assert overall["abstentions"]["unjudged_count"] == 5


def test_missing_reported_usage_does_not_become_zero(records):
    records[0]["judging"]["provider"]["usage"]["input_tokens"] = None
    summary = summarize_revision(
        revision_plan(records), records, judge_attempts(records), status="complete"
    )
    judge = summary["overall"]["judging"]
    assert judge["tokens"]["input_tokens"] is None
    assert judge["tokens"]["output_tokens"] == 40
    assert judge["calls_missing_token_counts"]["input_tokens"] == 1
    assert judge["cost_usd_at_frozen_uncached_rates"] is None
    assert judge["observed_cost_subtotal_usd_at_frozen_uncached_rates"] == pytest.approx(0.00061)


def test_absent_overlap_does_not_compare_unpaired_conditional_means(records):
    records[0]["judging"]["judgment"]["correctness"].update(status="unsure", score=None)
    summary = summarize_revision(
        revision_plan(records), records, judge_attempts(records), status="complete"
    )
    paired = next(
        value for value in summary["paired_comparisons"] if value["dimension"] == "correctness"
    )
    assert paired["paired_count"] == 0
    assert paired["baseline_mean"] is paired["candidate_mean"] is paired["mean_delta"] is None
    assert paired["wins"] == paired["ties"] == paired["losses"] == 0


@pytest.mark.parametrize("score", [True, 4, -1, 1.5])
def test_malformed_ordinal_scores_cannot_be_reported(records, score):
    records[0]["judging"]["judgment"]["correctness"]["score"] = score
    with pytest.raises(ValueError, match="ordinal"):
        summarize_revision(
            revision_plan(records), records, judge_attempts(records), status="complete"
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "generation_attempt",
        "unplanned_call",
        "missing_attempt",
        "duplicate_attempt",
        "source_denominator",
        "order",
        "missing_omission",
        "invalid_omission",
        "eligible_invalid_source",
    ],
)
def test_invalid_revision_population_or_attempts_are_rejected(records, mutation):
    plan, journal = revision_plan(records), judge_attempts(records)
    if mutation == "generation_attempt":
        journal[0]["stage"] = "generation"
    elif mutation == "unplanned_call":
        journal[0]["model_call_planned"] = False
    elif mutation == "missing_attempt":
        journal.pop()
    elif mutation == "duplicate_attempt":
        journal.append(deepcopy(journal[0]))
    elif mutation == "source_denominator":
        plan["source_planned_count"] += 1
    elif mutation == "order":
        records.reverse()
    elif mutation == "missing_omission":
        plan["request_order"].pop()
        plan["request_count"] -= 1
    elif mutation == "invalid_omission":
        records.append(row("baseline", "bad-source", None, None))
        plan = revision_plan(records)
    else:
        records[0]["generation"] = None
        records[0]["judging"] = None
        journal = journal[1:]
    with pytest.raises(ValueError):
        summarize_revision(plan, records, journal, status="complete")


def test_pending_report_marks_fixture_provenance_and_escapes_names():
    records = [row("name|<script>\n# heading", "one", generation(), None)]
    summary = summarize_revision(revision_plan(records), records, [], status="pending")
    assert summary["overall"]["dimensions"]["correctness"]["mean"] is None
    assert "does not establish a live run" in render_revision(summary)
    summary["execution_mode"] = "injected_models"
    report = render_revision(summary)
    assert "Offline injected-model fixture results" in report
    assert "name\\|&lt;script&gt; \\# heading" in report
    assert "<script>" not in report and "\n# heading" not in report
    assert "not accuracy" in report
    assert "Labels: provisional" in report
    assert "Historical generation and judging costs are excluded" in report
    assert "not v1 versus v2 causal estimates" in report
    assert "New generation calls: 0" in report
    assert summary["human_reviewed"] is False
    assert summary["overall"]["judging"]["tokens"] == usage(0, 0)
