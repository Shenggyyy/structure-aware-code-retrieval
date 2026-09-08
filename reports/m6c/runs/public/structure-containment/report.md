# Retrieval Evaluation

Run: `structure-containment`.
Benchmark: `repoqa-marshmallow-retrieval` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `9c83d46c83fd22bd45bef3f048e72bdb12e1ffef798de5781886c4b18a663e08`.

## Overall

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 0.1000 |
| 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 0.0500 |
| 20 | 0.0300 | 0.6000 | 0.3300 | 0.3920 | 0.0300 |

Warm retrieval: p50 94.804 ms; p95 168.143 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 2026.1 | 42.2 | 280.7 |
| 5 | 6067.4 | 134.5 | 837.6 |
| 10 | 11545.2 | 260.2 | 1596.3 |
| 20 | 20025.0 | 465.3 | 2781.8 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 17.3, 'expanded_symbols': 9.4, 'edge_cap_seeds': 0}`.

## Repository: marshmallow

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 0.1000 |
| 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 0.0500 |
| 20 | 0.0300 | 0.6000 | 0.3300 | 0.3920 | 0.0300 |

Warm retrieval: p50 94.804 ms; p95 168.143 ms.

## Category: behavior

Queries: 10; answerable: 10; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 0.1000 |
| 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 0.0500 |
| 20 | 0.0300 | 0.6000 | 0.3300 | 0.3920 | 0.0300 |

Warm retrieval: p50 94.804 ms; p95 168.143 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
