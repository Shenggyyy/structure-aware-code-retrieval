"""Freeze shared judge evidence, exact settings, and a combined offline cost estimate."""

import hashlib
import json
import math
import os
import platform
import shutil
import tempfile
import tomllib
from datetime import date
from pathlib import Path

from structure_aware_retrieval.indexing import load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.context import _validate_chunk
from structure_aware_retrieval.qa.execution import _load, _validated_bundle
from structure_aware_retrieval.qa.judging import (
    judgment_messages,
    load_rubric,
    validate_reference,
)
from structure_aware_retrieval.qa.provider import OpenAIModel

PLAN_VERSION = 1
FRAMING_TOKENS = 4096
# validate_answer bounds accepted raw JSON to 64 KiB. Compact answer serialization
# cannot exceed that bound; reserve it again as judge input, not as output tokens.
MAX_ANSWER_BYTES = 65536
BUNDLE_FILES = ("plan.json", "cases.json", "requests.jsonl")


def _json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def implementation_record() -> dict:
    package = Path(__file__).resolve().parent.parent
    paths = [package / "cli.py", *sorted((package / "qa").glob("*.py"))]
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "source_files_sha256": {
            path.relative_to(package).as_posix(): _hash_file(path) for path in paths
        },
    }


def estimate_input_tokens(payload: dict) -> int:
    """Count model-visible message bytes plus schema/settings and framing allowance.

    HTTP JSON escapes are transport encoding, not additional model input. Keeping
    this boundary explicit also bounds an inserted answer by its valid JSON bytes.
    """
    settings = {key: value for key, value in payload.items() if key != "input"}
    return (
        sum(len(message["content"].encode("utf-8")) for message in payload["input"])
        + len(_json(settings).encode("utf-8"))
        + FRAMING_TOKENS
    )


