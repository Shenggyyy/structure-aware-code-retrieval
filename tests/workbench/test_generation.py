"""Offline generation uses canonical source prompts and explicit injected model responses."""

import json
import threading
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

import pytest

from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import complete_question, prepare_question
from structure_aware_retrieval.qa.assessment_plan import estimate_input_tokens
from structure_aware_retrieval.qa.provider import ModelProviderError, ModelResponse, OpenAIModel
from structure_aware_retrieval.retrieval import BM25Retriever
from structure_aware_retrieval.strategies import STRATEGIES
from structure_aware_retrieval.workbench import generation
from structure_aware_retrieval.workbench.comparison import _save, load_comparison
from structure_aware_retrieval.workbench.storage import read_json, safe_path, write_json


class FakeModel:
    def __init__(self, callback=None):
        self.calls = []
        self.callback = callback
        self.response = ModelResponse(
            text=json.dumps(
                {
                    "status": "answered",
                    "claims": [{"text": "Fixture checksum claim.", "citations": ["S1"]}],
                }
            ),
            model="injected-fixture",
            usage={
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
                "cached_tokens": 0,
                "reasoning_tokens": 0,
            },
            request_id="req-fixture",
            response_id="resp-fixture",
            raw_response={"id": "resp-fixture", "status": "completed"},
        )

    def complete(self, messages):
        self.calls.append(deepcopy(messages))
        if self.callback:
            return self.callback(len(self.calls), self.response)
        return self.response


@pytest.fixture
def preview(sample_repository, tmp_path):
    workspace = tmp_path / "workspace"
    index = tmp_path / "index.sqlite"
    build_index(sample_repository, index)
    retriever = BM25Retriever(load_index(index))
    prepared = prepare_question(retriever, "What does calculate_checksum do?", top_k=2)
    qa = complete_question(prepared)
    # Repeated real source context is intentional: generation may yield identical answers.
    record = {
        "schema_version": 1,
        "kind": "five_strategy_comparison",
        "run_id": uuid4().hex,
        "repository_id": "a" * 64,
        "mode": "context_preview",
        "status": "preview_complete",
        "question": prepared["question"],
        "created_at": "2026-09-09T00:00:00+00:00",
        "finished_at": "2026-09-09T00:00:00+00:00",
        "settings": {"context_top_k": 2, "max_context_bytes": 16000},
        "resources": {"snapshot_id": retriever.index.metadata["snapshot_id"]},
        "benchmark_metrics": None,
        "relevance_labels": "unlabeled",
        "encoder_mode": "offline_fixture",
        "api_calls": 0,
        "results": [
            {
                "strategy": strategy,
                "status": "preview",
                "qa": deepcopy(qa),
                "error": None,
                "hits": [{"fixture": "stored provenance"}],
                "timing_ms": {
                    "resource_load": 1.0,
                    "retrieval": prepared["timing_ms"]["retrieval"],
                    "context_and_prompt": prepared["timing_ms"]["context_and_prompt"],
                    "automatic_validation": qa["timing_ms"]["generation_and_validation"],
                    "generation": None,
                    "strategy_total": 2.0,
                },
                "tokens": {"input": None, "output": None, "total": None, "cached": None},
                "cost": {"estimated_usd": None, "billed_usd": None, "model_calls": 0},
            }
            for strategy in STRATEGIES
        ],
    }
    _save(workspace, record)
    return workspace, record, retriever


def plan_for(preview):
    workspace, record, _ = preview
    return generation.create_generation_plan(workspace, record["run_id"])


def execute(preview, plan, model, **kwargs):
    return generation.execute_generation_plan(
        preview[0],
        plan["plan_id"],
        budget_usd=plan["estimated_cost_usd"] + 0.01,
        confirmed_model=plan["model"],
        model=model,
        **kwargs,
    )


