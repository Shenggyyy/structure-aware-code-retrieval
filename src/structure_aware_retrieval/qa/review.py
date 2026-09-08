"""Validate self-attested manual QA reviews without assigning semantic judgments."""

import json
import os
import tempfile
from collections import Counter
from pathlib import Path

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import validate_answer
from structure_aware_retrieval.qa.execution import _cases, _constant, _object, _validate_prepared

REVIEW_FIELDS = {
    "id",
    "answer_fingerprint",
    "context_fingerprint",
    "status",
    "reviewer",
    "correctness",
    "citation_support",
    "notes",
}
SEMANTIC_STATUSES = {"answered", "insufficient_context"}
NONSEMANTIC_STATUSES = {"invalid_answer", "provider_error", "preview"}


def _parse(raw: bytes) -> object:
    try:
        return json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Invalid JSON in QA review bundle") from error


def _read(path: Path) -> object:
    return _parse(path.read_bytes())


def _rows(path: Path) -> list:
    return [_parse(line) for line in path.read_bytes().splitlines() if line.strip()]


def _fields(value: object, expected: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} requires exactly {sorted(expected)}")
    return value


def _validate_result(result: object, case: dict) -> None:
    if not isinstance(result, dict) or not isinstance(result.get("timing_ms"), dict):
        raise ValueError("Invalid archived QA result")
    prepared = {
        **result,
        "timing_ms": {
            key: result["timing_ms"].get(key) for key in ("retrieval", "context_and_prompt")
        },
    }
    _validate_prepared(prepared, case)
    status, answer = result.get("status"), result.get("answer")
    if not isinstance(status, str) or status not in SEMANTIC_STATUSES | NONSEMANTIC_STATUSES:
        raise ValueError("Unsupported archived QA status")
    if type(result.get("model_called")) is not bool:
        raise ValueError("Invalid archived model_called flag")
    evidence, raw, provider = (
        result["context"]["evidence"],
        result.get("raw_output"),
        result.get("provider"),
    )
    if result["model_called"] and not evidence:
        raise ValueError("Empty-evidence QA result cannot call a model")
    if provider is not None and (
        not isinstance(provider, dict)
        or not isinstance(provider.get("model"), str)
        or not provider["model"].strip()
    ):
        raise ValueError("Invalid archived provider metadata")
    if status in SEMANTIC_STATUSES:
        if result["model_called"]:
            if provider is None or validate_answer(raw, evidence) != answer:
                raise ValueError("Archived answer differs from validated model output")
        elif (
            evidence
            or provider is not None
            or raw is not None
            or answer != {"status": "insufficient_context", "claims": []}
        ):
            raise ValueError("Uncalled QA result must be an empty-evidence abstention")
        if not isinstance(answer, dict) or answer["status"] != status:
            raise ValueError("Archived answer status mismatch")
    elif answer is not None:
        raise ValueError("Unvalidated archived output cannot contain an accepted answer")
    if status == "invalid_answer":
        if not result["model_called"] or provider is None:
            raise ValueError("Invalid-answer status needs a recorded model response")
        try:
            validate_answer(raw, evidence)
        except ValueError:
            pass
        else:
            raise ValueError("Archived invalid-answer status contains a valid answer")
    if status in {"preview", "provider_error"}:
        if (
            provider is not None
            or raw is not None
            or result["model_called"] != (status == "provider_error")
        ):
            raise ValueError("Archived preview/provider-error metadata is inconsistent")
    fingerprint = stable_id(
        result["prompt_fingerprint"], status, answer, raw, provider["model"] if provider else None
    )
    if result.get("answer_fingerprint") != fingerprint:
        raise ValueError("Archived answer fingerprint mismatch")


