"""Deterministically summarize a complete frozen suite using saved evidence only."""

import json
import math
import os
import re
import tempfile
from pathlib import Path

from structure_aware_retrieval.evaluation.recorded import load_runs
from structure_aware_retrieval.models import stable_id

METRICS = ("recall", "precision", "mrr", "ndcg")
LATENCY_SCOPE = "Recorded query timing; outside the validated quality fingerprints."


def _names(values: list[str]) -> list[str]:
    if (
        not isinstance(values, list)
        or not values
        or any(
            not isinstance(v, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", v) for v in values
        )
        or len(set(values)) != len(values)
    ):
        raise ValueError("Expected nonempty, unique role or strategy names")
    return values


def build_overview(results_root: Path) -> dict:
    """Validate recorded bindings and quality; do not load models, indexes, or sources."""
    try:
        return _build_overview(results_root)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Malformed saved suite evidence") from exc


def _matches_settings(actual: object, expected: object) -> bool:
    # Recorded configurations add resolved defaults to the explicitly frozen inputs.
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and _matches_settings(actual[key], value)
            for key, value in expected.items()
        )
    return actual == expected


def _build_overview(results_root: Path) -> dict:
    plan = json.loads((results_root / "plan.json").read_text(encoding="utf-8"))
    suite = json.loads((results_root / "suite-results.json").read_text(encoding="utf-8"))
    if stable_id({k: v for k, v in plan.items() if k != "plan_digest"}) != plan["plan_digest"]:
        raise ValueError("Frozen plan digest mismatch")
    if (
        plan["schema_version"] != 1
        or suite["schema_version"] != 1
        or suite["complete"] is not True
        or suite["plan_digest"] != plan["plan_digest"]
        or type(plan["review_complete"]) is not bool
        or suite["review_complete"] is not plan["review_complete"]
        or suite["result_status"] != plan["result_status"]
        or plan["result_status"]
        != ("reviewed_labels" if plan["review_complete"] else "provisional")
        or type(plan["primary_k"]) is not int
        or plan["primary_k"] < 1
    ):
        raise ValueError("Suite completion, status, or plan binding mismatch")
    roles, names = _names(plan["roles"]), _names(plan["strategy_order"])
    members = {member["role"]: member for member in plan["members"]}
    if len(members) != len(plan["members"]) or set(members) != set(roles):
        raise ValueError("Plan members do not match roles")
    expected = {(role, name) for role in roles for name in names}
    workers = {(row["role"], row["name"]): row for row in suite["runs"]}
    if len(workers) != len(suite["runs"]) or set(workers) != expected:
        raise ValueError("Recorded workers do not match the complete strategy matrix")
    run_root = results_root / "runs"
    if {p.name for p in run_root.iterdir() if p.is_dir()} != set(roles):
        raise ValueError("Saved run directories do not match roles")
    datasets, rows = [], []
    for role in roles:
        member = members[role]
        repositories = {repo["id"]: repo["snapshot_id"] for repo in member["repositories"]}
        if not repositories or len(repositories) != len(member["repositories"]):
            raise ValueError("Plan repositories must be nonempty and unique")
        if type(member["query_count"]) is not int or member["query_count"] < 1:
            raise ValueError("Plan query count must be a positive integer")
        if {p.name for p in (run_root / role).iterdir() if p.is_dir()} != set(names):
            raise ValueError("Saved run directories do not match the strategy matrix")
        recorded = load_runs([run_root / role / name for name in names])
        for name, run in zip(names, recorded, strict=True):
            summary, worker = run.summary, workers[(role, name)]
            settings = plan["strategy_settings"][name]
            needs_encoder = settings["strategy"] in {"dense", "hybrid", "symbol"} or (
                settings["strategy"] == "structure"
                and settings["structure"]["seed_strategy"] != "bm25"
            )
            if (
                run.name != name
                or not _matches_settings(
                    summary["config"],
                    {key: value for key, value in settings.items() if key != "schema_version"},
                )
                or (
                    needs_encoder
                    and not _matches_settings(summary["config"].get("encoder"), plan["model"])
                )
                or plan["primary_k"] not in summary["config"]["ks"]
                or summary["benchmark"]["digest"] != member["benchmark_digest"]
                or summary["benchmark"]["id"] != member["benchmark_id"]
                or summary["benchmark"]["annotation_status"] != member["annotation_status"]
                or len(run.queries) != member["query_count"]
                or {q["repository"] for q in run.queries.values()} != set(repositories)
                or {r: index["snapshot_id"] for r, index in summary["indexes"].items()}
                != repositories
                or worker["kind"] != "experiment"
                or worker["details"]["quality_fingerprint"] != summary["quality_fingerprint"]
            ):
                raise ValueError(f"Recorded run does not match frozen plan/worker: {role}/{name}")
            latency = {key: summary["overall"]["latency_ms"][key] for key in ("p50", "p95")}
            if any(
                type(v) not in (int, float) or not math.isfinite(v) or v < 0
                for v in latency.values()
            ):
                raise ValueError("Recorded latency must be finite and nonnegative")
            metrics = summary["overall"]["metrics"][str(plan["primary_k"])]
            rows.append(
                {
                    "role": role,
                    "name": name,
                    "strategy": summary["config"]["strategy"],
                    "unit": summary["config"]["unit"],
                    "query_count": len(run.queries),
                    "metrics": {metric: metrics[metric] for metric in METRICS},
                    "recorded_latency_ms": latency,
                    "quality_fingerprint": summary["quality_fingerprint"],
                }
            )
        datasets.append(
            {
                "role": role,
                "benchmark_id": member["benchmark_id"],
                "benchmark_digest": member["benchmark_digest"],
                "annotation_status": member["annotation_status"],
                "query_count": member["query_count"],
                "snapshots": repositories,
            }
        )
    return {
        "schema_version": 1,
        "plan_digest": plan["plan_digest"],
        "result_status": plan["result_status"],
        "review_complete": plan["review_complete"],
        "primary_k": plan["primary_k"],
        "scope": {
            "roles": len(roles),
            "strategies_per_role": len(names),
            "validated_runs": len(rows),
            "queries": sum(d["query_count"] for d in datasets),
            "repositories": len({r for d in datasets for r in d["snapshots"]}),
        },
        "validation": (
            "Frozen matrix, plan/run/worker bindings, saved quality fingerprints and aggregates."
        ),
        "latency_scope": LATENCY_SCOPE,
        "datasets": datasets,
        "runs": rows,
    }


