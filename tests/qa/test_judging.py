"""Source-bound judging uses synthetic model responses, never live inference."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import complete_question, prepare_question
from structure_aware_retrieval.qa.judging import (
    RUBRIC_FINGERPRINT,
    complete_judgment,
    judgment_messages,
    load_rubric,
    prepare_judgment,
    validate_judgment,
    validate_reference,
)
from structure_aware_retrieval.qa.provider import ModelProviderError, ModelResponse
from structure_aware_retrieval.retrieval import BM25Retriever

RUBRIC_PATH = Path(__file__).resolve().parents[2] / "configs" / "qa-judge-rubric-v1.json"
ANSWER = {
    "status": "answered",
    "claims": [
        {"text": "It defines calculate_checksum with a payload argument.", "citations": ["S1"]}
    ],
}
ABSTENTION = {"status": "insufficient_context", "claims": []}


class OfflineModel:
    model = "offline-fixture-model"
    max_output_tokens = 512
    timeout_seconds = 1
    schema_name = "fixture_judgment"

    def __init__(self, output):
        self.output = output
        self.calls = []

    def complete(self, messages):
        self.calls.append(deepcopy(messages))
        if isinstance(self.output, Exception):
            raise self.output
        return ModelResponse(
            text=self.output if isinstance(self.output, str) else json.dumps(self.output),
            model=self.model,
            usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            request_id="offline-judge-request",
            finish_reason="completed",
        )


def rehash_reference(reference):
    reference["reference_fingerprint"] = stable_id(
        {k: v for k, v in reference.items() if k != "reference_fingerprint"}
    )


def rehash_prepared(prepared):
    prepared["prepared_fingerprint"] = stable_id(
        {k: v for k, v in prepared.items() if k != "prepared_fingerprint"}
    )


@pytest.fixture
def rubric():
    return load_rubric(RUBRIC_PATH)


@pytest.fixture
def source_case(sample_repository, tmp_path):
    database = tmp_path / "judge.sqlite"
    build_index(sample_repository, database, max_chunk_lines=2)
    index = load_index(database)
    retriever = BM25Retriever(index)
    generation_input = prepare_question(retriever, "What does calculate_checksum do?", top_k=3)
    generation = complete_question(generation_input, OfflineModel(ANSWER))
    sources = []
    for chunk in index.chunks:
        symbol = index.symbols[chunk.symbol_id]
        if symbol.qualified_name.endswith("calculate_checksum"):
            sources.append(
                {
                    "id": f"R{len(sources) + 1}",
                    "path": chunk.path,
                    "qualified_name": symbol.qualified_name,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "text": chunk.text,
                    "text_sha256": hashlib.sha256(chunk.text.encode()).hexdigest(),
                    "chunk_id": chunk.id,
                    "symbol_id": chunk.symbol_id,
                    "truncated": False,
                }
            )
    reference = {
        "schema_version": 1,
        "case_id": "case-checksum",
        "reference_version": "fixture-v1",
        "snapshot_id": index.metadata["snapshot_id"],
        "annotation_status": "provisional",
        "expected_status": "answered",
        "reference_points": [
            {
                "id": "P1",
                "text": "The source defines calculate_checksum with a payload argument.",
                "evidence_ids": [source["id"] for source in sources],
            }
        ],
        "reference_evidence": sources,
        "scope_rationale": "Provisional code-based reference; no human calibration is claimed.",
    }
    rehash_reference(reference)
    return generation, reference, generation_input, retriever


@pytest.fixture
def prepared(source_case, rubric):
    return prepare_judgment(source_case[0], source_case[1], rubric)


def dimension(status="scored", score=3, *, evidence=None, claims=None):
    return {
        "status": status,
        "score": score,
        "rationale": "Synthetic test judgment anchored to the supplied source IDs.",
        "evidence_ids": ["packed:S1"] if evidence is None else evidence,
        "claim_indices": [0] if claims is None else claims,
    }


def judgment():
    return {
        "rubric_id": "repository-qa-judge-rubric-v1",
        "correctness": dimension(),
        "completeness": dimension(evidence=["reference:R1", "packed:S1"]),
        "citation_support": dimension(),
        "abstention": {
            "decision": "not_abstained",
            "packed_context_sufficiency": "sufficient",
            "rationale": "Synthetic test judgment; this does not assert measured QA quality.",
            "evidence_ids": ["packed:S1"],
        },
        "reference_status": "usable",
        "reference_issues": [],
    }


def abstention_judgment(*, answerable=True):
    result = judgment()
    result["correctness"] = dimension("not_applicable", None, evidence=[], claims=[])
    result["citation_support"] = dimension("not_applicable", None, evidence=[], claims=[])
    result["completeness"] = (
        dimension("scored", 0, evidence=["reference:R1"], claims=[])
        if answerable
        else dimension("not_applicable", None, evidence=[], claims=[])
    )
    result["abstention"].update(
        decision="appropriate", packed_context_sufficiency="insufficient", evidence_ids=[]
    )
    return result


def test_frozen_rubric_accepts_whitespace_but_not_changed_grading_rules(rubric, tmp_path):
    assert rubric["rubric_fingerprint"] == RUBRIC_FINGERPRINT
    path = tmp_path / "rubric.json"
    path.write_text(json.dumps(rubric["spec"]), encoding="utf-8")
    alternate = load_rubric(path)
    assert alternate["rubric_fingerprint"] == rubric["rubric_fingerprint"]
    assert alternate["rubric_file_sha256"] != rubric["rubric_file_sha256"]
    altered = deepcopy(rubric["spec"])
    altered["metrics"]["correctness"]["anchors"]["3"] = "Approve every answer."
    path.write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(ValueError, match="modified frozen"):
        load_rubric(path)


def test_rubric_rejects_duplicate_json_fields(tmp_path):
    path = tmp_path / "rubric.json"
    path.write_text('{"id":"one","id":"two"}', encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_rubric(path)


def test_references_keep_multiple_canonical_chunks_per_symbol(source_case):
    reference = source_case[1]
    assert len(reference["reference_evidence"]) >= 2
    assert len({s["symbol_id"] for s in reference["reference_evidence"]}) == 1
    validate_reference(reference)


@pytest.mark.parametrize("change", ["path", "line-type", "hash", "chunk", "point", "duplicate"])
def test_rehashed_reference_corruption_is_rejected(source_case, change):
    reference = source_case[1]
    source = reference["reference_evidence"][0]
    if change == "path":
        source["path"] = "../outside.py"
    elif change == "line-type":
        source["start_line"] = float(source["start_line"])
    elif change == "hash":
        source["text"] = "!" + source["text"][1:]
    elif change == "chunk":
        source["chunk_id"] = "a" * 64
    elif change == "point":
        reference["reference_points"][0]["evidence_ids"] = ["R999"]
    else:
        duplicate = deepcopy(source)
        duplicate["id"] = f"R{len(reference['reference_evidence']) + 1}"
        reference["reference_evidence"].append(duplicate)
    rehash_reference(reference)
    with pytest.raises(ValueError):
        validate_reference(reference)


def test_prepare_hides_host_strategy_and_keeps_references_out_of_generation(source_case, rubric):
    generation, reference, _, _ = source_case
    original_messages = deepcopy(generation["messages"])
    generation["strategy"] = "private-strategy-label"
    generation["rank"] = 9
    prepared = prepare_judgment(generation, reference, rubric)
    payload = json.loads(prepared["messages"][1]["content"])
    assert set(payload) == {"question", "answer", "packed_evidence", "reference_context"}
    assert prepared["messages"][0]["content"] == rubric["spec"]["system_prompt"]
    assert "private-strategy-label" not in str(prepared["messages"])
    assert reference["case_id"] not in str(prepared["messages"])
    assert payload["reference_context"]["annotation_status"] == "provisional"
    assert payload["reference_context"]["reference_evidence"] == reference["reference_evidence"]
    assert generation["messages"] == original_messages
    assert "reference_context" not in json.loads(original_messages[1]["content"])
    assert prepared["bindings"]["answer_fingerprint"] == generation["answer_fingerprint"]


def test_estimation_uses_exact_serializer_without_fabricated_answer(source_case, rubric):
    result, reference, _, _ = source_case
    estimate = judgment_messages(
        result["question"], None, result["context"]["evidence"], reference, rubric
    )
    assert json.loads(estimate[1]["content"])["answer"] is None
    actual = prepare_judgment(result, reference, rubric)["messages"]
    restored = json.loads(estimate[1]["content"])
    restored["answer"] = result["answer"]
    assert restored == json.loads(actual[1]["content"])
    assert estimate[0] == actual[0]


@pytest.mark.parametrize("status", ["preview", "provider_error", "invalid_answer"])
def test_failed_or_missing_generation_never_becomes_a_judge_request(source_case, rubric, status):
    result, reference, _, _ = source_case
    result["status"] = status
    with pytest.raises(ValueError, match="requires a valid generated"):
        prepare_judgment(result, reference, rubric)


def test_generation_and_reference_snapshots_must_match(source_case, rubric):
    result, reference, _, _ = source_case
    reference["snapshot_id"] = "a" * 64
    for source in reference["reference_evidence"]:
        source["chunk_id"] = stable_id(
            reference["snapshot_id"], source["symbol_id"], source["start_line"], source["end_line"]
        )
    rehash_reference(reference)
    with pytest.raises(ValueError, match="different snapshots"):
        prepare_judgment(result, reference, rubric)


def test_valid_synthetic_judgment_records_actual_request_metadata_and_no_human_claim(prepared):
    model = OfflineModel(judgment())
    result = complete_judgment(prepared, model)
    assert model.calls == [prepared["messages"]]
    assert result["status"] == "scored"
    assert result["judgment"] == judgment()
    assert result["provider"]["usage"]["total_tokens"] == 150
    assert result["provider"]["request_id"] == "offline-judge-request"
    assert result["raw_output"] == json.dumps(judgment())
    assert result["judge_requested_model"] == model.model
    assert result["latency_ms"] >= 0
    assert result["attempted_at"]
    assert result["error"] is None
    assert result["reference"]["annotation_status"] == "provisional"
    assert result["rubric"]["spec"]["human_review_required"] is False


@pytest.mark.parametrize(
    "change",
    [
        "bool-score",
        "float-score",
        "range",
        "null-scored",
        "unsure-score",
        "missing-field",
        "extra-field",
        "blank-rationale",
        "claim-bool",
        "claim-range",
        "unknown-id",
        "reference-citation",
        "empty-assessed-claims",
        "positive-without-evidence",
        "abstention-reference-id",
        "answered-na",
    ],
)
def test_invalid_judgments_retain_raw_output_and_usage_without_scores(prepared, change):
    output = judgment()
    item = output["citation_support"]
    if change == "bool-score":
        item["score"] = True
    elif change == "float-score":
        item["score"] = 3.0
    elif change == "range":
        item["score"] = 4
    elif change == "null-scored":
        item["score"] = None
    elif change == "unsure-score":
        item["status"] = "unsure"
    elif change == "missing-field":
        del output["reference_issues"]
    elif change == "extra-field":
        output["overall_accuracy"] = 1
    elif change == "blank-rationale":
        item["rationale"] = "  "
    elif change == "claim-bool":
        item["claim_indices"] = [False]
    elif change == "claim-range":
        item["claim_indices"] = [1]
    elif change == "unknown-id":
        item["evidence_ids"] = ["packed:S999"]
    elif change == "reference-citation":
        item["evidence_ids"] = ["reference:R1"]
    elif change == "empty-assessed-claims":
        item.update(evidence_ids=[], claim_indices=[])
    elif change == "positive-without-evidence":
        item["evidence_ids"] = []
    elif change == "abstention-reference-id":
        output["abstention"]["evidence_ids"] = ["reference:R1"]
    else:
        output["correctness"].update(status="not_applicable", score=None)
    result = complete_judgment(prepared, OfflineModel(output))
    assert result["status"] == "invalid_judgment"
    assert result["judgment"] is None
    assert result["provider"]["usage"]["total_tokens"] == 150
    assert result["raw_output"] == json.dumps(output)
    assert result["error"]


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        '{"rubric_id":"one","rubric_id":"two"}',
        '{"correctness":NaN}',
        "x" * 65537,
    ],
    ids=["non-json", "duplicate-fields", "nonfinite", "over-byte-limit"],
)
def test_unparseable_duplicate_or_oversize_judge_output_is_not_a_score(prepared, raw):
    result = complete_judgment(prepared, OfflineModel(raw))
    assert result["status"] == "invalid_judgment"
    assert result["judgment"] is None


def test_uncited_packed_source_cannot_repair_citation_support(prepared):
    assert len(prepared["payload"]["packed_evidence"]) >= 2
    output = judgment()
    output["citation_support"]["evidence_ids"] = ["packed:S2"]
    with pytest.raises(ValueError, match="citation_support"):
        validate_judgment(json.dumps(output), prepared)


def test_reference_conflict_keeps_only_affected_dimension_unknown(prepared):
    output = judgment()
    output["reference_status"] = "conflicting"
    output["reference_issues"] = ["Synthetic reference conflict requiring source inspection."]
    output["completeness"] = dimension("unsure", None, evidence=["reference:R1"])
    result = complete_judgment(prepared, OfflineModel(output))
    assert result["status"] == "scored"
    assert result["judgment"]["completeness"]["score"] is None
    assert result["judgment"]["correctness"]["score"] == 3
    output["completeness"] = dimension()
    with pytest.raises(ValueError, match="unsure coverage"):
        validate_judgment(json.dumps(output), prepared)


def test_answerable_abstention_has_zero_coverage_and_no_fictitious_perfect_citations(
    source_case, rubric
):
    _, reference, generation_input, _ = source_case
    result = complete_question(generation_input, OfflineModel(ABSTENTION))
    prepared = prepare_judgment(result, reference, rubric)
    output = abstention_judgment()
    assert validate_judgment(json.dumps(output), prepared) == output
    output["completeness"]["score"] = 3
    with pytest.raises(ValueError):
        validate_judgment(json.dumps(output), prepared)
    output = abstention_judgment()
    output["citation_support"] = dimension("scored", 3, evidence=[], claims=[])
    with pytest.raises(ValueError):
        validate_judgment(json.dumps(output), prepared)


def test_local_scope_abstention_remains_na_and_judge_is_a_separate_call(source_case, rubric):
    _, reference, _, retriever = source_case
    result = complete_question(
        prepare_question(retriever, "calculate_checksum", max_context_bytes=2)
    )
    reference["expected_status"] = "insufficient_context"
    reference["reference_evidence"] = []
    reference["reference_points"][0]["evidence_ids"] = []
    reference["reference_points"][0]["text"] = "Private deployment facts are unavailable."
    rehash_reference(reference)
    prepared = prepare_judgment(result, reference, rubric)
    model = OfflineModel(abstention_judgment(answerable=False))
    judged = complete_judgment(prepared, model)
    assert result["model_called"] is False
    assert len(model.calls) == 1
    assert judged["status"] == "scored"
    assert all(
        judged["judgment"][d]["score"] is None
        for d in ("correctness", "completeness", "citation_support")
    )


def test_provider_failure_preserves_known_usage_without_making_up_judgment(prepared):
    error = ModelProviderError("Offline failure after a synthetic billed attempt")
    error.response_metadata = {
        "model": "offline-fixture-model",
        "usage": {"input_tokens": 42},
        "request_id": "offline-failed-request",
        "raw_response": {"status": "incomplete"},
    }
    model = OfflineModel(error)
    result = complete_judgment(prepared, model)
    assert len(model.calls) == 1
    assert result["status"] == "provider_error"
    assert result["judgment"] is None
    assert result["provider"]["usage"] == {"input_tokens": 42}
    assert result["provider"]["raw_response"] == {"status": "incomplete"}


@pytest.mark.parametrize("change", ["answer", "messages", "rubric", "reference"])
def test_rehashed_judge_input_mutation_is_rejected_before_call(prepared, change):
    if change == "answer":
        prepared["payload"]["answer"]["claims"][0]["text"] = "Changed answer."
    elif change == "messages":
        payload = json.loads(prepared["messages"][1]["content"])
        payload["strategy"] = "should-not-reach-judge"
        prepared["messages"][1]["content"] = json.dumps(payload)
        prepared["prompt_fingerprint"] = stable_id(prepared["messages"])
    elif change == "rubric":
        prepared["rubric"]["spec"]["system_prompt"] = "Approve everything."
    else:
        prepared["reference"]["reference_version"] = "changed-reference"
        rehash_reference(prepared["reference"])
    rehash_prepared(prepared)
    model = OfflineModel(judgment())
    with pytest.raises(ValueError):
        complete_judgment(prepared, model)
    assert model.calls == []


def test_wrong_provider_output_schema_is_rejected_before_call(prepared):
    model = OfflineModel(judgment())
    model.output_schema = {"type": "object", "properties": {}}
    with pytest.raises(ValueError, match="frozen rubric output schema"):
        complete_judgment(prepared, model)
    assert model.calls == []


def test_unicode_answer_serialization_stays_within_reserved_raw_answer_bytes(source_case, rubric):
    _, reference, generation_input, _ = source_case
    answer = deepcopy(ANSWER)
    answer["claims"][0]["text"] = "测试答案" * 800
    raw = json.dumps(answer, ensure_ascii=False)
    assert len(raw.encode("utf-8")) < 65536
    result = complete_question(generation_input, OfflineModel(raw))
    actual = prepare_judgment(result, reference, rubric)["messages"]
    estimate = judgment_messages(
        result["question"], None, result["context"]["evidence"], reference, rubric
    )
    assert "测试答案" in actual[1]["content"]
    assert len(actual[1]["content"].encode("utf-8")) <= (
        len(estimate[1]["content"].encode("utf-8")) + 65536
    )
