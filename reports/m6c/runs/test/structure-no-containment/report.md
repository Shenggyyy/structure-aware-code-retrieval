# Retrieval Evaluation

Run: `structure-no-containment`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `e7fcccab732ffc12d2e95d02a97d388fa594e3122e661f7ae6090132940d74c2`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1750 | 0.2250 | 0.2250 | 0.2250 |
| 5 | 0.1667 | 0.6403 | 0.4221 | 0.4549 | 0.1667 |
| 10 | 0.1058 | 0.7875 | 0.4403 | 0.5082 | 0.1058 |
| 20 | 0.0604 | 0.8972 | 0.4462 | 0.5382 | 0.0604 |

Warm retrieval: p50 52.245 ms; p95 362.418 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 986.1 | 26.3 | 136.3 |
| 5 | 4629.4 | 125.5 | 642.4 |
| 10 | 8878.0 | 242.7 | 1233.1 |
| 20 | 16886.8 | 461.6 | 2370.6 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 26.916666666666668, 'expanded_symbols': 9.516666666666667, 'edge_cap_seeds': 0.058333333333333334}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3056 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1917 | 0.7292 | 0.5306 | 0.5618 | 0.1917 |
| 10 | 0.1167 | 0.8542 | 0.5476 | 0.6104 | 0.1167 |
| 20 | 0.0646 | 0.9375 | 0.5514 | 0.6358 | 0.0646 |

Warm retrieval: p50 52.005 ms; p95 115.136 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.1667 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.1250 | 0.4375 | 0.3472 | 0.3511 | 0.1250 |
| 10 | 0.0833 | 0.6042 | 0.3681 | 0.4061 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.3806 | 0.4527 | 0.0521 |

Warm retrieval: p50 262.529 ms; p95 392.833 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1667 | 0.1181 | 0.1667 | 0.1667 | 0.1667 |
| 5 | 0.1667 | 0.6736 | 0.4215 | 0.4488 | 0.1667 |
| 10 | 0.1167 | 0.8681 | 0.4378 | 0.5188 | 0.1167 |
| 20 | 0.0646 | 0.9375 | 0.4413 | 0.5374 | 0.0646 |

Warm retrieval: p50 22.217 ms; p95 28.652 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0833 | 0.0625 | 0.0833 | 0.0833 | 0.0833 |
| 5 | 0.1417 | 0.5833 | 0.3403 | 0.3814 | 0.1417 |
| 10 | 0.1000 | 0.7708 | 0.3700 | 0.4513 | 0.1000 |
| 20 | 0.0583 | 0.8958 | 0.3775 | 0.4873 | 0.0583 |

Warm retrieval: p50 68.298 ms; p95 190.291 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2222 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.2083 | 0.7778 | 0.4708 | 0.5315 | 0.2083 |
| 10 | 0.1125 | 0.8403 | 0.4778 | 0.5544 | 0.1125 |
| 20 | 0.0625 | 0.9236 | 0.4804 | 0.5777 | 0.0625 |

Warm retrieval: p50 21.683 ms; p95 25.961 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1250 | 0.6250 | 0.3683 | 0.4330 | 0.1250 |
| 10 | 0.0800 | 0.8000 | 0.3928 | 0.4907 | 0.0800 |
| 20 | 0.0462 | 0.9250 | 0.4023 | 0.5233 | 0.0462 |

Warm retrieval: p50 51.351 ms; p95 374.986 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2750 | 0.1250 | 0.2750 | 0.2750 | 0.2750 |
| 5 | 0.2200 | 0.5208 | 0.4662 | 0.4137 | 0.2200 |
| 10 | 0.1550 | 0.7375 | 0.4907 | 0.5007 | 0.1550 |
| 20 | 0.0888 | 0.8417 | 0.4920 | 0.5325 | 0.0888 |

Warm retrieval: p50 53.572 ms; p95 351.345 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1800 | 0.9000 | 0.4933 | 0.5963 | 0.1800 |
| 10 | 0.0950 | 0.9500 | 0.4989 | 0.6114 | 0.0950 |
| 20 | 0.0500 | 1.0000 | 0.5020 | 0.6236 | 0.0500 |

Warm retrieval: p50 50.672 ms; p95 346.307 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1300 | 0.6500 | 0.3700 | 0.4399 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.3756 | 0.4549 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.3869 | 0.4940 | 0.0425 |

Warm retrieval: p50 55.422 ms; p95 362.828 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