def render_overview(summary: dict) -> str:
    k, scope = summary["primary_k"], summary["scope"]
    lines = [
        "# Saved Retrieval Evidence Overview",
        "",
        f"Result status: **{summary['result_status']}**; independent review complete: "
        f"**{str(summary['review_complete']).lower()}**.",
        f"Frozen plan: `{summary['plan_digest']}`.",
        "",
        f"Validated {scope['validated_runs']} saved runs across {scope['roles']} separate roles, "
        f"{scope['queries']} queries, and {scope['repositories']} repositories.",
        "This report reads saved evidence only; it does not rerun retrieval or call an LLM.",
        "",
        "Quality fingerprints and aggregates are validated against saved rankings and "
        "per-query metrics, with plan, configuration, snapshot, and worker bindings checked.",
        LATENCY_SCOPE,
    ]
    for dataset in summary["datasets"]:
        role = dataset["role"]
        lines.extend(
            [
                "",
                f"## {role}",
                "",
                f"{dataset['query_count']} queries; {len(dataset['snapshots'])} repositories. "
                f"Annotation status: **{dataset['annotation_status']}**.",
                "",
                f"| Strategy | Unit | Recall@{k} | Precision@{k} | MRR@{k} | NDCG@{k} | "
                "Recorded p50 ms | Recorded p95 ms |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in summary["runs"]:
            if row["role"] != role:
                continue
            cells = [
                "N/A" if row["metrics"][metric] is None else f"{row['metrics'][metric]:.4f}"
                for metric in METRICS
            ]
            latency = row["recorded_latency_ms"]
            lines.append(
                f"| {row['name']} | {row['unit']} | "
                + " | ".join(cells)
                + f" | {latency['p50']:.2f} | {latency['p95']:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "Known-label quality uses query-macro means over answerable questions; unjudged "
            "candidates score zero. Provisional labels and incomplete judgments require "
            "independent review before reviewed-quality claims.",
            "",
            "Dataset roles are reported separately. The public adaptation uses full-repository "
            "symbol retrieval, not original RepoQA scoring. Exposed test outcomes cannot support "
            "further tuning while remaining an untouched test set.",
            "",
            "Recorded timing reflects separate runs on an interactive host and excludes startup "
            "and offline construction. It does not establish production latency or reranking "
            "overhead. No LLM correctness, citation-support, or significance claim is made here.",
            "",
        ]
    )
    return "\n".join(lines)


def write_overview(summary: dict, output: Path, *, check: bool = False) -> None:
    """Write a new directory atomically, or check existing files without modifying them."""
    expected = {
        "summary.json": json.dumps(summary, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        "report.md": render_overview(summary),
    }
    if check:
        for name, content in expected.items():
            path = output / name
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise ValueError(f"Saved overview is missing or stale: {path}")
        return
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Overview output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-overview-", dir=output.parent) as temporary:
        for name, content in expected.items():
            (Path(temporary) / name).write_text(content, encoding="utf-8", newline="\n")
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Overview output was created concurrently: {output}")
        os.rename(temporary, output)
