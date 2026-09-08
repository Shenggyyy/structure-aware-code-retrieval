# Retrieval Evaluation

Run: `dense-seed`.
Benchmark: `repoqa-marshmallow-retrieval` / `0.1.0`; split: `test`.
Strategy: `dense`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `1d872262618b6e92445626f140b6b064f5c064301fe6fd1960d74b28d66d9c91`.

## Overall

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.2750 | 0.3292 | 0.1000 |
| 10 | 0.0700 | 0.7000 | 0.2975 | 0.3897 | 0.0700 |
| 20 | 0.0350 | 0.7000 | 0.2975 | 0.3897 | 0.0350 |

Warm retrieval: p50 42.144 ms; p95 54.645 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 588.0 | 14.9 | 76.9 |
| 5 | 3582.6 | 83.4 | 497.3 |
| 10 | 6207.1 | 147.1 | 844.9 |
| 20 | 12222.2 | 292.6 | 1665.0 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: marshmallow

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.2750 | 0.3292 | 0.1000 |
| 10 | 0.0700 | 0.7000 | 0.2975 | 0.3897 | 0.0700 |
| 20 | 0.0350 | 0.7000 | 0.2975 | 0.3897 | 0.0350 |

Warm retrieval: p50 42.144 ms; p95 54.645 ms.

## Category: behavior

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.2750 | 0.3292 | 0.1000 |
| 10 | 0.0700 | 0.7000 | 0.2975 | 0.3897 | 0.0700 |
| 20 | 0.0350 | 0.7000 | 0.2975 | 0.3897 | 0.0350 |

Warm retrieval: p50 42.144 ms; p95 54.645 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
