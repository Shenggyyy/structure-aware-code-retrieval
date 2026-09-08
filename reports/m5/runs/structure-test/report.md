# Retrieval Evaluation

Run: `structure-test`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `334d8020d2e9d6becb9619191730b28d4fbb66e59e0d2390fb26b5028cbb39a2`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4000 | 0.3167 | 0.4000 | 0.3833 | 0.4250 |
| 5 | 0.1800 | 0.7500 | 0.5842 | 0.5812 | 0.1850 |
| 10 | 0.1025 | 0.8208 | 0.5909 | 0.6082 | 0.1050 |
| 20 | 0.0625 | 0.9292 | 0.5948 | 0.6420 | 0.0638 |

Warm retrieval: p50 40.199 ms; p95 54.103 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 723.4 | 19.1 | 103.1 |
| 5 | 3556.5 | 93.8 | 497.9 |
| 10 | 7277.7 | 185.6 | 1008.8 |
| 20 | 14348.6 | 367.3 | 1981.8 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 9.125, 'expanded_symbols': 3.65, 'edge_cap_seeds': 0.025}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1500 | 0.1167 | 0.1500 | 0.1500 | 0.1500 |
| 5 | 0.1600 | 0.7083 | 0.4100 | 0.4571 | 0.1600 |
| 10 | 0.0950 | 0.8000 | 0.4234 | 0.4913 | 0.0950 |
| 20 | 0.0600 | 0.9083 | 0.4279 | 0.5293 | 0.0600 |

Warm retrieval: p50 46.707 ms; p95 65.411 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6500 | 0.5167 | 0.6500 | 0.6167 | 0.7000 |
| 5 | 0.2000 | 0.7917 | 0.7583 | 0.7053 | 0.2100 |
| 10 | 0.1100 | 0.8417 | 0.7583 | 0.7250 | 0.1150 |
| 20 | 0.0650 | 0.9500 | 0.7617 | 0.7547 | 0.0675 |

Warm retrieval: p50 28.761 ms; p95 36.040 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4375 | 0.3750 | 0.4375 | 0.3958 | 0.4375 |
| 5 | 0.2125 | 0.9375 | 0.6406 | 0.6955 | 0.2125 |
| 10 | 0.1063 | 0.9375 | 0.6406 | 0.6955 | 0.1063 |
| 20 | 0.0594 | 1.0000 | 0.6463 | 0.7166 | 0.0594 |

Warm retrieval: p50 37.303 ms; p95 54.026 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.2083 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1750 | 0.3750 | 0.6875 | 0.4261 | 0.1750 |
| 10 | 0.1375 | 0.6042 | 0.7031 | 0.5193 | 0.1375 |
| 20 | 0.1062 | 0.8958 | 0.7031 | 0.6151 | 0.1062 |

Warm retrieval: p50 38.740 ms; p95 51.307 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.3896 | 0.4772 | 0.1750 |
| 10 | 0.0750 | 0.7500 | 0.3896 | 0.4772 | 0.0875 |
| 20 | 0.0375 | 0.7500 | 0.3896 | 0.4772 | 0.0438 |

Warm retrieval: p50 39.228 ms; p95 60.357 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.5625 | 0.6116 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.5804 | 0.6533 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.5887 | 0.6845 | 0.0500 |

Warm retrieval: p50 43.855 ms; p95 117.486 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