def rewrite_plan(preview, plan):
    plan["fingerprint"] = stable_id({k: v for k, v in plan.items() if k != "fingerprint"})
    write_json(preview[0], f"generation-plans/{plan['plan_id']}/plan.json", plan)


def test_offline_plan_freezes_exact_requests_source_and_conservative_cost(preview, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(OpenAIModel, "complete", lambda *_: pytest.fail("Paid call in plan"))
    plan = plan_for(preview)
    assert plan["request_limit"] == 5 and plan["judge_calls"] == 0
    assert plan["preview_fingerprint"] == preview[1]["fingerprint"]
    expected = OpenAIModel(**plan["settings"])
    for row, source in zip(plan["strategies"], preview[1]["results"], strict=True):
        assert row["request_payload"] == expected.request_payload(source["qa"]["messages"])
        assert row["estimated_input_tokens"] == estimate_input_tokens(row["request_payload"])
        assert row["max_output_tokens"] == 1024
        assert row["estimated_cost_usd"] == pytest.approx(
            (row["estimated_input_tokens"] * 0.75 + 1024 * 4.5) / 1e6
        )
    assert plan["estimated_cost_usd"] == sum(x["estimated_cost_usd"] for x in plan["strategies"])
    assert generation.load_generation_plan(preview[0], plan["plan_id"]) == plan
    assert generation.load_generation_execution(preview[0], plan["plan_id"]) is None


def test_five_identical_answers_keep_source_original_immutable_and_archive_metadata(preview):
    plan = plan_for(preview)
    before = safe_path(preview[0], f"runs/{preview[1]['run_id']}/run.json").read_bytes()
    model = FakeModel()
    result = execute(preview, plan, model)
    assert result["status"] == "generation_complete"
    assert result["mode"] == "offline_test" and result["api_calls"] == 0
    assert result["parent_preview_run_id"] == preview[1]["run_id"]
    assert result["run_id"] != preview[1]["run_id"]
    assert result["benchmark_metrics"] is None and result["relevance_labels"] == "unlabeled"
    assert len(model.calls) == 5
    assert model.calls == [row["qa"]["messages"] for row in preview[1]["results"]]
    for row, original in zip(result["results"], preview[1]["results"], strict=True):
        assert row["qa"]["answer"]["claims"][0]["text"] == "Fixture checksum claim."
        assert row["qa"]["context"] == original["qa"]["context"]
        assert row["hits"] == original["hits"]
        assert row["timing_ms"]["retrieval"] == original["timing_ms"]["retrieval"]
        assert row["timing_ms"]["generation"] >= 0
        assert row["timing_ms"]["automatic_validation"] >= 0
        assert row["tokens"]["total"] == 120
        assert row["cost"]["estimated_usd"] == pytest.approx(0.000165)
        assert row["cost"]["billed_usd"] is None
        assert row["qa"]["provider"]["request_id"] == "req-fixture"
        assert row["qa"]["provider"]["raw_response"]["id"] == "resp-fixture"
        assert row["qa"]["automatic_checks"]["citation_ids_valid"] is True
        assert row["qa"]["evaluation"]["answer_correctness"] is None
        assert row["qa"]["llm_assessment"]["status"] == "not_run"
    summary = result["generation"]["summary"]
    assert summary["calls_started"] == summary["responses_received"] == 5
    assert summary["outcome_unknown"] == summary["not_run"] == 0
    assert summary["usage"]["tokens"]["total_tokens"] == 600
    assert generation.load_generation_execution(preview[0], plan["plan_id"]) == result
    assert safe_path(preview[0], f"runs/{preview[1]['run_id']}/run.json").read_bytes() == before


@pytest.mark.parametrize("budget", [0, -1, True, float("nan"), float("inf"), 0.00001])
def test_invalid_budget_cannot_consume_plan_or_call_model(preview, budget):
    plan = plan_for(preview)
    model = FakeModel()
    with pytest.raises(ValueError, match="Budget"):
        generation.execute_generation_plan(
            preview[0],
            plan["plan_id"],
            budget_usd=budget,
            confirmed_model=plan["model"],
            model=model,
        )
    assert not model.calls
    assert not safe_path(preview[0], f"generation-plans/{plan['plan_id']}/execution").exists()


def test_wrong_model_and_missing_or_invalid_key_leave_plan_unconsumed(preview, monkeypatch):
    plan = plan_for(preview)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="exact model"):
        generation.validate_generation_approval(
            preview[0], plan["plan_id"], budget_usd=1, confirmed_model="another-model"
        )
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        generation.validate_generation_approval(
            preview[0], plan["plan_id"], budget_usd=1, confirmed_model=plan["model"]
        )
    monkeypatch.setenv("OPENAI_API_KEY", "secret\ninvalid")
    with pytest.raises(ValueError, match="invalid characters") as failure:
        generation.validate_generation_approval(
            preview[0], plan["plan_id"], budget_usd=1, confirmed_model=plan["model"]
        )
    assert "secret" not in str(failure.value)
    assert not safe_path(preview[0], f"generation-plans/{plan['plan_id']}/execution").exists()


