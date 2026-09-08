# Retrieval Strategy Comparison

Baseline: `structure-full`; unit: `symbol`; annotation status: **provisional**.

Known-label scores; unjudged candidates score zero. Paired wins/losses are descriptive, not significance tests.

| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| structure-full | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 42.158 | 63.172 |
| structure-full | 5 | 0.1950 | 0.7333 | 0.4483 | 0.4994 | 42.158 | 63.172 |
| structure-full | 10 | 0.1200 | 0.8875 | 0.4647 | 0.5545 | 42.158 | 63.172 |
| structure-full | 20 | 0.0650 | 0.9625 | 0.4684 | 0.5755 | 42.158 | 63.172 |
| structure-none | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 35.598 | 47.900 |
| structure-none | 5 | 0.1750 | 0.7250 | 0.6279 | 0.6079 | 35.598 | 47.900 |
| structure-none | 10 | 0.1025 | 0.8208 | 0.6394 | 0.6450 | 35.598 | 47.900 |
| structure-none | 20 | 0.0625 | 0.9292 | 0.6433 | 0.6789 | 35.598 | 47.900 |
| structure-containment | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 40.020 | 53.611 |
| structure-containment | 5 | 0.1650 | 0.6750 | 0.6133 | 0.5846 | 40.020 | 53.611 |
| structure-containment | 10 | 0.1050 | 0.8333 | 0.6307 | 0.6417 | 40.020 | 53.611 |
| structure-containment | 20 | 0.0638 | 0.9417 | 0.6346 | 0.6748 | 40.020 | 53.611 |
| structure-import | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 39.221 | 58.106 |
| structure-import | 5 | 0.1700 | 0.7000 | 0.6217 | 0.5971 | 39.221 | 58.106 |
| structure-import | 10 | 0.1025 | 0.8208 | 0.6369 | 0.6430 | 39.221 | 58.106 |
| structure-import | 20 | 0.0625 | 0.9292 | 0.6409 | 0.6769 | 39.221 | 58.106 |
| structure-call | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 40.302 | 52.861 |
| structure-call | 5 | 0.2000 | 0.7583 | 0.4696 | 0.5211 | 40.302 | 52.861 |
| structure-call | 10 | 0.1200 | 0.8875 | 0.4840 | 0.5697 | 40.302 | 52.861 |
| structure-call | 20 | 0.0650 | 0.9625 | 0.4877 | 0.5907 | 40.302 | 52.861 |
| structure-test | 1 | 0.4000 | 0.3167 | 0.4000 | 0.3833 | 39.911 | 66.238 |
| structure-test | 5 | 0.1800 | 0.7500 | 0.5842 | 0.5812 | 39.911 | 66.238 |
| structure-test | 10 | 0.1025 | 0.8208 | 0.5909 | 0.6082 | 39.911 | 66.238 |
| structure-test | 20 | 0.0625 | 0.9292 | 0.5948 | 0.6420 | 39.911 | 66.238 |
| structure-no-containment | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 41.383 | 54.503 |
| structure-no-containment | 5 | 0.2000 | 0.7583 | 0.4554 | 0.5108 | 41.383 | 54.503 |
| structure-no-containment | 10 | 0.1200 | 0.8875 | 0.4691 | 0.5587 | 41.383 | 54.503 |
| structure-no-containment | 20 | 0.0650 | 0.9625 | 0.4727 | 0.5798 | 41.383 | 54.503 |
| structure-no-import | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 43.954 | 71.673 |
| structure-no-import | 5 | 0.1950 | 0.7333 | 0.4483 | 0.4994 | 43.954 | 71.673 |
| structure-no-import | 10 | 0.1200 | 0.8875 | 0.4651 | 0.5548 | 43.954 | 71.673 |
| structure-no-import | 20 | 0.0650 | 0.9625 | 0.4687 | 0.5761 | 43.954 | 71.673 |
| structure-no-call | 1 | 0.4000 | 0.3167 | 0.4000 | 0.3833 | 45.214 | 74.295 |
| structure-no-call | 5 | 0.1700 | 0.7000 | 0.5708 | 0.5590 | 45.214 | 74.295 |
| structure-no-call | 10 | 0.1050 | 0.8333 | 0.5834 | 0.6060 | 45.214 | 74.295 |
| structure-no-call | 20 | 0.0625 | 0.9292 | 0.5873 | 0.6354 | 45.214 | 74.295 |
| structure-no-test | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 49.463 | 80.831 |
| structure-no-test | 5 | 0.1950 | 0.7333 | 0.4600 | 0.5075 | 49.463 | 80.831 |
| structure-no-test | 10 | 0.1200 | 0.8875 | 0.4758 | 0.5621 | 49.463 | 80.831 |
| structure-no-test | 20 | 0.0663 | 0.9750 | 0.4794 | 0.5868 | 49.463 | 80.831 |
| structure-symbol-seed | 1 | 0.3500 | 0.2958 | 0.3500 | 0.3333 | 106.790 | 198.707 |
| structure-symbol-seed | 5 | 0.1600 | 0.6417 | 0.4883 | 0.5088 | 106.790 | 198.707 |
| structure-symbol-seed | 10 | 0.1075 | 0.8333 | 0.5095 | 0.5719 | 106.790 | 198.707 |
| structure-symbol-seed | 20 | 0.0600 | 0.9167 | 0.5139 | 0.5956 | 106.790 | 198.707 |

