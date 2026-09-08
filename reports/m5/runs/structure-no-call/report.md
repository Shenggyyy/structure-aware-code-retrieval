# Retrieval Evaluation

Run: `structure-no-call`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `e873fe4189bbdae3c5f7fd4b6ff630e4782f3aad709b8e3bc67ca8315a679c31`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4000 | 0.3167 | 0.4000 | 0.3833 | 0.4250 |
| 5 | 0.1700 | 0.7000 | 0.5708 | 0.5590 | 0.1750 |
| 10 | 0.1050 | 0.8333 | 0.5834 | 0.6060 | 0.1075 |
| 20 | 0.0625 | 0.9292 | 0.5873 | 0.6354 | 0.0638 |

Warm retrieval: p50 40.773 ms; p95 57.096 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 696.4 | 18.5 | 98.4 |
| 5 | 3581.8 | 92.4 | 504.2 |
| 10 | 7493.9 | 191.2 | 1038.5 |
| 20 | 14390.4 | 371.0 | 1990.7 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 21.975, 'expanded_symbols': 9.3, 'edge_cap_seeds': 0.05}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1500 | 0.1167 | 0.1500 | 0.1500 | 0.1500 |
| 5 | 0.1400 | 0.6083 | 0.3833 | 0.4128 | 0.1400 |
| 10 | 0.1000 | 0.8250 | 0.4085 | 0.4869 | 0.1000 |
| 20 | 0.0600 | 0.9083 | 0.4130 | 0.5164 | 0.0600 |

Warm retrieval: p50 46.975 ms; p95 137.672 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6500 | 0.5167 | 0.6500 | 0.6167 | 0.7000 |
| 5 | 0.2000 | 0.7917 | 0.7583 | 0.7053 | 0.2100 |
| 10 | 0.1100 | 0.8417 | 0.7583 | 0.7250 | 0.1150 |
| 20 | 0.0650 | 0.9500 | 0.7617 | 0.7544 | 0.0675 |

Warm retrieval: p50 29.134 ms; p95 35.923 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4375 | 0.3750 | 0.4375 | 0.3958 | 0.4375 |
| 5 | 0.2000 | 0.8750 | 0.6198 | 0.6643 | 0.2000 |
| 10 | 0.1063 | 0.9375 | 0.6302 | 0.6865 | 0.1063 |
| 20 | 0.0594 | 1.0000 | 0.6359 | 0.7076 | 0.0594 |

Warm retrieval: p50 38.376 ms; p95 53.890 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.2083 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1750 | 0.3750 | 0.6875 | 0.4261 | 0.1750 |
| 10 | 0.1500 | 0.6667 | 0.7000 | 0.5393 | 0.1500 |
| 20 | 0.1062 | 0.8958 | 0.7000 | 0.6131 | 0.1062 |

Warm retrieval: p50 40.844 ms; p95 61.019 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.3750 |
| 5 | 0.1250 | 0.6250 | 0.3646 | 0.4288 | 0.1500 |
| 10 | 0.0750 | 0.7500 | 0.3802 | 0.4683 | 0.0875 |
| 20 | 0.0375 | 0.7500 | 0.3802 | 0.4683 | 0.0438 |

Warm retrieval: p50 41.395 ms; p95 49.885 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.5625 | 0.6116 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.5764 | 0.6492 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.5847 | 0.6805 | 0.0500 |

Warm retrieval: p50 37.291 ms; p95 56.199 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
