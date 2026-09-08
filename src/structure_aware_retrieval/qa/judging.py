"""Frozen, source-bound LLM judging; schema validation never establishes semantic truth."""

import hashlib
import io
import json
import re
import time
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    _audit_prepared,
    _object,
    validate_answer,
)
from structure_aware_retrieval.qa.citations import audit_evidence, validate_source_target
from structure_aware_retrieval.qa.judgment_schema import build_schema, response_contract
from structure_aware_retrieval.qa.provider import AnswerModel

RUBRIC_ID = "repository-qa-judge-rubric-v1"
RUBRIC_FINGERPRINT = "1d84225c419d8b73c481c0b5c2c399f75cef2f8108d9c44ac19bafce7eb57926"
RUBRIC_V2_ID = "repository-qa-judge-rubric-v2"
RUBRIC_V2_FINGERPRINT = "0d1c8d68507d00d6211c266a6bd5345b80acad0fe43e9f3b1f232e197cd2f6cb"
REGISTERED_RUBRICS = {
    RUBRIC_FINGERPRINT: (RUBRIC_ID, 1),
    RUBRIC_V2_FINGERPRINT: (RUBRIC_V2_ID, 2),
}
MAX_JUDGMENT_BYTES = 65536
DIMENSIONS = ("correctness", "completeness", "citation_support")
SOURCE_FIELDS = {
    "id",
    "path",
    "qualified_name",
    "start_line",
    "end_line",
    "text",
    "text_sha256",
    "chunk_id",
    "symbol_id",
    "truncated",
}
REFERENCE_FIELDS = {
    "schema_version",
    "case_id",
    "snapshot_id",
    "annotation_status",
    "expected_status",
    "reference_version",
    "reference_points",
    "reference_evidence",
    "scope_rationale",
    "reference_fingerprint",
}
RUBRIC_FIELDS = {
    "spec",
    "rubric_id",
    "rubric_version",
    "rubric_file_sha256",
    "rubric_fingerprint",
    "system_prompt_sha256",
    "output_schema_sha256",
}


def _json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _constant(_value: str):
    raise ValueError("Nonfinite JSON constants are not allowed")


def _parse(text: str) -> object:
    try:
        return json.loads(text, object_pairs_hook=_object, parse_constant=_constant)
    except (UnicodeError, TypeError, ValueError, RecursionError) as error:
        raise ValueError("Invalid JSON in judge input or output") from error


def _fields(value: object, expected: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"Invalid {label} fields")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank text")
    try:
        value.encode("utf-8")
    except UnicodeError as error:
        raise ValueError(f"{label} must be valid Unicode") from error
    return value


