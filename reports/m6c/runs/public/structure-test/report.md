# Retrieval Evaluation

Run: `structure-test`.
Benchmark: `repoqa-marshmallow-retrieval` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `8e978b97e27fc3b002743bfb66ff46c022aff22d4fdc8d90ba622bf981c3a948`.

## Overall

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 0.1000 |
| 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 0.0500 |
| 20 | 0.0250 | 0.5000 | 0.3250 | 0.3693 | 0.0250 |

Warm retrieval: p50 84.937 ms; p95 158.988 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 2026.1 | 42.2 | 280.7 |
| 5 | 6147.4 | 135.6 | 856.2 |
| 10 | 11404.7 | 255.2 | 1585.8 |
| 20 | 19483.0 | 452.3 | 2704.8 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 51.4, 'expanded_symbols': 8.5, 'edge_cap_seeds': 0.4}`.

## Repository: marshmallow

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 0.1000 |
| 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 0.0500 |
| 20 | 0.0250 | 0.5000 | 0.3250 | 0.3693 | 0.0250 |

Warm retrieval: p50 84.937 ms; p95 158.988 ms.

## Category: behavior

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 0.1000 |
| 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 0.0500 |
| 20 | 0.0250 | 0.5000 | 0.3250 | 0.3693 | 0.0250 |

Warm retrieval: p50 84.937 ms; p95 158.988 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
