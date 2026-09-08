"""Validate the identity and recorded quality of existing experiment artifacts."""

import hashlib
import json
import math
import platform
import statistics
from dataclasses import dataclass
from pathlib import Path

from structure_aware_retrieval.evaluation.metrics import QUALITY_METRICS
from structure_aware_retrieval.models import stable_id


def analysis_provenance() -> dict:
    package = Path(__file__).resolve().parents[1]
    sources = [
        (
            path.relative_to(package).as_posix(),
            hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
        )
        for path in sorted(package.rglob("*.py"))
    ]
    return {"python": platform.python_version(), "normalized_source_hash": stable_id(sources)}


def read_jsonl(path: Path) -> list[dict]:
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: expected JSON objects")
    return rows


def keyed(rows: list[dict], key: str) -> dict[str, dict]:
    values = [row[key] for row in rows]
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"Invalid {key}")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {key}")
    return dict(zip(values, rows, strict=True))


@dataclass
class RecordedRun:
    summary: dict
    queries: dict[str, dict]
    rankings: dict[str, dict]

    @property
    def name(self) -> str:
        return self.summary["config"].get("name", self.summary["config"]["strategy"])


def load_runs(paths: list[Path]) -> list[RecordedRun]:
    if not paths:
        raise ValueError("At least one recorded run is required")
    runs = [
        RecordedRun(
            json.loads((path / "summary.json").read_text(encoding="utf-8")),
            keyed(read_jsonl(path / "per_query.jsonl"), "query_id"),
            keyed(read_jsonl(path / "rankings.jsonl"), "query_id"),
        )
        for path in paths
    ]

    def contract(run: RecordedRun) -> tuple:
        return (
            run.summary["benchmark"],
            run.summary["config"]["unit"],
            run.summary["config"]["ks"],
            {repo: item["snapshot_id"] for repo, item in run.summary["indexes"].items()},
        )

    if len({run.name for run in runs}) != len(runs):
        raise ValueError("Each compared run must have a distinct strategy")
    if any(contract(run) != contract(runs[0]) for run in runs[1:]):
        raise ValueError("Runs must share benchmark, unit, K values and indexed snapshots")
    for run in runs:
        if not run.queries or set(run.queries) != set(runs[0].queries):
            raise ValueError("Runs must contain the same query IDs")
        if set(run.rankings) != set(run.queries):
            raise ValueError("Rankings and metrics must contain the same query IDs")
        for query_id, row in run.queries.items():
            before = runs[0].queries[query_id]
            if any(row[k] != before[k] for k in ("repository", "category", "answerable")):
                raise ValueError("Inconsistent query metadata between runs")
            if run.rankings[query_id]["repository"] != row["repository"]:
                raise ValueError("Ranking repository does not match query metadata")
            if run.rankings[query_id]["query"] != runs[0].rankings[query_id]["query"]:
                raise ValueError("Inconsistent query text between runs")
            if type(row["answerable"]) is not bool:
                raise ValueError("Recorded answerability must be boolean")
            for k in run.summary["config"]["ks"]:
                for metric in QUALITY_METRICS:
                    value = row["metrics"][str(k)][metric]
                    if not row["answerable"]:
                        if value is not None:
                            raise ValueError("No-answer quality metrics must be null")
                    elif (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                        or not 0 <= value <= 1
                    ):
                        raise ValueError("Answerable quality metrics must be finite in [0, 1]")
        quality = [
            {
                k: v
                for k, v in row.items()
                if k not in {"latency_ms", "context_cost", "retrieval_work"}
            }
            for row in sorted(run.queries.values(), key=lambda row: row["query_id"])
        ]
        # The runner hashes integer K keys before JSON converts them to strings.
        # Restore numeric ordering (1, 5, 10), not lexical ordering (1, 10, 5).
        for row in quality:
            row["metrics"] = {int(k): values for k, values in row["metrics"].items()}
        fingerprint = stable_id(
            run.summary["benchmark"]["digest"],
            run.summary["config"]["unit"],
            run.summary["config"]["ks"],
            quality,
            sorted(run.rankings.values(), key=lambda row: row["query_id"]),
        )
        if fingerprint != run.summary["quality_fingerprint"]:
            raise ValueError("Recorded quality fingerprint mismatch")
        _validate_aggregates(run)
    return runs


def _validate_aggregates(run: RecordedRun) -> None:
    """Do not print stale summary quality beside correctly paired per-query scores."""
    rows = list(run.queries.values())
    groups = [(run.summary["overall"], rows)]
    for field in ("repository", "category"):
        expected = {row[field] for row in rows}
        summaries = run.summary[f"by_{field}"]
        if set(summaries) != expected:
            raise ValueError("Summary groups do not match recorded queries")
        groups.extend(
            (summaries[key], [row for row in rows if row[field] == key]) for key in expected
        )
    for summary, members in groups:
        answerable = [row for row in members if row["answerable"]]
        if summary["query_count"] != len(members) or summary["answerable_count"] != len(answerable):
            raise ValueError("Summary counts do not match recorded queries")
        for k in run.summary["config"]["ks"]:
            for metric in QUALITY_METRICS:
                expected = (
                    statistics.mean(row["metrics"][str(k)][metric] for row in answerable)
                    if answerable
                    else None
                )
                actual = summary["metrics"][str(k)][metric]
                if expected is None:
                    valid = actual is None
                else:
                    valid = (
                        type(actual) in (float, int)
                        and math.isfinite(actual)
                        and abs(actual - expected) <= 1e-12
                    )
                if not valid:
                    raise ValueError("Summary quality does not match recorded queries")
