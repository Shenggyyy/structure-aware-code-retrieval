# Retrieval Evaluation

Run: `structure-no-import`.
Benchmark: `repoqa-marshmallow-retrieval` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `b8653bb7d3601d769a5982c835752ceb2c21b895a75b5016b6e19a7f8a8409f3`.

## Overall

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 0.0800 |
| 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 0.0500 |
| 20 | 0.0250 | 0.5000 | 0.2500 | 0.3118 | 0.0250 |

Warm retrieval: p50 101.335 ms; p95 182.205 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1619.2 | 32.0 | 226.5 |
| 5 | 6116.9 | 136.9 | 837.7 |
| 10 | 11647.3 | 263.8 | 1608.3 |
| 20 | 20093.7 | 467.9 | 2774.0 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 67.1, 'expanded_symbols': 15.1, 'edge_cap_seeds': 0.6}`.

## Repository: marshmallow

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 0.0800 |
| 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 0.0500 |
| 20 | 0.0250 | 0.5000 | 0.2500 | 0.3118 | 0.0250 |

Warm retrieval: p50 101.335 ms; p95 182.205 ms.

## Category: behavior

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 0.0800 |
| 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 0.0500 |
| 20 | 0.0250 | 0.5000 | 0.2500 | 0.3118 | 0.0250 |

Warm retrieval: p50 101.335 ms; p95 182.205 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
