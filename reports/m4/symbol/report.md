# Retrieval Evaluation

Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `symbol`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `d816554dd625fa6fec7d78b8b345173092da4a8d389cb52dc6343e3dcf940158`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4250 | 0.3542 | 0.4250 | 0.4250 | 0.4500 |
| 5 | 0.1500 | 0.6333 | 0.5408 | 0.5292 | 0.1550 |
| 10 | 0.0975 | 0.7917 | 0.5610 | 0.5823 | 0.1000 |
| 20 | 0.0600 | 0.9333 | 0.5670 | 0.6202 | 0.0613 |

Warm retrieval: p50 66.779 ms; p95 110.317 ms.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2167 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.1500 | 0.6250 | 0.4367 | 0.4683 | 0.1500 |
| 10 | 0.1000 | 0.8167 | 0.4643 | 0.5311 | 0.1000 |
| 20 | 0.0600 | 0.9333 | 0.4668 | 0.5642 | 0.0600 |

Warm retrieval: p50 89.887 ms; p95 113.980 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6000 | 0.4917 | 0.6000 | 0.6000 | 0.6500 |
| 5 | 0.1500 | 0.6417 | 0.6450 | 0.5900 | 0.1600 |
| 10 | 0.0950 | 0.7667 | 0.6577 | 0.6336 | 0.1000 |
| 20 | 0.0600 | 0.9333 | 0.6672 | 0.6763 | 0.0625 |

Warm retrieval: p50 48.788 ms; p95 55.601 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.1125 | 0.5625 | 0.3583 | 0.4085 | 0.1125 |
| 10 | 0.0875 | 0.7812 | 0.3929 | 0.4847 | 0.0875 |
| 20 | 0.0563 | 0.9688 | 0.4039 | 0.5333 | 0.0563 |

Warm retrieval: p50 67.583 ms; p95 100.672 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6250 | 0.2708 | 0.6250 | 0.6250 | 0.6250 |
| 5 | 0.2000 | 0.4167 | 0.7125 | 0.4650 | 0.2000 |
| 10 | 0.1250 | 0.5208 | 0.7125 | 0.4993 | 0.1250 |
| 20 | 0.0875 | 0.7292 | 0.7125 | 0.5608 | 0.0875 |

Warm retrieval: p50 80.753 ms; p95 111.374 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.5000 |
| 5 | 0.1500 | 0.7500 | 0.5250 | 0.5811 | 0.1750 |
| 10 | 0.1000 | 1.0000 | 0.5567 | 0.6604 | 0.1125 |
| 20 | 0.0500 | 1.0000 | 0.5567 | 0.6604 | 0.0563 |

Warm retrieval: p50 64.746 ms; p95 90.792 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6250 | 0.6250 | 0.6250 | 0.6250 | 0.6250 |
| 5 | 0.1750 | 0.8750 | 0.7500 | 0.7827 | 0.1750 |
| 10 | 0.0875 | 0.8750 | 0.7500 | 0.7827 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.7578 | 0.8133 | 0.0500 |

Warm retrieval: p50 67.140 ms; p95 98.215 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
