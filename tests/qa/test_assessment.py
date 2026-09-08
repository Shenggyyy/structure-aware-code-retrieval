"""Offline integration checks for frozen generation-plus-judging experiments."""

import json
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.evaluation.dataset import load_benchmark, symbol_target
from structure_aware_retrieval.indexing import load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa import provider
from structure_aware_retrieval.qa.assessment_execution import execute_assessment
from structure_aware_retrieval.qa.assessment_plan import (
    make_model,
    prepare_assessment,
    validate_assessment_bundle,
)
from structure_aware_retrieval.qa.preparation import prepare_experiment
from structure_aware_retrieval.qa.provider import ModelProviderError, ModelResponse
from structure_aware_retrieval.relations import build_graph
from tests.qa.test_preparation import qa_experiment as qa_experiment  # noqa: F401

RUBRIC = Path(__file__).resolve().parents[2] / "configs/qa-judge-rubric-v1.json"
GENERATION_MODEL = "gpt-5.4-mini-2026-03-17"
JUDGE_MODEL = "offline-assessment-judge"


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write(path: Path, value):
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


@pytest.fixture(autouse=True)
def forbid_live_calls(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("Assessment integration must not access credentials or a live provider")

    monkeypatch.setattr(provider, "os", SimpleNamespace(environ=SimpleNamespace(get=forbidden)))
    monkeypatch.setattr(provider, "build_opener", forbidden)


def _prepare_study(config: Path, tmp_path: Path, *, max_reference_bytes=65536):
    index = load_index(config.parent / "index.sqlite")
    build_graph(index, config.parent / "graph.json")
    retrieval = (config.parent / "retrieval.toml").read_text(encoding="utf-8")
    (config.parent / "structure.toml").write_text(
        retrieval.replace('strategy = "bm25"', 'strategy = "structure"')
        + '\n[graphs]\nfixture = "graph.json"\n[structure]\nseed_strategy = "bm25"\n',
        encoding="utf-8",
    )
    config.write_text(
        config.read_text(encoding="utf-8") + 'structure = "structure.toml"\n', encoding="utf-8"
    )
    generation_bundle = tmp_path / "generation-bundle"
    generation_plan = prepare_experiment(config, generation_bundle)
    study_config = tmp_path / "study.toml"
    study_config.write_text(
        f'schema_version = 1\nrubric = "{RUBRIC.as_posix()}"\n'
        f'reference_version = "fixture-v1"\nmax_reference_bytes = {max_reference_bytes}\n'
        '[indexes]\nfixture = "index.sqlite"\n'
        f'[generation]\nmodel = "{GENERATION_MODEL}"\nmax_output_tokens = 1024\n'
        'api_key_env = "OPENAI_API_KEY"\nreasoning_effort = "none"\n'
        "[generation.pricing]\ninput_per_million = 0.75\noutput_per_million = 4.5\n"
        'as_of = "2026-09-08"\n'
        f'[judge]\nmodel = "{JUDGE_MODEL}"\nmax_output_tokens = 2048\n'
        'api_key_env = "OPENAI_API_KEY"\nreasoning_effort = "none"\n'
        "[judge.pricing]\ninput_per_million = 2.5\noutput_per_million = 15.0\n"
        'as_of = "2026-09-08"\n',
        encoding="utf-8",
    )
    output = tmp_path / "assessment-bundle"
    plan = prepare_assessment(generation_bundle, study_config, output)
    return SimpleNamespace(
        bundle=output,
        plan=plan,
        config=study_config,
        generation_bundle=generation_bundle,
        generation_plan=generation_plan,
        index=index,
    )


@pytest.fixture
def study(qa_experiment: Path, tmp_path: Path):
    return _prepare_study(qa_experiment, tmp_path)


def _dimension(status="scored", score=2, *, sources=None, claims=None):
    return {
        "status": status,
        "score": score,
        "rationale": "Offline transport fixture judgment; not a research result.",
        "evidence_ids": [] if sources is None else sources,
        "claim_indices": [] if claims is None else claims,
    }


class OfflineModel:
    def __init__(self, stage, events, *, behavior=None, output=None):
        self.stage = stage
        self.model = GENERATION_MODEL if stage == "generation" else JUDGE_MODEL
        self.events = events
        self.behavior = behavior
        self.output = output
        self.messages = []

    def complete(self, messages):
        payload = json.loads(messages[1]["content"])
        self.messages.append(deepcopy(messages))
        self.events.append((self.stage, payload["question"]))
        if self.output is not None:
            journal = _rows(self.output / "attempts.jsonl")
            assert journal[-1]["stage"] == self.stage
            assert (self.output / "summary.json").exists()
        if self.behavior is not None:
            response = self.behavior(payload)
            if response is not None:
                return response
        if self.stage == "generation":
            answer = (
                {"status": "insufficient_context", "claims": []}
                if payload["question"].startswith("Which private production")
                else {
                    "status": "answered",
                    "claims": [{"text": "An offline fixture claim.", "citations": ["S1"]}],
                }
            )
            return self.response(answer)
        abstained = payload["answer"]["status"] == "insufficient_context"
        if abstained:
            dimensions = {
                name: _dimension("not_applicable", None)
                for name in ("correctness", "completeness", "citation_support")
            }
            if payload["reference_context"]["expected_status"] == "answered":
                dimensions["completeness"] = _dimension(score=0)
        else:
            dimensions = {
                name: _dimension(sources=["packed:S1"], claims=[0])
                for name in ("correctness", "completeness", "citation_support")
            }
        return self.response(
            {
                "rubric_id": "repository-qa-judge-rubric-v1",
                **dimensions,
                "abstention": {
                    "decision": "appropriate" if abstained else "not_abstained",
                    "packed_context_sufficiency": "insufficient" if abstained else "sufficient",
                    "rationale": "Offline test fixture.",
                    "evidence_ids": [],
                },
                "reference_status": "usable",
                "reference_issues": [],
            }
        )

    def response(self, value):
        factor = 1 if self.stage == "generation" else 2
        return ModelResponse(
            text=json.dumps(value),
            model=self.model,
            usage={
                "input_tokens": 100 * factor,
                "output_tokens": 10 * factor,
                "total_tokens": 110 * factor,
                "cached_tokens": 0,
                "reasoning_tokens": 0,
            },
            request_id=f"offline-{self.stage}-{len(self.messages)}",
            finish_reason="completed",
            raw_response={"status": "completed", "fixture": True},
            response_id=f"resp-{self.stage}-{len(self.messages)}",
        )


def _execute(study, output, generation, judge, **overrides):
    settings = {
        "budget_usd": study.plan["estimated_cost"]["combined_usd"],
        "generation_model_id": GENERATION_MODEL,
        "judge_model_id": JUDGE_MODEL,
        "approved_plan": study.plan["plan_fingerprint"],
        "generation_model": generation,
        "judge_model": judge,
        **overrides,
    }
    return execute_assessment(study.bundle, output, **settings)


def test_preparation_freezes_shared_references_without_generation_leakage(study):
    plan, rows, references, rubric = validate_assessment_bundle(study.bundle)
    assert plan == study.plan
    assert len(rows) == 6
    assert {row["strategy"] for row in rows} == {"bm25", "structure"}
    assert len(references) == 3
    assert plan["annotation_status"] == "provisional"
    assert plan["human_review_required"] is False
    assert rubric["rubric_id"] == "repository-qa-judge-rubric-v1"
    for row in rows:
        messages = json.dumps(row["prepared"]["messages"])
        assert "REFERENCE-ONLY-MARKER" not in messages
        assert "RATIONALE-ONLY-MARKER" not in messages
        assert "reference_context" not in messages
        reference = references[row["case_id"]]
        assert reference["snapshot_id"] == row["prepared"]["context"]["snapshot_id"]
        assert reference["reference_points"][0]["text"].startswith("REFERENCE-ONLY-MARKER")
    assert not (study.bundle / "records.json").exists()


def test_reference_expansion_preserves_nested_definition_chunks(qa_experiment, tmp_path):
    index = load_index(qa_experiment.parent / "index.sqlite")
    parent = next(s for s in index.symbols.values() if s.qualified_name == "client.Client")
    child = next(
        s for s in index.symbols.values() if s.qualified_name == "client.Client.send_request"
    )
    target = asdict(symbol_target(parent))
    qrels = qa_experiment.parent / "benchmark/qrels.jsonl"
    with qrels.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps({"query_id": "q1", "target": target, "grade": 1, "rationale": "Nested"})
            + "\n"
        )
    cases_path = qa_experiment.parent / "cases.json"
    cases = _read(cases_path)
    cases["cases"][0]["source_targets"].append(target)
    cases["retrieval_benchmark_digest"] = load_benchmark(
        qa_experiment.parent / "benchmark/benchmark.json"
    ).digest
    _write(cases_path, cases)
    study = _prepare_study(qa_experiment, tmp_path)
    references = _read(study.bundle / "references.json")
    sources = references["qa-q1"]["reference_evidence"]
    expected_chunks = {
        chunk.id
        for chunk in index.chunks
        if chunk.path == parent.path
        and parent.start_line <= chunk.start_line <= chunk.end_line <= parent.end_line
    }
    assert expected_chunks <= {source["chunk_id"] for source in sources}
    assert child.id in {source["symbol_id"] for source in sources}
    assert "return url" in "".join(source["text"] for source in sources)
    assert all(source["truncated"] is False for source in sources)