@pytest.mark.parametrize(
    "field", ["model", "estimated_cost_usd", "request_limit", "pricing", "payload"]
)
def test_recomputed_checksum_cannot_hide_frozen_plan_tampering(preview, field):
    plan = plan_for(preview)
    if field == "payload":
        plan["strategies"][0]["request_payload"]["max_output_tokens"] = 9999
    elif field == "pricing":
        plan[field]["input_per_million"] = 0
    else:
        plan[field] = "another-model" if field == "model" else 0
    rewrite_plan(preview, plan)
    with pytest.raises(ValueError, match="configuration or estimate"):
        execute(preview, plan, FakeModel())


def test_preview_edit_after_freeze_requires_new_plan(preview):
    plan = plan_for(preview)
    preview[1]["results"][0]["hits"] = []
    _save(preview[0], preview[1])
    with pytest.raises(ValueError, match="preview changed"):
        execute(preview, plan, FakeModel())


def test_changed_system_message_is_rejected_even_if_hashes_are_recomputed(preview):
    preview[1]["results"][0]["qa"]["messages"][0]["content"] = "untrusted instructions"
    qa = preview[1]["results"][0]["qa"]
    qa["prompt_fingerprint"] = stable_id(qa["messages"])
    _save(preview[0], preview[1])
    with pytest.raises(ValueError, match="checked source evidence"):
        plan_for(preview)


def test_missing_retrieval_and_empty_evidence_do_not_call_or_inflate_estimate(preview):
    class EmptyRetriever:
        index = preview[2].index

        def search(self, *args, **kwargs):
            return []

    empty = complete_question(prepare_question(EmptyRetriever(), preview[1]["question"], top_k=2))
    preview[1]["results"][0].update(status="failed", qa=None, error={"message": "missing index"})
    preview[1]["results"][1].update(status="insufficient_context", qa=empty)
    preview[1]["status"] = "partial"
    _save(preview[0], preview[1])
    plan = plan_for(preview)
    assert plan["request_limit"] == 3
    assert [x["status"] for x in plan["strategies"][:2]] == ["unavailable", "no_evidence"]
    assert all(x["estimated_cost_usd"] == 0 for x in plan["strategies"][:2])
    model = FakeModel()
    result = execute(preview, plan, model)
    assert len(model.calls) == 3
    assert result["status"] == "partial"
    assert result["results"][0]["error"]["message"] == "missing index"
    assert result["results"][1]["status"] == "insufficient_context"


