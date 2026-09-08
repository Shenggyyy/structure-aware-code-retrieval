# Retrieval Evaluation

Run: `structure-call`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `0463392e8d73f35b5ebfa0ebc939468043c3d461417b1a3d60a9683703202ca6`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 0.2500 |
| 5 | 0.2000 | 0.7583 | 0.4696 | 0.5211 | 0.2050 |
| 10 | 0.1200 | 0.8875 | 0.4840 | 0.5697 | 0.1225 |
| 20 | 0.0650 | 0.9625 | 0.4877 | 0.5907 | 0.0663 |

Warm retrieval: p50 40.302 ms; p95 52.861 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 916.2 | 23.2 | 129.1 |
| 5 | 3832.9 | 99.7 | 538.0 |
| 10 | 7526.6 | 193.9 | 1041.1 |
| 20 | 15059.0 | 386.8 | 2074.5 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 9.925, 'expanded_symbols': 5.475, 'edge_cap_seeds': 0.025}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.0667 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.1700 | 0.6667 | 0.3708 | 0.4302 | 0.1700 |
| 10 | 0.1150 | 0.8750 | 0.3997 | 0.5017 | 0.1150 |
| 20 | 0.0625 | 0.9250 | 0.3997 | 0.5181 | 0.0625 |

Warm retrieval: p50 45.331 ms; p95 134.059 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.2750 | 0.3500 | 0.3500 | 0.4000 |
| 5 | 0.2300 | 0.8500 | 0.5683 | 0.6120 | 0.2400 |
| 10 | 0.1250 | 0.9000 | 0.5683 | 0.6377 | 0.1300 |
| 20 | 0.0675 | 1.0000 | 0.5756 | 0.6634 | 0.0700 |

Warm retrieval: p50 26.964 ms; p95 32.300 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1875 | 0.1562 | 0.1875 | 0.1875 | 0.1875 |
| 5 | 0.2125 | 0.9375 | 0.4760 | 0.5655 | 0.2125 |
| 10 | 0.1125 | 0.9688 | 0.4760 | 0.5839 | 0.1125 |
| 20 | 0.0594 | 1.0000 | 0.4760 | 0.5942 | 0.0594 |

Warm retrieval: p50 39.027 ms; p95 51.073 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1667 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.3250 | 0.6667 | 0.6042 | 0.5639 | 0.3250 |
| 10 | 0.2125 | 0.8750 | 0.6198 | 0.6422 | 0.2125 |
| 20 | 0.1125 | 0.9375 | 0.6198 | 0.6623 | 0.1125 |

Warm retrieval: p50 37.883 ms; p95 60.280 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.3750 |
| 5 | 0.1000 | 0.5000 | 0.3542 | 0.3914 | 0.1250 |
| 10 | 0.0750 | 0.7500 | 0.3929 | 0.4776 | 0.0875 |
| 20 | 0.0438 | 0.8750 | 0.4033 | 0.5113 | 0.0500 |

Warm retrieval: p50 40.362 ms; p95 49.275 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1250 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| 5 | 0.1500 | 0.7500 | 0.4375 | 0.5193 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.4554 | 0.5610 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.4632 | 0.5916 | 0.0500 |

Warm retrieval: p50 36.836 ms; p95 52.316 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