def test_combined_estimate_reserves_both_stages_and_answer_as_judge_input(study):
    estimate = study.plan["estimated_cost"]
    assert estimate["includes_llm_judging"] is True
    assert estimate["billing_guarantee"] is False
    assert estimate["generation"]["maximum_api_calls"] == 6
    assert estimate["judging"]["maximum_api_calls"] == 6
    assert estimate["generation"]["maximum_output_tokens"] == 6 * 1024
    assert estimate["judging"]["maximum_output_tokens"] == 6 * 2048
    assert estimate["maximum_answer_bytes_reserved_per_judge_call"] >= 65536
    assert estimate["judging"]["estimated_input_tokens"] > 6 * 65536
    assert estimate["combined_usd"] == pytest.approx(
        estimate["generation"]["estimated_cost_usd"] + estimate["judging"]["estimated_cost_usd"]
    )
    assert estimate["combined_usd"] > study.generation_plan["estimated_cost_usd"]


@pytest.mark.parametrize(
    "override",
    [
        {"budget_usd": 0.000001},
        {"budget_usd": float("nan")},
        {"approved_plan": "0" * 64},
        {"generation_model_id": "other-generation-model"},
        {"judge_model_id": "other-judge-model"},
        {"judge_model": None},
    ],
)
def test_invalid_approval_never_calls_models_or_creates_run(study, tmp_path, override):
    events = []
    generation = OfflineModel("generation", events)
    judge = OfflineModel("judging", events)
    output = tmp_path / "rejected-run"
    with pytest.raises(ValueError):
        _execute(study, output, generation, judge, **override)
    assert events == []
    assert not output.exists()


