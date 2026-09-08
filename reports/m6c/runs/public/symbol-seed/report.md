# Retrieval Evaluation

Run: `symbol-seed`.
Benchmark: `repoqa-marshmallow-retrieval` / `0.1.0`; split: `test`.
Strategy: `symbol`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `94a920983cb0bbcc15f9b7c55298836f0808876f9333026c08926f1e09a50f25`.

## Overall

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.1000 | 0.5000 | 0.2233 | 0.2905 | 0.1000 |
| 10 | 0.0600 | 0.6000 | 0.2400 | 0.3261 | 0.0600 |
| 20 | 0.0300 | 0.6000 | 0.2400 | 0.3261 | 0.0300 |

Warm retrieval: p50 330.318 ms; p95 418.015 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1641.5 | 34.7 | 239.8 |
| 5 | 5605.5 | 121.1 | 821.4 |
| 10 | 10002.2 | 229.2 | 1420.2 |
| 20 | 16928.2 | 400.0 | 2375.3 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: marshmallow

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.1000 | 0.5000 | 0.2233 | 0.2905 | 0.1000 |
| 10 | 0.0600 | 0.6000 | 0.2400 | 0.3261 | 0.0600 |
| 20 | 0.0300 | 0.6000 | 0.2400 | 0.3261 | 0.0300 |

Warm retrieval: p50 330.318 ms; p95 418.015 ms.

## Category: behavior

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.1000 | 0.5000 | 0.2233 | 0.2905 | 0.1000 |
| 10 | 0.0600 | 0.6000 | 0.2400 | 0.3261 | 0.0600 |
| 20 | 0.0300 | 0.6000 | 0.2400 | 0.3261 | 0.0300 |

Warm retrieval: p50 330.318 ms; p95 418.015 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