def _hash(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _validate_rubric(rubric: object) -> dict:
    rubric = _fields(rubric, RUBRIC_FIELDS, "loaded rubric")
    spec = rubric["spec"]
    fingerprint = stable_id(spec)
    registered = REGISTERED_RUBRICS.get(fingerprint)
    if (
        not isinstance(spec, dict)
        or registered is None
        or rubric["rubric_id"] != registered[0]
        or type(rubric["rubric_version"]) is not int
        or rubric["rubric_version"] != registered[1]
        or rubric["rubric_fingerprint"] != fingerprint
        or not _hash(rubric["rubric_file_sha256"])
        or rubric["system_prompt_sha256"] != _sha(spec["system_prompt"])
        or rubric["output_schema_sha256"] != _sha(_json(spec["output_schema"]))
    ):
        raise ValueError("Unsupported or modified frozen QA judge rubric")
    return spec


def load_rubric(path: Path) -> dict:
    """Load a registered frozen contract; whitespace may vary, grading rules may not."""
    raw = path.read_bytes()
    if len(raw) > 1_000_000:
        raise ValueError("QA judge rubric exceeds the size limit")
    try:
        spec = _parse(raw.decode("utf-8"))
    except UnicodeError as error:
        raise ValueError("QA judge rubric must be UTF-8") from error
    registered = REGISTERED_RUBRICS.get(stable_id(spec))
    if not isinstance(spec, dict) or registered is None:
        raise ValueError("Unsupported or modified frozen QA judge rubric")
    rubric = {
        "spec": spec,
        "rubric_id": registered[0],
        "rubric_version": registered[1],
        "rubric_file_sha256": hashlib.sha256(raw).hexdigest(),
        "rubric_fingerprint": stable_id(spec),
        "system_prompt_sha256": _sha(spec["system_prompt"]),
        "output_schema_sha256": _sha(_json(spec["output_schema"])),
    }
    _validate_rubric(rubric)
    return rubric


def validate_reference(reference: dict) -> None:
    """Validate canonical reference chunks without imposing packed-context dedup rules."""
    _fields(reference, REFERENCE_FIELDS, "reference")
    if (
        type(reference["schema_version"]) is not int
        or reference["schema_version"] != 1
        or not _hash(reference["snapshot_id"])
        or reference["annotation_status"] not in ("provisional", "human_reviewed")
        or reference["expected_status"] not in ("answered", "insufficient_context")
        or reference["reference_fingerprint"]
        != stable_id({k: v for k, v in reference.items() if k != "reference_fingerprint"})
    ):
        raise ValueError("Invalid reference version, status, snapshot or fingerprint")
    for field in ("case_id", "reference_version", "scope_rationale"):
        _text(reference[field], field)
    sources, points = reference["reference_evidence"], reference["reference_points"]
    if not isinstance(sources, list) or not isinstance(points, list) or not points:
        raise ValueError("Reference needs source and nonempty point lists")
    ids, chunks = set(), set()
    for ordinal, source in enumerate(sources, 1):
        _fields(source, SOURCE_FIELDS, "reference source")
        validate_source_target(source)
        _text(source["text"], "reference source text")
        if (
            source["id"] != f"R{ordinal}"
            or source["truncated"] is not False
            or not _hash(source["symbol_id"])
            or source["chunk_id"]
            != stable_id(
                reference["snapshot_id"],
                source["symbol_id"],
                source["start_line"],
                source["end_line"],
            )
            or source["chunk_id"] in chunks
            or source["text_sha256"] != _sha(source["text"])
            or len(io.StringIO(source["text"]).readlines())
            != source["end_line"] - source["start_line"] + 1
        ):
            raise ValueError("Reference source identity, text or canonical bounds are invalid")
        ids.add(source["id"])
        chunks.add(source["chunk_id"])
    for ordinal, point in enumerate(points, 1):
        _fields(point, {"id", "text", "evidence_ids"}, "reference point")
        _text(point["text"], "reference point text")
        if point["id"] != f"P{ordinal}":
            raise ValueError("Reference point IDs must be distinct and ordered")
        _ids(point["evidence_ids"], ids, "reference point")


def judgment_messages(
    question: str, answer: dict | None, evidence: list[dict], reference: dict, rubric: dict
) -> list[dict]:
    """Serialize exact messages; only v1 supports answer=None for offline estimation."""
    _text(question, "question")
    if len(question.encode("utf-8")) > 4000:
        raise ValueError("QA question exceeds 4000 bytes")
    spec = _validate_rubric(rubric)
    validate_reference(reference)
    audit_evidence(evidence)
    for source in evidence:
        _fields(source, SOURCE_FIELDS, "packed source")
    if answer is not None:
        validate_answer(_json(answer), evidence)
    elif rubric["rubric_version"] == 2:
        raise ValueError("Judge rubric v2 requires an exact archived answer")
    payload = {
        "question": question,
        "answer": answer,
        "packed_evidence": evidence,
        "reference_context": {
            field: reference[field]
            for field in (
                "annotation_status",
                "expected_status",
                "reference_points",
                "reference_evidence",
                "scope_rationale",
            )
        },
    }
    if rubric["rubric_version"] == 2:
        payload["response_contract"] = response_contract(answer, evidence, reference)
    return [
        {"role": "system", "content": spec["system_prompt"]},
        {"role": "user", "content": _json(payload)},
    ]


def judgment_schema(
    answer: dict | None, evidence: list[dict], reference: dict, rubric: dict
) -> dict:
    """Return the frozen v1 schema or the v2 schema bound to exact source and claim IDs."""
    spec = _validate_rubric(rubric)
    if rubric["rubric_version"] == 1:
        return deepcopy(spec["output_schema"])
    if answer is None:
        raise ValueError("Judge rubric v2 requires an exact archived answer")
    validate_reference(reference)
    audit_evidence(evidence)
    for source in evidence:
        _fields(source, SOURCE_FIELDS, "packed source")
    validate_answer(_json(answer), evidence)
    return build_schema(answer, evidence, reference, rubric["rubric_id"])


def _validated_generation(result: dict) -> None:
    if not isinstance(result, dict) or result.get("status") not in (
        "answered",
        "insufficient_context",
    ):
        raise ValueError("Judging requires a valid generated answer or local abstention")
    _audit_prepared(result)
    evidence = result["context"]["evidence"]
    answer = validate_answer(_json(result.get("answer")), evidence)
    provider, raw = result.get("provider"), result.get("raw_output")
    if answer["status"] != result["status"] or type(result.get("model_called")) is not bool:
        raise ValueError("Generation status does not match its answer")
    if result["model_called"]:
        if not evidence or not isinstance(provider, dict):
            raise ValueError("Generated answer needs provider metadata and source evidence")
        _text(provider.get("model"), "generation model")
        if stable_id(validate_answer(raw, evidence)) != stable_id(answer):
            raise ValueError("Generation answer differs from its raw response")
    elif (
        evidence
        or provider is not None
        or raw is not None
        or answer != {"status": "insufficient_context", "claims": []}
    ):
        raise ValueError("Uncalled generation must be an empty-context abstention")
    expected = stable_id(
        result["prompt_fingerprint"],
        result["status"],
        answer,
        raw,
        provider["model"] if provider else None,
    )
    if result.get("answer_fingerprint") != expected:
        raise ValueError("Generation answer fingerprint mismatch")


def prepare_judgment(result: dict, reference: dict, rubric: dict) -> dict:
    """Bind a completed generation to strategy-independent, provisional source references."""
    _validated_generation(result)
    validate_reference(reference)
    if reference["snapshot_id"] != result["context"]["snapshot_id"]:
        raise ValueError("Judge reference and generated answer use different snapshots")
    messages = judgment_messages(
        result["question"], result["answer"], result["context"]["evidence"], reference, rubric
    )
    prepared = {
        "schema_version": 1,
        "kind": "qa_judgment",
        "case_id": reference["case_id"],
        "snapshot_id": reference["snapshot_id"],
        "answer_status": result["status"],
        "messages": messages,
        "prompt_fingerprint": stable_id(messages),
        "messages_sha256": _sha(_json(messages)),
        "output_schema": judgment_schema(
            result["answer"], result["context"]["evidence"], reference, rubric
        ),
        "bindings": {
            "answer_fingerprint": result["answer_fingerprint"],
            "context_fingerprint": result["context"]["context_fingerprint"],
            "generation_prompt_fingerprint": result["prompt_fingerprint"],
            "reference_fingerprint": reference["reference_fingerprint"],
            "reference_version": reference["reference_version"],
            "question_sha256": _sha(result["question"]),
            "generation_reported_model": result["provider"]["model"]
            if result["provider"]
            else None,
        },
        "rubric": deepcopy(rubric),
        "reference": deepcopy(reference),
        "source_context": deepcopy(result["context"]),
        "generation_raw_output": result["raw_output"],
        "payload": _parse(messages[1]["content"]),
    }
    prepared["prepared_fingerprint"] = stable_id(prepared)
    return prepared


def _validate_prepared(prepared: dict) -> None:
    expected = {
        "schema_version",
        "kind",
        "case_id",
        "snapshot_id",
        "answer_status",
        "messages",
        "prompt_fingerprint",
        "messages_sha256",
        "output_schema",
        "bindings",
        "rubric",
        "reference",
        "source_context",
        "generation_raw_output",
        "payload",
        "prepared_fingerprint",
    }
    _fields(prepared, expected, "prepared judgment")
    if (
        type(prepared["schema_version"]) is not int
        or prepared["schema_version"] != 1
        or prepared["kind"] != "qa_judgment"
        or prepared["prepared_fingerprint"]
        != stable_id({k: v for k, v in prepared.items() if k != "prepared_fingerprint"})
    ):
        raise ValueError("Invalid prepared judgment version or fingerprint")
    _validate_rubric(prepared["rubric"])
    payload_fields = {"question", "answer", "packed_evidence", "reference_context"}
    if prepared["rubric"]["rubric_version"] == 2:
        payload_fields.add("response_contract")
    payload = _fields(
        prepared["payload"],
        payload_fields,
        "judge payload",
    )
    bindings = _fields(
        prepared["bindings"],
        {
            "answer_fingerprint",
            "context_fingerprint",
            "generation_prompt_fingerprint",
            "reference_fingerprint",
            "reference_version",
            "question_sha256",
            "generation_reported_model",
        },
        "judge bindings",
    )
    context = prepared["source_context"]
    if not isinstance(context, dict):
        raise ValueError("Invalid judge source context")
    generation_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {"question": payload["question"], "evidence": _parse(context.get("context_text"))},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        },
    ]
    generation = {
        "question": payload["question"],
        "context": context,
        "messages": generation_messages,
        "prompt_version": PROMPT_VERSION,
        "prompt_fingerprint": bindings["generation_prompt_fingerprint"],
        "status": prepared["answer_status"],
        "answer": payload["answer"],
        "model_called": bindings["generation_reported_model"] is not None,
        "provider": {"model": bindings["generation_reported_model"]}
        if bindings["generation_reported_model"] is not None
        else None,
        "raw_output": prepared["generation_raw_output"],
        "answer_fingerprint": bindings["answer_fingerprint"],
    }
    _validated_generation(generation)
    reference, rubric = prepared["reference"], prepared["rubric"]
    messages = judgment_messages(
        payload["question"], payload["answer"], payload["packed_evidence"], reference, rubric
    )
    if (
        prepared["case_id"] != reference["case_id"]
        or prepared["snapshot_id"] != reference["snapshot_id"]
        or prepared["snapshot_id"] != context["snapshot_id"]
        or bindings["context_fingerprint"] != context["context_fingerprint"]
        or bindings["reference_fingerprint"] != reference["reference_fingerprint"]
        or bindings["reference_version"] != reference["reference_version"]
        or bindings["question_sha256"] != _sha(payload["question"])
        or stable_id(payload["packed_evidence"]) != stable_id(context["evidence"])
        or stable_id(payload) != stable_id(_parse(messages[1]["content"]))
        or stable_id(prepared["output_schema"])
        != stable_id(
            judgment_schema(payload["answer"], payload["packed_evidence"], reference, rubric)
        )
        or prepared["messages_sha256"] != _sha(_json(messages))
        or prepared["prompt_fingerprint"] != stable_id(messages)
        or stable_id(prepared["messages"]) != stable_id(messages)
    ):
        raise ValueError("Judge messages, source evidence or provenance binding mismatch")


