# Retrieval Evaluation

Run: `structure-no-containment`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `15198cd24754ad3141e99b5dfe3847f200145ded805e3b2d1ea9be54db587137`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 0.2500 |
| 5 | 0.2000 | 0.7583 | 0.4554 | 0.5108 | 0.2050 |
| 10 | 0.1200 | 0.8875 | 0.4691 | 0.5587 | 0.1225 |
| 20 | 0.0650 | 0.9625 | 0.4727 | 0.5798 | 0.0663 |

Warm retrieval: p50 41.383 ms; p95 54.503 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 925.5 | 23.6 | 130.7 |
| 5 | 3848.2 | 100.5 | 541.6 |
| 10 | 7494.9 | 193.0 | 1038.2 |
| 20 | 15033.6 | 386.8 | 2074.1 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 19.85, 'expanded_symbols': 9.875, 'edge_cap_seeds': 0.05}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.0667 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.1800 | 0.7167 | 0.3642 | 0.4390 | 0.1800 |
| 10 | 0.1150 | 0.8750 | 0.3831 | 0.4914 | 0.1150 |
| 20 | 0.0625 | 0.9250 | 0.3831 | 0.5077 | 0.0625 |

Warm retrieval: p50 46.897 ms; p95 138.989 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.2750 | 0.3500 | 0.3500 | 0.4000 |
| 5 | 0.2200 | 0.8000 | 0.5467 | 0.5827 | 0.2300 |
| 10 | 0.1250 | 0.9000 | 0.5550 | 0.6261 | 0.1300 |
| 20 | 0.0675 | 1.0000 | 0.5623 | 0.6518 | 0.0700 |

Warm retrieval: p50 29.591 ms; p95 38.038 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1875 | 0.1562 | 0.1875 | 0.1875 | 0.1875 |
| 5 | 0.2000 | 0.8750 | 0.4437 | 0.5281 | 0.2000 |
| 10 | 0.1125 | 0.9688 | 0.4542 | 0.5687 | 0.1125 |
| 20 | 0.0594 | 1.0000 | 0.4542 | 0.5791 | 0.0594 |

Warm retrieval: p50 40.408 ms; p95 54.104 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1667 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.3250 | 0.6667 | 0.6042 | 0.5639 | 0.3250 |
| 10 | 0.2125 | 0.8750 | 0.6181 | 0.6411 | 0.2125 |
| 20 | 0.1125 | 0.9375 | 0.6181 | 0.6612 | 0.1125 |

Warm retrieval: p50 39.478 ms; p95 52.038 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.3750 |
| 5 | 0.1250 | 0.6250 | 0.3479 | 0.4147 | 0.1500 |
| 10 | 0.0750 | 0.7500 | 0.3658 | 0.4564 | 0.0875 |
| 20 | 0.0438 | 0.8750 | 0.3762 | 0.4901 | 0.0500 |

Warm retrieval: p50 41.383 ms; p95 51.394 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1250 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| 5 | 0.1500 | 0.7500 | 0.4375 | 0.5193 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.4531 | 0.5588 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.4609 | 0.5893 | 0.0500 |

Warm retrieval: p50 40.354 ms; p95 57.099 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
