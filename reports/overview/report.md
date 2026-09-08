# Saved Retrieval Evidence Overview

Result status: **provisional**; independent review complete: **false**.
Frozen plan: `00845048e1a4b2a002022fbe882fe72eff661e3426ebd402d7dd1f1c5cc0905d`.

Validated 45 saved runs across 3 separate roles, 170 queries, and 8 repositories.
This report reads saved evidence only; it does not rerun retrieval or call an LLM.

Quality fingerprints and aggregates are validated against saved rankings and per-query metrics, with plan, configuration, snapshot, and worker bindings checked.
Recorded query timing; outside the validated quality fingerprints.

## dev

40 queries; 2 repositories. Annotation status: **provisional**.

| Strategy | Unit | Recall@10 | Precision@10 | MRR@10 | NDCG@10 | Recorded p50 ms | Recorded p95 ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hybrid-seed | symbol | 0.8208 | 0.1025 | 0.6394 | 0.6450 | 35.17 | 50.79 |
| bm25-seed | symbol | 0.7542 | 0.0975 | 0.6182 | 0.6203 | 8.44 | 18.63 |
| dense-seed | symbol | 0.7833 | 0.1000 | 0.5738 | 0.5968 | 22.14 | 30.29 |
| symbol-seed | symbol | 0.7917 | 0.0975 | 0.5610 | 0.5823 | 70.75 | 98.99 |
| structure-full | symbol | 0.8875 | 0.1200 | 0.4647 | 0.5545 | 42.16 | 63.17 |
| structure-none | symbol | 0.8208 | 0.1025 | 0.6394 | 0.6450 | 35.60 | 47.90 |
| structure-containment | symbol | 0.8333 | 0.1050 | 0.6307 | 0.6417 | 40.02 | 53.61 |
| structure-import | symbol | 0.8208 | 0.1025 | 0.6369 | 0.6430 | 39.22 | 58.11 |
| structure-call | symbol | 0.8875 | 0.1200 | 0.4840 | 0.5697 | 40.30 | 52.86 |
| structure-test | symbol | 0.8208 | 0.1025 | 0.5909 | 0.6082 | 39.91 | 66.24 |
| structure-no-containment | symbol | 0.8875 | 0.1200 | 0.4691 | 0.5587 | 41.38 | 54.50 |
| structure-no-import | symbol | 0.8875 | 0.1200 | 0.4651 | 0.5548 | 43.95 | 71.67 |
| structure-no-call | symbol | 0.8333 | 0.1050 | 0.5834 | 0.6060 | 45.21 | 74.30 |
| structure-no-test | symbol | 0.8875 | 0.1200 | 0.4758 | 0.5621 | 49.46 | 80.83 |
| structure-symbol-seed | symbol | 0.8333 | 0.1075 | 0.5095 | 0.5719 | 106.79 | 198.71 |

## test

120 queries; 5 repositories. Annotation status: **provisional**.

