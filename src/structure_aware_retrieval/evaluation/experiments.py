"""Freeze and run the inherited strategy matrix, keeping dataset roles separate."""

import hashlib
import json
import os
import tomllib
from pathlib import Path

from structure_aware_retrieval.embeddings import MODEL_SPEC
from structure_aware_retrieval.evaluation.comparison import compare_runs
from structure_aware_retrieval.evaluation.config import load_config
from structure_aware_retrieval.evaluation.dataset import load_benchmark
from structure_aware_retrieval.evaluation.profiling import profile_job
from structure_aware_retrieval.evaluation.recorded import analysis_provenance
from structure_aware_retrieval.evaluation.reporting import _dump
from structure_aware_retrieval.evaluation.suite import audit_suite
from structure_aware_retrieval.indexing import load_index
from structure_aware_retrieval.models import stable_id

TEMPLATES = (
    "hybrid-seed",
    "bm25-seed",
    "dense-seed",
    "symbol-seed",
    "structure-full",
    "structure-none",
    "structure-containment",
    "structure-import",
    "structure-call",
    "structure-test",
    "structure-no-containment",
    "structure-no-import",
    "structure-no-call",
    "structure-no-test",
    "structure-symbol-seed",
)
PATH_FIELDS = {"benchmark", "indexes", "vectors", "graphs", "model_cache"}