def _write(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def _fields(value: object, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"Invalid {label} fields")


def _settings(value: object) -> dict:
    _fields(
        value,
        {"model", "max_output_tokens", "api_key_env", "reasoning_effort", "pricing"},
        "model settings",
    )
    if value["reasoning_effort"] not in ("none", "low", "medium", "high", "xhigh"):
        raise ValueError("Set an explicit supported reasoning_effort")
    if type(value["max_output_tokens"]) is not int or not 1 <= value["max_output_tokens"] <= 16384:
        raise ValueError("max_output_tokens must be an integer in [1, 16384]")
    pricing = value["pricing"]
    _fields(pricing, {"input_per_million", "output_per_million", "as_of"}, "pricing")
    for field in ("input_per_million", "output_per_million"):
        rate = pricing[field]
        if type(rate) not in (int, float) or not math.isfinite(rate) or rate < 0:
            raise ValueError("Pricing must be finite and nonnegative")
    if not isinstance(pricing["as_of"], str):
        raise ValueError("Pricing as_of must be an ISO date")
    date.fromisoformat(pricing["as_of"])
    make_model(value)
    return value


def make_model(settings: dict, rubric: dict | None = None) -> OpenAIModel:
    return OpenAIModel(
        model=settings["model"],
        api_key_env=settings["api_key_env"],
        max_output_tokens=settings["max_output_tokens"],
        reasoning_effort=settings["reasoning_effort"],
        output_schema=rubric["spec"]["output_schema"] if rubric else None,
        schema_name="repository_judgment" if rubric else "repository_answer",
    )


def _reference_context(case: dict, index, version: str, annotation_status: str) -> dict:
    chunks = {}
    for target in case["source_targets"]:
        matches = [
            symbol
            for symbol in index.symbols.values()
            if all(
                getattr(symbol, field) == target[field]
                for field in ("path", "qualified_name", "start_line", "end_line")
            )
        ]
        if len(matches) != 1:
            raise ValueError("Reference target does not resolve to one canonical snapshot symbol")
        # Parents exclude nested definitions in this parser. Include descendant-owned
        # chunks within the target range to preserve their code as reference evidence.
        candidates = [
            chunk
            for chunk in index.chunks
            if chunk.path == target["path"]
            and target["start_line"] <= chunk.start_line <= chunk.end_line <= target["end_line"]
        ]
        if not candidates:
            raise ValueError("Reference target has no indexed source evidence")
        for chunk in candidates:
            symbol = index.symbols[chunk.symbol_id]
            _validate_chunk(chunk, symbol, index.metadata["snapshot_id"])
            chunks[chunk.id] = (chunk, symbol)
    evidence = []
    for chunk, symbol in sorted(
        chunks.values(), key=lambda pair: (pair[0].path, pair[0].start_line, pair[0].id)
    ):
        evidence.append(
            {
                "id": f"R{len(evidence) + 1}",
                "path": chunk.path,
                "qualified_name": symbol.qualified_name,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "text": chunk.text,
                "text_sha256": hashlib.sha256(chunk.text.encode("utf-8")).hexdigest(),
                "chunk_id": chunk.id,
                "symbol_id": chunk.symbol_id,
                "truncated": False,
            }
        )
    reference = {
        "schema_version": 1,
        "case_id": case["id"],
        "reference_version": version,
        "snapshot_id": index.metadata["snapshot_id"],
        "annotation_status": annotation_status,
        "expected_status": case["expected_status"],
        "reference_points": [
            {"id": f"P{i}", "text": point, "evidence_ids": [source["id"] for source in evidence]}
            for i, point in enumerate(case["reference_points"], 1)
        ],
        "reference_evidence": evidence,
        "scope_rationale": case["rationale"],
    }
    reference["reference_fingerprint"] = stable_id(reference)
    validate_reference(reference)
    return reference


def _estimate(
    rows: list[dict], references: dict, rubric: dict, generation: dict, judge: dict
) -> dict:
    adapters = {"generation": make_model(generation), "judging": make_model(judge, rubric)}
    inputs = {stage: [] for stage in adapters}
    for row in rows:
        prepared = row["prepared"]
        if prepared["context"]["evidence"]:
            payload = adapters["generation"].request_payload(prepared["messages"])
            inputs["generation"].append(estimate_input_tokens(payload))
        template = judgment_messages(
            prepared["question"],
            None,
            prepared["context"]["evidence"],
            references[row["case_id"]],
            rubric,
        )
        payload = adapters["judging"].request_payload(template)
        inputs["judging"].append(estimate_input_tokens(payload) + MAX_ANSWER_BYTES)
    result = {}
    for stage, settings in (("generation", generation), ("judging", judge)):
        count, input_tokens = len(inputs[stage]), sum(inputs[stage])
        output_tokens = count * settings["max_output_tokens"]
        pricing = settings["pricing"]
        result[stage] = {
            "maximum_api_calls": count,
            "estimated_input_tokens": input_tokens,
            "maximum_input_tokens_per_call": max(inputs[stage], default=0),
            "maximum_output_tokens": output_tokens,
            "estimated_cost_usd": (
                input_tokens * pricing["input_per_million"]
                + output_tokens * pricing["output_per_million"]
            )
            / 1_000_000,
        }
    result.update(
        {
            "combined_usd": sum(result[stage]["estimated_cost_usd"] for stage in adapters),
            "method": "one token per message/schema/settings UTF-8 byte plus allowances",
            "framing_allowance_tokens_per_call": FRAMING_TOKENS,
            "maximum_answer_bytes_reserved_per_judge_call": MAX_ANSWER_BYTES,
            "billing_guarantee": False,
            "includes_llm_judging": True,
        }
    )
    return result


def _request_settings(settings: dict, rubric: dict | None = None) -> dict:
    payload = make_model(settings, rubric).request_payload(
        [{"role": "user", "content": "settings"}]
    )
    return {key: value for key, value in payload.items() if key != "input"}


def prepare_assessment(bundle: Path, config: Path, output: Path) -> dict:
    """Prepare both stages offline; no credential access or model completion."""
    if output.exists() or output.is_symlink():
        raise FileExistsError("Assessment output exists; choose a new directory")
    with config.open("rb") as handle:
        settings = tomllib.load(handle)
    _fields(
        settings,
        {
            "schema_version",
            "rubric",
            "reference_version",
            "max_reference_bytes",
            "indexes",
            "generation",
            "judge",
        },
        "assessment config",
    )
    if type(settings["schema_version"]) is not int or settings["schema_version"] != PLAN_VERSION:
        raise ValueError("Unsupported assessment config version")
    if (
        not isinstance(settings["reference_version"], str)
        or not settings["reference_version"].strip()
        or type(settings["max_reference_bytes"]) is not int
        or not 1 <= settings["max_reference_bytes"] <= 65536
    ):
        raise ValueError("Invalid reference version or byte budget")
    generation, judge = _settings(settings["generation"]), _settings(settings["judge"])
    source_plan = _load(bundle / "plan.json")
    original, raw_cases, cases, rows, _ = _validated_bundle(
        bundle, max(source_plan["estimated_cost_usd"], 1e-12)
    )
    if any(
        generation[key] != original[key] for key in ("model", "max_output_tokens", "api_key_env")
    ):
        raise ValueError("Generation model/token/key settings differ from the prepared QA bundle")
    rubric_path = config.parent / settings["rubric"]
    rubric = load_rubric(rubric_path)
    _fields(
        settings["indexes"], {case["repository"] for case in cases.values()}, "reference indexes"
    )
    indexes = {name: load_index(config.parent / path) for name, path in settings["indexes"].items()}
    references = {}
    for case_id, case in cases.items():
        index = indexes[case["repository"]]
        snapshots = {
            row["prepared"]["context"]["snapshot_id"] for row in rows if row["case_id"] == case_id
        }
        if snapshots != {index.metadata["snapshot_id"]}:
            raise ValueError("Reference index does not match generation source snapshot")
        reference = _reference_context(
            case, index, settings["reference_version"], raw_cases["annotation_status"]
        )
        if len(_json(reference).encode("utf-8")) > settings["max_reference_bytes"]:
            raise ValueError("Reference context exceeds byte budget; do not silently truncate")
        references[case_id] = reference
    plan = {
        "schema_version": PLAN_VERSION,
        "kind": "qa_assessment_plan",
        "status": "prepared",
        "annotation_status": raw_cases["annotation_status"],
        "human_review_required": False,
        "generation": generation,
        "judge": judge,
        "request_settings": {
            "generation": _request_settings(generation),
            "judging": _request_settings(judge, rubric),
        },
        "omitted_request_parameters": ["temperature", "seed", "service_tier", "tools"],
        "generation_plan_fingerprint": original["plan_fingerprint"],
        "generation_content_fingerprint": original["content_fingerprint"],
        "generation_files_sha256": {name: _hash_file(bundle / name) for name in BUNDLE_FILES},
        "reference_version": settings["reference_version"],
        "max_reference_bytes": settings["max_reference_bytes"],
        "references_fingerprint": stable_id(references),
        "reference_index_sha256": {
            name: _hash_file(config.parent / path) for name, path in settings["indexes"].items()
        },
        "rubric_file_sha256": rubric["rubric_file_sha256"],
        "rubric_fingerprint": rubric["rubric_fingerprint"],
        "estimated_cost": _estimate(rows, references, rubric, generation, judge),
        "request_count": len(rows),
        "request_order": [
            row["id"] for row in sorted(rows, key=lambda row: (row["case_id"], row["strategy"]))
        ],
        "execution_policy": "one attempt per stage; stop on provider error; no retries or resume",
        "runtime": {
            "generation_preparation": original["runtime"],
            "assessment_preparation": implementation_record(),
        },
        "config_sha256": _hash_file(config),
    }
    plan["plan_fingerprint"] = stable_id(plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-assessment-", dir=output.parent) as temporary:
        folder = Path(temporary)
        (folder / "generation").mkdir()
        for name in BUNDLE_FILES:
            shutil.copyfile(bundle / name, folder / "generation" / name)
        shutil.copyfile(rubric_path, folder / "rubric.json")
        _write(folder / "references.json", references)
        _write(folder / "plan.json", plan)
        (folder / "README.md").write_text(render_plan(plan), encoding="utf-8")
        validate_assessment_bundle(folder)
        if output.exists() or output.is_symlink():
            raise FileExistsError("Assessment output was created concurrently")
        os.rename(folder, output)
    return plan


def validate_assessment_bundle(bundle: Path) -> tuple[dict, list[dict], dict, dict]:
    try:
        return _validate_assessment_bundle(bundle)
    except (KeyError, TypeError, AttributeError, RecursionError) as error:
        raise ValueError("Malformed assessment bundle fields") from error


def _validate_assessment_bundle(bundle: Path) -> tuple[dict, list[dict], dict, dict]:
    plan = _load(bundle / "plan.json")
    if (
        not isinstance(plan, dict)
        or type(plan.get("schema_version")) is not int
        or plan["schema_version"] != PLAN_VERSION
        or plan.get("kind") != "qa_assessment_plan"
        or plan.get("plan_fingerprint")
        != stable_id({key: value for key, value in plan.items() if key != "plan_fingerprint"})
    ):
        raise ValueError("Invalid assessment plan or fingerprint")
    generation, judge = _settings(plan["generation"]), _settings(plan["judge"])
    for name in BUNDLE_FILES:
        if _hash_file(bundle / "generation" / name) != plan["generation_files_sha256"].get(name):
            raise ValueError("Frozen generation bundle changed")
    source_plan = _load(bundle / "generation/plan.json")
    original, raw_cases, cases, rows, _ = _validated_bundle(
        bundle / "generation", max(source_plan["estimated_cost_usd"], 1e-12)
    )
    if (
        original["plan_fingerprint"] != plan["generation_plan_fingerprint"]
        or original["content_fingerprint"] != plan["generation_content_fingerprint"]
        or any(
            generation[key] != original[key]
            for key in ("model", "max_output_tokens", "api_key_env")
        )
        or plan["annotation_status"] != raw_cases["annotation_status"]
    ):
        raise ValueError("Assessment and generation plans disagree")
    rubric = load_rubric(bundle / "rubric.json")
    if any(plan[key] != rubric[key] for key in ("rubric_file_sha256", "rubric_fingerprint")):
        raise ValueError("Frozen judge rubric changed")
    references = _load(bundle / "references.json")
    if (
        not isinstance(references, dict)
        or set(references) != set(cases)
        or stable_id(references) != plan["references_fingerprint"]
    ):
        raise ValueError("Frozen reference context changed or has missing cases")
    for case_id, reference in references.items():
        validate_reference(reference)
        case = cases[case_id]
        if (
            reference["case_id"] != case_id
            or reference["reference_version"] != plan["reference_version"]
            or reference["annotation_status"] != raw_cases["annotation_status"]
            or reference["expected_status"] != case["expected_status"]
            or reference["scope_rationale"] != case["rationale"]
            or [point["text"] for point in reference["reference_points"]]
            != case["reference_points"]
            or len(_json(reference).encode("utf-8")) > plan["max_reference_bytes"]
            or {
                row["prepared"]["context"]["snapshot_id"]
                for row in rows
                if row["case_id"] == case_id
            }
            != {reference["snapshot_id"]}
        ):
            raise ValueError("Reference context differs from its frozen case/snapshot")
        for source in reference["reference_evidence"]:
            if not any(
                source["path"] == target["path"]
                and target["start_line"]
                <= source["start_line"]
                <= source["end_line"]
                <= target["end_line"]
                for target in case["source_targets"]
            ):
                raise ValueError("Reference evidence lies outside the frozen source targets")
    if stable_id(plan["estimated_cost"]) != stable_id(
        _estimate(rows, references, rubric, generation, judge)
    ) or stable_id(plan["request_settings"]) != stable_id(
        {"generation": _request_settings(generation), "judging": _request_settings(judge, rubric)}
    ):
        raise ValueError("Combined estimate or request settings do not match frozen inputs")
    ordered = sorted(rows, key=lambda row: (row["case_id"], row["strategy"]))
    if (
        type(plan["request_count"]) is not int
        or plan["request_count"] != len(rows)
        or plan["request_order"] != [row["id"] for row in ordered]
    ):
        raise ValueError("Assessment request count/order changed")
    return plan, ordered, references, rubric


def render_plan(plan: dict) -> str:
    estimate = plan["estimated_cost"]
    return (
        "# Prepared QA and LLM Assessment\n\nNo API calls made; no live answers or scores.\n\n"
        "| Stage | Proposed model | Maximum calls | Estimated USD |\n| --- | --- | ---: | ---: |\n"
        f"| Generation | {plan['generation']['model']} | "
        f"{estimate['generation']['maximum_api_calls']} | "
        f"{estimate['generation']['estimated_cost_usd']:.6f} |\n"
        f"| LLM judging | {plan['judge']['model']} | "
        f"{estimate['judging']['maximum_api_calls']} | "
        f"{estimate['judging']['estimated_cost_usd']:.6f} |\n\n"
        f"**Combined estimate: ${estimate['combined_usd']:.6f} USD.** Not a billing hard cap.\n\n"
        "This conservative byte-based estimate reserves the full 65,536-byte valid-answer ceiling "
        "as additional judge input, plus schema/framing and both maximum output budgets. "
        "It can greatly exceed typical token usage. Rates are frozen uncached rates, "
        "not an invoice.\n\n"
        f"Plan fingerprint: `{plan['plan_fingerprint']}`.\n\n"
        "Confirm this exact plan, both models and the combined budget before execution. "
        "Existing generation-only approval does not authorize judging. "
        "No automatic retries/resume.\n\n"
        "References are provisional common candidate evidence, identical across strategies. "
        "They are excluded from generation; LLM scores are not human-reviewed accuracy.\n"
    )