def _load_run(run: Path) -> tuple[dict, list[dict], str]:
    plan, summary, raw_cases = (
        _read(run / name) for name in ("plan.json", "summary.json", "cases.json")
    )
    cases = _cases(raw_cases)
    if (
        not isinstance(plan, dict)
        or plan.get("schema_version") != 1
        or plan.get("plan_fingerprint")
        != stable_id({key: value for key, value in plan.items() if key != "plan_fingerprint"})
        or plan.get("cases_digest") != stable_id(raw_cases)
    ):
        raise ValueError("Archived QA plan/cases fingerprint mismatch")
    records, attempts = _rows(run / "results.jsonl"), _rows(run / "started.jsonl")
    identities = set()
    for record in records:
        _fields(record, {"id", "strategy", "case_id", "repository", "result"}, "Archived result")
        if (
            not isinstance(record["strategy"], str)
            or not record["strategy"].strip()
            or not isinstance(record["case_id"], str)
            or record["case_id"] not in cases
            or record["id"] != stable_id(record["strategy"], record["case_id"])
            or record["id"] in identities
            or record["repository"] != cases[record["case_id"]]["repository"]
        ):
            raise ValueError("Duplicate or mismatched archived QA identity")
        identities.add(record["id"])
        _validate_result(record["result"], cases[record["case_id"]])
    for attempt in attempts:
        _fields(attempt, {"id", "model_call_planned"}, "Attempt")
        if not isinstance(attempt["id"], str) or type(attempt["model_call_planned"]) is not bool:
            raise ValueError("Invalid archived QA attempt")
    if (
        len({attempt["id"] for attempt in attempts}) != len(attempts)
        or len(attempts) - len(records) not in (0, 1)
        or [record["id"] for record in records] != [row["id"] for row in attempts[: len(records)]]
        or any(
            attempt["model_call_planned"] != record["result"]["model_called"]
            for attempt, record in zip(attempts, records, strict=False)
        )
    ):
        raise ValueError("Archived attempts and results disagree")
    run_fingerprint = stable_id(
        plan["plan_fingerprint"],
        [
            (
                row["id"],
                row["result"]["answer_fingerprint"],
                row["result"]["context"]["context_fingerprint"],
            )
            for row in records
        ],
    )
    if (
        not isinstance(summary, dict)
        or summary.get("schema_version") != 1
        or summary.get("plan_fingerprint") != plan["plan_fingerprint"]
        or summary.get("run_fingerprint") != run_fingerprint
    ):
        raise ValueError("Archived run fingerprint mismatch")
    counts = {
        "requested": plan.get("request_count"),
        "attempted": len(attempts),
        "completed": sum(row["result"]["status"] in SEMANTIC_STATUSES for row in records),
        "failed": sum(row["result"]["status"] in NONSEMANTIC_STATUSES for row in records),
        "unknown_outcome": len(attempts) - len(records),
    }
    if type(counts["requested"]) is not int or counts["requested"] < len(attempts):
        raise ValueError("Invalid archived request count")
    counts["not_run"] = counts["requested"] - len(attempts)
    if any(
        type(summary.get(key)) is not int or summary[key] != value for key, value in counts.items()
    ):
        raise ValueError("Archived QA outcome counts disagree with records")
    return summary, records, run_fingerprint


def _judgment(review: dict, generation_status: str) -> None:
    for key in ("reviewer", "notes"):
        if not isinstance(review[key], str):
            raise ValueError("Reviewer and notes must be strings")
        review[key].encode("utf-8")
    if review["status"] == "pending":
        if review["correctness"] is not None or review["citation_support"] is not None:
            raise ValueError("Pending reviews must leave semantic judgments null")
        return
    if (
        review["status"] != "submitted"
        or not review["reviewer"].strip()
        or not review["notes"].strip()
    ):
        raise ValueError("Submitted reviews require a nonblank reviewer and notes")
    correctness, support = review["correctness"], review["citation_support"]
    if generation_status == "answered":
        allowed = ("pass", "partial", "fail"), ("supported", "unsupported")
    elif generation_status == "insufficient_context":
        allowed = ("pass", "fail"), ("not_applicable",)
    else:
        allowed = ("not_applicable",), ("not_applicable",)
    if correctness not in allowed[0] or support not in allowed[1]:
        raise ValueError("Semantic judgments do not apply to this generation status")


def _metrics(reviews: list[dict], records: dict[str, dict], requested: int | None) -> dict:
    semantic = [
        row for row in reviews if records[row["id"]]["result"]["status"] in SEMANTIC_STATUSES
    ]
    answers = [row for row in reviews if records[row["id"]]["result"]["status"] == "answered"]
    correct = Counter(row["correctness"] for row in semantic)
    supported = sum(row["citation_support"] == "supported" for row in answers)
    return {
        "answer_correctness": {
            "pass": correct["pass"],
            "partial": correct["partial"],
            "fail": correct["fail"],
            "denominator": len(semantic),
            "pass_rate": correct["pass"] / len(semantic) if semantic else None,
        },
        "citation_support": {
            "supported": supported,
            "unsupported": len(answers) - supported,
            "denominator": len(answers),
            "rate": supported / len(answers) if answers else None,
        },
        "pass_fraction_requested": correct["pass"] / requested if requested else None,
    }


