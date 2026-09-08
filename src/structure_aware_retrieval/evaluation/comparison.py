"""Compare compatible recorded runs without executing retrieval or changing labels."""

import os
import tempfile
from pathlib import Path

from structure_aware_retrieval.evaluation.metrics import QUALITY_METRICS
from structure_aware_retrieval.evaluation.recorded import analysis_provenance, load_runs
from structure_aware_retrieval.evaluation.reporting import _dump
from structure_aware_retrieval.evaluation.uncertainty import (
    MIN_REPOSITORIES,
    paired_statistics,
    validate_bootstrap,
)


def compare_runs(
    runs: list[Path], output: Path, *, bootstrap_samples: int = 2000, bootstrap_seed: int = 0
) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Comparison output already exists: {output}")
    if len(runs) < 2:
        raise ValueError("Comparison requires at least two runs; the first is the baseline")
    validate_bootstrap(bootstrap_samples, bootstrap_seed)
    recorded = load_runs(runs)
    summaries = [run.summary for run in recorded]
    queries = [run.queries for run in recorded]
    strategies = [run.name for run in recorded]
    repositories = {qid: row["repository"] for qid, row in queries[0].items()}
    result = {
        "baseline": strategies[0],
        "benchmark": summaries[0]["benchmark"],
        "unit": summaries[0]["config"]["unit"],
        "analysis_runtime": analysis_provenance(),
        "runs": [],
        "paired": {},
        "uncertainty": {
            "method": "paired_repository_cluster_percentile_bootstrap",
            "estimand": "query_macro_mean_difference",
            "confidence_level": 0.95,
            "samples": bootstrap_samples,
            "seed": bootstrap_seed,
            "minimum_repositories": MIN_REPOSITORIES,
            "multiplicity_adjusted": False,
        },
    }
    for strategy, summary, rows in zip(strategies, summaries, queries, strict=True):
        result["runs"].append(
            {
                "strategy": strategy,
                "retrieval_strategy": summary["config"]["strategy"],
                "structure": summary["config"].get("structure"),
                "quality_fingerprint": summary["quality_fingerprint"],
                "recorded_runtime": summary["runtime"],
                "overall": summary["overall"],
                "by_repository": summary["by_repository"],
                "by_category": summary["by_category"],
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
                    **paired_statistics(
                        differences, repositories, samples=bootstrap_samples, seed=bootstrap_seed
                    ),
                    "by_category": {
                        category: paired_statistics(
                            {
                                qid: value
                                for qid, value in differences.items()
                                if rows[qid]["category"] == category
                            },
                            repositories,
                            samples=bootstrap_samples,
                            seed=bootstrap_seed,
                        )
                        for category in sorted({row["category"] for row in rows.values()})
                    },
                }
        result["paired"][strategy] = paired
    lines = [
        "# Retrieval Strategy Comparison",
        "",
        f"Baseline: `{strategies[0]}`; unit: `{result['unit']}`; "
        f"annotation status: **{result['benchmark']['annotation_status']}**.",
        "",
        "Known-label scores; unjudged candidates score zero. "
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
            "## Paired differences and uncertainty",
            "",
            "Differences are candidate minus baseline over answerable queries. Resampling "
            "keeps all queries in a selected repository together and preserves pairing. "
            "Query-macro and equal-repository means are different estimands.",
            f"95% percentile intervals use {bootstrap_samples} draws, seed {bootstrap_seed}. "
            f"Intervals are withheld below {MIN_REPOSITORIES} contributing repositories "
            "(a reporting policy, not a sufficiency guarantee). Few or correlated repositories "
            "and incomplete labels limit inference; intervals do not correct label bias. "
            "No multiple-comparison correction or significance claim is made.",
            "",
            "| Strategy | K | Metric | Query mean delta | Repo mean delta | 95% interval | "
            "Repos | W/T/L |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for strategy in strategies[1:]:
        for k, metrics in result["paired"][strategy].items():
            for metric, values in metrics.items():
                interval = values["interval"]
                interval_text = (
                    f"[{interval['low']:.4f}, {interval['high']:.4f}]"
                    if interval is not None
                    else "withheld: insufficient repositories"
                )
                delta = values["mean_delta"]
                repo_delta = values["repository_macro_delta"]
                lines.append(
                    f"| {strategy} | {k} | {metric} | "
                    + (f"{delta:+.4f} | {repo_delta:+.4f}" if delta is not None else "N/A | N/A")
                    + f" | {interval_text} | {values['repository_count']} | "
                    + f"{values['wins']}/{values['ties']}/{values['losses']} |"
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
