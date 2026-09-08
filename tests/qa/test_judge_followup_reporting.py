"""Hand-calculated accounting for disjoint batches, with permanent prior unknown outcomes."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.assessment_execution import _skipped
from structure_aware_retrieval.qa.judge_followup_reporting import (
    render_followup,
    summarize_followup,
)
from tests.qa.test_assessment_reporting import generation, judgment, row, usage
from tests.qa.test_judge_reporting import revision_plan


def attempt(identity):
    return {"id": identity, "stage": "judging", "model_call_planned": True}


def make_batch(baseline="baseline"):
    prior = [
        row(baseline, "one", generation(), judgment()),
        row(baseline, "two", generation(), None),
        row("candidate", "one", generation(), None),
        row("candidate", "two", generation(), None),
    ]
    parent = revision_plan(prior)
    parent.update(kind="qa_judge_revision_plan", source_run={"source": "synthetic-v1"})
    historical_attempts = [attempt(value["id"]) for value in prior[:2]]
    plan = {
        **deepcopy(parent),
        "kind": "qa_judge_followup_plan",
        "plan_fingerprint": "synthetic-followup-plan",
        "request_order": [value["id"] for value in prior[2:]],
        "request_count": 2,
        "prior_run": {"execution_mode": "openai"},
        "prior_records_fingerprint": stable_id(prior),
        "prior_attempts_fingerprint": stable_id(historical_attempts),
        "excluded_prior_attempts": [
            {
                **{key: value[key] for key in ("id", "case_id", "strategy", "repository")},
                "status": "scored" if value["judging"] else "unknown_outcome",
            }
            for value in prior[:2]
        ],
    }
    records = deepcopy(prior)
    records[2]["judging"] = judgment((1, 3, 3))
    records[3]["judging"] = judgment((2, 2, 1))
    return SimpleNamespace(
        plan=plan,
        parent=parent,
        prior=prior,
        prior_attempts=historical_attempts,
        records=records,
        attempts=[attempt(value["id"]) for value in prior[2:]],
    )


@pytest.fixture
def batch():
    return make_batch()


def summary(batch, status="complete"):
    return summarize_followup(
        batch.plan,
        batch.parent,
        batch.prior,
        batch.prior_attempts,
        batch.records,
        batch.attempts,
        status=status,
    )


def test_disjoint_costs_tokens_latency_and_source_denominators(batch):
    original = deepcopy(batch)
    result = summary(batch)
    assert vars(batch) == vars(original)
    assert result["kind"] == "qa_judge_followup_summary"
    assert result["status"] == "complete"
    assert result["cumulative_status"] == "incomplete"
    assert result["new_generation_calls"] == 0
    prior, new, cumulative = (
        result["prior_judging"],
        result["new_judging"],
        result["cumulative"]["judging"],
    )
    assert new["tokens"] == usage(100, 20)
    assert new["cost_usd_at_frozen_uncached_rates"] == pytest.approx(0.00038)
    assert prior["observed_token_subtotals"] == usage(50, 10)
    assert prior["observed_cost_subtotal_usd_at_frozen_uncached_rates"] == pytest.approx(0.00019)
    assert cumulative["observed_token_subtotals"] == usage(150, 30)
    assert cumulative["observed_cost_subtotal_usd_at_frozen_uncached_rates"] == pytest.approx(
        0.00057
    )
    assert prior["cost_usd_at_frozen_uncached_rates"] is None
    assert cumulative["cost_usd_at_frozen_uncached_rates"] is None
    assert all(value is None for value in cumulative["tokens"].values())
    assert cumulative["calls_missing_token_counts"] == dict.fromkeys(usage(), 1)
    assert [stage["planned_case_count"] for stage in (prior, new, cumulative)] == [2, 2, 4]
    assert [stage["attempted_count"] for stage in (prior, new, cumulative)] == [2, 2, 4]
    assert [stage["completed_count"] for stage in (prior, new, cumulative)] == [1, 2, 3]
    assert [stage["unknown_outcome_count"] for stage in (prior, new, cumulative)] == [1, 0, 1]
    assert [stage["latency_ms"]["count"] for stage in (prior, new, cumulative)] == [1, 2, 3]
    assert [stage["latency_ms"]["total"] for stage in (prior, new, cumulative)] == [None, 40, None]
    assert cumulative["latency_ms"]["observed_total"] == 60
    assert cumulative["latency_ms"]["planned_case_count"] == 4
    assert "baseline" not in new["per_strategy"]
    assert new["per_strategy"]["candidate"]["completed_count"] == 2
    for values in result["overall"]["dimensions"].values():
        assert values["planned_case_count"] == 4
        assert values["mean"] == 2
        assert values["scored_count"] == 3
        assert values["scored_fraction_planned"] == 0.75
        assert values["unknown_outcome_count"] == 1
    for pair in result["paired_comparisons"]:
        assert pair["shared_scored_case_ids"] == ["one"]
        assert pair["paired_count"] == 1
    assert result["overall"] == result["cumulative"]["overall"]


def test_historical_generation_usage_never_changes_judging_accounting(batch):
    expected = summary(batch)
    for prior, record in zip(batch.prior, batch.records, strict=True):
        for value in (prior, record):
            value["generation"]["provider"]["usage"] = usage(10**12, 10**11)
            value["generation"]["timing_ms"]["generation_and_validation"] = 10**12
            value["prepared_timing_ms"] = {"retrieval": 10**12, "context_and_prompt": 10**12}
    batch.plan["prior_records_fingerprint"] = stable_id(batch.prior)
    assert summary(batch) == expected


def test_pending_batch_preserves_parent_unknown_and_does_not_duplicate_unrun(batch):
    batch.records = deepcopy(batch.prior)
    batch.attempts = []
    result = summary(batch, "pending")
    assert result["prior_judging"]["not_run_count"] == 0
    assert result["new_judging"]["not_run_count"] == 2
    assert result["new_judging"]["tokens"] == usage(0, 0)
    dimension = result["overall"]["dimensions"]["correctness"]
    assert dimension["unknown_outcome_count"] == 1
    assert dimension["not_run_count"] == 2
    assert dimension["scored_fraction_planned"] == 0.25


def test_new_unknown_remains_distinct_from_historical_unknown(batch):
    batch.records = deepcopy(batch.prior)
    batch.attempts = batch.attempts[:1]
    result = summary(batch, "interrupted")
    new = result["new_judging"]
    assert new["unknown_outcome_count"] == new["not_run_count"] == 1
    assert new["cost_usd_at_frozen_uncached_rates"] is None
    assert new["observed_cost_subtotal_usd_at_frozen_uncached_rates"] == 0
    assert result["cumulative"]["judging"]["unknown_outcome_count"] == 2
    assert result["cumulative"]["judging"]["calls_missing_token_counts"]["input_tokens"] == 2


def test_invalid_judgment_keeps_usage_but_does_not_become_an_ordinal_score(batch):
    batch.records[2]["judging"].update(status="invalid_judgment", judgment=None)
    result = summary(batch, "complete_with_failures")
    assert result["new_judging"]["failed_count"] == 1
    assert result["new_judging"]["tokens"] == usage(100, 20)
    assert result["new_judging"]["cost_usd_at_frozen_uncached_rates"] == pytest.approx(0.00038)
    assert result["overall"]["dimensions"]["correctness"]["invalid_judgment_count"] == 1
    assert result["paired_comparisons"][0]["paired_count"] == 0


def test_provider_error_and_missing_usage_never_become_zero_cost(batch):
    batch.records[2]["judging"].update(
        status="provider_error", judgment=None, provider=None, latency_ms=None
    )
    batch.records[3]["judging"] = None
    batch.attempts = batch.attempts[:1]
    result = summary(batch, "failed")
    assert result["new_judging"]["failed_count"] == 1
    assert result["new_judging"]["not_run_count"] == 1
    assert result["new_judging"]["cost_usd_at_frozen_uncached_rates"] is None
    assert result["new_judging"]["latency_ms"]["missing_count"] == 2
    assert result["cumulative"]["judging"]["calls_missing_token_counts"]["input_tokens"] == 2
    assert result["cumulative"]["judging"][
        "observed_cost_subtotal_usd_at_frozen_uncached_rates"
    ] == pytest.approx(0.00019)


def test_partially_missing_tokens_preserve_known_components(batch):
    batch.records[2]["judging"]["provider"]["usage"]["input_tokens"] = None
    result = summary(batch)
    new = result["new_judging"]
    assert new["tokens"]["input_tokens"] is None
    assert new["tokens"]["output_tokens"] == 20
    assert new["cost_usd_at_frozen_uncached_rates"] is None
    assert new["observed_cost_subtotal_usd_at_frozen_uncached_rates"] == pytest.approx(0.00023)
    assert result["cumulative"]["judging"][
        "observed_cost_subtotal_usd_at_frozen_uncached_rates"
    ] == pytest.approx(0.00042)


@pytest.mark.parametrize("invalid_source", [False, True])
def test_cumulative_completion_requires_no_missing_or_invalid_source_cases(batch, invalid_source):
    # This separate fixture has no historical unknown; the live interrupted run does.
    for population in (batch.prior, batch.records):
        population[1]["judging"] = judgment()
        if invalid_source:
            population.append(
                row(
                    "candidate",
                    "invalid",
                    generation("invalid_answer"),
                    _skipped("invalid_source_generation"),
                )
            )
    batch.parent.update(
        source_planned_count=len(batch.prior),
        omitted=[{"id": "candidate-invalid"}] if invalid_source else [],
    )
    batch.plan.update(
        source_planned_count=len(batch.prior),
        omitted=deepcopy(batch.parent["omitted"]),
        prior_records_fingerprint=stable_id(batch.prior),
    )
    batch.plan["excluded_prior_attempts"][1]["status"] = "scored"
    result = summary(batch)
    assert result["status"] == "complete"
    assert result["cumulative_status"] == (
        "complete_with_failures" if invalid_source else "complete"
    )
    assert result["overall"]["dimensions"]["correctness"]["invalid_generation_count"] == int(
        invalid_source
    )
    assert result["cumulative"]["judging"]["cost_usd_at_frozen_uncached_rates"] == pytest.approx(
        0.00076
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "source_config",
        "judge_config",
        "nested_followup",
        "prior_fingerprint",
        "prior_attempt_fingerprint",
        "excluded_status",
        "rejudge_unknown",
        "rewrite_prior_judgment",
        "rewrite_generation",
        "rewrite_identity",
        "drop_source_case",
        "source_order",
        "drop_remaining_request",
        "remaining_request_order",
        "new_attempt_order",
        "retry_prior_attempt",
        "duplicate_attempt",
        "unrecorded_attempt",
        "generation_attempt",
        "model_call_unplanned",
        "prior_attempt_order",
    ],
)
def test_unsafe_followup_population_or_journal_changes_are_rejected(batch, mutation):
    if mutation == "source_config":
        batch.plan["source_records_fingerprint"] = "different"
    elif mutation == "judge_config":
        batch.plan["judge"]["pricing"]["input_per_million"] = 99
    elif mutation == "nested_followup":
        batch.parent["kind"] = "qa_judge_followup_plan"
    elif mutation == "prior_fingerprint":
        batch.plan["prior_records_fingerprint"] = "different"
    elif mutation == "prior_attempt_fingerprint":
        batch.plan["prior_attempts_fingerprint"] = "different"
    elif mutation == "excluded_status":
        batch.plan["excluded_prior_attempts"][1]["status"] = "not_run"
    elif mutation == "rejudge_unknown":
        batch.records[1]["judging"] = judgment()
    elif mutation == "rewrite_prior_judgment":
        batch.records[0]["judging"]["judgment"]["correctness"]["score"] = 0
    elif mutation == "rewrite_generation":
        batch.records[2]["generation"]["provider"]["usage"] = usage(1, 1)
    elif mutation == "rewrite_identity":
        batch.records[2]["case_id"] = "different"
    elif mutation == "drop_source_case":
        batch.records.pop()
    elif mutation == "source_order":
        batch.records.reverse()
    elif mutation == "drop_remaining_request":
        batch.plan["request_order"].pop()
        batch.plan["request_count"] -= 1
    elif mutation == "remaining_request_order":
        batch.plan["request_order"].reverse()
    elif mutation == "new_attempt_order":
        batch.attempts.reverse()
    elif mutation == "retry_prior_attempt":
        batch.attempts[0] = deepcopy(batch.prior_attempts[1])
    elif mutation == "duplicate_attempt":
        batch.attempts.append(deepcopy(batch.attempts[-1]))
    elif mutation == "unrecorded_attempt":
        batch.attempts.pop()
    elif mutation == "generation_attempt":
        batch.attempts[0]["stage"] = "generation"
    elif mutation == "model_call_unplanned":
        batch.attempts[0]["model_call_planned"] = False
    else:
        batch.prior_attempts.reverse()
        batch.plan["prior_attempts_fingerprint"] = stable_id(batch.prior_attempts)
    with pytest.raises(ValueError):
        summary(batch)


def test_render_separates_batch_completion_provenance_costs_and_ordinal_scores():
    result = summary(make_batch("base|<script>\n# heading"))
    result["execution_mode"] = "injected_models"
    report = render_followup(result)
    assert "New batch status: complete. Cumulative cohort status: incomplete." in report
    assert "New execution mode: injected\\_models. Prior execution mode: openai." in report
    assert "Offline injected-model fixture results" in report
    assert "does not establish a cumulative live evaluation" in report
    assert "base\\|&lt;script&gt; \\# heading" in report
    assert "<script>" not in report and "\n# heading" not in report
    assert "Labels: provisional" in report
    assert "not accuracy" in report
    assert "Historical generation costs are never included" in report
    assert "| Prior attempts | 2 | 2 | 1 | 0 | 1 | 0 | unknown | unknown | unknown |" in report
    assert "| New batch | 2 | 2 | 2 | 0 | 0 | 0 | 100 | 20 |" in report
    assert "| Cumulative source cohort | 4 | 4 | 3 | 0 | 1 | 0 | unknown |" in report
    assert result["human_reviewed"] is False
    assert "does not establish a cumulative live evaluation" in render_followup(
        {**result, "execution_mode": "unspecified"}
    )


def test_all_live_provenance_does_not_claim_complete_or_human_reviewed_cohort(batch):
    result = {**summary(batch), "execution_mode": "openai"}
    report = render_followup(result)
    assert "Offline injected-model fixture" not in report
    assert "Cumulative cohort status: incomplete" in report
    assert "No human-review or true-accuracy claim is made" in report
