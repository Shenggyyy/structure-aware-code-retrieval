# Retrieval Evaluation

Run: `structure-symbol-seed`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `2a81cc1714cf6613d0b3ccf68fb0601a958973d09eee40eeef5b4db7428812ec`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.2958 | 0.3500 | 0.3333 | 0.3500 |
| 5 | 0.1600 | 0.6417 | 0.4883 | 0.5088 | 0.1650 |
| 10 | 0.1075 | 0.8333 | 0.5095 | 0.5719 | 0.1100 |
| 20 | 0.0600 | 0.9167 | 0.5139 | 0.5956 | 0.0613 |

Warm retrieval: p50 75.407 ms; p95 115.044 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 921.6 | 24.2 | 127.2 |
| 5 | 3433.8 | 90.2 | 481.4 |
| 10 | 6830.4 | 175.2 | 948.4 |
| 20 | 13523.3 | 348.2 | 1861.9 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 31.825, 'expanded_symbols': 13.625, 'edge_cap_seeds': 0.05}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3000 | 0.2667 | 0.3000 | 0.2667 | 0.3000 |
| 5 | 0.1400 | 0.6000 | 0.4308 | 0.4521 | 0.1400 |
| 10 | 0.1100 | 0.8583 | 0.4610 | 0.5432 | 0.1100 |
| 20 | 0.0600 | 0.9000 | 0.4610 | 0.5592 | 0.0600 |

Warm retrieval: p50 96.678 ms; p95 178.775 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4000 | 0.3250 | 0.4000 | 0.4000 | 0.4000 |
| 5 | 0.1800 | 0.6833 | 0.5458 | 0.5656 | 0.1900 |
| 10 | 0.1050 | 0.8083 | 0.5580 | 0.6007 | 0.1100 |
| 20 | 0.0600 | 0.9333 | 0.5667 | 0.6320 | 0.0625 |

Warm retrieval: p50 55.418 ms; p95 69.508 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3125 | 0.2812 | 0.3125 | 0.3125 | 0.3125 |
| 5 | 0.1125 | 0.5312 | 0.3958 | 0.4262 | 0.1125 |
| 10 | 0.0875 | 0.7812 | 0.4251 | 0.5008 | 0.0875 |
| 20 | 0.0531 | 0.9062 | 0.4325 | 0.5357 | 0.0531 |

Warm retrieval: p50 88.851 ms; p95 140.552 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1667 | 0.3750 | 0.2917 | 0.3750 |
| 5 | 0.2500 | 0.5208 | 0.5250 | 0.4388 | 0.2500 |
| 10 | 0.1750 | 0.7292 | 0.5429 | 0.5279 | 0.1750 |
| 20 | 0.0938 | 0.7708 | 0.5429 | 0.5473 | 0.0938 |

Warm retrieval: p50 73.015 ms; p95 111.062 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.1500 | 0.7500 | 0.4375 | 0.5164 | 0.1750 |
| 10 | 0.1000 | 1.0000 | 0.4670 | 0.5934 | 0.1125 |
| 20 | 0.0500 | 1.0000 | 0.4670 | 0.5934 | 0.0563 |

Warm retrieval: p50 71.504 ms; p95 97.013 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1750 | 0.8750 | 0.6875 | 0.7366 | 0.1750 |
| 10 | 0.0875 | 0.8750 | 0.6875 | 0.7366 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.6944 | 0.7660 | 0.0500 |

Warm retrieval: p50 91.406 ms; p95 176.821 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