def _schema(value: object, schema: dict, path: str = "judgment") -> None:
    """The frozen schema uses only this small, explicit JSON Schema subset."""
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            try:
                _schema(value, branch, path)
            except ValueError:
                continue
            break
        else:
            raise ValueError(f"No allowed judgment state at {path}")
        if "type" not in schema:
            return
    types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
    checks = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": type(value) is int,
        "null": value is None,
    }
    if not any(checks[t] for t in types):
        raise ValueError(f"Invalid judgment type at {path}")
    if "enum" in schema and not any(stable_id(value) == stable_id(v) for v in schema["enum"]):
        raise ValueError(f"Invalid judgment value at {path}")
    if isinstance(value, dict):
        _fields(value, set(schema["required"]), path)
        for key, item in value.items():
            _schema(item, schema["properties"][key], f"{path}.{key}")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or (
            "maxItems" in schema and len(value) > schema["maxItems"]
        ):
            raise ValueError(f"Invalid judgment array length at {path}")
        for item in value:
            _schema(item, schema["items"], f"{path}[]")
    elif isinstance(value, str):
        _text(value, path)
        if len(value) < schema.get("minLength", 0):
            raise ValueError(f"Invalid judgment string length at {path}")
    elif type(value) is int and "minimum" in schema and value < schema["minimum"]:
        raise ValueError(f"Invalid judgment minimum at {path}")


