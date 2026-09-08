# Retrieval Evaluation

Run: `structure-test`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `09ae1acab99d55de855e952a284c487b2125e0509a242739eaf7b143b94997a9`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4083 | 0.3403 | 0.4083 | 0.4083 | 0.4083 |
| 5 | 0.1750 | 0.6833 | 0.5404 | 0.5446 | 0.1750 |
| 10 | 0.1033 | 0.7819 | 0.5521 | 0.5805 | 0.1033 |
| 20 | 0.0600 | 0.8944 | 0.5583 | 0.6124 | 0.0600 |

Warm retrieval: p50 51.619 ms; p95 360.833 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1024.4 | 27.1 | 141.6 |
| 5 | 4626.7 | 124.5 | 639.7 |
| 10 | 8774.7 | 238.7 | 1216.3 |
| 20 | 16736.8 | 456.4 | 2348.1 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 11.783333333333333, 'expanded_symbols': 3.7666666666666666, 'edge_cap_seeds': 0.058333333333333334}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3750 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.1750 | 0.7292 | 0.5583 | 0.5717 | 0.1750 |
| 10 | 0.1125 | 0.8333 | 0.5699 | 0.6157 | 0.1125 |
| 20 | 0.0646 | 0.9375 | 0.5737 | 0.6482 | 0.0646 |

Warm retrieval: p50 51.578 ms; p95 111.627 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2500 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1250 | 0.4375 | 0.4056 | 0.3789 | 0.1250 |
| 10 | 0.0833 | 0.6042 | 0.4208 | 0.4327 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.4340 | 0.4800 | 0.0521 |

Warm retrieval: p50 263.594 ms; p95 399.641 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2639 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1750 | 0.6944 | 0.5083 | 0.5122 | 0.1750 |
| 10 | 0.1000 | 0.7986 | 0.5199 | 0.5476 | 0.1000 |
| 20 | 0.0625 | 0.9236 | 0.5266 | 0.5847 | 0.0625 |

Warm retrieval: p50 20.842 ms; p95 25.127 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3125 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1833 | 0.7292 | 0.5222 | 0.5524 | 0.1833 |
| 10 | 0.1042 | 0.8125 | 0.5421 | 0.5845 | 0.1042 |
| 20 | 0.0583 | 0.8958 | 0.5459 | 0.6092 | 0.0583 |

Warm retrieval: p50 68.860 ms; p95 192.444 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5833 | 0.5000 | 0.5833 | 0.5833 | 0.5833 |
| 5 | 0.2167 | 0.8264 | 0.7076 | 0.7076 | 0.2167 |
| 10 | 0.1167 | 0.8611 | 0.7076 | 0.7220 | 0.1167 |
| 20 | 0.0625 | 0.9236 | 0.7111 | 0.7401 | 0.0625 |

Warm retrieval: p50 20.495 ms; p95 23.781 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3250 | 0.3250 | 0.3250 | 0.3250 | 0.3250 |
| 5 | 0.1500 | 0.7500 | 0.4704 | 0.5395 | 0.1500 |
| 10 | 0.0825 | 0.8250 | 0.4801 | 0.5635 | 0.0825 |
| 20 | 0.0462 | 0.9250 | 0.4877 | 0.5895 | 0.0462 |

Warm retrieval: p50 49.941 ms; p95 365.110 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4000 | 0.1958 | 0.4000 | 0.4000 | 0.4000 |
| 5 | 0.2250 | 0.5500 | 0.5575 | 0.4617 | 0.2250 |
| 10 | 0.1450 | 0.6958 | 0.5728 | 0.5213 | 0.1450 |
| 20 | 0.0875 | 0.8333 | 0.5761 | 0.5650 | 0.0875 |

Warm retrieval: p50 51.961 ms; p95 360.833 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.7000 |
| 5 | 0.1700 | 0.8500 | 0.7583 | 0.7815 | 0.1700 |
| 10 | 0.0950 | 0.9500 | 0.7726 | 0.8149 | 0.0950 |
| 20 | 0.0500 | 1.0000 | 0.7768 | 0.8284 | 0.0500 |

Warm retrieval: p50 51.225 ms; p95 336.885 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3000 | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| 5 | 0.1300 | 0.6500 | 0.4283 | 0.4833 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.4339 | 0.4984 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.4452 | 0.5374 | 0.0425 |

Warm retrieval: p50 58.624 ms; p95 364.213 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
