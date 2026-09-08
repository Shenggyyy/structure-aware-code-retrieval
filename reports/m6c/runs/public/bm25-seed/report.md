# Retrieval Evaluation

Run: `bm25-seed`.
Benchmark: `repoqa-marshmallow-retrieval` / `0.1.0`; split: `test`.
Strategy: `bm25`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `feacbff242e5416f77079579e2f25b617508125a75fecb7709dfc31d43bfa3ff`.

## Overall

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.0600 | 0.3000 | 0.2333 | 0.2500 | 0.0600 |
| 10 | 0.0300 | 0.3000 | 0.2333 | 0.2500 | 0.0300 |
| 20 | 0.0200 | 0.4000 | 0.2424 | 0.2779 | 0.0200 |

Warm retrieval: p50 31.286 ms; p95 40.401 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 2568.6 | 51.1 | 381.1 |
| 5 | 8921.4 | 187.3 | 1294.9 |
| 10 | 14589.2 | 320.4 | 2082.1 |
| 20 | 25351.9 | 577.8 | 3598.8 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: marshmallow

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.0600 | 0.3000 | 0.2333 | 0.2500 | 0.0600 |
| 10 | 0.0300 | 0.3000 | 0.2333 | 0.2500 | 0.0300 |
| 20 | 0.0200 | 0.4000 | 0.2424 | 0.2779 | 0.0200 |

Warm retrieval: p50 31.286 ms; p95 40.401 ms.

## Category: behavior

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.0600 | 0.3000 | 0.2333 | 0.2500 | 0.0600 |
| 10 | 0.0300 | 0.3000 | 0.2333 | 0.2500 | 0.0300 |
| 20 | 0.0200 | 0.4000 | 0.2424 | 0.2779 | 0.0200 |

Warm retrieval: p50 31.286 ms; p95 40.401 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