def write_config(path: Path, settings: dict) -> None:
    """The supported config subset is strings, numbers, lists and one-level tables."""
    lines = [
        f"{key} = {json.dumps(value, ensure_ascii=True)}"
        for key, value in settings.items()
        if not isinstance(value, dict)
    ]
    for name, values in settings.items():
        if isinstance(values, dict):
            lines.extend(["", f"[{name}]"])
            lines.extend(
                f"{json.dumps(key)} = {json.dumps(value)}" for key, value in values.items()
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def freeze_experiments(root: Path, output: Path, *, allow_provisional: bool = False) -> dict:
    """Complete preflight/config freeze before building or executing a test query."""
    root, output = root.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError("Experiment output already exists; choose a new directory")
    suite_path = root / "benchmarks/suite-v1.json"
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    bases = {
        member["role"]: load_config(suite_path.parent / member["config"])
        for member in suite["members"]
    }
    if not allow_provisional and any(
        load_benchmark(config.benchmark).annotation_status != "human_reviewed"
        for config in bases.values()
    ):
        raise ValueError("Independent review is pending; use --allow-provisional for draft scores")
    templates = {}
    for name in TEMPLATES:
        path = root / f"configs/{name}.toml"
        load_config(path)
        templates[name] = tomllib.loads(path.read_text(encoding="utf-8"))
    # Audit verifies source snapshots, all labels, dataset digests and split isolation.
    audit = audit_suite(suite_path, output / "audit")
    plan = {
        "schema_version": 1,
        "suite_digest": audit["suite_digest"],
        "implementation": analysis_provenance(),
        "lockfile_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
        "allow_provisional": allow_provisional,
        "review_complete": audit["review_complete"],
        "result_status": "reviewed_labels" if audit["review_complete"] else "provisional",
        "primary_k": audit["primary_k"],
        "primary_metrics": audit["primary_metrics"],
        "model": MODEL_SPEC,
        "strategy_settings": {
            name: {key: value for key, value in data.items() if key not in PATH_FIELDS}
            for name, data in templates.items()
        },
        "roles": ["dev", "test", "public"],
        "strategy_order": list(TEMPLATES),
        "cost_protocol": {
            "build_repeats": 1,
            "worker": "fresh_process_per_build_or_experiment",
            "threads": 4,
            "downloads": False,
            "os_cache": "uncontrolled",
            "memory": "process_lifetime_peak_including_imports_not_children",
        },
        "members": audit["members"],
    }
    # This identity has no artifact destination paths or measured timings.
    plan["plan_digest"] = stable_id(plan)
    for role in plan["roles"]:
        base = bases[role]
        for name, template in templates.items():
            path = output / "configs" / role / f"{name}.toml"

            def relative(target: Path, path: Path = path) -> str:
                return Path(os.path.relpath(target, path.parent)).as_posix()

            data = {key: value for key, value in template.items() if key not in PATH_FIELDS}
            data["name"] = name
            data["benchmark"] = relative(base.benchmark)
            for key, suffix in (("indexes", ".sqlite"), ("vectors", ".npz"), ("graphs", ".json")):
                if key in template:
                    data[key] = {
                        repo: relative(output / "artifacts" / role / key / f"{repo}{suffix}")
                        for repo in base.indexes
                    }
            if "model_cache" in template:
                data["model_cache"] = relative(root / "artifacts/models")
            write_config(path, data)
            load_config(path)
    _dump(output / "plan.json", plan)
    return plan


def run_suite(root: Path, output: Path, *, allow_provisional: bool = False) -> dict:
    root, output = root.resolve(), output.resolve()
    plan = freeze_experiments(root, output, allow_provisional=allow_provisional)
    config_hashes = {
        path.relative_to(output).as_posix(): hashlib.sha256(
            path.read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()
        for path in sorted((output / "configs").rglob("*.toml"))
    }
    _dump(output / "configuration-files.json", config_hashes)
    suite_path = root / "benchmarks/suite-v1.json"
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    costs = []
    for member in suite["members"]:
        role = member["role"]
        base = load_config(suite_path.parent / member["config"])
        for repo, existing in base.indexes.items():
            index = load_index(existing)
            metadata = index.metadata
            artifact = output / "artifacts" / role
            database = artifact / "indexes" / f"{repo}.sqlite"
            for kind, destination in (
                ("index", database),
                ("graph", artifact / "graphs" / f"{repo}.json"),
                ("vectors", artifact / "vectors" / f"{repo}.npz"),
            ):
                job = {
                    "kind": kind,
                    "output": str(destination),
                    "snapshot_id": metadata["snapshot_id"],
                }
                if kind == "index":
                    job.update(
                        source=metadata["repository"],
                        commit=metadata["git"]["commit"],
                        index_options={
                            key: metadata["config"][key]
                            for key in ("max_chunk_lines", "max_file_bytes", "exclude")
                        },
                    )
                else:
                    job["index"] = str(database)
                    if kind == "vectors":
                        job["model_cache"] = str(root / "artifacts/models")
                print(f"Building {role}/{repo}/{kind}...", flush=True)
                result = profile_job(job, output / "profiles" / role / repo / kind)
                costs.append({"role": role, "repository": repo, **result})
            del index
    _dump(output / "build-costs.json", costs)
    experiments = []
    for role in plan["roles"]:
        runs = []
        for name in plan["strategy_order"]:
            # Refuse to mix code edited midway through a long experiment suite.
            if analysis_provenance() != plan["implementation"]:
                raise ValueError("Implementation changed after the experiment freeze")
            print(f"Retrieving {role}/{name}...", flush=True)
            run = output / "runs" / role / name
            result = profile_job(
                {
                    "kind": "experiment",
                    "output": str(run),
                    "config": str(output / "configs" / role / f"{name}.toml"),
                    "config_sha256": config_hashes[f"configs/{role}/{name}.toml"],
                    "benchmark_digest": next(
                        member["benchmark_digest"]
                        for member in plan["members"]
                        if member["role"] == role
                    ),
                },
                output / "profiles" / role / "runs" / name,
            )
            experiments.append({"role": role, "name": name, **result})
            runs.append(run)
        compare_runs(runs, output / "comparison" / role)
        # Full-structure reference exposes marginal ablation effects directly.
        compare_runs([runs[4], *runs[5:]], output / "ablations" / role)
    result = {
        "schema_version": 1,
        "complete": True,
        "plan_digest": plan["plan_digest"],
        "result_status": plan["result_status"],
        "review_complete": plan["review_complete"],
        "runs": experiments,
        "builds": costs,
    }
    write_suite_report(output, plan, result)
    _dump(output / "suite-results.json", result)
    return result


def write_suite_report(output: Path, plan: dict, result: dict) -> None:
    lines = [
        "# M6c: Fixed Retrieval Experiments",
        "",
        f"Result status: **{result['result_status']}**; plan `{plan['plan_digest']}`.",
        "",
        "Known-label metrics treat unjudged candidates as zero. Independent label review "
        "is a separate acceptance condition; completed runs do not establish reviewed quality.",
        "Public results use the adapted full-repository protocol, not original RepoQA scoring.",
        "",
    ]
    for role in plan["roles"]:
        lines.extend(
            [
                f"## {role}",
                "",
                "| Strategy | Recall@10 | NDCG@10 | MRR@10 | p50 ms | p95 ms |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        comparison = json.loads((output / "comparison" / role / "comparison.json").read_text())
        for run in comparison["runs"]:
            overall = run["overall"]
            metrics, latency = overall["metrics"]["10"], overall["latency_ms"]
            lines.append(
                f"| {run['strategy']} | {metrics['recall']:.4f} | {metrics['ndcg']:.4f} | "
                f"{metrics['mrr']:.4f} | {latency['p50']:.2f} | {latency['p95']:.2f} |"
            )
        lines.extend(
            [
                "",
                f"[Paired comparison](comparison/{role}/report.md); "
                f"[ablation differences](ablations/{role}/report.md).",
                "",
            ]
        )
    lines.extend(
        [
            "## Offline construction costs",
            "",
            "One fresh worker per operation. Seconds include imports, input loads, model loading "
            "where needed, construction and serialization. Source/model downloads are excluded.",
            "",
            "| Role | Repository | Operation | Seconds | Peak MiB | Artifact MiB |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in result["builds"]:
        lines.append(
            f"| {row['role']} | {row['repository']} | {row['kind']} | "
            f"{row['operation_seconds']:.2f} | {row['peak_memory']['bytes'] / 2**20:.2f} | "
            f"{row['details']['artifact_bytes'] / 2**20:.2f} |"
        )
    lines.extend(
        [
            "",
            "Peak memory is the OS process lifetime high-water mark including native/model "
            "allocations and imports, excluding child processes. It is not incremental allocation "
            "or a sum across repositories. OS caches are uncontrolled; one build sample and "
            "heterogeneous repositories do not establish asymptotic scalability.",
            "",
            "Query latency includes encoding, ranking, deduplication and fusion after warmup; "
            "it excludes startup and construction. Each experiment loads all repositories in its "
            "role into one worker, so its peak is not a per-repository memory measurement. "
            "See suite-results.json for experiment lifetime peaks and wall times.",
            "",
        ]
    )
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