def test_complete_run_journals_both_stages_and_uses_identical_case_references(study, tmp_path):
    events = []
    output = tmp_path / "complete-run"
    generation = OfflineModel("generation", events, output=output)
    judge = OfflineModel("judging", events, output=output)
    summary = _execute(study, output, generation, judge)
    assert summary["status"] == "complete"
    assert summary["execution_mode"] == "injected_models"
    assert summary["human_reviewed"] is False
    assert [stage for stage, _question in events] == ["generation", "judging"] * 6
    attempts, results = _rows(output / "attempts.jsonl"), _rows(output / "results.jsonl")
    assert [(r["id"], r["stage"]) for r in attempts] == [(r["id"], r["stage"]) for r in results]
    records = _read(output / "records.json")
    assert len(records) == 6
    assert all(row["generation"] and row["judging"] for row in records)
    refs_per_question = {}
    for messages in judge.messages:
        payload = json.loads(messages[1]["content"])
        reference = stable_id(payload["reference_context"])
        assert refs_per_question.setdefault(payload["question"], reference) == reference
        assert "strategy" not in payload
        assert "retrieval_scores" not in payload
    overall = summary["overall"]
    assert overall["dimensions"]["correctness"]["scored_count"] == 4
    assert overall["dimensions"]["correctness"]["not_applicable_count"] == 2
    assert overall["combined_usage"]["tokens"]["input_tokens"] == 1800
    assert overall["combined_usage"]["cost_usd_at_frozen_uncached_rates"] > 0
    assert _read(output / "summary.json") == summary
    assert (output / "report.md").exists()
    assert validate_assessment_bundle(output / "prepared")[0] == study.plan


def test_invalid_generation_skips_judging_without_semantic_zero_scores(study, tmp_path):
    events = []
    generation = OfflineModel("generation", events)
    generation.behavior = lambda _payload: generation.response(
        {"status": "answered", "claims": [{"text": "Bad source", "citations": ["S999"]}]}
    )
    judge = OfflineModel("judging", events)
    output = tmp_path / "invalid-generation"
    summary = _execute(study, output, generation, judge)
    assert summary["status"] == "complete_with_failures"
    assert len(generation.messages) == 6
    assert judge.messages == []
    assert {row["stage"] for row in _rows(output / "attempts.jsonl")} == {"generation"}
    overall = summary["overall"]
    assert overall["stages"]["judging"]["skipped_count"] == 6
    assert overall["dimensions"]["correctness"]["invalid_generation_count"] == 6
    assert overall["dimensions"]["correctness"]["mean"] is None
    assert overall["stages"]["judging"]["model_calls_observed"] == 0


