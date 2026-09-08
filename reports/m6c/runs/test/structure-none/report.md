# Retrieval Evaluation

Run: `structure-none`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `structure`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `8f83ba5fe9f588fdaf62e51c67484843a3243bbc9718ed76b8efa8fbb52a67b4`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3528 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.1783 | 0.6889 | 0.5529 | 0.5575 | 0.1783 |
| 10 | 0.1050 | 0.7944 | 0.5637 | 0.5947 | 0.1050 |
| 20 | 0.0600 | 0.8944 | 0.5693 | 0.6234 | 0.0600 |

Warm retrieval: p50 46.752 ms; p95 324.857 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1039.1 | 27.5 | 144.0 |
| 5 | 4608.9 | 124.3 | 637.7 |
| 10 | 8784.1 | 239.4 | 1219.1 |
| 20 | 16768.0 | 458.1 | 2351.4 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4583 | 0.4167 | 0.4583 | 0.4583 | 0.4583 |
| 5 | 0.1917 | 0.7569 | 0.6104 | 0.6187 | 0.1917 |
| 10 | 0.1125 | 0.8333 | 0.6150 | 0.6510 | 0.1125 |
| 20 | 0.0646 | 0.9375 | 0.6188 | 0.6836 | 0.0646 |

Warm retrieval: p50 46.752 ms; p95 122.972 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2500 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1250 | 0.4375 | 0.4056 | 0.3789 | 0.1250 |
| 10 | 0.0833 | 0.6042 | 0.4208 | 0.4327 | 0.0833 |
| 20 | 0.0521 | 0.7917 | 0.4340 | 0.4800 | 0.0521 |

Warm retrieval: p50 225.715 ms; p95 354.511 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3056 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1750 | 0.6944 | 0.5396 | 0.5347 | 0.1750 |
| 10 | 0.1000 | 0.7986 | 0.5512 | 0.5701 | 0.1000 |
| 20 | 0.0625 | 0.9236 | 0.5584 | 0.6090 | 0.0625 |

Warm retrieval: p50 23.001 ms; p95 31.106 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.2917 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1833 | 0.7292 | 0.4979 | 0.5433 | 0.1833 |
| 10 | 0.1042 | 0.8125 | 0.5160 | 0.5744 | 0.1042 |
| 20 | 0.0583 | 0.8958 | 0.5198 | 0.5990 | 0.0583 |

Warm retrieval: p50 58.754 ms; p95 174.225 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5833 | 0.5000 | 0.5833 | 0.5833 | 0.5833 |
| 5 | 0.2167 | 0.8264 | 0.7111 | 0.7116 | 0.2167 |
| 10 | 0.1250 | 0.9236 | 0.7153 | 0.7454 | 0.1250 |
| 20 | 0.0625 | 0.9236 | 0.7153 | 0.7454 | 0.0625 |

Warm retrieval: p50 21.943 ms; p95 28.047 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1500 | 0.7500 | 0.5017 | 0.5630 | 0.1500 |
| 10 | 0.0825 | 0.8250 | 0.5114 | 0.5870 | 0.0825 |
| 20 | 0.0462 | 0.9250 | 0.5189 | 0.6129 | 0.0462 |

Warm retrieval: p50 49.459 ms; p95 337.098 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.1833 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.2350 | 0.5667 | 0.5554 | 0.4704 | 0.2350 |
| 10 | 0.1475 | 0.7083 | 0.5655 | 0.5268 | 0.1475 |
| 20 | 0.0875 | 0.8333 | 0.5691 | 0.5673 | 0.0875 |

Warm retrieval: p50 42.317 ms; p95 324.857 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.7000 |
| 5 | 0.1700 | 0.8500 | 0.7667 | 0.7881 | 0.1700 |
| 10 | 0.1000 | 1.0000 | 0.7860 | 0.8359 | 0.1000 |
| 20 | 0.0500 | 1.0000 | 0.7860 | 0.8359 | 0.0500 |

Warm retrieval: p50 46.231 ms; p95 236.184 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3000 | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| 5 | 0.1300 | 0.6500 | 0.4367 | 0.4899 | 0.1300 |
| 10 | 0.0700 | 0.7000 | 0.4422 | 0.5049 | 0.0700 |
| 20 | 0.0425 | 0.8500 | 0.4536 | 0.5440 | 0.0425 |

Warm retrieval: p50 56.693 ms; p95 347.103 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
