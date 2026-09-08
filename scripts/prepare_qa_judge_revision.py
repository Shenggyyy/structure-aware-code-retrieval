"""Prepare and check a judge-only protocol revision from saved answers, entirely offline."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import tomllib
from collections import Counter
from copy import deepcopy
from pathlib import Path
from runpy import run_path

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.assessment_plan import (
    BUNDLE_FILES,
    _fields,
    _settings,
    estimate_input_tokens,
    implementation_record,
    validate_assessment_bundle,
)
from structure_aware_retrieval.qa.judging import (
    _json,
    _parse,
    _schema,
    load_rubric,
    prepare_judgment,
    validate_judgment,
)
from structure_aware_retrieval.qa.provider import OpenAIModel

VERIFY_SCRIPT = Path(__file__).with_name("verify_qa_assessment.py")
verify_run = run_path(str(VERIFY_SCRIPT))["verify_run"]
SOURCE_FILES = (
    "approval.json",
    "records.json",
    "summary.json",
    "attempts.jsonl",
    "results.jsonl",
    "prepared/plan.json",
    "prepared/references.json",
    "prepared/rubric.json",
    *(f"prepared/generation/{name}" for name in BUNDLE_FILES),
)
OUTPUT_FILES = ("plan.json", "requests.jsonl", "replay.json", "README.md")


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path):
    return _parse(path.read_text(encoding="utf-8"))


def _model(settings, prepared):
    return OpenAIModel(
        model=settings["model"],
        api_key_env=settings["api_key_env"],
        max_output_tokens=settings["max_output_tokens"],
        reasoning_effort=settings["reasoning_effort"],
        output_schema=prepared["output_schema"],
        schema_name="repository_judgment_v2",
    )


def _replay(previous, prepared):
    result = {"source_status": previous["status"] if previous else "not_run"}
    if not previous or previous["status"] not in ("scored", "invalid_judgment"):
        return {**result, "schema": "not_replayed", "validation": "not_replayed"}
    raw = previous["raw_output"]
    result["source_raw_output_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    try:
        value = _parse(raw)
        if not isinstance(value, dict) or value.get("rubric_id") != "repository-qa-judge-rubric-v1":
            raise ValueError("Replay requires an identifiable v1 JSON judgment")
        candidate = deepcopy(value)
        candidate["rubric_id"] = prepared["rubric"]["rubric_id"]
    except ValueError as error:
        return {
            **result,
            "schema": "not_replayed",
            "validation": "not_replayed",
            "error": str(error),
        }
    for name, validate in (
        ("schema", lambda: _schema(candidate, prepared["output_schema"])),
        ("validation", lambda: validate_judgment(_json(candidate), prepared)),
    ):
        try:
            validate()
        except ValueError as error:
            result[name] = "rejected"
            result[f"{name}_error"] = str(error)
        else:
            result[name] = "accepted"
    return result


def _build(folder, *, implementation=None):
    source = folder / "source"
    verified = verify_run(source)
    source_plan, _, references, source_rubric = validate_assessment_bundle(source / "prepared")
    if source_rubric["rubric_version"] != 1:
        raise ValueError("Revision preparation requires a recorded v1 source run")
    config = tomllib.loads((folder / "config.toml").read_text(encoding="utf-8"))
    _fields(config, {"schema_version", "rubric", "judge"}, "revision config")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("Unsupported revision config version")
    settings = _settings(config["judge"])
    rubric = load_rubric(folder / "rubric.json")
    if rubric["rubric_version"] != 2:
        raise ValueError("Revision preparation requires frozen rubric v2")
    records = _load(source / "records.json")
    requests, omitted, replay, input_tokens = [], [], [], []
    for record in records:
        identity = {key: record[key] for key in ("id", "case_id", "strategy", "repository")}
        generation = record["generation"]
        if not generation or generation["status"] not in ("answered", "insufficient_context"):
            omitted.append(
                {**identity, "reason": generation["status"] if generation else "not_run"}
            )
            continue
        prepared = prepare_judgment(generation, references[record["case_id"]], rubric)
        payload = _model(settings, prepared).request_payload(prepared["messages"])
        requests.append(
            {
                **identity,
                "prepared": prepared,
                "request_payload": payload,
                "request_payload_sha256": hashlib.sha256(
                    _json(payload).encode("utf-8")
                ).hexdigest(),
            }
        )
        input_tokens.append(estimate_input_tokens(payload))
        replay.append({**identity, **_replay(record["judging"], prepared)})
    count = len(requests)
    output_tokens = count * settings["max_output_tokens"]
    pricing = settings["pricing"]
    plan = {
        "schema_version": 1,
        "kind": "qa_judge_revision_plan",
        "status": "prepared_offline",
        "api_calls_made": 0,
        "execution_authorized": False,
        "source_run": verified,
        "source_generation_model": source_plan["generation"]["model"],
        "source_records_fingerprint": stable_id(records),
        "source_files_sha256": {name: _hash(source / name) for name in SOURCE_FILES},
        "annotation_status": source_plan["annotation_status"],
        "human_reviewed": False,
        "rubric_id": rubric["rubric_id"],
        "rubric_fingerprint": rubric["rubric_fingerprint"],
        "rubric_file_sha256": rubric["rubric_file_sha256"],
        "judge": settings,
        "source_planned_count": len(records),
        "request_count": count,
        "omitted": omitted,
        "request_order": [request["id"] for request in requests],
        "requests_fingerprint": stable_id(requests),
        "replay_fingerprint": stable_id(replay),
        "config_sha256": _hash(folder / "config.toml"),
        "estimated_cost": {
            "new_generation_calls": 0,
            "maximum_judge_calls": count,
            "estimated_input_tokens": sum(input_tokens),
            "maximum_input_tokens_per_call": max(input_tokens, default=0),
            "maximum_output_tokens": output_tokens,
            "combined_usd": (
                sum(input_tokens) * pricing["input_per_million"]
                + output_tokens * pricing["output_per_million"]
            )
            / 1_000_000,
            "method": (
                "Exact saved-answer request bytes, dynamic schemas, framing and maximum output"
            ),
            "prior_generation_cost_included": False,
            "billing_guarantee": False,
        },
        "replay_policy": (
            "Only rubric_id is retagged on an in-memory copy; no scores, IDs or claims repaired. "
            "Not v2 model results."
        ),
        "implementation": implementation
        if implementation is not None
        else {
            **implementation_record(),
            "preparation_script_sha256": _hash(Path(__file__)),
            "source_verifier_sha256": _hash(VERIFY_SCRIPT),
        },
    }
    plan["plan_fingerprint"] = stable_id(plan)
    diagnostic = {
        "kind": "offline_schema_migration_diagnostic",
        "api_calls_made": 0,
        "policy": plan["replay_policy"],
        "cases": replay,
        "counts": {
            name: dict(Counter(row[name] for row in replay))
            for name in ("source_status", "schema", "validation")
        },
    }
    return plan, requests, diagnostic


def _contents(plan, requests, diagnostic):
    def pretty(value):
        return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"

    return {
        "plan.json": pretty(plan),
        "requests.jsonl": "".join(_json(row) + "\n" for row in requests),
        "replay.json": pretty(diagnostic),
        "README.md": (
            "# Offline QA Judge Revision\n\n"
            f"Prepared {plan['request_count']} exact v2 judge requests over saved answers. "
            "No new answers, API calls or v2 model judgments were produced.\n\n"
            f"Judge-only proposal: {plan['judge']['model']}; estimated "
            f"US${plan['estimated_cost']['combined_usd']:.6f}. This is not a billing cap "
            "or approval. Prior generation costs are excluded.\n\n"
            f"Plan fingerprint: `{plan['plan_fingerprint']}`.\n\n"
            "The replay file is a schema/validator migration diagnostic on exposed v1 "
            "outputs. Only rubric_id is retagged in memory. No source IDs, scores, claims "
            "or labels are repaired. Schema acceptance is not future model compliance "
            "or semantic accuracy. Source files remain copied verbatim.\n\n"
            "This milestone has no v2 execution command. Any later judge-only run needs "
            "explicit model, scope and budget approval. The v1 combined runner cannot "
            "execute this bundle.\n"
        ),
    }


def check_revision(bundle: Path):
    saved = _load(bundle / "plan.json")
    fingerprint = saved.pop("plan_fingerprint", None)
    if fingerprint != stable_id(saved):
        raise ValueError("Revision plan fingerprint mismatch")
    # Creation host/code metadata is provenance, not a constraint on the replay host.
    # Recompute all requests and diagnostics; retain the fingerprinted creation record.
    plan, requests, diagnostic = _build(bundle, implementation=saved["implementation"])
    for name, expected in _contents(plan, requests, diagnostic).items():
        if (bundle / name).read_text(encoding="utf-8") != expected:
            raise ValueError(f"Revision output differs from recomputed content: {name}")
    return plan


def prepare_revision(run: Path, config: Path, output: Path):
    if output.exists() or output.is_symlink():
        raise FileExistsError("Revision output exists; use a new directory")
    config_data = tomllib.loads(config.read_text(encoding="utf-8"))
    _fields(config_data, {"schema_version", "rubric", "judge"}, "revision config")
    if not isinstance(config_data["rubric"], str) or not config_data["rubric"].strip():
        raise ValueError("Revision rubric must be a nonempty file path")
    rubric_path = config.parent / config_data["rubric"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".sacr-judge-revision-", dir=output.parent
    ) as temporary:
        folder = Path(temporary)
        for name in SOURCE_FILES:
            target = folder / "source" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(run / name, target)
        shutil.copyfile(config, folder / "config.toml")
        shutil.copyfile(rubric_path, folder / "rubric.json")
        plan, requests, diagnostic = _build(folder)
        for name, text in _contents(plan, requests, diagnostic).items():
            (folder / name).write_text(text, encoding="utf-8", newline="\n")
        check_revision(folder)
        if output.exists() or output.is_symlink():
            raise FileExistsError("Revision output was created concurrently")
        os.rename(folder, output)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--run", required=True, type=Path)
    prepare.add_argument("--config", required=True, type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    check = commands.add_parser("check")
    check.add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args()
    try:
        plan = (
            prepare_revision(args.run, args.config, args.output)
            if args.command == "prepare"
            else check_revision(args.bundle)
        )
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"Offline judge revision failed: {error}\n")
    print(
        json.dumps(
            {
                "request_count": plan["request_count"],
                "api_calls_made": 0,
                "estimated_cost_usd": plan["estimated_cost"]["combined_usd"],
                "plan_fingerprint": plan["plan_fingerprint"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
