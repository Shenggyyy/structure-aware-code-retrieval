# Retrieval Evaluation

Run: `structure-no-test`.
Benchmark: `repository-seed` / `0.1.0`; split: `dev`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `cb41e86c16761f52fb747af7e1afb53f27c54558f11271158ae755bc60623477`.

## Overall

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 0.2500 |
| 5 | 0.1950 | 0.7333 | 0.4600 | 0.5075 | 0.2000 |
| 10 | 0.1200 | 0.8875 | 0.4758 | 0.5621 | 0.1225 |
| 20 | 0.0663 | 0.9750 | 0.4794 | 0.5868 | 0.0675 |

Warm retrieval: p50 49.463 ms; p95 80.831 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 889.2 | 22.6 | 124.5 |
| 5 | 3930.9 | 100.5 | 551.8 |
| 10 | 7844.6 | 201.6 | 1085.2 |
| 20 | 14908.5 | 385.7 | 2058.3 |

Mean retrieval work: `{'seed_symbols': 5, 'edges_examined': 23.175, 'expanded_symbols': 11.35, 'edge_cap_seeds': 0.025}`.

## Repository: click

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1000 | 0.0667 | 0.1000 | 0.1000 | 0.1000 |
| 5 | 0.1600 | 0.6167 | 0.3517 | 0.4030 | 0.1600 |
| 10 | 0.1150 | 0.8750 | 0.3833 | 0.4866 | 0.1150 |
| 20 | 0.0650 | 0.9500 | 0.3833 | 0.5102 | 0.0650 |

Warm retrieval: p50 59.425 ms; p95 160.927 ms.

## Repository: requests

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.2750 | 0.3500 | 0.3500 | 0.4000 |
| 5 | 0.2300 | 0.8500 | 0.5683 | 0.6120 | 0.2400 |
| 10 | 0.1250 | 0.9000 | 0.5683 | 0.6377 | 0.1300 |
| 20 | 0.0675 | 1.0000 | 0.5756 | 0.6634 | 0.0700 |

Warm retrieval: p50 38.613 ms; p95 48.667 ms.

## Category: behavior

Queries: 16; answerable: 16; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1875 | 0.1562 | 0.1875 | 0.1875 | 0.1875 |
| 5 | 0.2000 | 0.8750 | 0.4521 | 0.5315 | 0.2000 |
| 10 | 0.1125 | 0.9688 | 0.4625 | 0.5722 | 0.1125 |
| 20 | 0.0594 | 1.0000 | 0.4625 | 0.5825 | 0.0594 |

Warm retrieval: p50 49.045 ms; p95 73.407 ms.

## Category: cross_file

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1667 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.3250 | 0.6667 | 0.6042 | 0.5639 | 0.3250 |
| 10 | 0.2125 | 0.8750 | 0.6167 | 0.6388 | 0.2125 |
| 20 | 0.1187 | 1.0000 | 0.6167 | 0.6770 | 0.1187 |

Warm retrieval: p50 52.705 ms; p95 74.431 ms.

## Category: symbol

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.3750 |
| 5 | 0.1000 | 0.5000 | 0.3542 | 0.3914 | 0.1250 |
| 10 | 0.0750 | 0.7500 | 0.3859 | 0.4707 | 0.0875 |
| 20 | 0.0438 | 0.8750 | 0.3963 | 0.5044 | 0.0500 |

Warm retrieval: p50 46.567 ms; p95 58.825 ms.

## Category: test

Queries: 8; answerable: 8; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1250 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| 5 | 0.1500 | 0.7500 | 0.4375 | 0.5193 | 0.1500 |
| 10 | 0.0875 | 0.8750 | 0.4514 | 0.5570 | 0.0875 |
| 20 | 0.0500 | 1.0000 | 0.4592 | 0.5875 | 0.0500 |

Warm retrieval: p50 54.951 ms; p95 132.617 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