def test_interrupted_judge_keeps_attempt_and_generation_but_unknown_combined_cost(study, tmp_path):
    events = []
    output = tmp_path / "interrupted-run"
    generation = OfflineModel("generation", events, output=output)

    def interrupt(_payload):
        raise KeyboardInterrupt("Offline simulated interruption after judge dispatch")

    judge = OfflineModel("judging", events, behavior=interrupt, output=output)
    with pytest.raises(KeyboardInterrupt):
        _execute(study, output, generation, judge)
    summary = _read(output / "summary.json")
    assert summary["status"] == "interrupted"
    assert [stage for stage, _question in events] == ["generation", "judging"]
    assert len(_rows(output / "attempts.jsonl")) == 2
    assert len(_rows(output / "results.jsonl")) == 1
    overall = summary["overall"]
    assert overall["stages"]["generation"]["completed_count"] == 1
    assert overall["stages"]["judging"]["unknown_outcome_count"] == 1
    assert overall["stages"]["judging"]["not_run_count"] == 5
    assert overall["combined_usage"]["tokens"]["input_tokens"] is None
    assert overall["combined_usage"]["cost_usd_at_frozen_uncached_rates"] is None
    assert overall["combined_usage"]["observed_token_subtotals"]["input_tokens"] == 100
    assert overall["dimensions"]["correctness"]["mean"] is None


@pytest.mark.parametrize("stage", ["generation", "judging"])
def test_known_failure_usage_is_archived_and_execution_stops(study, tmp_path, stage):
    events = []
    generation = OfflineModel("generation", events)
    judge = OfflineModel("judging", events)
    failed = generation if stage == "generation" else judge
    response = asdict(failed.response({"partial": "offline partial provider output"}))
    response["finish_reason"] = "incomplete"

    def fail(_payload):
        raise ModelProviderError("Offline incomplete output", response_metadata=response)

    failed.behavior = fail
    output = tmp_path / f"failed-{stage}"
    summary = _execute(study, output, generation, judge)
    assert summary["status"] == "failed"
    assert [event[0] for event in events] == (
        ["generation"] if stage == "generation" else ["generation", "judging"]
    )
    recorded = _read(output / "records.json")[0][stage]
    assert recorded["status"] == "provider_error"
    assert recorded["raw_output"] == response["text"]
    assert recorded["provider"]["usage"] == response["usage"]
    metrics = summary["overall"]["stages"][stage]
    assert metrics["tokens"]["input_tokens"] == response["usage"]["input_tokens"]
    assert metrics["cost_usd_at_frozen_uncached_rates"] > 0
    assert summary["overall"]["dimensions"]["correctness"]["mean"] is None


def test_existing_preparation_and_run_outputs_are_preserved(study, tmp_path):
    old_plan = (study.bundle / "plan.json").read_bytes()
    with pytest.raises(FileExistsError):
        prepare_assessment(study.generation_bundle, study.config, study.bundle)
    assert (study.bundle / "plan.json").read_bytes() == old_plan
    output = tmp_path / "existing-run"
    output.mkdir()
    marker = output / "preserve.txt"
    marker.write_text("preserve prior results", encoding="utf-8")
    events = []
    with pytest.raises(FileExistsError):
        _execute(study, output, OfflineModel("generation", events), OfflineModel("judging", events))
    assert events == []
    assert marker.read_text(encoding="utf-8") == "preserve prior results"


@pytest.mark.parametrize(
    "filename", ["references.json", "rubric.json", "generation/requests.jsonl"]
)
def test_changed_frozen_inputs_fail_before_dispatch(study, tmp_path, filename):
    path = study.bundle / filename
    if filename.endswith(".jsonl"):
        rows = _rows(path)
        rows[0]["prepared"]["question"] = "Changed frozen question"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    else:
        value = _read(path)
        if filename == "references.json":
            value["qa-q1"]["reference_points"][0]["text"] = "Changed frozen reference"
        else:
            value["system_prompt"] = "Changed rubric instructions"
        _write(path, value)
    events = []
    output = tmp_path / "tampered-run"
    with pytest.raises(ValueError):
        _execute(study, output, OfflineModel("generation", events), OfflineModel("judging", events))
    assert events == []
    assert not output.exists()


def test_reference_budget_refuses_truncation_without_publishing_partial_bundle(
    qa_experiment, tmp_path
):
    with pytest.raises(ValueError, match="Reference context exceeds"):
        _prepare_study(qa_experiment, tmp_path, max_reference_bytes=1)
    assert not (tmp_path / "assessment-bundle").exists()


