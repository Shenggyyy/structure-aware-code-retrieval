# Retrieval Evaluation

Run: `structure-import`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `85bb4cfdd7a08fbebba5baa427524510eb5b5c6cf04e7799c99d4b2c4654f459`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 0.5000 |
| 5 | 0.1700 | 0.7000 | 0.6217 | 0.5971 | 0.1750 |
| 10 | 0.1025 | 0.8208 | 0.6369 | 0.6430 | 0.1050 |
| 20 | 0.0625 | 0.9292 | 0.6409 | 0.6769 | 0.0638 |

Warm retrieval: p50 39.221 ms; p95 58.106 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 751.5 | 20.1 | 107.7 |
| 5 | 3570.8 | 92.3 | 503.2 |
| 10 | 7222.2 | 184.2 | 1003.0 |
| 20 | 14404.8 | 370.7 | 1990.9 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 2.65, 'expanded_symbols': 1.975, 'edge_cap_seeds': 0}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1500 | 0.1167 | 0.1500 | 0.1500 | 0.1500 |
| 5 | 0.1400 | 0.6083 | 0.3933 | 0.4206 | 0.1400 |
| 10 | 0.0950 | 0.8000 | 0.4239 | 0.4911 | 0.0950 |
| 20 | 0.0600 | 0.9083 | 0.4284 | 0.5291 | 0.0600 |

Warm retrieval: p50 46.848 ms; p95 133.687 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.8000 | 0.6667 | 0.8000 | 0.7667 | 0.8500 |
| 5 | 0.2000 | 0.7917 | 0.8500 | 0.7737 | 0.2100 |
| 10 | 0.1100 | 0.8417 | 0.8500 | 0.7949 | 0.1150 |
| 20 | 0.0650 | 0.9500 | 0.8533 | 0.8246 | 0.0675 |

Warm retrieval: p50 27.075 ms; p95 31.056 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5625 | 0.5000 | 0.5625 | 0.5208 | 0.5625 |
| 5 | 0.2125 | 0.9375 | 0.7104 | 0.7471 | 0.2125 |
| 10 | 0.1063 | 0.9375 | 0.7104 | 0.7471 | 0.1063 |
| 20 | 0.0594 | 1.0000 | 0.7161 | 0.7681 | 0.0594 |

Warm retrieval: p50 36.398 ms; p95 53.100 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.2083 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1750 | 0.3750 | 0.6875 | 0.4261 | 0.1750 |
| 10 | 0.1375 | 0.6042 | 0.7014 | 0.5216 | 0.1375 |
| 20 | 0.1062 | 0.8958 | 0.7014 | 0.6177 | 0.1062 |

Warm retrieval: p50 35.880 ms; p95 57.767 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.5000 |
| 5 | 0.1000 | 0.5000 | 0.4375 | 0.4539 | 0.1250 |
| 10 | 0.0750 | 0.7500 | 0.4792 | 0.5429 | 0.0875 |
| 20 | 0.0375 | 0.7500 | 0.4792 | 0.5429 | 0.0438 |

Warm retrieval: p50 35.838 ms; p95 48.410 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.5625 | 0.6116 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.5833 | 0.6561 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.5917 | 0.6874 | 0.0500 |

Warm retrieval: p50 43.923 ms; p95 107.823 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
