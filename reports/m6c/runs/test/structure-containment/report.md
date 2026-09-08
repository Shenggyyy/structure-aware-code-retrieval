# Retrieval Evaluation

Run: `structure-containment`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `1a86a43d83be59eafb4b69abf954e9f9ba2f2d6d8ce93829761d6e8b6a8f2aba`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4083 | 0.3486 | 0.4083 | 0.4083 | 0.4083 |
| 5 | 0.1767 | 0.6847 | 0.5450 | 0.5525 | 0.1767 |
| 10 | 0.1075 | 0.8042 | 0.5591 | 0.5958 | 0.1075 |
| 20 | 0.0604 | 0.8972 | 0.5638 | 0.6215 | 0.0604 |

Warm retrieval: p50 49.089 ms; p95 335.564 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1045.3 | 27.7 | 145.5 |
| 5 | 4644.0 | 125.3 | 642.9 |
| 10 | 8795.8 | 239.6 | 1216.5 |
| 20 | 16728.6 | 457.3 | 2347.3 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 10.891666666666667, 'expanded_symbols': 6.6, 'edge_cap_seeds': 0.008333333333333333}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4583 | 0.4167 | 0.4583 | 0.4583 | 0.4583 |
| 5 | 0.2000 | 0.7778 | 0.6139 | 0.6304 | 0.2000 |
| 10 | 0.1125 | 0.8333 | 0.6185 | 0.6541 | 0.1125 |
| 20 | 0.0646 | 0.9375 | 0.6220 | 0.6858 | 0.0646 |

Warm retrieval: p50 48.859 ms; p95 116.666 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2917 | 0.2292 | 0.2917 | 0.2917 | 0.2917 |
| 5 | 0.1167 | 0.4167 | 0.3764 | 0.3563 | 0.1167 |
| 10 | 0.0833 | 0.6042 | 0.3981 | 0.4186 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.4112 | 0.4659 | 0.0521 |

Warm retrieval: p50 241.179 ms; p95 363.497 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3056 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1667 | 0.6736 | 0.5257 | 0.5219 | 0.1667 |
| 10 | 0.1125 | 0.8472 | 0.5457 | 0.5864 | 0.1125 |
| 20 | 0.0625 | 0.9236 | 0.5491 | 0.6058 | 0.0625 |

Warm retrieval: p50 23.536 ms; p95 31.944 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2917 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1833 | 0.7292 | 0.4979 | 0.5433 | 0.1833 |
| 10 | 0.1042 | 0.8125 | 0.5160 | 0.5744 | 0.1042 |
| 20 | 0.0583 | 0.8958 | 0.5198 | 0.5990 | 0.0583 |

Warm retrieval: p50 63.784 ms; p95 185.542 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5833 | 0.5000 | 0.5833 | 0.5833 | 0.5833 |
| 5 | 0.2167 | 0.8264 | 0.7111 | 0.7105 | 0.2167 |
| 10 | 0.1250 | 0.9236 | 0.7171 | 0.7457 | 0.1250 |
| 20 | 0.0646 | 0.9375 | 0.7171 | 0.7508 | 0.0646 |

Warm retrieval: p50 20.086 ms; p95 24.771 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.5017 | 0.5630 | 0.1500 |
| 10 | 0.0825 | 0.8250 | 0.5102 | 0.5858 | 0.0825 |
| 20 | 0.0462 | 0.9250 | 0.5176 | 0.6116 | 0.0462 |

Warm retrieval: p50 47.876 ms; p95 338.195 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.1708 | 0.3500 | 0.3500 | 0.3500 |
| 5 | 0.2300 | 0.5542 | 0.5317 | 0.4554 | 0.2300 |
| 10 | 0.1550 | 0.7375 | 0.5518 | 0.5302 | 0.1550 |
| 20 | 0.0888 | 0.8417 | 0.5531 | 0.5618 | 0.0888 |

Warm retrieval: p50 51.362 ms; p95 342.646 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.7000 |
| 5 | 0.1700 | 0.8500 | 0.7667 | 0.7881 | 0.1700 |
| 10 | 0.1000 | 1.0000 | 0.7881 | 0.8381 | 0.1000 |
| 20 | 0.0500 | 1.0000 | 0.7881 | 0.8381 | 0.0500 |

Warm retrieval: p50 46.021 ms; p95 315.474 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3000 | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| 5 | 0.1300 | 0.6500 | 0.4367 | 0.4899 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.4422 | 0.5049 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.4536 | 0.5440 | 0.0425 |

Warm retrieval: p50 50.972 ms; p95 366.555 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
