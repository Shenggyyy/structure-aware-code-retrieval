# Retrieval Evaluation

Run: `structure-symbol-seed`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `403da73a653e18c531b26ee1d4f97723f2561f849cea7e4f3e978421eff96e45`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2917 | 0.2514 | 0.2917 | 0.2917 | 0.2917 |
| 5 | 0.1517 | 0.6042 | 0.4326 | 0.4534 | 0.1517 |
| 10 | 0.1050 | 0.7972 | 0.4558 | 0.5234 | 0.1050 |
| 20 | 0.0596 | 0.8778 | 0.4612 | 0.5473 | 0.0596 |

Warm retrieval: p50 96.948 ms; p95 591.881 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 949.4 | 26.5 | 131.4 |
| 5 | 4061.3 | 113.1 | 561.6 |
| 10 | 7882.9 | 221.3 | 1103.2 |
| 20 | 14480.7 | 404.4 | 2036.5 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 40.925, 'expanded_symbols': 13.741666666666667, 'edge_cap_seeds': 0.10833333333333334}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3472 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.2000 | 0.7917 | 0.5771 | 0.5981 | 0.2000 |
| 10 | 0.1167 | 0.8750 | 0.5882 | 0.6312 | 0.1167 |
| 20 | 0.0646 | 0.9375 | 0.5882 | 0.6511 | 0.0646 |

Warm retrieval: p50 96.700 ms; p95 209.516 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2083 | 0.1667 | 0.2083 | 0.2083 | 0.2083 |
| 5 | 0.1417 | 0.5000 | 0.3604 | 0.3670 | 0.1417 |
| 10 | 0.0958 | 0.7083 | 0.3816 | 0.4352 | 0.0958 |
| 20 | 0.0521 | 0.7500 | 0.3816 | 0.4490 | 0.0521 |

Warm retrieval: p50 506.811 ms; p95 664.995 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1250 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| 5 | 0.1083 | 0.4653 | 0.2611 | 0.3056 | 0.1083 |
| 10 | 0.0833 | 0.6667 | 0.2931 | 0.3818 | 0.0833 |
| 20 | 0.0604 | 0.8819 | 0.3104 | 0.4430 | 0.0604 |

Warm retrieval: p50 42.150 ms; p95 49.304 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3750 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.1417 | 0.6042 | 0.4910 | 0.4993 | 0.1417 |
| 10 | 0.1083 | 0.8333 | 0.5191 | 0.5830 | 0.1083 |
| 20 | 0.0583 | 0.8958 | 0.5255 | 0.6009 | 0.0583 |

Warm retrieval: p50 130.127 ms; p95 243.966 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2917 | 0.2431 | 0.2917 | 0.2917 | 0.2917 |
| 5 | 0.1667 | 0.6597 | 0.4736 | 0.4973 | 0.1667 |
| 10 | 0.1208 | 0.9028 | 0.4971 | 0.5859 | 0.1208 |
| 20 | 0.0625 | 0.9236 | 0.5001 | 0.5925 | 0.0625 |

Warm retrieval: p50 40.522 ms; p95 48.826 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1300 | 0.6500 | 0.3508 | 0.4240 | 0.1300 |
| 10 | 0.0850 | 0.8500 | 0.3796 | 0.4908 | 0.0850 |
| 20 | 0.0450 | 0.9000 | 0.3830 | 0.5033 | 0.0450 |

Warm retrieval: p50 93.474 ms; p95 601.908 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1042 | 0.2250 | 0.2250 | 0.2250 |
| 5 | 0.1750 | 0.4125 | 0.3829 | 0.3258 | 0.1750 |
| 10 | 0.1450 | 0.6917 | 0.4104 | 0.4367 | 0.1450 |
| 20 | 0.0900 | 0.8583 | 0.4208 | 0.4888 | 0.0900 |

Warm retrieval: p50 99.582 ms; p95 594.532 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4000 | 0.4000 | 0.4000 | 0.4000 | 0.4000 |
| 5 | 0.1800 | 0.9000 | 0.5933 | 0.6701 | 0.1800 |
| 10 | 0.0950 | 0.9500 | 0.5989 | 0.6852 | 0.0950 |
| 20 | 0.0500 | 1.0000 | 0.6034 | 0.6991 | 0.0500 |

Warm retrieval: p50 87.587 ms; p95 498.790 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1200 | 0.6000 | 0.5350 | 0.5509 | 0.1200 |
| 10 | 0.0750 | 0.7500 | 0.5560 | 0.6004 | 0.0750 |
| 20 | 0.0375 | 0.7500 | 0.5560 | 0.6004 | 0.0375 |

Warm retrieval: p50 100.593 ms; p95 634.381 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
