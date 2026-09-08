"""Explicit, budget-checked QA execution with durable records and pending review."""

import hashlib
import io
import json
import math
import os
import re
from collections import Counter
from pathlib import Path, PurePosixPath

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    complete_question,
    render_answer,
)
from structure_aware_retrieval.qa.context import CONTEXT_VERSION, SELECTION_POLICY
from structure_aware_retrieval.qa.provider import ANSWER_SCHEMA, AnswerModel, OpenAIModel

TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cached_tokens",
    "reasoning_tokens",
)
SUCCESS_STATUSES = ("answered", "insufficient_context")
FRAMING_ALLOWANCE_TOKENS = 4096


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON fields in QA bundle")
        result[key] = value
    return result


def _constant(_value):
    raise ValueError("Nonfinite JSON values are not allowed in QA bundles")


def _load(path: Path):
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_object, parse_constant=_constant
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f"Invalid QA bundle JSON: {path.name}") from error


def _number(value, *, positive=False):
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and (value > 0 if positive else value >= 0)
    )


def _string(value):
    return isinstance(value, str) and bool(value.strip())


def _hash(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[a-f0-9]{64}", value))


def _source_target(target):
    if not isinstance(target, dict):
        raise ValueError("Invalid source target in QA bundle")
    path = target.get("path")
    if (
        not _string(path)
        or "\\" in path
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or not _string(target.get("qualified_name"))
        or type(target.get("start_line")) is not int
        or target["start_line"] < 1
        or type(target.get("end_line")) is not int
        or target["end_line"] < target["start_line"]
    ):
        raise ValueError("Invalid source path, symbol, or line range in QA bundle")


def _cases(raw: object) -> dict:
    fields = {
        "schema_version",
        "id",
        "version",
        "annotation_status",
        "retrieval_benchmark",
        "retrieval_benchmark_digest",
        "cases",
    }
    if (
        not isinstance(raw, dict)
        or set(raw) != fields
        or type(raw["schema_version"]) is not int
        or raw["schema_version"] != 1
        or not _hash(raw["retrieval_benchmark_digest"])
        or any(not _string(raw[key]) for key in fields - {"schema_version", "cases"})
        or not isinstance(raw["cases"], list)
        or not raw["cases"]
    ):
        raise ValueError("Invalid frozen QA cases schema")
    result = {}
    case_fields = {
        "id",
        "repository",
        "question",
        "source_query_id",
        "expected_status",
        "reference_points",
        "source_targets",
        "rationale",
    }
    for case in raw["cases"]:
        if (
            not isinstance(case, dict)
            or set(case) != case_fields
            or any(not _string(case[key]) for key in ("id", "repository", "question", "rationale"))
            or case["id"] in result
            or case["expected_status"] not in SUCCESS_STATUSES
            or (case["source_query_id"] is not None and not _string(case["source_query_id"]))
            or not isinstance(case["reference_points"], list)
            or not case["reference_points"]
            or any(not _string(point) for point in case["reference_points"])
            or not isinstance(case["source_targets"], list)
        ):
            raise ValueError("Invalid or duplicate frozen QA case")
        for target in case["source_targets"]:
            if not isinstance(target, dict) or set(target) != {
                "path",
                "qualified_name",
                "start_line",
                "end_line",
            }:
                raise ValueError("Invalid QA case source target fields")
            _source_target(target)
        result[case["id"]] = case
    return result


def _validate_prepared(prepared: object, case: dict) -> None:
    if (
        not isinstance(prepared, dict)
        or prepared.get("schema_version") != 1
        or prepared.get("question") != case["question"]
        or len(case["question"].encode("utf-8")) > 4000
        or prepared.get("prompt_version") != PROMPT_VERSION
    ):
        raise ValueError("Prepared prompt does not match its QA case/version")
    messages, context = prepared.get("messages"), prepared.get("context")
    if (
        not isinstance(messages, list)
        or len(messages) != 2
        or messages[0] != {"role": "system", "content": SYSTEM_PROMPT}
        or not isinstance(messages[1], dict)
        or set(messages[1]) != {"role", "content"}
        or messages[1]["role"] != "user"
        or not isinstance(messages[1]["content"], str)
        or prepared.get("prompt_fingerprint") != stable_id(messages)
        or not isinstance(context, dict)
        or context.get("schema_version") != CONTEXT_VERSION
    ):
        raise ValueError("Prepared messages, prompt fingerprint, or context schema is invalid")
    config, evidence, budget = context.get("config"), context.get("evidence"), context.get("budget")
    if (
        not isinstance(config, dict)
        or not isinstance(evidence, list)
        or not isinstance(budget, dict)
        or not _hash(context.get("snapshot_id"))
        or config.get("policy") != SELECTION_POLICY
        or config.get("serialization") != "compact_sorted_json_utf8"
        or type(config.get("top_k")) is not int
        or config["top_k"] < 1
        or type(config.get("max_context_bytes")) is not int
        or config["max_context_bytes"] < 2
        or len(evidence) > config["top_k"]
        or context.get("context_fingerprint")
        != stable_id(CONTEXT_VERSION, context["snapshot_id"], config, evidence)
    ):
        raise ValueError("Prepared context configuration or fingerprint is invalid")
    source_fields = ("id", "path", "qualified_name", "start_line", "end_line", "text")
    sources, symbols, ranges = [], set(), {}
    for ordinal, source in enumerate(evidence, 1):
        _source_target(source)
        if (
            source.get("id") != f"S{ordinal}"
            or not isinstance(source.get("text"), str)
            or type(source.get("truncated")) is not bool
            or not _hash(source.get("chunk_id"))
            or not _hash(source.get("symbol_id"))
            or source["symbol_id"] in symbols
        ):
            raise ValueError("Prepared evidence has invalid or duplicate source identity")
        text = source["text"]
        if (
            source.get("text_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest()
            or len(io.StringIO(text).readlines()) != source["end_line"] - source["start_line"] + 1
            or any(
                a <= source["end_line"] and source["start_line"] <= b
                for a, b in ranges.get(source["path"], [])
            )
        ):
            raise ValueError("Prepared evidence text, line ranges, or hash are invalid")
        symbols.add(source["symbol_id"])
        ranges.setdefault(source["path"], []).append((source["start_line"], source["end_line"]))
        sources.append({field: source[field] for field in source_fields})
    serialized = json.dumps(sources, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    size = len(serialized.encode("utf-8"))
    if (
        context.get("context_text") != serialized
        or budget.get("unit") != "utf8_bytes"
        or budget.get("max_context_bytes") != config["max_context_bytes"]
        or budget.get("used_context_bytes") != size
        or size > config["max_context_bytes"]
    ):
        raise ValueError("Prepared context bytes or budget do not match evidence")
    try:
        user = json.loads(
            messages[1]["content"], object_pairs_hook=_object, parse_constant=_constant
        )
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Prepared user message is not valid JSON") from error
    if user != {"question": case["question"], "evidence": sources}:
        raise ValueError("Prepared user message differs from its case and evidence")
    timings = prepared.get("timing_ms")
    if (
        not isinstance(timings, dict)
        or set(timings) != {"retrieval", "context_and_prompt"}
        or not all(_number(value) for value in timings.values())
    ):
        raise ValueError("Prepared timing measurements are invalid")


def _validated_bundle(bundle: Path, budget_usd: float):
    if not _number(budget_usd, positive=True):
        raise ValueError("budget_usd must be a positive finite number")
    plan, raw_cases = _load(bundle / "plan.json"), _load(bundle / "cases.json")
    cases = _cases(raw_cases)
    if (
        not isinstance(plan, dict)
        or plan.get("schema_version") != 1
        or plan.get("plan_fingerprint")
        != stable_id({key: value for key, value in plan.items() if key != "plan_fingerprint"})
        or plan.get("cases_digest") != stable_id(raw_cases)
    ):
        raise ValueError("QA plan or cases fingerprint does not match")
    try:
        rows = [
            json.loads(line, object_pairs_hook=_object, parse_constant=_constant)
            for line in (bundle / "requests.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Invalid prepared QA requests") from error
    if (
        type(plan.get("request_count")) is not int
        or plan["request_count"] != len(rows)
        or not rows
        or plan.get("request_digest") != stable_id(rows)
    ):
        raise ValueError("QA request count or digest does not match")
    identities = set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or set(row) != {"id", "strategy", "case_id", "repository", "prepared"}
            or not _string(row["strategy"])
            or not isinstance(row["case_id"], str)
            or row["case_id"] not in cases
            or row["repository"] != cases[row["case_id"]]["repository"]
            or row["id"] != stable_id(row["strategy"], row["case_id"])
            or row["id"] in identities
        ):
            raise ValueError("QA request identity or case binding is invalid")
        identities.add(row["id"])
        _validate_prepared(row["prepared"], cases[row["case_id"]])
    if set(row["case_id"] for row in rows) != set(cases):
        raise ValueError("QA requests must cover every frozen case")
    for strategy in {row["strategy"] for row in rows}:
        if {row["case_id"] for row in rows if row["strategy"] == strategy} != set(cases):
            raise ValueError("Every QA strategy must use the same frozen cases")
    if "content_fingerprint" in plan and plan["content_fingerprint"] != stable_id(
        [(row["id"], row["prepared"]["prompt_fingerprint"]) for row in rows]
    ):
        raise ValueError("QA content fingerprint does not match its prepared prompts")
    if (
        "retrieval_benchmark_digest" in plan
        and plan["retrieval_benchmark_digest"] != raw_cases["retrieval_benchmark_digest"]
    ):
        raise ValueError("QA plan and cases use different retrieval benchmarks")
    if "maximum_api_calls" in plan and plan["maximum_api_calls"] != sum(
        bool(row["prepared"]["context"]["evidence"]) for row in rows
    ):
        raise ValueError("QA planned API call count does not match the prepared evidence")
    if "strategies" in plan:
        strategies = plan["strategies"]
        if not isinstance(strategies, dict) or set(strategies) != {row["strategy"] for row in rows}:
            raise ValueError("QA plan strategy metadata does not match requests")
        for row in rows:
            metadata = strategies[row["strategy"]]
            if not isinstance(metadata, dict) or not isinstance(metadata.get("indexes"), dict):
                raise ValueError("QA plan is missing strategy index metadata")
            source = metadata["indexes"].get(row["repository"])
            if (
                not isinstance(source, dict)
                or source.get("snapshot_id") != row["prepared"]["context"]["snapshot_id"]
            ):
                raise ValueError("QA prompt snapshot differs from the frozen strategy index")
    for row in rows:
        for field in ("max_context_bytes", "top_k"):
            if field in plan and row["prepared"]["context"]["config"][field] != plan[field]:
                raise ValueError("QA context configuration differs from the frozen plan")
    if (
        type(plan.get("max_output_tokens")) is not int
        or not 1 <= plan["max_output_tokens"] <= 16384
        or not isinstance(plan.get("model"), str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}", plan["model"])
        or not isinstance(plan.get("api_key_env"), str)
        or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", plan["api_key_env"])
    ):
        raise ValueError("Frozen QA model configuration is invalid")
    pricing = plan.get("pricing")
    if (
        not isinstance(pricing, dict)
        or not _number(pricing.get("input_per_million"))
        or not _number(pricing.get("output_per_million"))
        or not _number(plan.get("estimated_cost_usd"))
    ):
        raise ValueError("Frozen QA pricing or cost estimate is invalid")
    schema_size = len(
        json.dumps(ANSWER_SCHEMA, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    recomputed = sum(
        (
            (
                sum(
                    len(message["content"].encode("utf-8"))
                    for message in row["prepared"]["messages"]
                )
                + FRAMING_ALLOWANCE_TOKENS
                + schema_size
            )
            * pricing["input_per_million"]
            + plan["max_output_tokens"] * pricing["output_per_million"]
        )
        / 1_000_000
        for row in rows
        if row["prepared"]["context"]["evidence"]
    )
    if not math.isclose(plan["estimated_cost_usd"], recomputed, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("Frozen QA cost estimate does not match requests and pricing")
    if budget_usd < recomputed:
        raise ValueError("Budget is below the frozen conservative cost estimate; no requests sent")
    # All budget/integrity checks precede constructing the live adapter.
    configuration = OpenAIModel(
        model=plan["model"],
        api_key_env=plan["api_key_env"],
        max_output_tokens=plan["max_output_tokens"],
    )
    return plan, raw_cases, cases, rows, configuration


def _write(path: Path, value: object):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _append(handle, value):
    handle.write(json.dumps(value, ensure_ascii=True, allow_nan=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def _usage(records: list[dict], unknown_outcomes: int, pricing: dict) -> dict:
    called = [record["result"] for record in records if record["result"]["model_called"]]
    available = {field: [] for field in TOKEN_FIELDS}
    missing = {field: unknown_outcomes for field in TOKEN_FIELDS}
    for result in called:
        usage = (result.get("provider") or {}).get("usage") or {}
        for field in TOKEN_FIELDS:
            value = usage.get(field)
            if type(value) is int and value >= 0:
                available[field].append(value)
            else:
                missing[field] += 1
    totals = {field: None if missing[field] else sum(available[field]) for field in TOKEN_FIELDS}
    cost = None
    if totals["input_tokens"] is not None and totals["output_tokens"] is not None:
        cost = (
            totals["input_tokens"] * pricing["input_per_million"]
            + totals["output_tokens"] * pricing["output_per_million"]
        ) / 1_000_000
    return {
        "tokens": totals,
        "observed_token_subtotals": {field: sum(values) for field, values in available.items()},
        "calls_missing_token_counts": missing,
        "cost_usd_at_frozen_uncached_rates": cost,
        "cost_note": "Projection from reported usage at frozen uncached rates; not an invoice. "
        "Unknown usage makes total cost unavailable.",
    }


def _metrics(records: list[dict], cases: dict) -> dict:
    identities = [record["result"]["evaluation"]["citation_identity_valid"] for record in records]
    valid, invalid = identities.count(True), identities.count(False)
    evaluated = [record for record in records if record["result"]["status"] in SUCCESS_STATUSES]
    agreements = sum(
        record["result"]["status"] == cases[record["case_id"]]["expected_status"]
        for record in evaluated
    )
    controls = [
        record
        for record in records
        if cases[record["case_id"]]["expected_status"] == "insufficient_context"
    ]
    abstentions = sum(record["result"]["status"] == "insufficient_context" for record in controls)
    timings = [record["result"]["timing_ms"]["generation_and_validation"] for record in records]
    return {
        "model_calls": sum(record["result"]["model_called"] for record in records),
        "local_abstentions": sum(
            record["result"]["status"] == "insufficient_context"
            and not record["result"]["model_called"]
            for record in records
        ),
        "model_abstentions": sum(
            record["result"]["status"] == "insufficient_context"
            and record["result"]["model_called"]
            for record in records
        ),
        "status_counts": dict(
            sorted(Counter(record["result"]["status"] for record in records).items())
        ),
        "citation_identity": {
            "valid": valid,
            "invalid": invalid,
            "unavailable": len(records) - valid - invalid,
            "rate": valid / (valid + invalid) if valid + invalid else None,
        },
        "draft_expected_status_agreement": {
            "matches": agreements,
            "evaluated": len(evaluated),
            "rate": agreements / len(evaluated) if evaluated else None,
        },
        "abstention_controls": {
            "matched": abstentions,
            "attempted": len(controls),
            "rate": abstentions / len(controls) if controls else None,
        },
        "generation_and_validation_latency_ms": {
            "count": len(timings),
            "mean": sum(timings) / len(timings) if timings else None,
            "total": sum(timings),
        },
        "latency_ms": {
            stage: {
                "count": len(records),
                "mean": sum(record["result"]["timing_ms"][stage] for record in records)
                / len(records)
                if records
                else None,
                "total": sum(record["result"]["timing_ms"][stage] for record in records),
            }
            for stage in (
                "retrieval",
                "context_and_prompt",
                "generation_and_validation",
                "total_excluding_load",
            )
        },
        "answer_correctness": None,
        "citation_support": None,
        "review_status": "pending",
    }


def _review(plan, records, cases):
    return {
        "schema_version": 1,
        "plan_fingerprint": plan["plan_fingerprint"],
        "run_fingerprint": stable_id(
            plan["plan_fingerprint"],
            [
                (
                    record["id"],
                    record["result"]["answer_fingerprint"],
                    record["result"]["context"]["context_fingerprint"],
                )
                for record in records
            ],
        ),
        "reviews": [
            {
                "id": record["id"],
                "answer_fingerprint": record["result"]["answer_fingerprint"],
                "context_fingerprint": record["result"]["context"]["context_fingerprint"],
                "status": "pending",
                "reviewer": "",
                "correctness": None,
                "citation_support": None,
                "notes": "",
            }
            for record in records
        ],
    }


def execute_bundle(
    bundle: Path, output: Path, *, budget_usd: float, model: AnswerModel | None = None
) -> dict:
    """Execute an explicitly authorized frozen bundle once, refusing any existing output.

    Budget gates a conservative projection, not a guaranteed provider spending cap.
    Each attempted request is journaled before its call; each result is flushed before
    proceeding. A provider error stops the run without retrying. Interrupted outcomes
    remain unknown and require checking the provider before a separate run.
    """
    plan, raw_cases, cases, rows, configured_model = _validated_bundle(Path(bundle), budget_usd)
    if isinstance(model, OpenAIModel) and (
        model.model,
        model.api_key_env,
        model.max_output_tokens,
    ) != (configured_model.model, configured_model.api_key_env, configured_model.max_output_tokens):
        raise ValueError("Injected model configuration differs from the frozen QA plan")
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(
            "QA execution output already exists; never reuse a paid run directory"
        )
    output.mkdir(parents=True, exist_ok=False)
    _write(output / "plan.json", plan)
    _write(output / "cases.json", raw_cases)
    records, started = [], []
    interrupted = False

    def checkpoint():
        unknown = len(started) - len(records)
        review = _review(plan, records, cases)
        failures = sum(record["result"]["status"] not in SUCCESS_STATUSES for record in records)
        stopped = any(record["result"]["status"] == "provider_error" for record in records)
        status = "running"
        if interrupted:
            status = "interrupted"
        elif stopped:
            status = "failed"
        elif len(records) == len(rows):
            status = "failed" if failures else "complete"
        per_strategy = {}
        for strategy in sorted({row["strategy"] for row in rows}):
            selected = [record for record in records if record["strategy"] == strategy]
            selected_ids = {row["id"] for row in rows if row["strategy"] == strategy}
            unknown_calls = sum(
                item["model_call_planned"] and item["id"] in selected_ids
                for item in started[len(records) :]
            )
            per_strategy[strategy] = {
                **_metrics(selected, cases),
                **_usage(selected, unknown_calls, plan["pricing"]),
                "requested": len(selected_ids),
                "attempted": sum(item["id"] in selected_ids for item in started),
            }
        summary = {
            "schema_version": 1,
            "status": status,
            "plan_fingerprint": plan["plan_fingerprint"],
            "run_fingerprint": review["run_fingerprint"],
            "requested_model": plan["model"],
            "budget_usd": budget_usd,
            "estimated_cost_usd": plan["estimated_cost_usd"],
            "pricing": plan["pricing"],
            "requested": len(rows),
            "attempted": len(started),
            "completed": sum(record["result"]["status"] in SUCCESS_STATUSES for record in records),
            "failed": failures,
            "not_run": len(rows) - len(started),
            "unknown_outcome": unknown,
            "model_calls_attempted": sum(item["model_call_planned"] for item in started),
            "interrupted": interrupted,
            "stopped_after_provider_error": stopped,
            "reported_models": sorted(
                {
                    record["result"]["provider"]["model"]
                    for record in records
                    if record["result"].get("provider")
                }
            ),
            **_metrics(records, cases),
            **_usage(
                records,
                sum(item["model_call_planned"] for item in started[len(records) :]),
                plan["pricing"],
            ),
            "per_strategy": per_strategy,
        }
        _write(output / "summary.json", summary)
        _write(output / "review-template.json", review)
        return summary

    checkpoint()
    try:
        with (
            (output / "started.jsonl").open("x", encoding="utf-8", newline="\n") as attempts,
            (output / "results.jsonl").open("x", encoding="utf-8", newline="\n") as results,
        ):
            for ordinal, row in enumerate(rows, 1):
                attempt = {
                    "id": row["id"],
                    "model_call_planned": bool(row["prepared"]["context"]["evidence"]),
                }
                _append(attempts, attempt)
                started.append(attempt)
                checkpoint()
                result = complete_question(
                    row["prepared"], model if model is not None else configured_model
                )
                record = {key: row[key] for key in ("id", "strategy", "case_id", "repository")}
                record["result"] = result
                _append(results, record)
                records.append(record)
                # Ordinal filenames cannot be controlled by a repository/question/model string.
                (output / f"answer-{ordinal:04d}.md").write_text(
                    render_answer(result), encoding="utf-8"
                )
                checkpoint()
                if result["status"] == "provider_error":
                    break
    except BaseException:
        interrupted = True
        raise
    finally:
        summary = checkpoint()
    return summary
