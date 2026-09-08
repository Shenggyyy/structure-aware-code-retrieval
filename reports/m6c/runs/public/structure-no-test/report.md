# Retrieval Evaluation

Run: `structure-no-test`.
Benchmark: `repoqa-marshmallow-retrieval` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `bff551f19efac6d84695f8149acab2b30642dc586ec6de8572fd0cc6d2ba88b6`.

## Overall

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 0.0800 |
| 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 0.0500 |
| 20 | 0.0300 | 0.6000 | 0.2550 | 0.3346 | 0.0300 |

Warm retrieval: p50 97.119 ms; p95 191.304 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1619.2 | 32.0 | 226.5 |
| 5 | 6113.3 | 136.5 | 835.9 |
| 10 | 11882.3 | 270.1 | 1630.9 |
| 20 | 20783.0 | 481.2 | 2873.0 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 34.8, 'expanded_symbols': 13.9, 'edge_cap_seeds': 0}`.

## Repository: marshmallow

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 0.0800 |
| 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 0.0500 |
| 20 | 0.0300 | 0.6000 | 0.2550 | 0.3346 | 0.0300 |

Warm retrieval: p50 97.119 ms; p95 191.304 ms.

## Category: behavior

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 0.0800 |
| 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 0.0500 |
| 20 | 0.0300 | 0.6000 | 0.2550 | 0.3346 | 0.0300 |

Warm retrieval: p50 97.119 ms; p95 191.304 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