def _per_strategy(run_summary: dict, rows: list[dict], reviews: list[dict], complete: bool) -> dict:
    planned = run_summary.get("per_strategy", {})
    if not isinstance(planned, dict) or any(
        not isinstance(name, str)
        or not name.strip()
        or not isinstance(value, dict)
        or type(value.get("requested")) is not int
        or value["requested"] < 0
        for name, value in planned.items()
    ):
        raise ValueError("Invalid per-strategy requested counts in QA run")
    observed = {row["strategy"] for row in rows}
    if planned and (
        observed - set(planned)
        or sum(value["requested"] for value in planned.values()) != run_summary["requested"]
    ):
        raise ValueError("Per-strategy requested counts disagree with QA run")
    results = {}
    for strategy in sorted(observed | set(planned)):
        selected = {row["id"]: row for row in rows if row["strategy"] == strategy}
        judgments = [row for row in reviews if row["id"] in selected]
        requested = planned.get(strategy, {}).get("requested")
        if requested is not None and requested < len(selected):
            raise ValueError("Per-strategy requested count is below recorded outcomes")
        reviewed = sum(row["status"] == "submitted" for row in judgments)
        result = {
            "requested": requested,
            "recorded": len(selected),
            "reviewed": reviewed,
            "pending": len(selected) - reviewed,
            "status_counts": dict(
                sorted(Counter(row["result"]["status"] for row in selected.values()).items())
            ),
            "answer_correctness": None,
            "citation_support": None,
            "pass_fraction_requested": None,
        }
        if complete:
            result.update(_metrics(judgments, selected, requested))
        results[strategy] = result
    return results


def check_qa_review(run: Path, judgments: Path, output: Path) -> dict:
    """Bind supplied judgments to archived evidence; never infer review labels.

    All recorded outcomes must have submitted reviews before publishing quality
    metrics. Failed/unrun requests stay visible in separate denominators. Reviewer
    names are self-attested; identity and independence cannot be verified here.
    """
    if output.exists() or output.is_symlink():
        raise FileExistsError("QA review output already exists; choose a new directory")
    run_summary, rows, run_fingerprint = _load_run(run)
    raw = judgments.read_bytes()
    data = _fields(
        _parse(raw), {"schema_version", "plan_fingerprint", "run_fingerprint", "reviews"}, "Review"
    )
    if (
        type(data["schema_version"]) is not int
        or data["schema_version"] != 1
        or data["plan_fingerprint"] != run_summary["plan_fingerprint"]
        or data["run_fingerprint"] != run_fingerprint
        or not isinstance(data["reviews"], list)
    ):
        raise ValueError("Review schema or run fingerprint mismatch")
    records, seen = {row["id"]: row for row in rows}, set()
    for review in data["reviews"]:
        _fields(review, REVIEW_FIELDS, "Review row")
        if not isinstance(review["id"], str) or review["id"] not in records or review["id"] in seen:
            raise ValueError("Duplicate or unknown reviewed request")
        seen.add(review["id"])
        result = records[review["id"]]["result"]
        if (
            review["answer_fingerprint"] != result["answer_fingerprint"]
            or review["context_fingerprint"] != result["context"]["context_fingerprint"]
        ):
            raise ValueError("Review answer/context fingerprint mismatch")
        _judgment(review, result["status"])
    if seen != set(records):
        raise ValueError("Reviews must cover exactly every recorded QA outcome")
    submitted = sum(row["status"] == "submitted" for row in data["reviews"])
    complete = bool(records) and submitted == len(records)
    summary = {
        "schema_version": 1,
        "plan_fingerprint": run_summary["plan_fingerprint"],
        "run_fingerprint": run_fingerprint,
        "judgments_fingerprint": stable_id(data),
        "review_complete": complete,
        "review_status": "complete" if complete else "pending",
        "reviewed": submitted,
        "pending": len(records) - submitted,
        "reviewer_identity_verified": False,
        "independence_verified": False,
        "reviewer_attestation": "Reviewer names and judgments are supplied by the reviewer; "
        "this validator cannot establish identity or independence.",
        "denominators": {
            key: run_summary[key]
            for key in (
                "requested",
                "attempted",
                "completed",
                "failed",
                "not_run",
                "unknown_outcome",
            )
        },
        "status_counts": dict(sorted(Counter(row["result"]["status"] for row in rows).items())),
        "answer_correctness": None,
        "citation_support": None,
        "pass_fraction_requested": None,
        "metric_policy": "Correctness pass rate covers answered/abstained outcomes; partial is "
        "not pass. Citation support requires all claims supported and covers "
        "answered outcomes only. Pass fraction uses all requested cases. "
        "Abstentions require source-based review, not draft expected_status.",
    }
    if complete:
        summary.update(_metrics(data["reviews"], records, run_summary["requested"]))
    summary["per_strategy"] = _per_strategy(run_summary, rows, data["reviews"], complete)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-qa-review-", dir=output.parent) as temporary:
        folder = Path(temporary)
        (folder / "judgments.json").write_bytes(raw)
        (folder / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        if output.exists() or output.is_symlink():
            raise FileExistsError("QA review output was created concurrently")
        os.rename(folder, output)
    return summary
