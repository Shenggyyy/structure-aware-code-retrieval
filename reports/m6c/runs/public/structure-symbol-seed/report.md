# Retrieval Evaluation

Run: `structure-symbol-seed`.
Benchmark: `repoqa-marshmallow-retrieval` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `abd000df9fad5e52bfc77e9e1e0e286448714edb9770b3ed45cb732ec45062d5`.

## Overall

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.1950 | 0.2448 | 0.0800 |
| 10 | 0.0600 | 0.6000 | 0.2260 | 0.3138 | 0.0600 |
| 20 | 0.0300 | 0.6000 | 0.2260 | 0.3138 | 0.0300 |

Warm retrieval: p50 362.601 ms; p95 461.480 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1587.8 | 33.3 | 229.0 |
| 5 | 5458.6 | 117.0 | 796.8 |
| 10 | 9325.2 | 210.9 | 1330.0 |
| 20 | 16605.5 | 392.4 | 2326.3 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 104.5, 'expanded_symbols': 18.3, 'edge_cap_seeds': 0.9}`.

## Repository: marshmallow

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.1950 | 0.2448 | 0.0800 |
| 10 | 0.0600 | 0.6000 | 0.2260 | 0.3138 | 0.0600 |
| 20 | 0.0300 | 0.6000 | 0.2260 | 0.3138 | 0.0300 |

Warm retrieval: p50 362.601 ms; p95 461.480 ms.

## Category: behavior

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.1950 | 0.2448 | 0.0800 |
| 10 | 0.0600 | 0.6000 | 0.2260 | 0.3138 | 0.0600 |
| 20 | 0.0300 | 0.6000 | 0.2260 | 0.3138 | 0.0300 |

Warm retrieval: p50 362.601 ms; p95 461.480 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
