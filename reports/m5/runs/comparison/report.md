# Retrieval Strategy Comparison

Baseline: `hybrid`; unit: `symbol`; annotation status: **provisional**.

Known-label development scores; unjudged candidates score zero. Paired wins/losses are descriptive, not significance tests.

| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 33.606 | 46.917 |
| hybrid | 5 | 0.1750 | 0.7250 | 0.6279 | 0.6079 | 33.606 | 46.917 |
| hybrid | 10 | 0.1025 | 0.8208 | 0.6394 | 0.6450 | 33.606 | 46.917 |
| hybrid | 20 | 0.0625 | 0.9292 | 0.6433 | 0.6789 | 33.606 | 46.917 |
| symbol | 1 | 0.4250 | 0.3542 | 0.4250 | 0.4250 | 71.584 | 110.269 |
| symbol | 5 | 0.1500 | 0.6333 | 0.5408 | 0.5292 | 71.584 | 110.269 |
| symbol | 10 | 0.0975 | 0.7917 | 0.5610 | 0.5823 | 71.584 | 110.269 |
| symbol | 20 | 0.0600 | 0.9333 | 0.5670 | 0.6202 | 71.584 | 110.269 |
| structure-full | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 41.080 | 56.953 |
| structure-full | 5 | 0.1950 | 0.7333 | 0.4483 | 0.4994 | 41.080 | 56.953 |
| structure-full | 10 | 0.1200 | 0.8875 | 0.4647 | 0.5545 | 41.080 | 56.953 |
| structure-full | 20 | 0.0650 | 0.9625 | 0.4684 | 0.5755 | 41.080 | 56.953 |
| structure-none | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 34.770 | 47.287 |
| structure-none | 5 | 0.1750 | 0.7250 | 0.6279 | 0.6079 | 34.770 | 47.287 |
| structure-none | 10 | 0.1025 | 0.8208 | 0.6394 | 0.6450 | 34.770 | 47.287 |
| structure-none | 20 | 0.0625 | 0.9292 | 0.6433 | 0.6789 | 34.770 | 47.287 |
| structure-containment | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 42.159 | 60.989 |
| structure-containment | 5 | 0.1650 | 0.6750 | 0.6133 | 0.5846 | 42.159 | 60.989 |
| structure-containment | 10 | 0.1050 | 0.8333 | 0.6307 | 0.6417 | 42.159 | 60.989 |
| structure-containment | 20 | 0.0638 | 0.9417 | 0.6346 | 0.6748 | 42.159 | 60.989 |
| structure-import | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 41.063 | 53.472 |
| structure-import | 5 | 0.1700 | 0.7000 | 0.6217 | 0.5971 | 41.063 | 53.472 |
| structure-import | 10 | 0.1025 | 0.8208 | 0.6369 | 0.6430 | 41.063 | 53.472 |
| structure-import | 20 | 0.0625 | 0.9292 | 0.6409 | 0.6769 | 41.063 | 53.472 |
| structure-call | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 42.224 | 60.152 |
| structure-call | 5 | 0.2000 | 0.7583 | 0.4696 | 0.5211 | 42.224 | 60.152 |
| structure-call | 10 | 0.1200 | 0.8875 | 0.4840 | 0.5697 | 42.224 | 60.152 |
| structure-call | 20 | 0.0650 | 0.9625 | 0.4877 | 0.5907 | 42.224 | 60.152 |
| structure-test | 1 | 0.4000 | 0.3167 | 0.4000 | 0.3833 | 40.199 | 54.103 |
| structure-test | 5 | 0.1800 | 0.7500 | 0.5842 | 0.5812 | 40.199 | 54.103 |
| structure-test | 10 | 0.1025 | 0.8208 | 0.5909 | 0.6082 | 40.199 | 54.103 |
| structure-test | 20 | 0.0625 | 0.9292 | 0.5948 | 0.6420 | 40.199 | 54.103 |
| structure-no-containment | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 41.392 | 54.981 |
| structure-no-containment | 5 | 0.2000 | 0.7583 | 0.4554 | 0.5108 | 41.392 | 54.981 |
| structure-no-containment | 10 | 0.1200 | 0.8875 | 0.4691 | 0.5587 | 41.392 | 54.981 |
| structure-no-containment | 20 | 0.0650 | 0.9625 | 0.4727 | 0.5798 | 41.392 | 54.981 |
| structure-no-import | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 40.910 | 54.440 |
| structure-no-import | 5 | 0.1950 | 0.7333 | 0.4483 | 0.4994 | 40.910 | 54.440 |
| structure-no-import | 10 | 0.1200 | 0.8875 | 0.4651 | 0.5548 | 40.910 | 54.440 |
| structure-no-import | 20 | 0.0650 | 0.9625 | 0.4687 | 0.5761 | 40.910 | 54.440 |
| structure-no-call | 1 | 0.4000 | 0.3167 | 0.4000 | 0.3833 | 40.773 | 57.096 |
| structure-no-call | 5 | 0.1700 | 0.7000 | 0.5708 | 0.5590 | 40.773 | 57.096 |
| structure-no-call | 10 | 0.1050 | 0.8333 | 0.5834 | 0.6060 | 40.773 | 57.096 |
| structure-no-call | 20 | 0.0625 | 0.9292 | 0.5873 | 0.6354 | 40.773 | 57.096 |
| structure-no-test | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 41.694 | 57.118 |
| structure-no-test | 5 | 0.1950 | 0.7333 | 0.4600 | 0.5075 | 41.694 | 57.118 |
| structure-no-test | 10 | 0.1200 | 0.8875 | 0.4758 | 0.5621 | 41.694 | 57.118 |
| structure-no-test | 20 | 0.0663 | 0.9750 | 0.4794 | 0.5868 | 41.694 | 57.118 |
| structure-symbol-seed | 1 | 0.3500 | 0.2958 | 0.3500 | 0.3333 | 75.407 | 115.044 |
| structure-symbol-seed | 5 | 0.1600 | 0.6417 | 0.4883 | 0.5088 | 75.407 | 115.044 |
| structure-symbol-seed | 10 | 0.1075 | 0.8333 | 0.5095 | 0.5719 | 75.407 | 115.044 |
| structure-symbol-seed | 20 | 0.0600 | 0.9167 | 0.5139 | 0.5956 | 75.407 | 115.044 |

See `comparison.json` for per-query paired differences and quality fingerprints.
Latency comes from separate recorded runs and depends on hardware/load; it includes query encoding and fusion, but excludes startup and offline embedding.
