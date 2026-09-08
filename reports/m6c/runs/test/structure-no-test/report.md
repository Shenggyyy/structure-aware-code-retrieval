# Retrieval Evaluation

Run: `structure-no-test`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `a8515a7094e16bc5a5308824b368cd6708be552f81c47c1678367285fc5c74b1`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1792 | 0.2250 | 0.2250 | 0.2250 |
| 5 | 0.1750 | 0.6639 | 0.4300 | 0.4696 | 0.1750 |
| 10 | 0.1067 | 0.7917 | 0.4453 | 0.5157 | 0.1067 |
| 20 | 0.0613 | 0.9042 | 0.4515 | 0.5469 | 0.0613 |

Warm retrieval: p50 54.630 ms; p95 389.861 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1006.5 | 26.7 | 139.8 |
| 5 | 4627.9 | 125.2 | 643.1 |
| 10 | 8923.9 | 243.8 | 1241.2 |
| 20 | 16921.2 | 462.9 | 2375.6 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 26.791666666666668, 'expanded_symbols': 11.808333333333334, 'edge_cap_seeds': 0.016666666666666666}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3472 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.2083 | 0.7708 | 0.5722 | 0.6064 | 0.2083 |
| 10 | 0.1208 | 0.8750 | 0.5823 | 0.6453 | 0.1208 |
| 20 | 0.0646 | 0.9375 | 0.5858 | 0.6633 | 0.0646 |

Warm retrieval: p50 54.462 ms; p95 120.384 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2083 | 0.1458 | 0.2083 | 0.2083 | 0.2083 |
| 5 | 0.1250 | 0.4375 | 0.3264 | 0.3384 | 0.1250 |
| 10 | 0.0833 | 0.6042 | 0.3468 | 0.3930 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.3593 | 0.4396 | 0.0521 |

Warm retrieval: p50 284.246 ms; p95 416.378 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1667 | 0.1181 | 0.1667 | 0.1667 | 0.1667 |
| 5 | 0.1750 | 0.6875 | 0.4319 | 0.4610 | 0.1750 |
| 10 | 0.1083 | 0.8056 | 0.4441 | 0.5075 | 0.1083 |
| 20 | 0.0667 | 0.9583 | 0.4514 | 0.5518 | 0.0667 |

Warm retrieval: p50 25.921 ms; p95 32.767 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0833 | 0.0625 | 0.0833 | 0.0833 | 0.0833 |
| 5 | 0.1417 | 0.5833 | 0.3472 | 0.3869 | 0.1417 |
| 10 | 0.1000 | 0.7708 | 0.3769 | 0.4567 | 0.1000 |
| 20 | 0.0583 | 0.8958 | 0.3845 | 0.4928 | 0.0583 |

Warm retrieval: p50 70.897 ms; p95 195.438 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2222 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.2250 | 0.8403 | 0.4722 | 0.5553 | 0.2250 |
| 10 | 0.1208 | 0.9028 | 0.4764 | 0.5759 | 0.1208 |
| 20 | 0.0646 | 0.9375 | 0.4764 | 0.5873 | 0.0646 |

Warm retrieval: p50 24.666 ms; p95 35.072 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.2250 | 0.2250 | 0.2250 | 0.2250 |
| 5 | 0.1300 | 0.6500 | 0.3942 | 0.4585 | 0.1300 |
| 10 | 0.0775 | 0.7750 | 0.4120 | 0.5000 | 0.0775 |
| 20 | 0.0462 | 0.9250 | 0.4236 | 0.5394 | 0.0462 |

Warm retrieval: p50 53.037 ms; p95 400.522 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.1125 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.2400 | 0.5667 | 0.4558 | 0.4256 | 0.2400 |
| 10 | 0.1575 | 0.7500 | 0.4759 | 0.5001 | 0.1575 |
| 20 | 0.0912 | 0.8625 | 0.4771 | 0.5350 | 0.0912 |

Warm retrieval: p50 53.730 ms; p95 390.021 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1800 | 0.9000 | 0.5017 | 0.6029 | 0.1800 |
| 10 | 0.1000 | 1.0000 | 0.5122 | 0.6324 | 0.1000 |
| 20 | 0.0500 | 1.0000 | 0.5122 | 0.6324 | 0.0500 |

Warm retrieval: p50 53.844 ms; p95 356.518 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1300 | 0.6500 | 0.3783 | 0.4464 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.3839 | 0.4615 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.3952 | 0.5005 | 0.0425 |

Warm retrieval: p50 59.454 ms; p95 400.122 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