## Paired differences and uncertainty

Differences are candidate minus baseline over answerable queries. Resampling keeps all queries in a selected repository together and preserves pairing. Query-macro and equal-repository means are different estimands.
95% percentile intervals use 2000 draws, seed 0. Intervals are withheld below 5 contributing repositories (a reporting policy, not a sufficiency guarantee). Few or correlated repositories and incomplete labels limit inference; intervals do not correct label bias. No multiple-comparison correction or significance claim is made.

| Strategy | K | Metric | Query mean delta | Repo mean delta | 95% interval | Repos | W/T/L |
| --- | --- | --- | --- | --- | --- | --- | --- |
| structure-none | 1 | precision | +0.2500 | +0.2500 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-none | 1 | recall | +0.2208 | +0.2208 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-none | 1 | mrr | +0.2500 | +0.2500 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-none | 1 | ndcg | +0.2333 | +0.2333 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-none | 5 | precision | -0.0200 | -0.0200 | withheld: insufficient repositories | 2 | 4/29/7 |
| structure-none | 5 | recall | -0.0083 | -0.0083 | withheld: insufficient repositories | 2 | 4/29/7 |
| structure-none | 5 | mrr | +0.1796 | +0.1796 | withheld: insufficient repositories | 2 | 18/19/3 |
| structure-none | 5 | ndcg | +0.1085 | +0.1085 | withheld: insufficient repositories | 2 | 16/17/7 |
| structure-none | 10 | precision | -0.0175 | -0.0175 | withheld: insufficient repositories | 2 | 0/35/5 |
| structure-none | 10 | recall | -0.0667 | -0.0667 | withheld: insufficient repositories | 2 | 0/35/5 |
| structure-none | 10 | mrr | +0.1747 | +0.1747 | withheld: insufficient repositories | 2 | 20/17/3 |
| structure-none | 10 | ndcg | +0.0906 | +0.0906 | withheld: insufficient repositories | 2 | 18/15/7 |
| structure-none | 20 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-none | 20 | recall | -0.0333 | -0.0333 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-none | 20 | mrr | +0.1749 | +0.1749 | withheld: insufficient repositories | 2 | 21/15/4 |
| structure-none | 20 | ndcg | +0.1034 | +0.1034 | withheld: insufficient repositories | 2 | 20/13/7 |
| structure-containment | 1 | precision | +0.2500 | +0.2500 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-containment | 1 | recall | +0.2208 | +0.2208 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-containment | 1 | mrr | +0.2500 | +0.2500 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-containment | 1 | ndcg | +0.2333 | +0.2333 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-containment | 5 | precision | -0.0300 | -0.0300 | withheld: insufficient repositories | 2 | 2/31/7 |
| structure-containment | 5 | recall | -0.0583 | -0.0583 | withheld: insufficient repositories | 2 | 2/31/7 |
| structure-containment | 5 | mrr | +0.1650 | +0.1650 | withheld: insufficient repositories | 2 | 15/21/4 |
| structure-containment | 5 | ndcg | +0.0852 | +0.0852 | withheld: insufficient repositories | 2 | 13/19/8 |
| structure-containment | 10 | precision | -0.0150 | -0.0150 | withheld: insufficient repositories | 2 | 1/34/5 |
| structure-containment | 10 | recall | -0.0542 | -0.0542 | withheld: insufficient repositories | 2 | 1/34/5 |
| structure-containment | 10 | mrr | +0.1660 | +0.1660 | withheld: insufficient repositories | 2 | 17/19/4 |
| structure-containment | 10 | ndcg | +0.0872 | +0.0872 | withheld: insufficient repositories | 2 | 15/17/8 |
| structure-containment | 20 | precision | -0.0012 | -0.0012 | withheld: insufficient repositories | 2 | 1/37/2 |
| structure-containment | 20 | recall | -0.0208 | -0.0208 | withheld: insufficient repositories | 2 | 1/37/2 |
| structure-containment | 20 | mrr | +0.1663 | +0.1663 | withheld: insufficient repositories | 2 | 18/17/5 |
| structure-containment | 20 | ndcg | +0.0992 | +0.0992 | withheld: insufficient repositories | 2 | 18/14/8 |
| structure-import | 1 | precision | +0.2500 | +0.2500 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-import | 1 | recall | +0.2208 | +0.2208 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-import | 1 | mrr | +0.2500 | +0.2500 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-import | 1 | ndcg | +0.2333 | +0.2333 | withheld: insufficient repositories | 2 | 11/28/1 |
| structure-import | 5 | precision | -0.0250 | -0.0250 | withheld: insufficient repositories | 2 | 3/30/7 |
| structure-import | 5 | recall | -0.0333 | -0.0333 | withheld: insufficient repositories | 2 | 3/30/7 |
| structure-import | 5 | mrr | +0.1733 | +0.1733 | withheld: insufficient repositories | 2 | 17/20/3 |
| structure-import | 5 | ndcg | +0.0977 | +0.0977 | withheld: insufficient repositories | 2 | 15/18/7 |
| structure-import | 10 | precision | -0.0175 | -0.0175 | withheld: insufficient repositories | 2 | 0/35/5 |
| structure-import | 10 | recall | -0.0667 | -0.0667 | withheld: insufficient repositories | 2 | 0/35/5 |
| structure-import | 10 | mrr | +0.1722 | +0.1722 | withheld: insufficient repositories | 2 | 19/18/3 |
| structure-import | 10 | ndcg | +0.0885 | +0.0885 | withheld: insufficient repositories | 2 | 17/16/7 |
| structure-import | 20 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-import | 20 | recall | -0.0333 | -0.0333 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-import | 20 | mrr | +0.1725 | +0.1725 | withheld: insufficient repositories | 2 | 20/16/4 |
| structure-import | 20 | ndcg | +0.1013 | +0.1013 | withheld: insufficient repositories | 2 | 19/14/7 |
| structure-call | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-call | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-call | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-call | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-call | 5 | precision | +0.0050 | +0.0050 | withheld: insufficient repositories | 2 | 2/37/1 |
| structure-call | 5 | recall | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 2/37/1 |
| structure-call | 5 | mrr | +0.0212 | +0.0212 | withheld: insufficient repositories | 2 | 7/32/1 |
| structure-call | 5 | ndcg | +0.0217 | +0.0217 | withheld: insufficient repositories | 2 | 7/32/1 |
| structure-call | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-call | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-call | 10 | mrr | +0.0193 | +0.0193 | withheld: insufficient repositories | 2 | 10/29/1 |
| structure-call | 10 | ndcg | +0.0152 | +0.0152 | withheld: insufficient repositories | 2 | 12/27/1 |
| structure-call | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-call | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-call | 20 | mrr | +0.0193 | +0.0193 | withheld: insufficient repositories | 2 | 10/29/1 |
| structure-call | 20 | ndcg | +0.0152 | +0.0152 | withheld: insufficient repositories | 2 | 12/27/1 |
| structure-test | 1 | precision | +0.1750 | +0.1750 | withheld: insufficient repositories | 2 | 8/31/1 |
| structure-test | 1 | recall | +0.1458 | +0.1458 | withheld: insufficient repositories | 2 | 8/31/1 |
| structure-test | 1 | mrr | +0.1750 | +0.1750 | withheld: insufficient repositories | 2 | 8/31/1 |
| structure-test | 1 | ndcg | +0.1583 | +0.1583 | withheld: insufficient repositories | 2 | 8/31/1 |
| structure-test | 5 | precision | -0.0150 | -0.0150 | withheld: insufficient repositories | 2 | 4/30/6 |
| structure-test | 5 | recall | +0.0167 | +0.0167 | withheld: insufficient repositories | 2 | 4/30/6 |
| structure-test | 5 | mrr | +0.1358 | +0.1358 | withheld: insufficient repositories | 2 | 17/21/2 |
| structure-test | 5 | ndcg | +0.0818 | +0.0818 | withheld: insufficient repositories | 2 | 15/19/6 |
| structure-test | 10 | precision | -0.0175 | -0.0175 | withheld: insufficient repositories | 2 | 0/35/5 |
| structure-test | 10 | recall | -0.0667 | -0.0667 | withheld: insufficient repositories | 2 | 0/35/5 |
| structure-test | 10 | mrr | +0.1261 | +0.1261 | withheld: insufficient repositories | 2 | 19/19/2 |
| structure-test | 10 | ndcg | +0.0537 | +0.0537 | withheld: insufficient repositories | 2 | 17/17/6 |
| structure-test | 20 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-test | 20 | recall | -0.0333 | -0.0333 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-test | 20 | mrr | +0.1264 | +0.1264 | withheld: insufficient repositories | 2 | 20/17/3 |
| structure-test | 20 | ndcg | +0.0665 | +0.0665 | withheld: insufficient repositories | 2 | 19/15/6 |
| structure-no-containment | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-containment | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-containment | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-containment | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-containment | 5 | precision | +0.0050 | +0.0050 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-containment | 5 | recall | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-containment | 5 | mrr | +0.0071 | +0.0071 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-no-containment | 5 | ndcg | +0.0114 | +0.0114 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-no-containment | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-containment | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-containment | 10 | mrr | +0.0043 | +0.0043 | withheld: insufficient repositories | 2 | 4/36/0 |
| structure-no-containment | 10 | ndcg | +0.0042 | +0.0042 | withheld: insufficient repositories | 2 | 6/34/0 |
| structure-no-containment | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-containment | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-containment | 20 | mrr | +0.0043 | +0.0043 | withheld: insufficient repositories | 2 | 4/36/0 |
| structure-no-containment | 20 | ndcg | +0.0042 | +0.0042 | withheld: insufficient repositories | 2 | 6/34/0 |
| structure-no-import | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 5 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 5 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 10 | mrr | +0.0003 | +0.0003 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-import | 10 | ndcg | +0.0004 | +0.0004 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-import | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-import | 20 | mrr | +0.0003 | +0.0003 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-import | 20 | ndcg | +0.0006 | +0.0006 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-no-call | 1 | precision | +0.1750 | +0.1750 | withheld: insufficient repositories | 2 | 8/31/1 |
| structure-no-call | 1 | recall | +0.1458 | +0.1458 | withheld: insufficient repositories | 2 | 8/31/1 |
| structure-no-call | 1 | mrr | +0.1750 | +0.1750 | withheld: insufficient repositories | 2 | 8/31/1 |
| structure-no-call | 1 | ndcg | +0.1583 | +0.1583 | withheld: insufficient repositories | 2 | 8/31/1 |
| structure-no-call | 5 | precision | -0.0250 | -0.0250 | withheld: insufficient repositories | 2 | 2/32/6 |
| structure-no-call | 5 | recall | -0.0333 | -0.0333 | withheld: insufficient repositories | 2 | 2/32/6 |
| structure-no-call | 5 | mrr | +0.1225 | +0.1225 | withheld: insufficient repositories | 2 | 14/24/2 |
| structure-no-call | 5 | ndcg | +0.0596 | +0.0596 | withheld: insufficient repositories | 2 | 12/22/6 |
| structure-no-call | 10 | precision | -0.0150 | -0.0150 | withheld: insufficient repositories | 2 | 1/34/5 |
| structure-no-call | 10 | recall | -0.0542 | -0.0542 | withheld: insufficient repositories | 2 | 1/34/5 |
| structure-no-call | 10 | mrr | +0.1187 | +0.1187 | withheld: insufficient repositories | 2 | 16/21/3 |
| structure-no-call | 10 | ndcg | +0.0515 | +0.0515 | withheld: insufficient repositories | 2 | 14/19/7 |
| structure-no-call | 20 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-no-call | 20 | recall | -0.0333 | -0.0333 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-no-call | 20 | mrr | +0.1190 | +0.1190 | withheld: insufficient repositories | 2 | 17/19/4 |
| structure-no-call | 20 | ndcg | +0.0599 | +0.0599 | withheld: insufficient repositories | 2 | 16/17/7 |
| structure-no-test | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-test | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-test | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-test | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-test | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 1/38/1 |
| structure-no-test | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 1/38/1 |
| structure-no-test | 5 | mrr | +0.0117 | +0.0117 | withheld: insufficient repositories | 2 | 5/33/2 |
| structure-no-test | 5 | ndcg | +0.0081 | +0.0081 | withheld: insufficient repositories | 2 | 5/33/2 |
| structure-no-test | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-test | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-test | 10 | mrr | +0.0111 | +0.0111 | withheld: insufficient repositories | 2 | 6/31/3 |
| structure-no-test | 10 | ndcg | +0.0077 | +0.0077 | withheld: insufficient repositories | 2 | 6/31/3 |
| structure-no-test | 20 | precision | +0.0013 | +0.0013 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-test | 20 | recall | +0.0125 | +0.0125 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-test | 20 | mrr | +0.0111 | +0.0111 | withheld: insufficient repositories | 2 | 6/31/3 |
| structure-no-test | 20 | ndcg | +0.0113 | +0.0113 | withheld: insufficient repositories | 2 | 7/31/2 |
| structure-symbol-seed | 1 | precision | +0.1250 | +0.1250 | withheld: insufficient repositories | 2 | 9/27/4 |
| structure-symbol-seed | 1 | recall | +0.1250 | +0.1250 | withheld: insufficient repositories | 2 | 9/27/4 |
| structure-symbol-seed | 1 | mrr | +0.1250 | +0.1250 | withheld: insufficient repositories | 2 | 9/27/4 |
| structure-symbol-seed | 1 | ndcg | +0.1083 | +0.1083 | withheld: insufficient repositories | 2 | 9/27/4 |
| structure-symbol-seed | 5 | precision | -0.0350 | -0.0350 | withheld: insufficient repositories | 2 | 4/26/10 |
| structure-symbol-seed | 5 | recall | -0.0917 | -0.0917 | withheld: insufficient repositories | 2 | 4/26/10 |
| structure-symbol-seed | 5 | mrr | +0.0400 | +0.0400 | withheld: insufficient repositories | 2 | 14/14/12 |
| structure-symbol-seed | 5 | ndcg | +0.0094 | +0.0094 | withheld: insufficient repositories | 2 | 14/11/15 |
| structure-symbol-seed | 10 | precision | -0.0125 | -0.0125 | withheld: insufficient repositories | 2 | 3/30/7 |
| structure-symbol-seed | 10 | recall | -0.0542 | -0.0542 | withheld: insufficient repositories | 2 | 3/30/7 |
| structure-symbol-seed | 10 | mrr | +0.0448 | +0.0448 | withheld: insufficient repositories | 2 | 16/11/13 |
| structure-symbol-seed | 10 | ndcg | +0.0174 | +0.0174 | withheld: insufficient repositories | 2 | 17/7/16 |
| structure-symbol-seed | 20 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 1/34/5 |
| structure-symbol-seed | 20 | recall | -0.0458 | -0.0458 | withheld: insufficient repositories | 2 | 1/34/5 |
| structure-symbol-seed | 20 | mrr | +0.0455 | +0.0455 | withheld: insufficient repositories | 2 | 16/10/14 |
| structure-symbol-seed | 20 | ndcg | +0.0201 | +0.0201 | withheld: insufficient repositories | 2 | 17/6/17 |

See `comparison.json` for per-query paired differences and quality fingerprints.
Latency comes from separate recorded runs and depends on hardware/load; it includes query encoding and fusion, but excludes startup and offline embedding.