def _ids(values: object, allowed: set[str], label: str) -> None:
    if (
        not isinstance(values, list)
        or any(not isinstance(value, str) or value not in allowed for value in values)
        or len(values) != len(set(values))
    ):
        raise ValueError(f"Unknown or duplicate evidence IDs in {label}")


def validate_judgment(text: str, prepared: dict) -> dict:
    """Check types, evidence bindings and rubric constraints, not whether scores are true."""
    _validate_prepared(prepared)
    if not isinstance(text, str):
        raise ValueError("Judgment must be JSON text")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError as error:
        raise ValueError("Judgment must be valid Unicode") from error
    if size > MAX_JUDGMENT_BYTES:
        raise ValueError("Judgment exceeds the output byte limit")
    judgment = _parse(text)
    _schema(judgment, prepared["output_schema"])
    payload = prepared["payload"]
    claims = payload["answer"]["claims"]
    packed = {f"packed:{source['id']}" for source in payload["packed_evidence"]}
    reference = {
        f"reference:{source['id']}" for source in payload["reference_context"]["reference_evidence"]
    }
    for dimension in DIMENSIONS:
        item = judgment[dimension]
        if (item["status"] == "scored") != (type(item["score"]) is int):
            raise ValueError("Scored judgments need integers; unsure/N/A need null")
        indices = item["claim_indices"]
        if len(indices) != len(set(indices)) or any(i >= len(claims) for i in indices):
            raise ValueError("Judgment claim indices are duplicate or out of bounds")
        _ids(item["evidence_ids"], packed | reference, dimension)
        if (
            item["status"] == "scored"
            and item["score"] > 0
            and (not item["evidence_ids"] or not indices)
        ):
            raise ValueError("Positive judgments require source IDs and assessed claims")
        if dimension == "citation_support":
            cited = {f"packed:{citation}" for i in indices for citation in claims[i]["citations"]}
            _ids(item["evidence_ids"], cited, dimension)
            if item["status"] == "scored" and not indices:
                raise ValueError("Citation scoring needs assessed claim indices")
    abstention = judgment["abstention"]
    _ids(abstention["evidence_ids"], packed, "packed-context sufficiency")
    ref_status = judgment["reference_status"]
    if ref_status != "usable":
        if not judgment["reference_issues"] or judgment["completeness"]["status"] != "unsure":
            raise ValueError("Inadequate/conflicting references require issues and unsure coverage")
    elif payload["reference_context"]["expected_status"] == "answered" and (
        not reference
        or any(not p["evidence_ids"] for p in payload["reference_context"]["reference_points"])
    ):
        raise ValueError("Usable answer references require source-linked reference points")
    if prepared["answer_status"] == "answered":
        if abstention["decision"] != "not_abstained" or any(
            judgment[dimension]["status"] == "not_applicable" for dimension in DIMENSIONS
        ):
            raise ValueError("Answered output cannot use abstention or N/A scores")
    else:
        if any(
            judgment[d]["status"] != "not_applicable" for d in ("correctness", "citation_support")
        ):
            raise ValueError("Abstention correctness and citation support must be N/A")
        expected_decision = {
            "sufficient": "unnecessary",
            "insufficient": "appropriate",
            "unsure": "unsure",
        }[abstention["packed_context_sufficiency"]]
        if abstention["decision"] != expected_decision:
            raise ValueError("Abstention decision conflicts with packed-context sufficiency")
        if not packed and abstention["packed_context_sufficiency"] != "insufficient":
            raise ValueError("Empty packed context cannot establish an answer")
        if ref_status == "usable":
            complete = judgment["completeness"]
            if payload["reference_context"]["expected_status"] == "answered":
                if complete["status"] != "scored" or complete["score"] != 0:
                    raise ValueError("Abstention on a source-established answer has zero coverage")
            elif complete["status"] != "not_applicable":
                raise ValueError("Out-of-scope abstention completeness must be N/A")
    return judgment


