# Retrieval Evaluation

Run: `structure-import`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `526924a4dd046c14aed5e6e21d5b8310232935793b91a16997bb8534c12e7005`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3528 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.1767 | 0.6847 | 0.5497 | 0.5539 | 0.1767 |
| 10 | 0.1042 | 0.7861 | 0.5608 | 0.5903 | 0.1042 |
| 20 | 0.0600 | 0.8944 | 0.5672 | 0.6214 | 0.0600 |

Warm retrieval: p50 47.412 ms; p95 336.354 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1024.9 | 27.2 | 142.1 |
| 5 | 4607.8 | 124.8 | 639.1 |
| 10 | 8773.4 | 239.8 | 1220.4 |
| 20 | 16824.6 | 460.2 | 2362.3 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 5.241666666666666, 'expanded_symbols': 2.808333333333333, 'edge_cap_seeds': 0.008333333333333333}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4583 | 0.4167 | 0.4583 | 0.4583 | 0.4583 |
| 5 | 0.1917 | 0.7569 | 0.6083 | 0.6176 | 0.1917 |
| 10 | 0.1125 | 0.8333 | 0.6130 | 0.6499 | 0.1125 |
| 20 | 0.0646 | 0.9375 | 0.6168 | 0.6824 | 0.0646 |

Warm retrieval: p50 47.261 ms; p95 105.812 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2500 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1250 | 0.4375 | 0.4056 | 0.3789 | 0.1250 |
| 10 | 0.0833 | 0.6042 | 0.4208 | 0.4327 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.4340 | 0.4800 | 0.0521 |

Warm retrieval: p50 233.762 ms; p95 361.976 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3056 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1667 | 0.6736 | 0.5312 | 0.5248 | 0.1667 |
| 10 | 0.1000 | 0.7986 | 0.5488 | 0.5684 | 0.1000 |
| 20 | 0.0625 | 0.9236 | 0.5560 | 0.6073 | 0.0625 |

Warm retrieval: p50 21.828 ms; p95 25.856 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2917 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1833 | 0.7292 | 0.4924 | 0.5375 | 0.1833 |
| 10 | 0.1042 | 0.8125 | 0.5105 | 0.5685 | 0.1042 |
| 20 | 0.0583 | 0.8958 | 0.5143 | 0.5932 | 0.0583 |

Warm retrieval: p50 58.621 ms; p95 174.372 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5833 | 0.5000 | 0.5833 | 0.5833 | 0.5833 |
| 5 | 0.2167 | 0.8264 | 0.7111 | 0.7105 | 0.2167 |
| 10 | 0.1208 | 0.8819 | 0.7111 | 0.7322 | 0.1208 |
| 20 | 0.0625 | 0.9236 | 0.7149 | 0.7439 | 0.0625 |

Warm retrieval: p50 20.843 ms; p95 26.152 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.4983 | 0.5602 | 0.1500 |
| 10 | 0.0825 | 0.8250 | 0.5075 | 0.5836 | 0.0825 |
| 20 | 0.0462 | 0.9250 | 0.5150 | 0.6095 | 0.0462 |

Warm retrieval: p50 44.678 ms; p95 339.865 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1833 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.2300 | 0.5542 | 0.5492 | 0.4624 | 0.2300 |
| 10 | 0.1475 | 0.7083 | 0.5634 | 0.5243 | 0.1475 |
| 20 | 0.0875 | 0.8333 | 0.5671 | 0.5649 | 0.0875 |

Warm retrieval: p50 47.522 ms; p95 333.402 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.7000 |
| 5 | 0.1700 | 0.8500 | 0.7667 | 0.7881 | 0.1700 |
| 10 | 0.0950 | 0.9500 | 0.7810 | 0.8214 | 0.0950 |
| 20 | 0.0500 | 1.0000 | 0.7855 | 0.8354 | 0.0500 |

Warm retrieval: p50 46.565 ms; p95 316.210 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3000 | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| 5 | 0.1300 | 0.6500 | 0.4367 | 0.4899 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.4422 | 0.5049 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.4536 | 0.5440 | 0.0425 |

Warm retrieval: p50 51.994 ms; p95 341.666 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
