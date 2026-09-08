# Retrieval Evaluation

Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `bm25`; evaluation unit: `file`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `b8c697958b829f0acd366a4f73602b89b5f10a89415eed65d95161e40397b249`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6750 | 0.6000 | 0.6750 | 0.6750 | 0.6750 |
| 5 | 0.2350 | 0.9875 | 0.8187 | 0.8589 | 0.2400 |
| 10 | 0.1200 | 1.0000 | 0.8187 | 0.8640 | 0.1225 |
| 20 | 0.0600 | 1.0000 | 0.8187 | 0.8640 | 0.0613 |

Warm retrieval: p50 3.914 ms; p95 7.380 ms.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5500 | 0.5000 | 0.5500 | 0.5500 | 0.5500 |
| 5 | 0.2400 | 1.0000 | 0.7583 | 0.8275 | 0.2400 |
| 10 | 0.1200 | 1.0000 | 0.7583 | 0.8275 | 0.1200 |
| 20 | 0.0600 | 1.0000 | 0.7583 | 0.8275 | 0.0600 |

Warm retrieval: p50 5.136 ms; p95 8.191 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.8000 | 0.7000 | 0.8000 | 0.8000 | 0.8000 |
| 5 | 0.2300 | 0.9750 | 0.8792 | 0.8903 | 0.2400 |
| 10 | 0.1200 | 1.0000 | 0.8792 | 0.9005 | 0.1250 |
| 20 | 0.0600 | 1.0000 | 0.8792 | 0.9005 | 0.0625 |

Warm retrieval: p50 2.727 ms; p95 4.202 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6875 | 0.6875 | 0.6875 | 0.6875 | 0.6875 |
| 5 | 0.2000 | 1.0000 | 0.8281 | 0.8721 | 0.2000 |
| 10 | 0.1000 | 1.0000 | 0.8281 | 0.8721 | 0.1000 |
| 20 | 0.0500 | 1.0000 | 0.8281 | 0.8721 | 0.0500 |

Warm retrieval: p50 3.717 ms; p95 6.073 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.7500 | 0.3750 | 0.7500 | 0.7500 | 0.7500 |
| 5 | 0.3750 | 0.9375 | 0.8542 | 0.8597 | 0.3750 |
| 10 | 0.2000 | 1.0000 | 0.8542 | 0.8852 | 0.2000 |
| 20 | 0.1000 | 1.0000 | 0.8542 | 0.8852 | 0.1000 |

Warm retrieval: p50 4.000 ms; p95 8.449 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6250 | 0.6250 | 0.6250 | 0.6250 | 0.6250 |
| 5 | 0.2000 | 1.0000 | 0.8125 | 0.8616 | 0.2250 |
| 10 | 0.1000 | 1.0000 | 0.8125 | 0.8616 | 0.1125 |
| 20 | 0.0500 | 1.0000 | 0.8125 | 0.8616 | 0.0563 |

Warm retrieval: p50 3.656 ms; p95 6.858 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6250 | 0.6250 | 0.6250 | 0.6250 | 0.6250 |
| 5 | 0.2000 | 1.0000 | 0.7708 | 0.8289 | 0.2000 |
| 10 | 0.1000 | 1.0000 | 0.7708 | 0.8289 | 0.1000 |
| 20 | 0.0500 | 1.0000 | 0.7708 | 0.8289 | 0.0500 |

Warm retrieval: p50 5.035 ms; p95 7.491 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
