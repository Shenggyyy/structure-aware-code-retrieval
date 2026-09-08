# Retrieval Evaluation

Run: `structure-no-import`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `e70c7642c56540c02288dbfe1e89ecae1c02bc26db52bda778548f21d33a019d`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2167 | 0.1708 | 0.2167 | 0.2167 | 0.2167 |
| 5 | 0.1700 | 0.6528 | 0.4217 | 0.4578 | 0.1700 |
| 10 | 0.1067 | 0.7917 | 0.4370 | 0.5080 | 0.1067 |
| 20 | 0.0608 | 0.9014 | 0.4429 | 0.5376 | 0.0608 |

Warm retrieval: p50 48.858 ms; p95 348.029 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 993.2 | 26.5 | 137.7 |
| 5 | 4669.7 | 126.1 | 647.0 |
| 10 | 8842.3 | 241.6 | 1229.2 |
| 20 | 16878.0 | 461.0 | 2366.4 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 32.50833333333333, 'expanded_symbols': 12.333333333333334, 'edge_cap_seeds': 0.08333333333333333}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3056 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.2000 | 0.7500 | 0.5410 | 0.5728 | 0.2000 |
| 10 | 0.1208 | 0.8750 | 0.5511 | 0.6214 | 0.1208 |
| 20 | 0.0646 | 0.9375 | 0.5546 | 0.6393 | 0.0646 |

Warm retrieval: p50 48.643 ms; p95 111.905 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2083 | 0.1458 | 0.2083 | 0.2083 | 0.2083 |
| 5 | 0.1250 | 0.4375 | 0.3264 | 0.3384 | 0.1250 |
| 10 | 0.0833 | 0.6042 | 0.3468 | 0.3930 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.3593 | 0.4396 | 0.0521 |

Warm retrieval: p50 242.185 ms; p95 366.734 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1667 | 0.1181 | 0.1667 | 0.1667 | 0.1667 |
| 5 | 0.1667 | 0.6736 | 0.4215 | 0.4488 | 0.1667 |
| 10 | 0.1167 | 0.8681 | 0.4378 | 0.5188 | 0.1167 |
| 20 | 0.0667 | 0.9583 | 0.4413 | 0.5431 | 0.0667 |

Warm retrieval: p50 22.400 ms; p95 28.665 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0833 | 0.0625 | 0.0833 | 0.0833 | 0.0833 |
| 5 | 0.1500 | 0.6250 | 0.3486 | 0.3975 | 0.1500 |
| 10 | 0.1000 | 0.7708 | 0.3713 | 0.4525 | 0.1000 |
| 20 | 0.0583 | 0.8958 | 0.3789 | 0.4886 | 0.0583 |

Warm retrieval: p50 61.801 ms; p95 178.435 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2222 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.2083 | 0.7778 | 0.4708 | 0.5315 | 0.2083 |
| 10 | 0.1125 | 0.8403 | 0.4778 | 0.5544 | 0.1125 |
| 20 | 0.0625 | 0.9236 | 0.4804 | 0.5776 | 0.0625 |

Warm retrieval: p50 22.239 ms; p95 29.540 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1300 | 0.6500 | 0.3733 | 0.4427 | 0.1300 |
| 10 | 0.0800 | 0.8000 | 0.3936 | 0.4915 | 0.0800 |
| 20 | 0.0462 | 0.9250 | 0.4030 | 0.5239 | 0.0462 |

Warm retrieval: p50 47.717 ms; p95 346.444 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.1125 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.2250 | 0.5333 | 0.4600 | 0.4126 | 0.2250 |
| 10 | 0.1575 | 0.7500 | 0.4800 | 0.4995 | 0.1575 |
| 20 | 0.0900 | 0.8542 | 0.4813 | 0.5303 | 0.0900 |

Warm retrieval: p50 48.643 ms; p95 348.068 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1800 | 0.9000 | 0.4933 | 0.5963 | 0.1800 |
| 10 | 0.0950 | 0.9500 | 0.4989 | 0.6114 | 0.0950 |
| 20 | 0.0500 | 1.0000 | 0.5020 | 0.6236 | 0.0500 |

Warm retrieval: p50 46.539 ms; p95 325.133 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1300 | 0.6500 | 0.3700 | 0.4399 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.3756 | 0.4549 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.3869 | 0.4940 | 0.0425 |

Warm retrieval: p50 51.455 ms; p95 362.626 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