def test_empty_generation_contexts_still_prepare_and_judge_without_generation_calls(
    qa_experiment, tmp_path
):
    qa_experiment.write_text(
        qa_experiment.read_text(encoding="utf-8").replace(
            "max_context_bytes = 16000", "max_context_bytes = 2"
        ),
        encoding="utf-8",
    )
    study = _prepare_study(qa_experiment, tmp_path)
    estimate = study.plan["estimated_cost"]
    assert estimate["generation"]["maximum_api_calls"] == 0
    assert estimate["generation"]["estimated_cost_usd"] == 0
    assert estimate["judging"]["maximum_api_calls"] == 6
    assert estimate["combined_usd"] > 0
    events = []
    generation = OfflineModel("generation", events)
    judge = OfflineModel("judging", events)
    summary = _execute(study, tmp_path / "local-generation-run", generation, judge)
    assert summary["status"] == "complete"
    assert generation.messages == []
    assert len(judge.messages) == 6
    assert summary["overall"]["abstentions"]["local_count"] == 6
    assert summary["overall"]["dimensions"]["completeness"]["mean"] == 0
    assert summary["overall"]["stages"]["generation"]["model_calls_observed"] == 0


@pytest.mark.parametrize("live_stage", ["generation", "judging"])
def test_mixed_api_and_fake_stages_are_rejected_without_calls(study, tmp_path, live_stage):
    _plan, _rows, _refs, rubric = validate_assessment_bundle(study.bundle)
    events = []
    generation = (
        make_model(study.plan["generation"])
        if live_stage == "generation"
        else OfflineModel("generation", events)
    )
    judge = (
        make_model(study.plan["judge"], rubric)
        if live_stage == "judging"
        else OfflineModel("judging", events)
    )
    output = tmp_path / "mixed-mode"
    with pytest.raises(ValueError):
        _execute(study, output, generation, judge)
    assert events == []
    assert not output.exists()


def test_two_api_adapters_are_labeled_consistently_with_offline_transport_stubs(
    study, tmp_path, monkeypatch
):
    _plan, _rows, _refs, rubric = validate_assessment_bundle(study.bundle)
    events = []
    fake_generation = OfflineModel("generation", events)
    fake_judge = OfflineModel("judging", events)

    def offline_complete(model, messages):
        fake = fake_generation if model.model == GENERATION_MODEL else fake_judge
        return fake.complete(messages)

    monkeypatch.setattr(provider.OpenAIModel, "complete", offline_complete)
    summary = _execute(
        study,
        tmp_path / "api-adapter-offline-test",
        make_model(study.plan["generation"]),
        make_model(study.plan["judge"], rubric),
    )
    assert summary["execution_mode"] == "openai"
    assert len(events) == 12


def test_false_valued_test_models_are_used_without_live_fallback(study, tmp_path):
    class FalseyOfflineModel(OfflineModel):
        def __bool__(self):
            return False

    events = []
    generation = FalseyOfflineModel("generation", events)
    judge = FalseyOfflineModel("judging", events)
    summary = _execute(study, tmp_path / "falsey-model-run", generation, judge)
    assert summary["status"] == "complete"
    assert summary["execution_mode"] == "injected_models"
    assert len(events) == 12


def test_cli_checks_offline_and_requires_execute_even_with_approval_flags(
    study, tmp_path, monkeypatch
):
    def forbidden_execution(*_args, **_kwargs):
        pytest.fail("CLI dispatched a run without --execute")

    monkeypatch.setattr(
        "structure_aware_retrieval.qa.assessment_execution.execute_assessment",
        forbidden_execution,
    )
    runner = CliRunner()
    before = (study.bundle / "plan.json").read_bytes()
    checked = runner.invoke(app, ["check-qa-assessment", "--bundle", str(study.bundle)])
    assert checked.exit_code == 0, checked.output
    assert "no API calls made" in checked.output
    assert (study.bundle / "plan.json").read_bytes() == before
    output = tmp_path / "cli-not-executed"
    result = runner.invoke(
        app,
        [
            "run-qa-assessment",
            "--bundle",
            str(study.bundle),
            "--output",
            str(output),
            "--generation-model",
            GENERATION_MODEL,
            "--judge-model",
            JUDGE_MODEL,
            "--approve-plan",
            study.plan["plan_fingerprint"],
            "--budget-usd",
            str(study.plan["estimated_cost"]["combined_usd"]),
        ],
    )
    assert result.exit_code == 1, result.output
    assert "No calls made" in result.output
    assert not output.exists()
