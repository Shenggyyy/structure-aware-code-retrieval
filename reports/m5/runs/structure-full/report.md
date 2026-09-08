# Retrieval Evaluation

Run: `structure-full`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `7e9c330e43ddce1429d3edc8e0ef1f1b3f156e6c86c2ce653983c6a2d87281a5`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 0.2500 |
| 5 | 0.1950 | 0.7333 | 0.4483 | 0.4994 | 0.2000 |
| 10 | 0.1200 | 0.8875 | 0.4647 | 0.5545 | 0.1225 |
| 20 | 0.0650 | 0.9625 | 0.4684 | 0.5755 | 0.0663 |

Warm retrieval: p50 41.080 ms; p95 56.953 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 906.9 | 23.1 | 127.3 |
| 5 | 3867.0 | 99.6 | 543.1 |
| 10 | 7673.6 | 197.2 | 1062.8 |
| 20 | 14869.1 | 383.4 | 2052.1 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 30.3, 'expanded_symbols': 12.925, 'edge_cap_seeds': 0.05}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.0667 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.1700 | 0.6667 | 0.3500 | 0.4162 | 0.1700 |
| 10 | 0.1150 | 0.8750 | 0.3744 | 0.4829 | 0.1150 |
| 20 | 0.0625 | 0.9250 | 0.3744 | 0.4992 | 0.0625 |

Warm retrieval: p50 46.581 ms; p95 64.790 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.2750 | 0.3500 | 0.3500 | 0.4000 |
| 5 | 0.2200 | 0.8000 | 0.5467 | 0.5827 | 0.2300 |
| 10 | 0.1250 | 0.9000 | 0.5550 | 0.6261 | 0.1300 |
| 20 | 0.0675 | 1.0000 | 0.5623 | 0.6518 | 0.0700 |

Warm retrieval: p50 27.350 ms; p95 35.684 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1875 | 0.1562 | 0.1875 | 0.1875 | 0.1875 |
| 5 | 0.1875 | 0.8125 | 0.4260 | 0.4996 | 0.1875 |
| 10 | 0.1125 | 0.9688 | 0.4469 | 0.5625 | 0.1125 |
| 20 | 0.0594 | 1.0000 | 0.4469 | 0.5728 | 0.0594 |

Warm retrieval: p50 36.645 ms; p95 58.743 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1667 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.3250 | 0.6667 | 0.6042 | 0.5639 | 0.3250 |
| 10 | 0.2125 | 0.8750 | 0.6181 | 0.6397 | 0.2125 |
| 20 | 0.1125 | 0.9375 | 0.6181 | 0.6598 | 0.1125 |

Warm retrieval: p50 37.757 ms; p95 55.920 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.3750 |
| 5 | 0.1250 | 0.6250 | 0.3479 | 0.4147 | 0.1500 |
| 10 | 0.0750 | 0.7500 | 0.3618 | 0.4523 | 0.0875 |
| 20 | 0.0438 | 0.8750 | 0.3722 | 0.4861 | 0.0500 |

Warm retrieval: p50 40.434 ms; p95 53.995 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1250 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| 5 | 0.1500 | 0.7500 | 0.4375 | 0.5193 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.4500 | 0.5555 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.4578 | 0.5860 | 0.0500 |

Warm retrieval: p50 44.267 ms; p95 50.653 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