def test_invalid_answer_and_known_provider_failure_preserve_other_answers(preview):
    def respond(number, response):
        if number == 2:
            return replace(response, text="not valid json")
        if number == 3:
            raise ModelProviderError(
                "Known refusal",
                response_metadata={
                    "model": "injected-fixture",
                    "usage": response.usage,
                    "raw_response": {"status": "completed", "refusal": "fixture"},
                },
            )
        return response

    model = FakeModel(respond)
    result = execute(preview, plan_for(preview), model)
    assert len(model.calls) == 5
    assert result["status"] == "partial"
    assert [x["status"] for x in result["results"]] == [
        "answered",
        "invalid_answer",
        "provider_error",
        "answered",
        "answered",
    ]
    assert result["results"][1]["qa"]["raw_output"] == "not valid json"
    assert result["results"][2]["qa"]["provider"]["raw_response"]["refusal"] == "fixture"
    assert result["generation"]["summary"]["responses_received"] == 5


def test_transport_unknown_stops_remaining_calls_without_retry(preview):
    def respond(number, response):
        if number == 2:
            raise ModelProviderError("Timeout; request may have been processed")
        return response

    plan = plan_for(preview)
    model = FakeModel(respond)
    result = execute(preview, plan, model)
    assert len(model.calls) == 2
    assert result["status"] == "interrupted"
    assert [x["status"] for x in result["results"]] == [
        "answered",
        "outcome_unknown",
        "not_run",
        "not_run",
        "not_run",
    ]
    summary = result["generation"]["summary"]
    assert summary["calls_started"] == 2
    assert summary["responses_received"] == 1
    assert summary["outcome_unknown"] == 1 and summary["not_run"] == 3
    assert summary["usage"]["cost_usd_at_frozen_uncached_rates"] is None
    assert summary["usage"]["observed_token_subtotals"]["input_tokens"] == 100
    with pytest.raises(FileExistsError, match="already consumed"):
        execute(preview, plan, model)
    assert len(model.calls) == 2


def test_missing_usage_keeps_unknown_total_and_known_subtotals(preview):
    model = FakeModel(
        lambda number, response: replace(response, usage={}) if number == 2 else response
    )
    result = execute(preview, plan_for(preview), model)
    assert result["status"] == "generation_complete"
    assert all(value is None for value in result["results"][1]["tokens"].values())
    assert result["results"][1]["cost"]["estimated_usd"] is None
    usage = result["generation"]["summary"]["usage"]
    assert usage["tokens"]["input_tokens"] is None
    assert usage["observed_token_subtotals"]["input_tokens"] == 400
    assert usage["calls_missing_token_counts"]["input_tokens"] == 1


def test_attempt_is_durable_before_provider_call_and_keyboard_interrupt_is_unknown(preview):
    plan = plan_for(preview)

    def respond(number, response):
        record = generation.load_generation_execution(preview[0], plan["plan_id"])
        assert record["results"][number - 1]["execution"]["state"] == "started"
        assert record["generation"]["summary"]["calls_started"] == number
        if number == 2:
            raise KeyboardInterrupt()
        return response

    with pytest.raises(KeyboardInterrupt):
        execute(preview, plan, FakeModel(respond))
    saved = generation.load_generation_execution(preview[0], plan["plan_id"])
    assert saved["status"] == "interrupted"
    assert [x["status"] for x in saved["results"]] == [
        "answered",
        "outcome_unknown",
        "not_run",
        "not_run",
        "not_run",
    ]
    assert saved["results"][1]["timing_ms"]["generation"] >= 0


def test_callback_interruption_before_requests_is_known_zero_calls(preview):
    plan = plan_for(preview)
    model = FakeModel()

    def stop(_record):
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        execute(preview, plan, model, on_progress=stop)
    saved = generation.load_generation_execution(preview[0], plan["plan_id"])
    assert not model.calls
    assert saved["generation"]["summary"]["calls_started"] == 0
    assert saved["generation"]["summary"]["not_run"] == 5
    assert all(row["status"] == "not_run" for row in saved["results"])


