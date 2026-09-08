"""Frozen v2 contracts constrain syntax without claiming improved semantic judgments."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import complete_question, prepare_question
from structure_aware_retrieval.qa.judging import (
    RUBRIC_FINGERPRINT,
    RUBRIC_V2_FINGERPRINT,
    RUBRIC_V2_ID,
    _schema,
    complete_judgment,
    judgment_messages,
    judgment_schema,
    load_rubric,
    prepare_judgment,
    validate_judgment,
)
from structure_aware_retrieval.qa.provider import OpenAIModel
from tests.qa.test_judging import (
    ABSTENTION,
    ANSWER,
    OfflineModel,
    abstention_judgment,
    dimension,
    judgment,
    rehash_prepared,
    rehash_reference,
)
from tests.qa.test_judging import source_case as source_case  # noqa: F401

CONFIGS = Path(__file__).resolve().parents[2] / "configs"


@pytest.fixture(autouse=True)
def no_live_calls(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("V2 protocol tests must never call a live provider")

    monkeypatch.setattr(OpenAIModel, "complete", forbidden)


@pytest.fixture
def rubric():
    return load_rubric(CONFIGS / "qa-judge-rubric-v2.json")


@pytest.fixture
def prepared(source_case, rubric):
    return prepare_judgment(source_case[0], source_case[1], rubric)


def output_v2(*, abstained=False, answerable=True):
    output = abstention_judgment(answerable=answerable) if abstained else judgment()
    output["rubric_id"] = RUBRIC_V2_ID
    return output


def schema_nodes(schema):
    yield schema
    for child in schema.get("properties", {}).values():
        yield from schema_nodes(child)
    if "items" in schema:
        yield from schema_nodes(schema["items"])
    for branch in schema.get("anyOf", []):
        yield from schema_nodes(branch)


def test_frozen_v2_keeps_v1_anchors_and_policies_without_relabeling(rubric, tmp_path):
    old = load_rubric(CONFIGS / "qa-judge-rubric-v1.json")
    assert old["rubric_fingerprint"] == RUBRIC_FINGERPRINT
    assert rubric["rubric_fingerprint"] == RUBRIC_V2_FINGERPRINT
    for section in ("metrics", "policies", "aggregation", "semantic_validation_rules"):
        assert rubric["spec"][section] == old["spec"][section]
    assert rubric["rubric_version"] == 2
    assert rubric["spec"]["human_review_required"] is False
    path = tmp_path / "v2.json"
    path.write_text(json.dumps(rubric["spec"]), encoding="utf-8")
    assert load_rubric(path)["rubric_fingerprint"] == RUBRIC_V2_FINGERPRINT
    changed = deepcopy(rubric["spec"])
    changed["schema_specialization"]["version"] = 3
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="modified frozen"):
        load_rubric(path)


def test_v1_exact_messages_schema_and_fingerprints_remain_unchanged(source_case):
    generation, reference, _, _ = source_case
    old = load_rubric(CONFIGS / "qa-judge-rubric-v1.json")
    evidence = generation["context"]["evidence"]
    payload = {
        "question": generation["question"],
        "answer": generation["answer"],
        "packed_evidence": evidence,
        "reference_context": {
            key: reference[key]
            for key in (
                "annotation_status",
                "expected_status",
                "reference_points",
                "reference_evidence",
                "scope_rationale",
            )
        },
    }
    expected = [
        {"role": "system", "content": old["spec"]["system_prompt"]},
        {
            "role": "user",
            "content": json.dumps(
                payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ),
        },
    ]
    prepared = prepare_judgment(generation, reference, old)
    assert prepared["messages"] == expected
    assert prepared["prompt_fingerprint"] == stable_id(expected)
    encoded = json.dumps(expected, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert prepared["messages_sha256"] == hashlib.sha256(encoded.encode()).hexdigest()
    assert prepared["output_schema"] == old["spec"]["output_schema"]
    assert judgment_schema(None, [], reference, old) == old["spec"]["output_schema"]
    assert validate_judgment(json.dumps(judgment()), prepared) == judgment()


def test_catalog_changes_no_answer_source_or_reference_text(prepared, source_case):
    generation, reference, _, _ = source_case
    payload = prepared["payload"]
    assert payload["answer"] == generation["answer"]
    assert payload["packed_evidence"] == generation["context"]["evidence"]
    assert payload["reference_context"]["reference_evidence"] == reference["reference_evidence"]
    assert payload["reference_context"]["reference_points"] == reference["reference_points"]
    catalog = payload["response_contract"]
    assert catalog["packed_evidence_ids"] == [
        f"packed:{source['id']}" for source in payload["packed_evidence"]
    ]
    assert catalog["claims"] == [{"claim_index": 0, "citation_evidence_ids": ["packed:S1"]}]
    assert catalog["dimensions"]["citation_support"]["evidence_ids"] == ["packed:S1"]
    assert all("reference:P" not in item for item in catalog["reference_evidence_ids"])
    text = prepared["messages"][1]["content"]
    assert reference["case_id"] not in text
    assert "strategy" not in payload
    assert reference["reference_fingerprint"] not in text


def test_dynamic_schema_uses_supported_strict_subset(prepared):
    schema = prepared["output_schema"]
    assert schema["type"] == "object"
    assert "anyOf" not in schema
    for node in schema_nodes(schema):
        assert not (set(node) & {"allOf", "if", "then", "else", "uniqueItems"})
        if node.get("type") == "object":
            assert set(node["required"]) == set(node["properties"])
            assert node["additionalProperties"] is False
        if "enum" in node:
            assert node["enum"]
    output = output_v2()
    assert validate_judgment(json.dumps(output), prepared) == output
    model = OfflineModel(output)
    model.output_schema = deepcopy(schema)
    assert complete_judgment(prepared, model)["status"] == "scored"
    assert len(model.calls) == 1


@pytest.mark.parametrize("function", [judgment_messages, judgment_schema])
def test_v2_requires_exact_answer_for_offline_preparation(source_case, rubric, function):
    generation, reference, _, _ = source_case
    args = [None, generation["context"]["evidence"], reference, rubric]
    if function is judgment_messages:
        args.insert(0, generation["question"])
    with pytest.raises(ValueError, match="exact archived answer"):
        function(*args)


@pytest.mark.parametrize(
    ("dimension_name", "field", "value"),
    [
        ("correctness", "evidence_ids", ["S1"]),
        ("correctness", "evidence_ids", ["reference:P1"]),
        ("correctness", "evidence_ids", ["pack:S1"]),
        ("correctness", "evidence_ids", ["packed:R1"]),
        ("correctness", "score", True),
        ("correctness", "score", None),
        ("correctness", "claim_indices", [1]),
        ("correctness", "claim_indices", [False]),
        ("correctness", "claim_indices", []),
        ("correctness", "evidence_ids", []),
        ("correctness", "rationale", ""),
        ("citation_support", "evidence_ids", ["reference:R1"]),
        ("citation_support", "evidence_ids", ["packed:S2"]),
        ("abstention", "evidence_ids", ["reference:R1"]),
        ("abstention", "decision", "appropriate"),
    ],
)
def test_bad_states_are_rejected_by_provider_schema_before_host_checks(
    prepared, dimension_name, field, value
):
    output = output_v2()
    output[dimension_name][field] = value
    with pytest.raises(ValueError):
        _schema(output, prepared["output_schema"])
    model = OfflineModel(output)
    result = complete_judgment(prepared, model)
    assert result["status"] == "invalid_judgment"
    assert result["raw_output"] == json.dumps(output)
    assert result["provider"]["usage"]["total_tokens"] == 150
    assert result["judgment"] is None


@pytest.mark.parametrize("dimension_name", ["correctness", "completeness", "citation_support"])
def test_answered_unsure_and_zero_remain_available(prepared, dimension_name):
    output = output_v2()
    output[dimension_name] = dimension("unsure", None, evidence=[], claims=[])
    assert validate_judgment(json.dumps(output), prepared) == output
    output[dimension_name] = dimension("scored", 0, evidence=[])
    assert validate_judgment(json.dumps(output), prepared) == output
    output[dimension_name].update(status="not_applicable", score=None)
    with pytest.raises(ValueError):
        _schema(output, prepared["output_schema"])


def test_cross_claim_citation_binding_remains_host_checked(source_case, rubric):
    _, reference, generation_input, _ = source_case
    answer = deepcopy(ANSWER)
    answer["claims"].append({"text": "Second synthetic claim.", "citations": ["S2"]})
    generated = complete_question(generation_input, OfflineModel(answer))
    prepared = prepare_judgment(generated, reference, rubric)
    output = output_v2()
    output["citation_support"].update(evidence_ids=["packed:S2"], claim_indices=[0])
    _schema(output, prepared["output_schema"])
    with pytest.raises(ValueError, match="citation_support"):
        validate_judgment(json.dumps(output), prepared)


def test_duplicate_ids_remain_host_checked(prepared):
    output = output_v2()
    output["correctness"]["evidence_ids"] = ["packed:S1", "packed:S1"]
    _schema(output, prepared["output_schema"])
    with pytest.raises(ValueError, match="duplicate"):
        validate_judgment(json.dumps(output), prepared)


@pytest.mark.parametrize("answerable", [True, False])
def test_abstention_states_preserve_evidence_and_reference_coupling(
    source_case, rubric, answerable
):
    _, reference, generation_input, _ = source_case
    reference["expected_status"] = "answered" if answerable else "insufficient_context"
    rehash_reference(reference)
    generated = complete_question(generation_input, OfflineModel(ABSTENTION))
    prepared = prepare_judgment(generated, reference, rubric)
    output = output_v2(abstained=True, answerable=answerable)
    # A valid historical N/A rationale can still cite actual source IDs.
    output["correctness"]["evidence_ids"] = ["packed:S1"]
    assert validate_judgment(json.dumps(output), prepared) == output
    output["completeness"] = dimension("unsure", None, evidence=[], claims=[])
    _schema(output, prepared["output_schema"])
    with pytest.raises(ValueError, match="coverage|completeness"):
        validate_judgment(json.dumps(output), prepared)
    for reference_status in ("inadequate", "conflicting"):
        output["reference_status"] = reference_status
        output["reference_issues"] = ["Synthetic uncertainty about the provisional reference."]
        assert validate_judgment(json.dumps(output), prepared) == output
    output["reference_issues"] = []
    with pytest.raises(ValueError, match="require issues"):
        validate_judgment(json.dumps(output), prepared)
    catalog = prepared["payload"]["response_contract"]
    expected = (
        {"status": "scored", "scores": [0]}
        if answerable
        else {"status": "not_applicable", "scores": [None]}
    )
    assert catalog["reference_rules"]["usable"]["completeness"] == [expected]
    assert (
        "To report uncertain completeness for an abstention" in prepared["messages"][0]["content"]
    )


def test_empty_source_catalogs_use_empty_arrays_not_empty_enums(source_case, rubric):
    _, reference, _, retriever = source_case
    generated = complete_question(
        prepare_question(retriever, "calculate_checksum", max_context_bytes=2)
    )
    reference["expected_status"] = "insufficient_context"
    reference["reference_evidence"] = []
    reference["reference_points"][0]["evidence_ids"] = []
    rehash_reference(reference)
    prepared = prepare_judgment(generated, reference, rubric)
    output = output_v2(abstained=True, answerable=False)
    assert validate_judgment(json.dumps(output), prepared) == output
    for node in schema_nodes(prepared["output_schema"]):
        assert node.get("enum") != []
    output["abstention"].update(decision="unsure", packed_context_sufficiency="unsure")
    with pytest.raises(ValueError):
        _schema(output, prepared["output_schema"])


@pytest.mark.parametrize("change", ["schema", "response_contract"])
def test_rehashed_schema_or_catalog_tampering_is_rejected_before_call(prepared, change):
    changed = deepcopy(prepared)
    if change == "schema":
        changed["output_schema"]["properties"]["correctness"]["anyOf"][0]["properties"][
            "evidence_ids"
        ]["items"]["enum"].append("packed:INVENTED")
    else:
        changed["payload"]["response_contract"]["packed_evidence_ids"].append("packed:INVENTED")
        changed["messages"][1]["content"] = json.dumps(
            changed["payload"], sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        changed["prompt_fingerprint"] = stable_id(changed["messages"])
        serialized = json.dumps(
            changed["messages"], sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        changed["messages_sha256"] = hashlib.sha256(serialized.encode()).hexdigest()
    rehash_prepared(changed)
    model = OfflineModel(output_v2())
    with pytest.raises(ValueError, match="binding mismatch"):
        complete_judgment(changed, model)
    assert model.calls == []


def test_static_v2_template_cannot_replace_bound_provider_schema(prepared, rubric):
    model = OfflineModel(output_v2())
    model.output_schema = rubric["spec"]["output_schema"]
    with pytest.raises(ValueError, match="output schema"):
        complete_judgment(prepared, model)
    assert model.calls == []
