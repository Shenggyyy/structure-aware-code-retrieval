"""Machine-readable artifacts and a human-readable report from one set of results."""

import csv
import json
from pathlib import Path

from structure_aware_retrieval.evaluation.metrics import QUALITY_METRICS


def _dump(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def write_report(directory: Path, summary: dict, queries: list[dict], rankings: list[dict]) -> None:
    _dump(directory / "summary.json", summary)
    for name, records in (("per_query.jsonl", queries), ("rankings.jsonl", rankings)):
        with (directory / name).open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=True, allow_nan=False) + "\n")
    with (directory / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "query_id",
            "repository",
            "category",
            "answerable",
            "k",
            *QUALITY_METRICS,
            "returned",
            "unjudged",
            "judged_fraction",
            "latency_p50_ms",
            "latency_p95_ms",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for query in queries:
            for k, values in query["metrics"].items():
                writer.writerow(
                    {
                        "query_id": query["query_id"],
                        "repository": query["repository"],
                        "category": query["category"],
                        "answerable": query["answerable"],
                        "k": k,
                        **values,
                        "latency_p50_ms": query["latency_ms"]["p50"],
                        "latency_p95_ms": query["latency_ms"]["p95"],
                    }
                )
    lines = [
        "# Retrieval Evaluation",
        "",
        f"Benchmark: `{summary['benchmark']['id']}` / `{summary['benchmark']['version']}`; "
        f"split: `{summary['benchmark']['split']}`.",
        f"Strategy: `{summary['config']['strategy']}`; "
        f"evaluation unit: `{summary['config']['unit']}`.",
        "",
        f"Annotation status: **{summary['benchmark']['annotation_status']}**.",
        "Unjudged results count as nonrelevant for scoring. Recall uses known positives only; "
        "these are not exhaustive relevance judgments.",
        "Provisional labels require independent human review before formal claims."
        if summary["benchmark"]["annotation_status"] == "provisional"
        else "Human-review status is declared by the benchmark's maintainers.",
        "",
        f"Quality fingerprint: `{summary['quality_fingerprint']}`.",
        "",
    ]

    def table(title: str, group: dict) -> None:
        lines.extend(
            [
                f"## {title}",
                "",
                f"Queries: {group['query_count']}; answerable: {group['answerable_count']}; "
                f"no-answer: {group['no_answer_count']}.",
                "",
                "| K | Precision | Recall | MRR | NDCG | Judged fraction |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for k, metrics in group["metrics"].items():
            values = [metrics[name] for name in (*QUALITY_METRICS, "judged_fraction")]
            cells = ["N/A" if value is None else f"{value:.4f}" for value in values]
            lines.append(f"| {k} | " + " | ".join(cells) + " |")
        lines.extend(
            [
                "",
                f"Warm retrieval: p50 {group['latency_ms']['p50']:.3f} ms; "
                f"p95 {group['latency_ms']['p95']:.3f} ms.",
                "",
            ]
        )

    table("Overall", summary["overall"])
    for key, value in summary["by_repository"].items():
        table(f"Repository: {key}", value)
    for key, value in summary["by_category"].items():
        table(f"Category: {key}", value)
    lines.extend(
        [
            "## Timing and reproduction",
            "",
            "Timing includes query preprocessing, scoring every chunk, result materialization, "
            "and deduplication to the selected unit. It excludes metric calculation, report "
            "writing, and one-time index/model loading.",
            "Index/model load timings, individual latency samples, runtime/code/config provenance, "
            "and source fingerprints are in `summary.json` and `per_query.jsonl`.",
            "Index load measurements are observed startup costs, not guaranteed cold disk-cache "
            "measurements. No OS cache flushing is performed.",
            "Rankings are stored up to the largest configured K after all matching chunks have "
            "been considered. Repeat runs should match the quality fingerprint; timing will vary.",
            "",
        ]
    )
    (directory / "report.md").write_text("\n".join(lines), encoding="utf-8")
