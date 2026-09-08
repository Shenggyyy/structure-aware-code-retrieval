# Retrieval Evaluation

Run: `dense-seed`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `dense`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `c6de0cdd062f952bdc67152a8593c60d027254635ec4735b98ef42d96ba96ac8`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4333 | 0.3778 | 0.4333 | 0.4333 | 0.4333 |
| 5 | 0.1633 | 0.6403 | 0.5347 | 0.5340 | 0.1633 |
| 10 | 0.0958 | 0.7292 | 0.5480 | 0.5675 | 0.0958 |
| 20 | 0.0538 | 0.7986 | 0.5503 | 0.5871 | 0.0538 |

Warm retrieval: p50 32.418 ms; p95 171.720 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 749.4 | 21.7 | 102.5 |
| 5 | 3578.5 | 101.3 | 495.8 |
| 10 | 6579.7 | 186.3 | 917.0 |
| 20 | 12052.6 | 339.4 | 1694.0 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3333 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1333 | 0.5347 | 0.4528 | 0.4546 | 0.1333 |
| 10 | 0.1000 | 0.7500 | 0.4858 | 0.5364 | 0.1000 |
| 20 | 0.0563 | 0.8333 | 0.4890 | 0.5612 | 0.0563 |

Warm retrieval: p50 33.998 ms; p95 54.709 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2708 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1250 | 0.4792 | 0.4285 | 0.4053 | 0.1250 |
| 10 | 0.0750 | 0.5417 | 0.4406 | 0.4315 | 0.0750 |
| 20 | 0.0417 | 0.6042 | 0.4436 | 0.4486 | 0.0417 |

Warm retrieval: p50 121.844 ms; p95 258.592 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3750 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.1917 | 0.7222 | 0.5604 | 0.5770 | 0.1917 |
| 10 | 0.1083 | 0.8264 | 0.5772 | 0.6127 | 0.1083 |
| 20 | 0.0625 | 0.9028 | 0.5772 | 0.6335 | 0.0625 |

Warm retrieval: p50 16.403 ms; p95 20.963 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5417 | 0.4792 | 0.5417 | 0.5417 | 0.5417 |
| 5 | 0.1667 | 0.6875 | 0.6146 | 0.6064 | 0.1667 |
| 10 | 0.0875 | 0.7083 | 0.6146 | 0.6141 | 0.0875 |
| 20 | 0.0500 | 0.7917 | 0.6195 | 0.6363 | 0.0500 |

Warm retrieval: p50 38.344 ms; p95 53.245 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.4306 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.2000 | 0.7778 | 0.6174 | 0.6270 | 0.2000 |
| 10 | 0.1083 | 0.8194 | 0.6220 | 0.6427 | 0.1083 |
| 20 | 0.0583 | 0.8611 | 0.6220 | 0.6558 | 0.0583 |

Warm retrieval: p50 16.799 ms; p95 21.419 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4750 | 0.4750 | 0.4750 | 0.4750 | 0.4750 |
| 5 | 0.1450 | 0.7250 | 0.5529 | 0.5951 | 0.1450 |
| 10 | 0.0800 | 0.8000 | 0.5633 | 0.6197 | 0.0800 |
| 20 | 0.0413 | 0.8250 | 0.5647 | 0.6256 | 0.0413 |

Warm retrieval: p50 32.805 ms; p95 171.720 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3250 | 0.1583 | 0.3250 | 0.3250 | 0.3250 |
| 5 | 0.2000 | 0.4708 | 0.4671 | 0.3878 | 0.2000 |
| 10 | 0.1300 | 0.6125 | 0.4883 | 0.4456 | 0.1300 |
| 20 | 0.0788 | 0.7458 | 0.4898 | 0.4855 | 0.0788 |

Warm retrieval: p50 32.487 ms; p95 183.143 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1600 | 0.8000 | 0.6017 | 0.6505 | 0.1600 |
| 10 | 0.0850 | 0.8500 | 0.6100 | 0.6683 | 0.0850 |
| 20 | 0.0425 | 0.8500 | 0.6100 | 0.6683 | 0.0425 |

Warm retrieval: p50 30.296 ms; p95 159.455 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1300 | 0.6500 | 0.5667 | 0.5881 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.5750 | 0.6059 | 0.0700 |
| 20 | 0.0400 | 0.8000 | 0.5824 | 0.6318 | 0.0400 |

Warm retrieval: p50 30.215 ms; p95 122.653 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
