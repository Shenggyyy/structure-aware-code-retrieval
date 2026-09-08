"""Paid-run accounting and integrity checks use injected offline models only."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa import execution
from structure_aware_retrieval.qa.answering import prepare_question
from structure_aware_retrieval.qa.execution import execute_bundle
from structure_aware_retrieval.qa.provider import ANSWER_SCHEMA, ModelProviderError, ModelResponse
from structure_aware_retrieval.retrieval import BM25Retriever

ANSWER = '{"status":"answered","claims":[{"text":"It computes a checksum.","citations":["S1"]}]}'
ABSTENTION = '{"status":"insufficient_context","claims":[]}'


class FakeModel:
    def __init__(self, outputs=None):
        self.outputs = [ANSWER, ABSTENTION] if outputs is None else outputs
        self.calls = []
        self.before_call = None

    def complete(self, messages):
        if self.before_call:
            self.before_call(len(self.calls))
        self.calls.append(deepcopy(messages))
        value = self.outputs[len(self.calls) - 1]
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, ModelResponse):
            return value
        return ModelResponse(
            text=value,
            model="offline-model",
            request_id=f"req-{len(self.calls)}",
            finish_reason="completed",
            usage={
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
                "cached_tokens": 0,
                "reasoning_tokens": 0,
            },
        )


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True), encoding="utf-8")


def update_bundle(bundle, *, mutate=None, recalculate=True):
    plan, cases, rows = (
        read(bundle / "plan.json"),
        read(bundle / "cases.json"),
        read_rows(bundle / "requests.jsonl"),
    )
    if mutate:
        mutate(plan, cases, rows)
    if recalculate:
        plan["request_count"] = len(rows)
        plan["request_digest"] = stable_id(rows)
        plan["cases_digest"] = stable_id(cases)
        plan["content_fingerprint"] = stable_id(
            [(row["id"], row["prepared"]["prompt_fingerprint"]) for row in rows]
        )
        plan["plan_fingerprint"] = stable_id(
            {key: value for key, value in plan.items() if key != "plan_fingerprint"}
        )
    write(bundle / "plan.json", plan)
    write(bundle / "cases.json", cases)
    (bundle / "requests.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


@pytest.fixture
def bundle(sample_repository: Path, tmp_path: Path):
    database = tmp_path / "index.sqlite"
    build_index(sample_repository, database)
    retriever = BM25Retriever(load_index(database))
    cases = {
        "schema_version": 1,
        "id": "qa-test",
        "version": "0.1.0",
        "annotation_status": "provisional",
        "retrieval_benchmark": "../original/benchmark.json",
        "retrieval_benchmark_digest": stable_id("original-benchmark"),
        "cases": [
            {
                "id": "checksum",
                "repository": "sample",
                "question": "What does calculate_checksum do?",
                "source_query_id": "checksum-query",
                "expected_status": "answered",
                "reference_points": ["It computes the checksum."],
                "source_targets": [],
                "rationale": "Source-based draft.",
            },
            {
                "id": "control",
                "repository": "sample",
                "question": "Which deployed server currently calls calculate_checksum?",
                "source_query_id": None,
                "expected_status": "insufficient_context",
                "reference_points": [
                    "A deployment inventory is unavailable in this source snapshot."
                ],
                "source_targets": [],
                "rationale": "Repository scope control.",
            },
        ],
    }
    rows = [
        {
            "id": stable_id("bm25", case["id"]),
            "strategy": "bm25",
            "case_id": case["id"],
            "repository": "sample",
            "prepared": prepare_question(retriever, case["question"], top_k=3),
        }
        for case in cases["cases"]
    ]
    source = rows[0]["prepared"]["context"]["evidence"][0]
    cases["cases"][0]["source_targets"] = [
        {key: source[key] for key in ("path", "qualified_name", "start_line", "end_line")}
    ]
    pricing = {"input_per_million": 0.75, "output_per_million": 4.5, "as_of": "2026-09-08"}
    schema_size = len(
        json.dumps(ANSWER_SCHEMA, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    )
    estimate = sum(
        (
            (
                sum(len(message["content"].encode()) for message in row["prepared"]["messages"])
                + 4096
                + schema_size
            )
            * 0.75
            + 1024 * 4.5
        )
        / 1_000_000
        for row in rows
    )
    plan = {
        "schema_version": 1,
        "model": "offline-model",
        "max_output_tokens": 1024,
        "api_key_env": "OPENAI_API_KEY",
        "request_count": len(rows),
        "request_digest": stable_id(rows),
        "cases_digest": stable_id(cases),
        "estimated_cost_usd": estimate,
        "pricing": pricing,
        "content_fingerprint": stable_id(
            [(r["id"], r["prepared"]["prompt_fingerprint"]) for r in rows]
        ),
    }
    plan["plan_fingerprint"] = stable_id(plan)
    directory = tmp_path / "prepared"
    directory.mkdir()
    write(directory / "plan.json", plan)
    write(directory / "cases.json", cases)
    (directory / "requests.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    return directory


def test_success_archives_answers_without_automatic_semantic_grades(bundle, tmp_path):
    model, output = FakeModel(), tmp_path / "execution"
    summary = execute_bundle(bundle, output, budget_usd=1, model=model)
    assert len(model.calls) == 2
    assert summary["requested"] == summary["attempted"] == summary["completed"] == 2
    assert summary["failed"] == summary["not_run"] == summary["unknown_outcome"] == 0
    assert summary["status"] == "complete"
    assert summary["local_abstentions"] == 0
    assert summary["model_abstentions"] == 1
    assert summary["model_calls"] == 2
    assert summary["tokens"]["input_tokens"] == 200
    assert summary["tokens"]["output_tokens"] == 40
    assert summary["cost_usd_at_frozen_uncached_rates"] == pytest.approx(
        (200 * 0.75 + 40 * 4.5) / 1e6
    )
    assert summary["answer_correctness"] is summary["citation_support"] is None
    assert summary["citation_identity"] == {"valid": 1, "invalid": 0, "unavailable": 1, "rate": 1}
    assert summary["draft_expected_status_agreement"] == {"matches": 2, "evaluated": 2, "rate": 1}
    assert summary["abstention_controls"] == {"matched": 1, "attempted": 1, "rate": 1}
    assert summary["per_strategy"]["bm25"]["answer_correctness"] is None
    assert summary["per_strategy"]["bm25"]["tokens"] == summary["tokens"]
    assert summary["latency_ms"]["total_excluding_load"]["mean"] == pytest.approx(
        sum(
            summary["latency_ms"][stage]["mean"]
            for stage in ("retrieval", "context_and_prompt", "generation_and_validation")
        )
    )
    assert read(output / "summary.json") == summary
    records = read_rows(output / "results.jsonl")
    template = read(output / "review-template.json")
    assert template["run_fingerprint"] == summary["run_fingerprint"]
    assert [item["answer_fingerprint"] for item in template["reviews"]] == [
        record["result"]["answer_fingerprint"] for record in records
    ]
    assert all(item["status"] == "pending" for item in template["reviews"])
    assert all(
        item["correctness"] is item["citation_support"] is None for item in template["reviews"]
    )
    assert read(output / "cases.json") == read(bundle / "cases.json")
    assert (output / "answer-0001.md").exists()
    assert (output / "answer-0002.md").exists()
    assert "reference_points" not in json.dumps(model.calls)


def test_journals_start_and_flushes_previous_result_before_next_call(bundle, tmp_path):
    output, model = tmp_path / "execution", FakeModel()

    def before_call(ordinal):
        assert len(read_rows(output / "started.jsonl")) == ordinal + 1
        assert len(read_rows(output / "results.jsonl")) == ordinal
        assert read(output / "summary.json")["unknown_outcome"] == 1

    model.before_call = before_call
    execute_bundle(bundle, output, budget_usd=1, model=model)


def test_invalid_answer_preserves_usage_and_does_not_stop_other_cases(bundle, tmp_path):
    output, model = tmp_path / "execution", FakeModel(["malformed", ABSTENTION])
    summary = execute_bundle(bundle, output, budget_usd=1, model=model)
    assert summary["failed"] == summary["completed"] == 1
    assert summary["not_run"] == 0
    assert summary["tokens"]["total_tokens"] == 240
    assert summary["citation_identity"]["invalid"] == 1
    first = read_rows(output / "results.jsonl")[0]["result"]
    assert first["provider"]["usage"]["input_tokens"] == 100
    assert first["raw_output"] == "malformed"
    assert first["answer"] is None


def test_provider_error_stops_without_retry_and_usage_remains_unknown(bundle, tmp_path):
    model = FakeModel([ModelProviderError("Offline failure"), ANSWER])
    output = tmp_path / "execution"
    summary = execute_bundle(bundle, output, budget_usd=1, model=model)
    assert len(model.calls) == 1
    assert summary["failed"] == summary["not_run"] == 1
    assert summary["completed"] == summary["unknown_outcome"] == 0
    assert summary["stopped_after_provider_error"] is True
    assert summary["status"] == "failed"
    assert summary["tokens"]["input_tokens"] is None
    assert summary["cost_usd_at_frozen_uncached_rates"] is None
    assert summary["calls_missing_token_counts"]["input_tokens"] == 1
    with pytest.raises(FileExistsError):
        execute_bundle(bundle, output, budget_usd=1, model=model)
    assert len(model.calls) == 1


def test_partial_known_usage_is_not_a_false_total_after_later_failure(bundle, tmp_path):
    summary = execute_bundle(
        bundle,
        tmp_path / "execution",
        budget_usd=1,
        model=FakeModel([ANSWER, ModelProviderError("Offline failure")]),
    )
    assert summary["completed"] == summary["failed"] == 1
    assert summary["tokens"]["input_tokens"] is None
    assert summary["observed_token_subtotals"]["input_tokens"] == 100
    assert summary["cost_usd_at_frozen_uncached_rates"] is None


@pytest.mark.parametrize("error", [KeyboardInterrupt(), RuntimeError("Unexpected local failure")])
def test_interrupted_inflight_request_has_unknown_outcome_not_not_run(bundle, tmp_path, error):
    model, output = FakeModel([error]), tmp_path / "execution"
    with pytest.raises(type(error)):
        execute_bundle(bundle, output, budget_usd=1, model=model)
    summary = read(output / "summary.json")
    assert summary["attempted"] == summary["unknown_outcome"] == summary["not_run"] == 1
    assert summary["completed"] == summary["failed"] == 0
    assert summary["interrupted"] is True
    assert summary["status"] == "interrupted"
    assert summary["cost_usd_at_frozen_uncached_rates"] is None
    assert read_rows(output / "results.jsonl") == []
    assert len(read_rows(output / "started.jsonl")) == 1
    with pytest.raises(FileExistsError):
        execute_bundle(bundle, output, budget_usd=1, model=model)
    assert len(model.calls) == 1


@pytest.mark.parametrize("budget", [True, None, 0, -1, float("nan"), float("inf"), 0.000001])
def test_invalid_or_insufficient_budget_never_constructs_live_adapter(
    bundle, tmp_path, monkeypatch, budget
):
    adapter = Mock(side_effect=AssertionError("Must not construct provider before budget check"))
    monkeypatch.setattr(execution, "OpenAIModel", adapter)
    output = tmp_path / "execution"
    with pytest.raises(ValueError):
        execute_bundle(bundle, output, budget_usd=budget)
    adapter.assert_not_called()
    assert not output.exists()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda plan, cases, rows: plan.update(model=""),
        lambda plan, cases, rows: plan.update(max_output_tokens=True),
        lambda plan, cases, rows: plan.update(estimated_cost_usd=0),
        lambda plan, cases, rows: plan["pricing"].update(input_per_million=-1),
        lambda plan, cases, rows: cases.update(annotation_status=None),
        lambda plan, cases, rows: cases["cases"][0].update(expected_status="unknown"),
        lambda plan, cases, rows: cases["cases"][0].update(source_targets=[None]),
        lambda plan, cases, rows: rows[0].update(repository="other-repository"),
        lambda plan, cases, rows: rows[0].update(case_id="unknown-case"),
        lambda plan, cases, rows: rows[0].update(id="wrong-id"),
        lambda plan, cases, rows: rows.append(deepcopy(rows[0])),
        lambda plan, cases, rows: rows.pop(),
        lambda plan, cases, rows: rows[0]["prepared"].update(question="different question"),
        lambda plan, cases, rows: rows[0]["prepared"].update(prompt_version="future-version"),
        lambda plan, cases, rows: rows[0]["prepared"]["messages"][0].update(
            content="changed system"
        ),
        lambda plan, cases, rows: rows[0]["prepared"].update(prompt_fingerprint="wrong-hash"),
        lambda plan, cases, rows: rows[0]["prepared"]["context"].update(
            context_fingerprint="wrong-hash"
        ),
        lambda plan, cases, rows: rows[0]["prepared"]["context"]["budget"].update(
            used_context_bytes=0
        ),
        lambda plan, cases, rows: rows[0]["prepared"]["timing_ms"].update(retrieval=-1),
    ],
)
def test_rehashed_invalid_bundle_is_rejected_before_calls(bundle, tmp_path, mutate):
    update_bundle(bundle, mutate=mutate)
    model, output = FakeModel(), tmp_path / "execution"
    with pytest.raises(ValueError):
        execute_bundle(bundle, output, budget_usd=1, model=model)
    assert not output.exists()
    assert model.calls == []


@pytest.mark.parametrize(
    "field", ["plan_fingerprint", "cases_digest", "request_digest", "request_count"]
)
def test_raw_digest_or_count_corruption_is_rejected(bundle, tmp_path, field):
    plan = read(bundle / "plan.json")
    plan[field] = 3 if field == "request_count" else "corrupted"
    write(bundle / "plan.json", plan)
    with pytest.raises(ValueError):
        execute_bundle(bundle, tmp_path / "execution", budget_usd=1, model=FakeModel())


def test_missing_usage_is_unknown_even_when_answer_valid(bundle, tmp_path):
    response = ModelResponse(ANSWER, "offline-model", {}, "req", "completed")
    summary = execute_bundle(
        bundle,
        tmp_path / "execution",
        budget_usd=1,
        model=FakeModel([response, replace(response, text=ABSTENTION)]),
    )
    assert summary["completed"] == 2
    assert all(value is None for value in summary["tokens"].values())
    assert summary["cost_usd_at_frozen_uncached_rates"] is None


def test_existing_directory_is_never_reused(bundle, tmp_path):
    output, model = tmp_path / "execution", FakeModel()
    output.mkdir()
    (output / "keep.txt").write_text("Existing data", encoding="utf-8")
    with pytest.raises(FileExistsError):
        execute_bundle(bundle, output, budget_usd=1, model=model)
    assert (output / "keep.txt").read_text(encoding="utf-8") == "Existing data"
    assert model.calls == []


def test_zero_calls_have_true_zero_cost_and_do_not_require_credentials(
    bundle, tmp_path, monkeypatch
):
    from structure_aware_retrieval.qa.context import pack_context

    rows = read_rows(bundle / "requests.jsonl")
    index = load_index(tmp_path / "index.sqlite")
    context = pack_context(index, [], max_context_bytes=2)

    def clear_context(plan, _cases, rows):
        for row in rows:
            prepared = row["prepared"]
            prepared["context"] = context
            prepared["messages"][1]["content"] = json.dumps(
                {"question": prepared["question"], "evidence": []}
            )
            prepared["prompt_fingerprint"] = stable_id(prepared["messages"])
        plan["estimated_cost_usd"] = 0

    update_bundle(bundle, mutate=clear_context)
    model = FakeModel([AssertionError("Empty contexts must not call the provider")])
    summary = execute_bundle(bundle, tmp_path / "execution", budget_usd=1, model=model)
    assert model.calls == []
    assert summary["model_calls_attempted"] == 0
    assert summary["completed"] == len(rows)
    assert summary["cost_usd_at_frozen_uncached_rates"] == 0
    assert summary["tokens"]["input_tokens"] == 0
    assert summary["local_abstentions"] == 2
    assert summary["model_abstentions"] == 0


def test_per_strategy_cost_keeps_unknown_failure_separate_from_completed_strategy(bundle, tmp_path):
    def add_strategy(plan, _cases, rows):
        additions = deepcopy(rows)
        for row in additions:
            row["strategy"] = "symbol"
            row["id"] = stable_id("symbol", row["case_id"])
        rows.extend(additions)
        plan["estimated_cost_usd"] *= 2

    update_bundle(bundle, mutate=add_strategy)
    model = FakeModel([ANSWER, ABSTENTION, ANSWER, ModelProviderError("Offline failure")])
    summary = execute_bundle(bundle, tmp_path / "execution", budget_usd=1, model=model)
    first, second = summary["per_strategy"]["bm25"], summary["per_strategy"]["symbol"]
    assert first["tokens"]["input_tokens"] == 200
    assert first["cost_usd_at_frozen_uncached_rates"] is not None
    assert second["tokens"]["input_tokens"] is None
    assert second["cost_usd_at_frozen_uncached_rates"] is None
    assert second["observed_token_subtotals"]["input_tokens"] == 100
    assert first["requested"] == second["requested"] == 2


@pytest.mark.parametrize(
    "field", ["content_fingerprint", "maximum_api_calls", "top_k", "strategies"]
)
def test_plan_metadata_must_match_prepared_requests(bundle, tmp_path, field):
    def corrupt(plan, _cases, _rows):
        plan[field] = {} if field == "strategies" else 0

    update_bundle(bundle, mutate=corrupt)
    # Refresh helper intentionally recomputes the prompt fingerprint; override that field again.
    if field == "content_fingerprint":
        plan = read(bundle / "plan.json")
        plan[field] = stable_id("wrong-content")
        plan["plan_fingerprint"] = stable_id(
            {key: value for key, value in plan.items() if key != "plan_fingerprint"}
        )
        write(bundle / "plan.json", plan)
    model = FakeModel()
    with pytest.raises(ValueError):
        execute_bundle(bundle, tmp_path / "execution", budget_usd=1, model=model)
    assert model.calls == []


def test_prompt_evidence_tampering_is_rejected_even_when_outer_hashes_are_refreshed(
    bundle, tmp_path
):
    def corrupt(_plan, _cases, rows):
        context = rows[0]["prepared"]["context"]
        context["evidence"][0]["text"] = "private changed source\n"
        context["context_fingerprint"] = stable_id(
            context["schema_version"],
            context["snapshot_id"],
            context["config"],
            context["evidence"],
        )

    update_bundle(bundle, mutate=corrupt)
    model = FakeModel()
    with pytest.raises(ValueError, match="text, line ranges, or hash"):
        execute_bundle(bundle, tmp_path / "execution", budget_usd=1, model=model)
    assert model.calls == []


def test_failure_saving_markdown_keeps_paid_result_and_refuses_reexecution(
    bundle, tmp_path, monkeypatch
):
    output, model = tmp_path / "execution", FakeModel()
    original = Path.write_text

    def fail_markdown(path, *args, **kwargs):
        if path.suffix == ".md":
            raise OSError("Simulated output failure")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_markdown)
    with pytest.raises(OSError, match="output failure"):
        execute_bundle(bundle, output, budget_usd=1, model=model)
    assert len(read_rows(output / "results.jsonl")) == 1
    summary = read(output / "summary.json")
    assert summary["completed"] == 1
    assert summary["unknown_outcome"] == 0
    assert summary["not_run"] == 1
    assert summary["status"] == "interrupted"
    with pytest.raises(FileExistsError):
        execute_bundle(bundle, output, budget_usd=1, model=model)
    assert len(model.calls) == 1
