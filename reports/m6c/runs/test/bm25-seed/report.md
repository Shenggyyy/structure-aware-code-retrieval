# Retrieval Evaluation

Run: `bm25-seed`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `bm25`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `247fab21bba792626a4b28882cb1b5783e598818f3badca0963d89d2e23cdc02`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3583 | 0.2986 | 0.3583 | 0.3583 | 0.3583 |
| 5 | 0.1300 | 0.5042 | 0.4454 | 0.4382 | 0.1300 |
| 10 | 0.0825 | 0.6444 | 0.4644 | 0.4854 | 0.0825 |
| 20 | 0.0496 | 0.7403 | 0.4710 | 0.5138 | 0.0496 |

Warm retrieval: p50 12.046 ms; p95 150.688 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 1198.9 | 31.2 | 168.5 |
| 5 | 5600.4 | 147.3 | 783.8 |
| 10 | 10924.5 | 290.3 | 1531.3 |
| 20 | 21114.0 | 564.7 | 2981.8 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.3889 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1667 | 0.6111 | 0.6007 | 0.5486 | 0.1667 |
| 10 | 0.1000 | 0.7153 | 0.6049 | 0.5841 | 0.1000 |
| 20 | 0.0604 | 0.8542 | 0.6114 | 0.6240 | 0.0604 |

Warm retrieval: p50 12.572 ms; p95 31.149 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2083 | 0.1667 | 0.2083 | 0.2083 | 0.2083 |
| 5 | 0.1167 | 0.3958 | 0.3229 | 0.3268 | 0.1167 |
| 10 | 0.0833 | 0.6042 | 0.3508 | 0.3962 | 0.0833 |
| 20 | 0.0438 | 0.6250 | 0.3508 | 0.4026 | 0.0438 |

Warm retrieval: p50 121.894 ms; p95 198.352 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.4167 | 0.3750 | 0.4167 | 0.4167 | 0.4167 |
| 5 | 0.1250 | 0.5347 | 0.4736 | 0.4715 | 0.1250 |
| 10 | 0.0708 | 0.6181 | 0.4865 | 0.5002 | 0.0708 |
| 20 | 0.0417 | 0.6736 | 0.4949 | 0.5188 | 0.0417 |

Warm retrieval: p50 5.046 ms; p95 8.152 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2917 | 0.2500 | 0.2917 | 0.2917 | 0.2917 |
| 5 | 0.0833 | 0.3542 | 0.3194 | 0.3172 | 0.0833 |
| 10 | 0.0667 | 0.5625 | 0.3536 | 0.3873 | 0.0667 |
| 20 | 0.0438 | 0.6875 | 0.3655 | 0.4244 | 0.0438 |

Warm retrieval: p50 18.227 ms; p95 47.991 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3750 | 0.3125 | 0.3750 | 0.3750 | 0.3750 |
| 5 | 0.1583 | 0.6250 | 0.5104 | 0.5269 | 0.1583 |
| 10 | 0.0917 | 0.7222 | 0.5260 | 0.5593 | 0.0917 |
| 20 | 0.0583 | 0.8611 | 0.5326 | 0.5990 | 0.0583 |

Warm retrieval: p50 4.579 ms; p95 7.369 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.3500 | 0.3500 | 0.3500 | 0.3500 |
| 5 | 0.1050 | 0.5250 | 0.4250 | 0.4506 | 0.1050 |
| 10 | 0.0700 | 0.7000 | 0.4448 | 0.5036 | 0.0700 |
| 20 | 0.0363 | 0.7250 | 0.4467 | 0.5102 | 0.0363 |

Warm retrieval: p50 10.482 ms; p95 145.439 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3500 | 0.1708 | 0.3500 | 0.3500 | 0.3500 |
| 5 | 0.1700 | 0.4125 | 0.4508 | 0.3744 | 0.1700 |
| 10 | 0.1050 | 0.5083 | 0.4665 | 0.4131 | 0.1050 |
| 20 | 0.0725 | 0.6958 | 0.4794 | 0.4726 | 0.0725 |

Warm retrieval: p50 11.961 ms; p95 153.429 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6000 | 0.6000 | 0.6000 | 0.6000 | 0.6000 |
| 5 | 0.1700 | 0.8500 | 0.6958 | 0.7346 | 0.1700 |
| 10 | 0.1000 | 1.0000 | 0.7196 | 0.7869 | 0.1000 |
| 20 | 0.0500 | 1.0000 | 0.7196 | 0.7869 | 0.0500 |

Warm retrieval: p50 10.951 ms; p95 84.448 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1500 | 0.1500 | 0.1500 | 0.1500 | 0.1500 |
| 5 | 0.0600 | 0.3000 | 0.2250 | 0.2446 | 0.0600 |
| 10 | 0.0450 | 0.4500 | 0.2439 | 0.2921 | 0.0450 |
| 20 | 0.0300 | 0.6000 | 0.2545 | 0.3301 | 0.0300 |

Warm retrieval: p50 19.132 ms; p95 195.155 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
