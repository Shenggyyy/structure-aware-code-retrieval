"""Compare compatible recorded runs without executing retrieval or changing labels."""

import json
import os
import tempfile
from pathlib import Path

from structure_aware_retrieval.evaluation.metrics import QUALITY_METRICS
from structure_aware_retrieval.evaluation.reporting import _dump


def compare_runs(runs: list[Path], output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Comparison output already exists: {output}")
    if len(runs) < 2:
        raise ValueError("Comparison requires at least two runs; the first is the baseline")
    summaries = [json.loads((run / "summary.json").read_text(encoding="utf-8")) for run in runs]
    queries = [
        {
            row["query_id"]: row
            for row in (
                json.loads(line)
                for line in (run / "per_query.jsonl").read_text(encoding="utf-8").splitlines()
            )
        }
        for run in runs
    ]

    def contract(summary: dict) -> tuple:
        return (
            summary["benchmark"],
            summary["config"]["unit"],
            summary["config"]["ks"],
            {repo: item["snapshot_id"] for repo, item in summary["indexes"].items()},
        )

    strategies = [summary["config"]["strategy"] for summary in summaries]
    if len(set(strategies)) != len(strategies):
        raise ValueError("Each compared run must have a distinct strategy")
    if any(contract(summary) != contract(summaries[0]) for summary in summaries[1:]):
        raise ValueError("Runs must share benchmark, unit, K values and indexed snapshots")
    if any(set(rows) != set(queries[0]) for rows in queries[1:]):
        raise ValueError("Runs must contain the same query IDs")
    result = {
        "baseline": strategies[0],
        "benchmark": summaries[0]["benchmark"],
        "unit": summaries[0]["config"]["unit"],
        "runs": [],
        "paired": {},
    }
    for strategy, summary, rows in zip(strategies, summaries, queries, strict=True):
        result["runs"].append(
            {
                "strategy": strategy,
                "quality_fingerprint": summary["quality_fingerprint"],
                "overall": summary["overall"],
            }
        )
        paired = {}
        for k in summary["config"]["ks"]:
            paired[str(k)] = {}
            for metric in QUALITY_METRICS:
                differences = {}
                for query_id, row in rows.items():
                    before = queries[0][query_id]["metrics"][str(k)][metric]
                    after = row["metrics"][str(k)][metric]
                    if (before is None) != (after is None):
                        raise ValueError("Inconsistent no-answer metrics between runs")
                    if before is not None:
                        differences[query_id] = after - before
                paired[str(k)][metric] = {
                    "wins": sum(value > 1e-12 for value in differences.values()),
                    "ties": sum(abs(value) <= 1e-12 for value in differences.values()),
                    "losses": sum(value < -1e-12 for value in differences.values()),
                    "query_deltas": differences,
                }
        result["paired"][strategy] = paired
    lines = [
        "# Retrieval Strategy Comparison",
        "",
        f"Baseline: `{strategies[0]}`; unit: `{result['unit']}`; "
        f"annotation status: **{result['benchmark']['annotation_status']}**.",
        "",
        "Known-label development scores; unjudged candidates score zero. "
        "Paired wins/losses are descriptive, not significance tests.",
        "",
        "| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for run in result["runs"]:
        for k, values in run["overall"]["metrics"].items():
            cells = [
                "N/A" if values[name] is None else f"{values[name]:.4f}" for name in QUALITY_METRICS
            ]
            latency = run["overall"]["latency_ms"]
            lines.append(
                f"| {run['strategy']} | {k} | "
                + " | ".join(cells)
                + f" | {latency['p50']:.3f} | {latency['p95']:.3f} |"
            )
    lines.extend(
        [
            "",
            "See `comparison.json` for per-query paired differences and quality fingerprints.",
            "Latency comes from separate recorded runs and depends on hardware/load; "
            "it includes query encoding and fusion, but excludes startup and offline embedding.",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-comparison-", dir=output.parent) as temporary:
        _dump(Path(temporary) / "comparison.json", result)
        (Path(temporary) / "report.md").write_text("\n".join(lines), encoding="utf-8")
        if output.exists():
            raise FileExistsError(f"Comparison output was created concurrently: {output}")
        os.rename(temporary, output)
    return result
