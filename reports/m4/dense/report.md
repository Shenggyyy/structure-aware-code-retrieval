# Retrieval Evaluation

Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `dense`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `cc5d920f0a1b22e313021fa04910a77bb3a2a706838d3283ddd32c3b8bc47869`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4000 | 0.3417 | 0.4000 | 0.4000 | 0.4250 |
| 5 | 0.1600 | 0.6583 | 0.5542 | 0.5494 | 0.1650 |
| 10 | 0.1000 | 0.7833 | 0.5738 | 0.5968 | 0.1025 |
| 20 | 0.0550 | 0.8542 | 0.5776 | 0.6151 | 0.0563 |

Warm retrieval: p50 20.867 ms; p95 29.185 ms.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.1667 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1400 | 0.5750 | 0.4042 | 0.4263 | 0.1400 |
| 10 | 0.0900 | 0.7000 | 0.4280 | 0.4737 | 0.0900 |
| 20 | 0.0500 | 0.8000 | 0.4356 | 0.4999 | 0.0500 |

Warm retrieval: p50 25.002 ms; p95 32.821 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6000 | 0.5167 | 0.6000 | 0.6000 | 0.6500 |
| 5 | 0.1800 | 0.7417 | 0.7042 | 0.6725 | 0.1900 |
| 10 | 0.1100 | 0.8667 | 0.7196 | 0.7198 | 0.1150 |
| 20 | 0.0600 | 0.9083 | 0.7196 | 0.7302 | 0.0625 |

Warm retrieval: p50 15.041 ms; p95 18.440 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4375 | 0.4062 | 0.4375 | 0.4375 | 0.4375 |
| 5 | 0.1625 | 0.7188 | 0.5729 | 0.5996 | 0.1625 |
| 10 | 0.1125 | 0.9375 | 0.6012 | 0.6796 | 0.1125 |
| 20 | 0.0594 | 1.0000 | 0.6051 | 0.6949 | 0.0594 |

Warm retrieval: p50 22.692 ms; p95 28.699 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1458 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1750 | 0.3542 | 0.5625 | 0.3747 | 0.1750 |
| 10 | 0.1250 | 0.5417 | 0.6042 | 0.4515 | 0.1250 |
| 20 | 0.0750 | 0.6458 | 0.6042 | 0.4774 | 0.0750 |

Warm retrieval: p50 19.477 ms; p95 28.357 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.3750 |
| 5 | 0.1000 | 0.5000 | 0.3125 | 0.3577 | 0.1250 |
| 10 | 0.0500 | 0.5000 | 0.3125 | 0.3577 | 0.0625 |
| 20 | 0.0312 | 0.6250 | 0.3239 | 0.3925 | 0.0375 |

Warm retrieval: p50 18.724 ms; p95 32.503 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.2000 | 1.0000 | 0.7500 | 0.8155 | 0.2000 |
| 10 | 0.1000 | 1.0000 | 0.7500 | 0.8155 | 0.1000 |
| 20 | 0.0500 | 1.0000 | 0.7500 | 0.8155 | 0.0500 |

Warm retrieval: p50 19.868 ms; p95 27.221 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
