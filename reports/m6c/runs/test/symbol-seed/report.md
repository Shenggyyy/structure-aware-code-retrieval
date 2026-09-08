# Retrieval Evaluation

Run: `symbol-seed`.
Benchmark: `repository-expanded` / `0.1.0`; split: `test`.
Strategy: `symbol`; evaluation unit: `symbol`.

Annotation status: **provisional**.
Unjudged results count as nonrelevant for scoring. Recall uses known positives only; these are not exhaustive relevance judgments.
Provisional labels require independent human review before formal claims.

Quality fingerprint: `8ca033d58577cce17de1fd5574ecd1742129bd06d1ba470b638285bbbaa08ec7`.

## Overall

Queries: 120; answerable: 120; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3917 | 0.3361 | 0.3917 | 0.3917 | 0.3917 |
| 5 | 0.1783 | 0.6875 | 0.5276 | 0.5459 | 0.1783 |
| 10 | 0.1042 | 0.7931 | 0.5438 | 0.5838 | 0.1042 |
| 20 | 0.0592 | 0.8722 | 0.5473 | 0.6072 | 0.0592 |

Warm retrieval: p50 105.575 ms; p95 605.536 ms.

## Returned context cost

Mean cost of one evidence chunk per returned unit. Lexical tokens are a proxy, not LLM tokens.

| K | UTF-8 bytes | Lines | Lexical tokens |
| --- | --- | --- | --- |
| 1 | 843.3 | 24.1 | 116.7 |
| 5 | 3779.4 | 106.8 | 524.1 |
| 10 | 7682.6 | 216.0 | 1077.3 |
| 20 | 14402.0 | 401.8 | 2031.0 |

Mean retrieval work: `{'seed_symbols': 0, 'edges_examined': 0, 'expanded_symbols': 0, 'edge_cap_seeds': 0}`.

## Repository: flask

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.4306 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1917 | 0.7292 | 0.6035 | 0.6119 | 0.1917 |
| 10 | 0.1083 | 0.8125 | 0.6210 | 0.6421 | 0.1083 |
| 20 | 0.0646 | 0.9375 | 0.6242 | 0.6791 | 0.0646 |

Warm retrieval: p50 105.575 ms; p95 220.520 ms.

## Repository: networkx

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.2917 | 0.2292 | 0.2917 | 0.2917 | 0.2917 |
| 5 | 0.1500 | 0.5417 | 0.4389 | 0.4278 | 0.1500 |
| 10 | 0.0917 | 0.6667 | 0.4495 | 0.4704 | 0.0917 |
| 20 | 0.0521 | 0.7500 | 0.4524 | 0.4945 | 0.0521 |

Warm retrieval: p50 538.483 ms; p95 678.924 ms.

## Repository: packaging

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.3125 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1667 | 0.6736 | 0.4819 | 0.5105 | 0.1667 |
| 10 | 0.0958 | 0.7500 | 0.4967 | 0.5383 | 0.0958 |
| 20 | 0.0583 | 0.8611 | 0.5021 | 0.5706 | 0.0583 |

Warm retrieval: p50 45.084 ms; p95 56.228 ms.

## Repository: rich

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3333 | 0.3125 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 0.1583 | 0.6458 | 0.4736 | 0.5005 | 0.1583 |
| 10 | 0.1042 | 0.8333 | 0.5056 | 0.5690 | 0.1042 |
| 20 | 0.0563 | 0.8750 | 0.5084 | 0.5815 | 0.0563 |

Warm retrieval: p50 137.066 ms; p95 254.063 ms.

## Repository: tomlkit

Queries: 24; answerable: 24; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.3958 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.2250 | 0.8472 | 0.6403 | 0.6788 | 0.2250 |
| 10 | 0.1208 | 0.9028 | 0.6462 | 0.6992 | 0.1208 |
| 20 | 0.0646 | 0.9375 | 0.6492 | 0.7103 | 0.0646 |

Warm retrieval: p50 48.691 ms; p95 67.439 ms.

## Category: behavior

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1750 | 0.1750 | 0.1750 | 0.1750 | 0.1750 |
| 5 | 0.1350 | 0.6750 | 0.3633 | 0.4412 | 0.1350 |
| 10 | 0.0825 | 0.8250 | 0.3839 | 0.4903 | 0.0825 |
| 20 | 0.0450 | 0.9000 | 0.3894 | 0.5097 | 0.0450 |

Warm retrieval: p50 103.296 ms; p95 621.755 ms.

## Category: cross_file

Queries: 40; answerable: 40; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.3250 | 0.1583 | 0.3250 | 0.3250 | 0.3250 |
| 5 | 0.2350 | 0.5625 | 0.4963 | 0.4484 | 0.2350 |
| 10 | 0.1425 | 0.6792 | 0.5178 | 0.4971 | 0.1425 |
| 20 | 0.0888 | 0.8417 | 0.5227 | 0.5480 | 0.0888 |

Warm retrieval: p50 107.145 ms; p95 606.174 ms.

## Category: symbol

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.8500 |
| 5 | 0.2000 | 1.0000 | 0.9017 | 0.9259 | 0.2000 |
| 10 | 0.1000 | 1.0000 | 0.9017 | 0.9259 | 0.1000 |
| 20 | 0.0500 | 1.0000 | 0.9017 | 0.9259 | 0.0500 |

Warm retrieval: p50 94.609 ms; p95 502.227 ms.

## Category: test

Queries: 20; answerable: 20; no-answer: 0.

| K | Precision | Recall | MRR | NDCG | Judged fraction |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| 5 | 0.1300 | 0.6500 | 0.5450 | 0.5702 | 0.1300 |
| 10 | 0.0750 | 0.7500 | 0.5577 | 0.6019 | 0.0750 |
| 20 | 0.0375 | 0.7500 | 0.5577 | 0.6019 | 0.0375 |

Warm retrieval: p50 116.677 ms; p95 685.414 ms.

## Timing and reproduction

Timing includes query preprocessing, scoring every chunk, result materialization, and deduplication to the selected unit. It excludes metric calculation, report writing, and one-time index/model loading.
Index/model load timings, individual latency samples, runtime/code/config provenance, and source fingerprints are in `summary.json` and `per_query.jsonl`.
Index load measurements are observed startup costs, not guaranteed cold disk-cache measurements. No OS cache flushing is performed.
Rankings are stored up to the largest configured K after all matching chunks have been considered. Repeat runs should match the quality fingerprint; timing will vary.
