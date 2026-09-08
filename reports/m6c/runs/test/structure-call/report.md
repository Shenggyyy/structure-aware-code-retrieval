# Retrieval Evaluation

Run: `structure-call`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `f1a9cb801a7f0db3df076691d0e4397d7bfd9ed94c49bea7dc26e78ced9ba746`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2333 | 0.1833 | 0.2333 | 0.2333 | 0.2333 |
| 5 | 0.1767 | 0.6722 | 0.4365 | 0.4757 | 0.1767 |
| 10 | 0.1067 | 0.7875 | 0.4497 | 0.5183 | 0.1067 |
| 20 | 0.0608 | 0.9014 | 0.4566 | 0.5493 | 0.0608 |

Warm retrieval: p50 46.903 ms; p95 338.760 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 999.5 | 26.5 | 138.4 |
| 5 | 4651.8 | 125.7 | 644.9 |
| 10 | 8888.7 | 242.9 | 1234.3 |
| 20 | 16966.6 | 463.0 | 2379.3 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 12.033333333333333, 'expanded_symbols': 5.691666666666666, 'edge_cap_seeds': 0.008333333333333333}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3472 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.2083 | 0.7708 | 0.5722 | 0.6064 | 0.2083 |
| 10 | 0.1208 | 0.8750 | 0.5823 | 0.6442 | 0.1208 |
| 20 | 0.0646 | 0.9375 | 0.5861 | 0.6625 | 0.0646 |

Warm retrieval: p50 46.538 ms; p95 106.312 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.1667 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.1250 | 0.4375 | 0.3472 | 0.3511 | 0.1250 |
| 10 | 0.0833 | 0.6042 | 0.3681 | 0.4061 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.3806 | 0.4527 | 0.0521 |

Warm retrieval: p50 231.762 ms; p95 365.860 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1667 | 0.1181 | 0.1667 | 0.1667 | 0.1667 |
| 5 | 0.1750 | 0.6875 | 0.4354 | 0.4627 | 0.1750 |
| 10 | 0.1125 | 0.8264 | 0.4476 | 0.5188 | 0.1125 |
| 20 | 0.0667 | 0.9583 | 0.4548 | 0.5553 | 0.0667 |

Warm retrieval: p50 21.300 ms; p95 27.922 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0833 | 0.0625 | 0.0833 | 0.0833 | 0.0833 |
| 5 | 0.1500 | 0.6250 | 0.3556 | 0.4030 | 0.1500 |
| 10 | 0.1000 | 0.7708 | 0.3783 | 0.4580 | 0.1000 |
| 20 | 0.0583 | 0.8958 | 0.3859 | 0.4940 | 0.0583 |

Warm retrieval: p50 58.614 ms; p95 174.610 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2222 | 0.2500 | 0.2500 | 0.2500 |
| 5 | 0.2250 | 0.8403 | 0.4722 | 0.5553 | 0.2250 |
| 10 | 0.1167 | 0.8611 | 0.4722 | 0.5644 | 0.1167 |
| 20 | 0.0625 | 0.9236 | 0.4754 | 0.5817 | 0.0625 |

Warm retrieval: p50 20.823 ms; p95 28.627 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.2250 | 0.2250 | 0.2250 | 0.2250 |
| 5 | 0.1350 | 0.6750 | 0.3992 | 0.4681 | 0.1350 |
| 10 | 0.0775 | 0.7750 | 0.4128 | 0.5008 | 0.0775 |
| 20 | 0.0462 | 0.9250 | 0.4246 | 0.5404 | 0.0462 |

Warm retrieval: p50 46.684 ms; p95 333.876 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2750 | 0.1250 | 0.2750 | 0.2750 | 0.2750 |
| 5 | 0.2400 | 0.5667 | 0.4704 | 0.4343 | 0.2400 |
| 10 | 0.1600 | 0.7625 | 0.4907 | 0.5144 | 0.1600 |
| 20 | 0.0900 | 0.8542 | 0.4920 | 0.5416 | 0.0900 |

Warm retrieval: p50 48.026 ms; p95 339.103 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1800 | 0.9000 | 0.5017 | 0.6029 | 0.1800 |
| 10 | 0.0950 | 0.9500 | 0.5072 | 0.6179 | 0.0950 |
| 20 | 0.0500 | 1.0000 | 0.5111 | 0.6311 | 0.0500 |

Warm retrieval: p50 43.555 ms; p95 317.464 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1300 | 0.6500 | 0.3783 | 0.4464 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.3839 | 0.4615 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.3952 | 0.5005 | 0.0425 |

Warm retrieval: p50 48.292 ms; p95 349.750 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
