# Retrieval Evaluation

Run: `structure-full`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `783bfd46f3650ad3d84ecec1904560b6e168936c6f5434577851ab0537c115d3`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1792 | 0.2250 | 0.2250 | 0.2250 |
| 5 | 0.1683 | 0.6444 | 0.4242 | 0.4577 | 0.1683 |
| 10 | 0.1067 | 0.7917 | 0.4409 | 0.5109 | 0.1067 |
| 20 | 0.0608 | 0.9014 | 0.4468 | 0.5405 | 0.0608 |

Warm retrieval: p50 54.519 ms; p95 391.982 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 994.0 | 26.6 | 137.8 |
| 5 | 4639.6 | 125.5 | 644.0 |
| 10 | 8869.0 | 242.7 | 1232.3 |
| 20 | 16879.1 | 461.3 | 2368.0 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 36.625, 'expanded_symbols': 12.858333333333333, 'edge_cap_seeds': 0.08333333333333333}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3056 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.2000 | 0.7500 | 0.5410 | 0.5728 | 0.2000 |
| 10 | 0.1208 | 0.8750 | 0.5511 | 0.6214 | 0.1208 |
| 20 | 0.0646 | 0.9375 | 0.5546 | 0.6393 | 0.0646 |

Warm retrieval: p50 53.845 ms; p95 129.030 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2083 | 0.1458 | 0.2083 | 0.2083 | 0.2083 |
| 5 | 0.1250 | 0.4375 | 0.3264 | 0.3384 | 0.1250 |
| 10 | 0.0833 | 0.6042 | 0.3468 | 0.3930 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.3593 | 0.4396 | 0.0521 |

Warm retrieval: p50 279.921 ms; p95 438.529 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1667 | 0.1181 | 0.1667 | 0.1667 | 0.1667 |
| 5 | 0.1667 | 0.6736 | 0.4215 | 0.4488 | 0.1667 |
| 10 | 0.1167 | 0.8681 | 0.4378 | 0.5183 | 0.1167 |
| 20 | 0.0667 | 0.9583 | 0.4413 | 0.5427 | 0.0667 |

Warm retrieval: p50 36.089 ms; p95 45.848 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0833 | 0.0625 | 0.0833 | 0.0833 | 0.0833 |
| 5 | 0.1417 | 0.5833 | 0.3403 | 0.3814 | 0.1417 |
| 10 | 0.1000 | 0.7708 | 0.3700 | 0.4513 | 0.1000 |
| 20 | 0.0583 | 0.8958 | 0.3775 | 0.4873 | 0.0583 |

Warm retrieval: p50 69.539 ms; p95 206.439 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2917 | 0.2639 | 0.2917 | 0.2917 | 0.2917 |
| 5 | 0.2083 | 0.7778 | 0.4917 | 0.5469 | 0.2083 |
| 10 | 0.1125 | 0.8403 | 0.4986 | 0.5703 | 0.1125 |
| 20 | 0.0625 | 0.9236 | 0.5012 | 0.5934 | 0.0625 |

Warm retrieval: p50 33.401 ms; p95 44.147 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1250 | 0.6250 | 0.3683 | 0.4330 | 0.1250 |
| 10 | 0.0800 | 0.8000 | 0.3928 | 0.4907 | 0.0800 |
| 20 | 0.0462 | 0.9250 | 0.4021 | 0.5231 | 0.0462 |

Warm retrieval: p50 51.054 ms; p95 390.486 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.1125 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.2250 | 0.5333 | 0.4600 | 0.4126 | 0.2250 |
| 10 | 0.1575 | 0.7500 | 0.4800 | 0.4995 | 0.1575 |
| 20 | 0.0900 | 0.8542 | 0.4813 | 0.5303 | 0.0900 |

Warm retrieval: p50 57.289 ms; p95 416.864 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.1800 | 0.9000 | 0.5183 | 0.6148 | 0.1800 |
| 10 | 0.0950 | 0.9500 | 0.5239 | 0.6298 | 0.0950 |
| 20 | 0.0500 | 1.0000 | 0.5270 | 0.6421 | 0.0500 |

Warm retrieval: p50 54.995 ms; p95 372.692 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1300 | 0.6500 | 0.3700 | 0.4399 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.3756 | 0.4549 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.3869 | 0.4940 | 0.0425 |

Warm retrieval: p50 56.792 ms; p95 385.454 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
