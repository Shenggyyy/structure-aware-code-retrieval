# Retrieval Evaluation

Run: `structure-none`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `c7335a38926235df83754b0c34d7409f83bfb8ddd8d6f0c88b1771ec95ef4e53`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 0.5000 |
| 5 | 0.1750 | 0.7250 | 0.6279 | 0.6079 | 0.1800 |
| 10 | 0.1025 | 0.8208 | 0.6394 | 0.6450 | 0.1050 |
| 20 | 0.0625 | 0.9292 | 0.6433 | 0.6789 | 0.0638 |

Warm retrieval: p50 34.770 ms; p95 47.287 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 759.9 | 20.1 | 108.9 |
| 5 | 3560.0 | 92.5 | 497.6 |
| 10 | 7189.6 | 182.8 | 997.4 |
| 20 | 14332.0 | 367.1 | 1979.8 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1500 | 0.1167 | 0.1500 | 0.1500 | 0.1500 |
| 5 | 0.1500 | 0.6583 | 0.4058 | 0.4421 | 0.1500 |
| 10 | 0.0950 | 0.8000 | 0.4288 | 0.4952 | 0.0950 |
| 20 | 0.0600 | 0.9083 | 0.4333 | 0.5333 | 0.0600 |

Warm retrieval: p50 39.891 ms; p95 52.967 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.8000 | 0.6667 | 0.8000 | 0.7667 | 0.8500 |
| 5 | 0.2000 | 0.7917 | 0.8500 | 0.7737 | 0.2100 |
| 10 | 0.1100 | 0.8417 | 0.8500 | 0.7949 | 0.1150 |
| 20 | 0.0650 | 0.9500 | 0.8533 | 0.8246 | 0.0675 |

Warm retrieval: p50 24.173 ms; p95 31.633 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5625 | 0.5000 | 0.5625 | 0.5208 | 0.5625 |
| 5 | 0.2125 | 0.9375 | 0.7135 | 0.7498 | 0.2125 |
| 10 | 0.1063 | 0.9375 | 0.7135 | 0.7498 | 0.1063 |
| 20 | 0.0594 | 1.0000 | 0.7192 | 0.7709 | 0.0594 |

Warm retrieval: p50 33.185 ms; p95 46.390 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.2083 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1750 | 0.3750 | 0.6875 | 0.4261 | 0.1750 |
| 10 | 0.1375 | 0.6042 | 0.7031 | 0.5227 | 0.1375 |
| 20 | 0.1062 | 0.8958 | 0.7031 | 0.6188 | 0.1062 |

Warm retrieval: p50 35.498 ms; p95 48.637 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.5000 |
| 5 | 0.1250 | 0.6250 | 0.4625 | 0.5022 | 0.1500 |
| 10 | 0.0750 | 0.7500 | 0.4833 | 0.5467 | 0.0875 |
| 20 | 0.0375 | 0.7500 | 0.4833 | 0.5467 | 0.0438 |

Warm retrieval: p50 31.706 ms; p95 42.385 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.5625 | 0.6116 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.5833 | 0.6561 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.5917 | 0.6874 | 0.0500 |

Warm retrieval: p50 34.230 ms; p95 44.326 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