def complete_judgment(prepared: dict, model: AnswerModel) -> dict:
    """Perform exactly one already-authorized judge request, retaining unsuccessful attempts."""
    _validate_prepared(prepared)
    if hasattr(model, "output_schema") and stable_id(model.output_schema) != stable_id(
        prepared["output_schema"]
    ):
        raise ValueError("Judge model must use the frozen rubric output schema")
    started = time.perf_counter()
    result = {
        **deepcopy(prepared),
        "status": "provider_error",
        "judgment": None,
        "model_called": True,
        "provider": None,
        "raw_output": None,
        "error": None,
        "attempted_at": datetime.now(UTC).isoformat(),
        "judge_requested_model": getattr(model, "model", None),
        "judge_settings": {
            field: getattr(model, field)
            for field in ("max_output_tokens", "timeout_seconds", "schema_name", "reasoning_effort")
            if hasattr(model, field)
        },
    }
    try:
        response = model.complete(prepared["messages"])
    except ValueError as error:
        result["error"] = str(error)
        metadata = getattr(error, "response_metadata", None)
        if isinstance(metadata, dict):
            result["provider"] = deepcopy(metadata)
            result["raw_output"] = result["provider"].pop("text", None)
    else:
        result["provider"] = asdict(response)
        result["provider"].pop("text")
        result["raw_output"] = response.text
        try:
            result["judgment"] = validate_judgment(response.text, prepared)
        except ValueError as error:
            result["status"] = "invalid_judgment"
            result["error"] = str(error)
        else:
            result["status"] = "scored"
    result["latency_ms"] = (time.perf_counter() - started) * 1000
    result["judgment_fingerprint"] = stable_id(
        prepared["prepared_fingerprint"],
        result["status"],
        result["judgment"],
        result["raw_output"],
        result["provider"],
    )
    return result