| Strategy | Unit | Recall@10 | Precision@10 | MRR@10 | NDCG@10 | Recorded p50 ms | Recorded p95 ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hybrid-seed | symbol | 0.7944 | 0.1050 | 0.5637 | 0.5947 | 55.16 | 373.14 |
| bm25-seed | symbol | 0.6444 | 0.0825 | 0.4644 | 0.4854 | 12.05 | 150.69 |
| dense-seed | symbol | 0.7292 | 0.0958 | 0.5480 | 0.5675 | 32.42 | 171.72 |
| symbol-seed | symbol | 0.7931 | 0.1042 | 0.5438 | 0.5838 | 105.57 | 605.54 |
| structure-full | symbol | 0.7917 | 0.1067 | 0.4409 | 0.5109 | 54.52 | 391.98 |
| structure-none | symbol | 0.7944 | 0.1050 | 0.5637 | 0.5947 | 46.75 | 324.86 |
| structure-containment | symbol | 0.8042 | 0.1075 | 0.5591 | 0.5958 | 49.09 | 335.56 |
| structure-import | symbol | 0.7861 | 0.1042 | 0.5608 | 0.5903 | 47.41 | 336.35 |
| structure-call | symbol | 0.7875 | 0.1067 | 0.4497 | 0.5183 | 46.90 | 338.76 |
| structure-test | symbol | 0.7819 | 0.1033 | 0.5521 | 0.5805 | 51.62 | 360.83 |
| structure-no-containment | symbol | 0.7875 | 0.1058 | 0.4403 | 0.5082 | 52.24 | 362.42 |
| structure-no-import | symbol | 0.7917 | 0.1067 | 0.4370 | 0.5080 | 48.86 | 348.03 |
| structure-no-call | symbol | 0.7819 | 0.1033 | 0.5449 | 0.5758 | 55.05 | 380.37 |
| structure-no-test | symbol | 0.7917 | 0.1067 | 0.4453 | 0.5157 | 54.63 | 389.86 |
| structure-symbol-seed | symbol | 0.7972 | 0.1050 | 0.4558 | 0.5234 | 96.95 | 591.88 |

## public

10 queries; 1 repositories. Annotation status: **provisional**.

| Strategy | Unit | Recall@10 | Precision@10 | MRR@10 | NDCG@10 | Recorded p50 ms | Recorded p95 ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hybrid-seed | symbol | 0.5000 | 0.0500 | 0.3250 | 0.3693 | 79.70 | 161.33 |
| bm25-seed | symbol | 0.3000 | 0.0300 | 0.2333 | 0.2500 | 31.29 | 40.40 |
| dense-seed | symbol | 0.7000 | 0.0700 | 0.2975 | 0.3897 | 42.14 | 54.65 |
| symbol-seed | symbol | 0.6000 | 0.0600 | 0.2400 | 0.3261 | 330.32 | 418.01 |
| structure-full | symbol | 0.5000 | 0.0500 | 0.2500 | 0.3118 | 79.46 | 164.45 |
| structure-none | symbol | 0.5000 | 0.0500 | 0.3250 | 0.3693 | 75.61 | 166.24 |
| structure-containment | symbol | 0.5000 | 0.0500 | 0.3250 | 0.3693 | 94.80 | 168.14 |
| structure-import | symbol | 0.5000 | 0.0500 | 0.3250 | 0.3693 | 95.35 | 192.52 |
| structure-call | symbol | 0.5000 | 0.0500 | 0.2500 | 0.3118 | 89.30 | 173.67 |
| structure-test | symbol | 0.5000 | 0.0500 | 0.3250 | 0.3693 | 84.94 | 158.99 |
| structure-no-containment | symbol | 0.5000 | 0.0500 | 0.2500 | 0.3118 | 86.05 | 168.45 |
| structure-no-import | symbol | 0.5000 | 0.0500 | 0.2500 | 0.3118 | 101.34 | 182.20 |
| structure-no-call | symbol | 0.5000 | 0.0500 | 0.3250 | 0.3693 | 99.22 | 198.84 |
| structure-no-test | symbol | 0.5000 | 0.0500 | 0.2500 | 0.3118 | 97.12 | 191.30 |
| structure-symbol-seed | symbol | 0.6000 | 0.0600 | 0.2260 | 0.3138 | 362.60 | 461.48 |

## Interpretation limits

Known-label quality uses query-macro means over answerable questions; unjudged candidates score zero. Provisional labels and incomplete judgments require independent review before reviewed-quality claims.

Dataset roles are reported separately. The public adaptation uses full-repository symbol retrieval, not original RepoQA scoring. Exposed test outcomes cannot support further tuning while remaining an untouched test set.

Recorded timing reflects separate runs on an interactive host and excludes startup and offline construction. It does not establish production latency or reranking overhead. No LLM correctness, citation-support, or significance claim is made here.
