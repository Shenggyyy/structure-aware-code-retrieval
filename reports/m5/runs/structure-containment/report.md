# Retrieval Evaluation

Run: `structure-containment`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `bf0c52df7c6d4d4aa4623a1415c6e0cbd21ce7e2c2b530affec3e8fff4a50c33`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 0.5000 |
| 5 | 0.1650 | 0.6750 | 0.6133 | 0.5846 | 0.1700 |
| 10 | 0.1050 | 0.8333 | 0.6307 | 0.6417 | 0.1075 |
| 20 | 0.0638 | 0.9417 | 0.6346 | 0.6748 | 0.0650 |

Warm retrieval: p50 42.159 ms; p95 60.989 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 732.9 | 19.5 | 104.2 |
| 5 | 3495.4 | 89.3 | 492.2 |
| 10 | 7378.7 | 188.6 | 1021.8 |
| 20 | 14189.3 | 364.1 | 1959.7 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 10.8, 'expanded_symbols': 5.925, 'edge_cap_seeds': 0}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1500 | 0.1167 | 0.1500 | 0.1500 | 0.1500 |
| 5 | 0.1300 | 0.5583 | 0.3767 | 0.3956 | 0.1300 |
| 10 | 0.1000 | 0.8250 | 0.4114 | 0.4886 | 0.1000 |
| 20 | 0.0625 | 0.9333 | 0.4159 | 0.5252 | 0.0625 |

Warm retrieval: p50 47.129 ms; p95 67.225 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.8000 | 0.6667 | 0.8000 | 0.7667 | 0.8500 |
| 5 | 0.2000 | 0.7917 | 0.8500 | 0.7737 | 0.2100 |
| 10 | 0.1100 | 0.8417 | 0.8500 | 0.7949 | 0.1150 |
| 20 | 0.0650 | 0.9500 | 0.8533 | 0.8243 | 0.0675 |

Warm retrieval: p50 28.174 ms; p95 35.922 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5625 | 0.5000 | 0.5625 | 0.5208 | 0.5625 |
| 5 | 0.2000 | 0.8750 | 0.6896 | 0.7158 | 0.2000 |
| 10 | 0.1063 | 0.9375 | 0.7000 | 0.7381 | 0.1063 |
| 20 | 0.0594 | 1.0000 | 0.7057 | 0.7592 | 0.0594 |

Warm retrieval: p50 41.834 ms; p95 56.627 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.2083 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1750 | 0.3750 | 0.6875 | 0.4261 | 0.1750 |
| 10 | 0.1500 | 0.6667 | 0.7014 | 0.5436 | 0.1500 |
| 20 | 0.1125 | 0.9583 | 0.7014 | 0.6354 | 0.1125 |

Warm retrieval: p50 36.664 ms; p95 127.903 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.5000 |
| 5 | 0.1000 | 0.5000 | 0.4375 | 0.4539 | 0.1250 |
| 10 | 0.0750 | 0.7500 | 0.4740 | 0.5378 | 0.0875 |
| 20 | 0.0375 | 0.7500 | 0.4740 | 0.5378 | 0.0438 |

Warm retrieval: p50 38.909 ms; p95 53.494 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.5625 | 0.6116 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.5781 | 0.6510 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.5865 | 0.6823 | 0.0500 |

Warm retrieval: p50 43.438 ms; p95 49.729 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
