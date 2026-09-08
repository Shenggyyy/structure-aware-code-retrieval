# Retrieval Evaluation

Run: `structure-no-call`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `fb7564f14e6007dd4c799708b230e362d1bd351955da3c0d7a0a77eb184f13d6`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4000 | 0.3361 | 0.4000 | 0.4000 | 0.4000 |
| 5 | 0.1700 | 0.6708 | 0.5307 | 0.5343 | 0.1700 |
| 10 | 0.1033 | 0.7819 | 0.5449 | 0.5758 | 0.1033 |
| 20 | 0.0600 | 0.8944 | 0.5509 | 0.6075 | 0.0600 |

Warm retrieval: p50 55.048 ms; p95 380.369 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1016.5 | 27.0 | 141.2 |
| 5 | 4605.2 | 124.5 | 638.0 |
| 10 | 8795.5 | 239.8 | 1215.2 |
| 20 | 16736.4 | 457.1 | 2348.0 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 25.975, 'expanded_symbols': 9.716666666666667, 'edge_cap_seeds': 0.06666666666666667}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3750 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.1750 | 0.7292 | 0.5583 | 0.5717 | 0.1750 |
| 10 | 0.1125 | 0.8333 | 0.5699 | 0.6167 | 0.1125 |
| 20 | 0.0646 | 0.9375 | 0.5734 | 0.6484 | 0.0646 |

Warm retrieval: p50 54.705 ms; p95 117.016 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2917 | 0.2292 | 0.2917 | 0.2917 | 0.2917 |
| 5 | 0.1167 | 0.4167 | 0.3764 | 0.3563 | 0.1167 |
| 10 | 0.0833 | 0.6042 | 0.3981 | 0.4186 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.4112 | 0.4659 | 0.0521 |

Warm retrieval: p50 277.579 ms; p95 413.808 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2639 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1667 | 0.6736 | 0.4944 | 0.4994 | 0.1667 |
| 10 | 0.1000 | 0.7986 | 0.5125 | 0.5445 | 0.1000 |
| 20 | 0.0625 | 0.9236 | 0.5192 | 0.5816 | 0.0625 |

Warm retrieval: p50 25.677 ms; p95 35.659 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3125 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1833 | 0.7292 | 0.5167 | 0.5466 | 0.1833 |
| 10 | 0.1042 | 0.8125 | 0.5365 | 0.5787 | 0.1042 |
| 20 | 0.0583 | 0.8958 | 0.5403 | 0.6033 | 0.0583 |

Warm retrieval: p50 66.370 ms; p95 192.419 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5833 | 0.5000 | 0.5833 | 0.5833 | 0.5833 |
| 5 | 0.2083 | 0.8056 | 0.7076 | 0.6977 | 0.2083 |
| 10 | 0.1167 | 0.8611 | 0.7076 | 0.7207 | 0.1167 |
| 20 | 0.0625 | 0.9236 | 0.7106 | 0.7383 | 0.0625 |

Warm retrieval: p50 24.780 ms; p95 30.746 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3250 | 0.3250 | 0.3250 | 0.3250 | 0.3250 |
| 5 | 0.1500 | 0.7500 | 0.4671 | 0.5367 | 0.1500 |
| 10 | 0.0825 | 0.8250 | 0.4763 | 0.5601 | 0.0825 |
| 20 | 0.0462 | 0.9250 | 0.4836 | 0.5858 | 0.0462 |

Warm retrieval: p50 54.425 ms; p95 380.369 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1833 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.2100 | 0.5125 | 0.5317 | 0.4339 | 0.2100 |
| 10 | 0.1450 | 0.6958 | 0.5553 | 0.5108 | 0.1450 |
| 20 | 0.0875 | 0.8333 | 0.5585 | 0.5541 | 0.0875 |

Warm retrieval: p50 53.035 ms; p95 384.774 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.7000 |
| 5 | 0.1700 | 0.8500 | 0.7583 | 0.7815 | 0.1700 |
| 10 | 0.0950 | 0.9500 | 0.7726 | 0.8149 | 0.0950 |
| 20 | 0.0500 | 1.0000 | 0.7762 | 0.8277 | 0.0500 |

Warm retrieval: p50 55.358 ms; p95 357.051 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3000 | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| 5 | 0.1300 | 0.6500 | 0.4283 | 0.4833 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.4339 | 0.4984 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.4452 | 0.5374 | 0.0425 |

Warm retrieval: p50 58.121 ms; p95 396.173 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