def test_recovery_reconciles_only_abandoned_linked_records_and_preserves_final(preview):
    plan = plan_for(preview)
    final = execute(preview, plan, FakeModel())
    path = safe_path(preview[0], f"runs/{final['run_id']}/run.json")
    before = path.read_bytes()
    generation.recover_generation(preview[0])
    assert path.read_bytes() == before
    stale = deepcopy(final)
    stale["status"] = "running"
    stale["results"][1]["execution"]["state"] = "started"
    stale["results"][1]["status"] = "running"
    for row in stale["results"][2:]:
        row["execution"]["state"] = "pending"
        row["status"] = "pending"
    _save(preview[0], stale)
    generation.recover_generation(preview[0])
    recovered = load_comparison(preview[0], stale["run_id"])
    assert recovered["status"] == "interrupted"
    assert recovered["results"][0] == final["results"][0]
    assert recovered["results"][1]["status"] == "outcome_unknown"
    assert all(row["status"] == "not_run" for row in recovered["results"][2:])
    assert load_comparison(preview[0], preview[1]["run_id"]) == preview[1]


def test_concurrent_duplicate_rejected_and_recovery_skips_active_execution(preview):
    plan = plan_for(preview)
    entered, release = threading.Event(), threading.Event()
    results, errors = [], []

    def respond(number, response):
        if number == 1:
            entered.set()
            assert release.wait(timeout=10)
        return response

    model = FakeModel(respond)

    def run():
        try:
            results.append(execute(preview, plan, model))
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert entered.wait(timeout=10)
        with pytest.raises(FileExistsError, match="already consumed"):
            execute(preview, plan, FakeModel())
        generation.recover_generation(preview[0])
        active = generation.load_generation_execution(preview[0], plan["plan_id"])
        assert active["status"] == "running"
        assert active["results"][0]["execution"]["state"] == "started"
    finally:
        release.set()
        worker.join(timeout=10)
    assert not worker.is_alive() and not errors
    assert results[0]["status"] == "generation_complete"
    assert len(model.calls) == 5


def test_bad_claim_never_recovers_an_unrelated_run(preview):
    plan = plan_for(preview)
    result = execute(preview, plan, FakeModel())
    relative = f"generation-plans/{plan['plan_id']}/execution/claim.json"
    claim = read_json(preview[0], relative)
    claim["run_id"] = preview[1]["run_id"]
    claim["fingerprint"] = stable_id({k: v for k, v in claim.items() if k != "fingerprint"})
    write_json(preview[0], relative, claim)
    with pytest.raises(ValueError, match="does not match"):
        generation.load_generation_execution(preview[0], plan["plan_id"])
    generation.recover_generation(preview[0])
    assert load_comparison(preview[0], preview[1]["run_id"]) == preview[1]
    assert load_comparison(preview[0], result["run_id"]) == result


@pytest.mark.parametrize("field", ["snapshot_id", "context_top_k", "max_context_bytes"])
def test_preview_context_must_match_resource_version_and_uniform_settings(preview, field):
    section = "resources" if field == "snapshot_id" else "settings"
    preview[1][section][field] = "different-snapshot" if field == "snapshot_id" else 10
    _save(preview[0], preview[1])
    with pytest.raises(ValueError, match="snapshot or settings"):
        plan_for(preview)


def test_conservative_context_window_limit_rejects_plan_before_call(preview, monkeypatch):
    monkeypatch.setattr(generation, "estimate_input_tokens", lambda _: 399_000)
    with pytest.raises(ValueError, match="exceeds the model context window"):
        plan_for(preview)


def test_pre_call_progress_shows_running_without_marking_request_sent(preview):
    plan = plan_for(preview)
    model = FakeModel()

    def stop_before_send(record):
        if record["results"][0]["status"] == "running":
            assert record["results"][0]["execution"]["state"] == "pending"
            assert record["generation"]["summary"]["calls_started"] == 0
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        execute(preview, plan, model, on_progress=stop_before_send)
    result = generation.load_generation_execution(preview[0], plan["plan_id"])
    assert result["results"][0]["status"] == "not_run"
    assert not model.calls
