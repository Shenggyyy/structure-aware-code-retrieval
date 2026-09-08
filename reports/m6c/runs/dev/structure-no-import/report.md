# Retrieval Evaluation

Run: `structure-no-import`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `c0b67fb6b3f2a5288e437e1818f45d4358d65d30e4515f6899be10ffc1ff955b`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 0.2500 |
| 5 | 0.1950 | 0.7333 | 0.4483 | 0.4994 | 0.2000 |
| 10 | 0.1200 | 0.8875 | 0.4651 | 0.5548 | 0.1225 |
| 20 | 0.0650 | 0.9625 | 0.4687 | 0.5761 | 0.0663 |

Warm retrieval: p50 43.954 ms; p95 71.673 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 906.9 | 23.1 | 127.3 |
| 5 | 3817.8 | 98.8 | 535.5 |
| 10 | 7570.6 | 195.0 | 1048.8 |
| 20 | 14789.4 | 380.7 | 2039.2 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 27.975, 'expanded_symbols': 12.45, 'edge_cap_seeds': 0.05}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.0667 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.1700 | 0.6667 | 0.3500 | 0.4162 | 0.1700 |
| 10 | 0.1150 | 0.8750 | 0.3751 | 0.4836 | 0.1150 |
| 20 | 0.0625 | 0.9250 | 0.3751 | 0.5004 | 0.0625 |

Warm retrieval: p50 50.774 ms; p95 147.395 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.2750 | 0.3500 | 0.3500 | 0.4000 |
| 5 | 0.2200 | 0.8000 | 0.5467 | 0.5827 | 0.2300 |
| 10 | 0.1250 | 0.9000 | 0.5550 | 0.6261 | 0.1300 |
| 20 | 0.0675 | 1.0000 | 0.5623 | 0.6518 | 0.0700 |

Warm retrieval: p50 29.483 ms; p95 35.135 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1875 | 0.1562 | 0.1875 | 0.1875 | 0.1875 |
| 5 | 0.1875 | 0.8125 | 0.4260 | 0.4996 | 0.1875 |
| 10 | 0.1125 | 0.9688 | 0.4469 | 0.5625 | 0.1125 |
| 20 | 0.0594 | 1.0000 | 0.4469 | 0.5728 | 0.0594 |

Warm retrieval: p50 40.846 ms; p95 64.919 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1667 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.3250 | 0.6667 | 0.6042 | 0.5639 | 0.3250 |
| 10 | 0.2125 | 0.8750 | 0.6181 | 0.6397 | 0.2125 |
| 20 | 0.1125 | 0.9375 | 0.6181 | 0.6611 | 0.1125 |

Warm retrieval: p50 40.540 ms; p95 79.454 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.3750 |
| 5 | 0.1250 | 0.6250 | 0.3479 | 0.4147 | 0.1500 |
| 10 | 0.0750 | 0.7500 | 0.3635 | 0.4541 | 0.0875 |
| 20 | 0.0438 | 0.8750 | 0.3740 | 0.4879 | 0.0500 |

Warm retrieval: p50 43.954 ms; p95 57.237 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1250 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| 5 | 0.1500 | 0.7500 | 0.4375 | 0.5193 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.4500 | 0.5555 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.4578 | 0.5860 | 0.0500 |

Warm retrieval: p50 38.656 ms; p95 57.677 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
