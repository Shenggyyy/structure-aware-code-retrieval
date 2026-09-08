"""Freeze a new judge-only plan for requests never journaled in an interrupted run."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from runpy import run_path

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.assessment_plan import (
    estimate_input_tokens,
    implementation_record,
)
from structure_aware_retrieval.qa.judging import _json, _parse

HERE = Path(__file__).resolve().parent
REVISION = run_path(str(HERE / "prepare_qa_judge_revision.py"))
REVISION_BUNDLE_FILES = (
    *REVISION["OUTPUT_FILES"],
    "config.toml",
    "rubric.json",
    *(f"source/{name}" for name in REVISION["SOURCE_FILES"]),
)
PRIOR_FILES = (
    "approval.json",
    "records.json",
    "summary.json",
    "attempts.jsonl",
    "results.jsonl",
    "report.md",
    *(f"prepared/{name}" for name in REVISION_BUNDLE_FILES),
)
OUTPUT_FILES = ("plan.json", "requests.jsonl", "README.md")
BUNDLE_FILES = (*OUTPUT_FILES, *(f"prior/{name}" for name in PRIOR_FILES))


def _load(path):
    return _parse(path.read_text(encoding="utf-8"))


def _rows(path):
    return [_parse(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prior_files(run):
    diagnostic = run / "interruption.json"
    return (
        (*PRIOR_FILES, "interruption.json")
        if diagnostic.exists() or diagnostic.is_symlink()
        else PRIOR_FILES
    )


def bundle_files(bundle: Path) -> tuple[str, ...]:
    """Return only fixed paths; never follow filenames supplied by a plan or manifest."""
    return (*OUTPUT_FILES, *(f"prior/{name}" for name in _prior_files(Path(bundle) / "prior")))


def _verified_prior(run):
    parent_plan = _load(run / "prepared/plan.json")
    if parent_plan.get("kind") != "qa_judge_revision_plan":
        raise ValueError("Follow-up requires an original revision run, not another follow-up")
    if _load(run / "summary.json").get("status") not in {"interrupted", "failed"}:
        raise ValueError("Follow-up requires an interrupted or failed original revision run")
    # Load after inspecting the parent format: the verifier also imports this module.
    verifier = run_path(str(HERE / "verify_qa_judge_revision.py"))["verify_run"]
    verified = verifier(run)
    return parent_plan, verified


def _build(folder, *, implementation=None):
    prior = folder / "prior"
    parent_plan, verified = _verified_prior(prior)
    records = _load(prior / "records.json")
    attempts = _rows(prior / "attempts.jsonl")
    attempted = {row["id"] for row in attempts}
    by_id = {row["id"]: row for row in records}
    requests = [
        row for row in _rows(prior / "prepared/requests.jsonl") if row["id"] not in attempted
    ]
    if not requests:
        raise ValueError("No never-attempted judge requests remain")
    excluded = []
    for attempt in attempts:
        record = by_id[attempt["id"]]
        judging = record["judging"]
        excluded.append(
            {
                **{key: record[key] for key in ("id", "case_id", "strategy", "repository")},
                "status": judging["status"] if judging else "unknown_outcome",
            }
        )
    settings = parent_plan["judge"]
    input_tokens = [estimate_input_tokens(row["request_payload"]) for row in requests]
    output_tokens = len(requests) * settings["max_output_tokens"]
    pricing = settings["pricing"]
    plan = {
        "schema_version": 1,
        "kind": "qa_judge_followup_plan",
        "status": "prepared_offline",
        "api_calls_made": 0,
        "execution_authorized": False,
        "source_run": parent_plan["source_run"],
        "prior_run": verified,
        "prior_files_sha256": {name: _hash(prior / name) for name in _prior_files(prior)},
        "prior_records_fingerprint": stable_id(records),
        "prior_attempts_fingerprint": stable_id(attempts),
        "source_generation_model": parent_plan["source_generation_model"],
        "source_records_fingerprint": parent_plan["source_records_fingerprint"],
        "annotation_status": parent_plan["annotation_status"],
        "human_reviewed": False,
        "rubric_id": parent_plan["rubric_id"],
        "rubric_fingerprint": parent_plan["rubric_fingerprint"],
        "rubric_file_sha256": parent_plan["rubric_file_sha256"],
        "judge": settings,
        "source_planned_count": parent_plan["source_planned_count"],
        "request_count": len(requests),
        "request_order": [row["id"] for row in requests],
        "omitted": parent_plan["omitted"],
        "excluded_prior_attempts": excluded,
        "requests_fingerprint": stable_id(requests),
        "estimated_cost": {
            "new_generation_calls": 0,
            "maximum_judge_calls": len(requests),
            "estimated_input_tokens": sum(input_tokens),
            "maximum_input_tokens_per_call": max(input_tokens),
            "maximum_output_tokens": output_tokens,
            "combined_usd": (
                sum(input_tokens) * pricing["input_per_million"]
                + output_tokens * pricing["output_per_million"]
            )
            / 1_000_000,
            "method": "Exact unchanged remaining request bytes, framing and maximum output",
            "prior_generation_cost_included": False,
            "prior_judging_cost_included": False,
            "billing_guarantee": False,
        },
        "implementation": implementation
        if implementation is not None
        else {
            **implementation_record(),
            "preparation_script_sha256": _hash(Path(__file__)),
            "prior_verifier_sha256": _hash(HERE / "verify_qa_judge_revision.py"),
            "revision_preparation_script_sha256": _hash(HERE / "prepare_qa_judge_revision.py"),
        },
    }
    plan["plan_fingerprint"] = stable_id(plan)
    return plan, requests


def _contents(plan, requests):
    unknown = sum(row["status"] == "unknown_outcome" for row in plan["excluded_prior_attempts"])
    return {
        "plan.json": json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        "requests.jsonl": "".join(_json(row) + "\n" for row in requests),
        "README.md": (
            "# Offline Judge Follow-up Plan\n\n"
            f"Prepared {plan['request_count']} unchanged requests never journaled in the "
            "verified prior revision run. No new generation, API calls or model judgments "
            "were produced. This is a new plan, not a retry or an in-place resume.\n\n"
            f"All {len(plan['excluded_prior_attempts'])} prior attempts are excluded, "
            f"including {unknown} unknown outcomes. An unknown outcome may have been billed; "
            "no absence of billing or provider processing is inferred. "
            f"The full source population remains {plan['source_planned_count']} cases.\n\n"
            f"Judge-only proposal: {plan['judge']['model']}; estimated additional "
            f"US${plan['estimated_cost']['combined_usd']:.6f}. Historical generation and "
            "judging costs are excluded. This estimate is not a billing cap or approval. "
            "Any execution requires explicit approval of the model, scope and new budget.\n\n"
            f"Plan fingerprint: `{plan['plan_fingerprint']}`.\n\n"
            "The prior directory freezes the verified run, original requests and complete "
            "saved-answer provenance. Requests, model, rubric and pricing are unchanged; "
            "no historical results or labels are repaired. Labels remain provisional, "
            "and model scores do not establish true accuracy or human review. "
            "Only one follow-up from an original interrupted or failed revision is supported.\n"
        ),
    }


def check_followup(bundle: Path) -> dict:
    """Revalidate the parent and recompute the exact never-attempted request selection."""
    bundle = Path(bundle)
    saved = _load(bundle / "plan.json")
    fingerprint = saved.pop("plan_fingerprint", None)
    if fingerprint != stable_id(saved):
        raise ValueError("Follow-up plan fingerprint mismatch")
    plan, requests = _build(bundle, implementation=saved["implementation"])
    for name, expected in _contents(plan, requests).items():
        if (bundle / name).read_text(encoding="utf-8") != expected:
            raise ValueError(f"Follow-up output differs from recomputed content: {name}")
    return plan


def prepare_followup(run: Path, output: Path) -> dict:
    """Publish an immutable offline bundle; no credentials or provider calls are needed."""
    run, output = Path(run), Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError("Follow-up output exists; use a new directory")
    _verified_prior(run)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".sacr-judge-followup-", dir=output.parent
    ) as temporary:
        folder = Path(temporary)
        for name in _prior_files(run):
            target = folder / "prior" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(run / name, target)
        plan, requests = _build(folder)
        for name, content in _contents(plan, requests).items():
            (folder / name).write_text(content, encoding="utf-8", newline="\n")
        check_followup(folder)
        if output.exists() or output.is_symlink():
            raise FileExistsError("Follow-up output was created concurrently")
        os.rename(folder, output)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--run", required=True, type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    check = commands.add_parser("check")
    check.add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args()
    try:
        plan = (
            prepare_followup(args.run, args.output)
            if args.command == "prepare"
            else check_followup(args.bundle)
        )
    except (OSError, ValueError, TypeError, KeyError):
        parser.exit(1, "Offline judge follow-up failed; inspect source and bundle integrity.\n")
    print(
        json.dumps(
            {
                "request_count": plan["request_count"],
                "excluded_prior_attempts": len(plan["excluded_prior_attempts"]),
                "api_calls_made": 0,
                "estimated_cost_usd": plan["estimated_cost"]["combined_usd"],
                "plan_fingerprint": plan["plan_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
