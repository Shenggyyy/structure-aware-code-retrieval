# Retrieval Evaluation

Run: `bm25-seed`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `bm25`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `490a2b5d836d280ab8cb657f41d6705fd4b45ebcafff201200b28c8f6f2b4d50`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.4208 | 0.5000 | 0.4833 | 0.5000 |
| 5 | 0.1700 | 0.6875 | 0.6062 | 0.5931 | 0.1750 |
| 10 | 0.0975 | 0.7542 | 0.6182 | 0.6203 | 0.1000 |
| 20 | 0.0588 | 0.8917 | 0.6252 | 0.6553 | 0.0600 |

Warm retrieval: p50 8.442 ms; p95 18.634 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 877.3 | 22.6 | 124.5 |
| 5 | 4478.8 | 111.9 | 631.1 |
| 10 | 8488.0 | 213.2 | 1189.8 |
| 20 | 19328.0 | 475.9 | 2704.4 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.3250 | 0.3500 | 0.3500 | 0.3500 |
| 5 | 0.1300 | 0.5583 | 0.4667 | 0.4818 | 0.1300 |
| 10 | 0.0900 | 0.6917 | 0.4905 | 0.5360 | 0.0900 |
| 20 | 0.0575 | 0.8750 | 0.5017 | 0.5833 | 0.0575 |

Warm retrieval: p50 11.503 ms; p95 19.921 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6500 | 0.5167 | 0.6500 | 0.6167 | 0.6500 |
| 5 | 0.2100 | 0.8167 | 0.7458 | 0.7045 | 0.2200 |
| 10 | 0.1050 | 0.8167 | 0.7458 | 0.7045 | 0.1100 |
| 20 | 0.0600 | 0.9083 | 0.7486 | 0.7272 | 0.0625 |

Warm retrieval: p50 6.874 ms; p95 9.766 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.4688 | 0.5000 | 0.4583 | 0.5000 |
| 5 | 0.1750 | 0.7812 | 0.6302 | 0.6359 | 0.1750 |
| 10 | 0.0938 | 0.8438 | 0.6406 | 0.6582 | 0.0938 |
| 20 | 0.0531 | 0.9375 | 0.6445 | 0.6841 | 0.0531 |

Warm retrieval: p50 7.070 ms; p95 11.942 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6250 | 0.2917 | 0.6250 | 0.6250 | 0.6250 |
| 5 | 0.2250 | 0.5000 | 0.6875 | 0.5361 | 0.2250 |
| 10 | 0.1625 | 0.7083 | 0.7262 | 0.6272 | 0.1625 |
| 20 | 0.1000 | 0.8333 | 0.7262 | 0.6540 | 0.1000 |

Warm retrieval: p50 9.196 ms; p95 19.146 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1250 | 0.6250 | 0.5625 | 0.5789 | 0.1500 |
| 10 | 0.0625 | 0.6250 | 0.5625 | 0.5789 | 0.0750 |
| 20 | 0.0438 | 0.8750 | 0.5784 | 0.6403 | 0.0500 |

Warm retrieval: p50 7.176 ms; p95 14.655 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.5208 | 0.5789 | 0.1500 |
| 10 | 0.0750 | 0.7500 | 0.5208 | 0.5789 | 0.0750 |
| 20 | 0.0438 | 0.8750 | 0.5322 | 0.6137 | 0.0438 |

Warm retrieval: p50 12.785 ms; p95 20.282 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
