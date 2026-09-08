# Retrieval Strategy Comparison

Baseline: `hybrid-seed`; unit: `symbol`; annotation status: **provisional**.

Known-label scores; unjudged candidates score zero. Paired wins/losses are descriptive, not significance tests.

| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid-seed | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 35.170 | 50.789 |
| hybrid-seed | 5 | 0.1750 | 0.7250 | 0.6279 | 0.6079 | 35.170 | 50.789 |
| hybrid-seed | 10 | 0.1025 | 0.8208 | 0.6394 | 0.6450 | 35.170 | 50.789 |
| hybrid-seed | 20 | 0.0625 | 0.9292 | 0.6433 | 0.6789 | 35.170 | 50.789 |
| bm25-seed | 1 | 0.5000 | 0.4208 | 0.5000 | 0.4833 | 8.442 | 18.634 |
| bm25-seed | 5 | 0.1700 | 0.6875 | 0.6062 | 0.5931 | 8.442 | 18.634 |
| bm25-seed | 10 | 0.0975 | 0.7542 | 0.6182 | 0.6203 | 8.442 | 18.634 |
| bm25-seed | 20 | 0.0588 | 0.8917 | 0.6252 | 0.6553 | 8.442 | 18.634 |
| dense-seed | 1 | 0.4000 | 0.3417 | 0.4000 | 0.4000 | 22.136 | 30.291 |
| dense-seed | 5 | 0.1600 | 0.6583 | 0.5542 | 0.5494 | 22.136 | 30.291 |
| dense-seed | 10 | 0.1000 | 0.7833 | 0.5738 | 0.5968 | 22.136 | 30.291 |
| dense-seed | 20 | 0.0550 | 0.8542 | 0.5776 | 0.6151 | 22.136 | 30.291 |
| symbol-seed | 1 | 0.4250 | 0.3542 | 0.4250 | 0.4250 | 70.753 | 98.989 |
| symbol-seed | 5 | 0.1500 | 0.6333 | 0.5408 | 0.5292 | 70.753 | 98.989 |
| symbol-seed | 10 | 0.0975 | 0.7917 | 0.5610 | 0.5823 | 70.753 | 98.989 |
| symbol-seed | 20 | 0.0600 | 0.9333 | 0.5670 | 0.6202 | 70.753 | 98.989 |
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
| bm25-seed | 1 | precision | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 6/29/5 |
| bm25-seed | 1 | recall | +0.0292 | +0.0292 | withheld: insufficient repositories | 2 | 6/29/5 |
| bm25-seed | 1 | mrr | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 6/29/5 |
| bm25-seed | 1 | ndcg | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 6/29/5 |
| bm25-seed | 5 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 4/31/5 |
| bm25-seed | 5 | recall | -0.0375 | -0.0375 | withheld: insufficient repositories | 2 | 4/31/5 |
| bm25-seed | 5 | mrr | -0.0217 | -0.0217 | withheld: insufficient repositories | 2 | 7/23/10 |
| bm25-seed | 5 | ndcg | -0.0148 | -0.0148 | withheld: insufficient repositories | 2 | 10/20/10 |
| bm25-seed | 10 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 2/34/4 |
| bm25-seed | 10 | recall | -0.0667 | -0.0667 | withheld: insufficient repositories | 2 | 2/34/4 |
| bm25-seed | 10 | mrr | -0.0212 | -0.0212 | withheld: insufficient repositories | 2 | 8/21/11 |
| bm25-seed | 10 | ndcg | -0.0248 | -0.0248 | withheld: insufficient repositories | 2 | 11/18/11 |
| bm25-seed | 20 | precision | -0.0038 | -0.0037 | withheld: insufficient repositories | 2 | 2/34/4 |
| bm25-seed | 20 | recall | -0.0375 | -0.0375 | withheld: insufficient repositories | 2 | 2/34/4 |
| bm25-seed | 20 | mrr | -0.0181 | -0.0181 | withheld: insufficient repositories | 2 | 9/18/13 |
| bm25-seed | 20 | ndcg | -0.0237 | -0.0237 | withheld: insufficient repositories | 2 | 11/14/15 |
| dense-seed | 1 | precision | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 2/33/5 |
| dense-seed | 1 | recall | -0.0500 | -0.0500 | withheld: insufficient repositories | 2 | 2/33/5 |
| dense-seed | 1 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 2/33/5 |
| dense-seed | 1 | ndcg | -0.0583 | -0.0583 | withheld: insufficient repositories | 2 | 3/32/5 |
| dense-seed | 5 | precision | -0.0150 | -0.0150 | withheld: insufficient repositories | 2 | 4/29/7 |
| dense-seed | 5 | recall | -0.0667 | -0.0667 | withheld: insufficient repositories | 2 | 4/29/7 |
| dense-seed | 5 | mrr | -0.0737 | -0.0738 | withheld: insufficient repositories | 2 | 6/22/12 |
| dense-seed | 5 | ndcg | -0.0585 | -0.0585 | withheld: insufficient repositories | 2 | 8/20/12 |
| dense-seed | 10 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 2/34/4 |
| dense-seed | 10 | recall | -0.0375 | -0.0375 | withheld: insufficient repositories | 2 | 2/34/4 |
| dense-seed | 10 | mrr | -0.0656 | -0.0656 | withheld: insufficient repositories | 2 | 7/20/13 |
| dense-seed | 10 | ndcg | -0.0483 | -0.0483 | withheld: insufficient repositories | 2 | 9/17/14 |
| dense-seed | 20 | precision | -0.0075 | -0.0075 | withheld: insufficient repositories | 2 | 0/34/6 |
| dense-seed | 20 | recall | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/34/6 |
| dense-seed | 20 | mrr | -0.0657 | -0.0657 | withheld: insufficient repositories | 2 | 7/20/13 |
| dense-seed | 20 | ndcg | -0.0639 | -0.0639 | withheld: insufficient repositories | 2 | 8/15/17 |
| symbol-seed | 1 | precision | -0.0500 | -0.0500 | withheld: insufficient repositories | 2 | 5/28/7 |
| symbol-seed | 1 | recall | -0.0375 | -0.0375 | withheld: insufficient repositories | 2 | 5/28/7 |
| symbol-seed | 1 | mrr | -0.0500 | -0.0500 | withheld: insufficient repositories | 2 | 5/28/7 |
| symbol-seed | 1 | ndcg | -0.0333 | -0.0333 | withheld: insufficient repositories | 2 | 5/28/7 |
| symbol-seed | 5 | precision | -0.0250 | -0.0250 | withheld: insufficient repositories | 2 | 4/29/7 |
| symbol-seed | 5 | recall | -0.0917 | -0.0917 | withheld: insufficient repositories | 2 | 4/29/7 |
| symbol-seed | 5 | mrr | -0.0871 | -0.0871 | withheld: insufficient repositories | 2 | 8/20/12 |
| symbol-seed | 5 | ndcg | -0.0788 | -0.0788 | withheld: insufficient repositories | 2 | 9/19/12 |
| symbol-seed | 10 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 4/31/5 |
| symbol-seed | 10 | recall | -0.0292 | -0.0292 | withheld: insufficient repositories | 2 | 4/31/5 |
| symbol-seed | 10 | mrr | -0.0784 | -0.0784 | withheld: insufficient repositories | 2 | 10/17/13 |
| symbol-seed | 10 | ndcg | -0.0627 | -0.0627 | withheld: insufficient repositories | 2 | 13/13/14 |
| symbol-seed | 20 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 2/34/4 |
| symbol-seed | 20 | recall | +0.0042 | +0.0042 | withheld: insufficient repositories | 2 | 2/34/4 |
| symbol-seed | 20 | mrr | -0.0763 | -0.0763 | withheld: insufficient repositories | 2 | 10/16/14 |
| symbol-seed | 20 | ndcg | -0.0587 | -0.0587 | withheld: insufficient repositories | 2 | 11/11/18 |
| structure-full | 1 | precision | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-full | 1 | recall | -0.2208 | -0.2208 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-full | 1 | mrr | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-full | 1 | ndcg | -0.2333 | -0.2333 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-full | 5 | precision | +0.0200 | +0.0200 | withheld: insufficient repositories | 2 | 7/29/4 |
| structure-full | 5 | recall | +0.0083 | +0.0083 | withheld: insufficient repositories | 2 | 7/29/4 |
| structure-full | 5 | mrr | -0.1796 | -0.1796 | withheld: insufficient repositories | 2 | 3/19/18 |
| structure-full | 5 | ndcg | -0.1085 | -0.1085 | withheld: insufficient repositories | 2 | 7/17/16 |
| structure-full | 10 | precision | +0.0175 | +0.0175 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-full | 10 | recall | +0.0667 | +0.0667 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-full | 10 | mrr | -0.1747 | -0.1747 | withheld: insufficient repositories | 2 | 3/17/20 |
| structure-full | 10 | ndcg | -0.0906 | -0.0906 | withheld: insufficient repositories | 2 | 7/15/18 |
| structure-full | 20 | precision | +0.0025 | +0.0025 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-full | 20 | recall | +0.0333 | +0.0333 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-full | 20 | mrr | -0.1749 | -0.1749 | withheld: insufficient repositories | 2 | 4/15/21 |
| structure-full | 20 | ndcg | -0.1034 | -0.1034 | withheld: insufficient repositories | 2 | 7/13/20 |
| structure-none | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 5 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 5 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 10 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 10 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 20 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-none | 20 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-containment | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-containment | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-containment | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-containment | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-containment | 5 | precision | -0.0100 | -0.0100 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-containment | 5 | recall | -0.0500 | -0.0500 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-containment | 5 | mrr | -0.0146 | -0.0146 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-containment | 5 | ndcg | -0.0233 | -0.0233 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-containment | 10 | precision | +0.0025 | +0.0025 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-containment | 10 | recall | +0.0125 | +0.0125 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-containment | 10 | mrr | -0.0087 | -0.0087 | withheld: insufficient repositories | 2 | 0/35/5 |
| structure-containment | 10 | ndcg | -0.0033 | -0.0033 | withheld: insufficient repositories | 2 | 1/33/6 |
| structure-containment | 20 | precision | +0.0013 | +0.0013 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-containment | 20 | recall | +0.0125 | +0.0125 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-containment | 20 | mrr | -0.0087 | -0.0087 | withheld: insufficient repositories | 2 | 0/35/5 |
| structure-containment | 20 | ndcg | -0.0042 | -0.0042 | withheld: insufficient repositories | 2 | 2/32/6 |
| structure-import | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-import | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-import | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-import | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-import | 5 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 0/39/1 |
| structure-import | 5 | recall | -0.0250 | -0.0250 | withheld: insufficient repositories | 2 | 0/39/1 |
| structure-import | 5 | mrr | -0.0063 | -0.0063 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-import | 5 | ndcg | -0.0108 | -0.0108 | withheld: insufficient repositories | 2 | 0/38/2 |
| structure-import | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-import | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-import | 10 | mrr | -0.0024 | -0.0024 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-import | 10 | ndcg | -0.0021 | -0.0021 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-import | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-import | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-import | 20 | mrr | -0.0024 | -0.0024 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-import | 20 | ndcg | -0.0021 | -0.0021 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-call | 1 | precision | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-call | 1 | recall | -0.2208 | -0.2208 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-call | 1 | mrr | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-call | 1 | ndcg | -0.2333 | -0.2333 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-call | 5 | precision | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 6/32/2 |
| structure-call | 5 | recall | +0.0333 | +0.0333 | withheld: insufficient repositories | 2 | 6/32/2 |
| structure-call | 5 | mrr | -0.1583 | -0.1583 | withheld: insufficient repositories | 2 | 2/23/15 |
| structure-call | 5 | ndcg | -0.0868 | -0.0868 | withheld: insufficient repositories | 2 | 6/21/13 |
| structure-call | 10 | precision | +0.0175 | +0.0175 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-call | 10 | recall | +0.0667 | +0.0667 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-call | 10 | mrr | -0.1554 | -0.1554 | withheld: insufficient repositories | 2 | 2/21/17 |
| structure-call | 10 | ndcg | -0.0753 | -0.0753 | withheld: insufficient repositories | 2 | 6/19/15 |
| structure-call | 20 | precision | +0.0025 | +0.0025 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-call | 20 | recall | +0.0333 | +0.0333 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-call | 20 | mrr | -0.1557 | -0.1557 | withheld: insufficient repositories | 2 | 3/19/18 |
| structure-call | 20 | ndcg | -0.0882 | -0.0882 | withheld: insufficient repositories | 2 | 6/17/17 |
| structure-test | 1 | precision | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-test | 1 | recall | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-test | 1 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-test | 1 | ndcg | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-test | 5 | precision | +0.0050 | +0.0050 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-test | 5 | recall | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-test | 5 | mrr | -0.0438 | -0.0438 | withheld: insufficient repositories | 2 | 1/35/4 |
| structure-test | 5 | ndcg | -0.0267 | -0.0267 | withheld: insufficient repositories | 2 | 1/35/4 |
| structure-test | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-test | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-test | 10 | mrr | -0.0485 | -0.0485 | withheld: insufficient repositories | 2 | 1/34/5 |
| structure-test | 10 | ndcg | -0.0369 | -0.0369 | withheld: insufficient repositories | 2 | 1/33/6 |
| structure-test | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-test | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-test | 20 | mrr | -0.0485 | -0.0485 | withheld: insufficient repositories | 2 | 1/34/5 |
| structure-test | 20 | ndcg | -0.0370 | -0.0370 | withheld: insufficient repositories | 2 | 1/32/7 |
| structure-no-containment | 1 | precision | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-containment | 1 | recall | -0.2208 | -0.2208 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-containment | 1 | mrr | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-containment | 1 | ndcg | -0.2333 | -0.2333 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-containment | 5 | precision | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 7/30/3 |
| structure-no-containment | 5 | recall | +0.0333 | +0.0333 | withheld: insufficient repositories | 2 | 7/30/3 |
| structure-no-containment | 5 | mrr | -0.1725 | -0.1725 | withheld: insufficient repositories | 2 | 3/20/17 |
| structure-no-containment | 5 | ndcg | -0.0971 | -0.0971 | withheld: insufficient repositories | 2 | 7/18/15 |
| structure-no-containment | 10 | precision | +0.0175 | +0.0175 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-no-containment | 10 | recall | +0.0667 | +0.0667 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-no-containment | 10 | mrr | -0.1703 | -0.1703 | withheld: insufficient repositories | 2 | 3/18/19 |
| structure-no-containment | 10 | ndcg | -0.0863 | -0.0863 | withheld: insufficient repositories | 2 | 7/16/17 |
| structure-no-containment | 20 | precision | +0.0025 | +0.0025 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-no-containment | 20 | recall | +0.0333 | +0.0333 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-no-containment | 20 | mrr | -0.1706 | -0.1706 | withheld: insufficient repositories | 2 | 4/16/20 |
| structure-no-containment | 20 | ndcg | -0.0992 | -0.0992 | withheld: insufficient repositories | 2 | 7/14/19 |
| structure-no-import | 1 | precision | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-import | 1 | recall | -0.2208 | -0.2208 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-import | 1 | mrr | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-import | 1 | ndcg | -0.2333 | -0.2333 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-import | 5 | precision | +0.0200 | +0.0200 | withheld: insufficient repositories | 2 | 7/29/4 |
| structure-no-import | 5 | recall | +0.0083 | +0.0083 | withheld: insufficient repositories | 2 | 7/29/4 |
| structure-no-import | 5 | mrr | -0.1796 | -0.1796 | withheld: insufficient repositories | 2 | 3/19/18 |
| structure-no-import | 5 | ndcg | -0.1085 | -0.1085 | withheld: insufficient repositories | 2 | 7/17/16 |
| structure-no-import | 10 | precision | +0.0175 | +0.0175 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-no-import | 10 | recall | +0.0667 | +0.0667 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-no-import | 10 | mrr | -0.1743 | -0.1743 | withheld: insufficient repositories | 2 | 3/17/20 |
| structure-no-import | 10 | ndcg | -0.0902 | -0.0902 | withheld: insufficient repositories | 2 | 7/15/18 |
| structure-no-import | 20 | precision | +0.0025 | +0.0025 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-no-import | 20 | recall | +0.0333 | +0.0333 | withheld: insufficient repositories | 2 | 2/38/0 |
| structure-no-import | 20 | mrr | -0.1746 | -0.1746 | withheld: insufficient repositories | 2 | 4/15/21 |
| structure-no-import | 20 | ndcg | -0.1028 | -0.1028 | withheld: insufficient repositories | 2 | 7/13/20 |
| structure-no-call | 1 | precision | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-no-call | 1 | recall | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-no-call | 1 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-no-call | 1 | ndcg | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/37/3 |
| structure-no-call | 5 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 1/37/2 |
| structure-no-call | 5 | recall | -0.0250 | -0.0250 | withheld: insufficient repositories | 2 | 1/37/2 |
| structure-no-call | 5 | mrr | -0.0571 | -0.0571 | withheld: insufficient repositories | 2 | 1/32/7 |
| structure-no-call | 5 | ndcg | -0.0489 | -0.0489 | withheld: insufficient repositories | 2 | 1/32/7 |
| structure-no-call | 10 | precision | +0.0025 | +0.0025 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-call | 10 | recall | +0.0125 | +0.0125 | withheld: insufficient repositories | 2 | 1/39/0 |
| structure-no-call | 10 | mrr | -0.0560 | -0.0560 | withheld: insufficient repositories | 2 | 1/30/9 |
| structure-no-call | 10 | ndcg | -0.0391 | -0.0391 | withheld: insufficient repositories | 2 | 2/27/11 |
| structure-no-call | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-call | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 2 | 0/40/0 |
| structure-no-call | 20 | mrr | -0.0560 | -0.0560 | withheld: insufficient repositories | 2 | 1/30/9 |
| structure-no-call | 20 | ndcg | -0.0436 | -0.0436 | withheld: insufficient repositories | 2 | 2/25/13 |
| structure-no-test | 1 | precision | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-test | 1 | recall | -0.2208 | -0.2208 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-test | 1 | mrr | -0.2500 | -0.2500 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-test | 1 | ndcg | -0.2333 | -0.2333 | withheld: insufficient repositories | 2 | 1/28/11 |
| structure-no-test | 5 | precision | +0.0200 | +0.0200 | withheld: insufficient repositories | 2 | 6/31/3 |
| structure-no-test | 5 | recall | +0.0083 | +0.0083 | withheld: insufficient repositories | 2 | 6/31/3 |
| structure-no-test | 5 | mrr | -0.1679 | -0.1679 | withheld: insufficient repositories | 2 | 2/21/17 |
| structure-no-test | 5 | ndcg | -0.1004 | -0.1004 | withheld: insufficient repositories | 2 | 6/19/15 |
| structure-no-test | 10 | precision | +0.0175 | +0.0175 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-no-test | 10 | recall | +0.0667 | +0.0667 | withheld: insufficient repositories | 2 | 5/35/0 |
| structure-no-test | 10 | mrr | -0.1636 | -0.1636 | withheld: insufficient repositories | 2 | 2/18/20 |
| structure-no-test | 10 | ndcg | -0.0829 | -0.0829 | withheld: insufficient repositories | 2 | 6/16/18 |
| structure-no-test | 20 | precision | +0.0037 | +0.0037 | withheld: insufficient repositories | 2 | 3/37/0 |
| structure-no-test | 20 | recall | +0.0458 | +0.0458 | withheld: insufficient repositories | 2 | 3/37/0 |
| structure-no-test | 20 | mrr | -0.1639 | -0.1639 | withheld: insufficient repositories | 2 | 3/16/21 |
| structure-no-test | 20 | ndcg | -0.0922 | -0.0922 | withheld: insufficient repositories | 2 | 7/14/19 |
| structure-symbol-seed | 1 | precision | -0.1250 | -0.1250 | withheld: insufficient repositories | 2 | 5/25/10 |
| structure-symbol-seed | 1 | recall | -0.0958 | -0.0958 | withheld: insufficient repositories | 2 | 5/25/10 |
| structure-symbol-seed | 1 | mrr | -0.1250 | -0.1250 | withheld: insufficient repositories | 2 | 5/25/10 |
| structure-symbol-seed | 1 | ndcg | -0.1250 | -0.1250 | withheld: insufficient repositories | 2 | 6/23/11 |
| structure-symbol-seed | 5 | precision | -0.0150 | -0.0150 | withheld: insufficient repositories | 2 | 7/24/9 |
| structure-symbol-seed | 5 | recall | -0.0833 | -0.0833 | withheld: insufficient repositories | 2 | 7/24/9 |
| structure-symbol-seed | 5 | mrr | -0.1396 | -0.1396 | withheld: insufficient repositories | 2 | 8/16/16 |
| structure-symbol-seed | 5 | ndcg | -0.0991 | -0.0991 | withheld: insufficient repositories | 2 | 12/12/16 |
| structure-symbol-seed | 10 | precision | +0.0050 | +0.0050 | withheld: insufficient repositories | 2 | 8/27/5 |
| structure-symbol-seed | 10 | recall | +0.0125 | +0.0125 | withheld: insufficient repositories | 2 | 8/27/5 |
| structure-symbol-seed | 10 | mrr | -0.1299 | -0.1299 | withheld: insufficient repositories | 2 | 10/13/17 |
| structure-symbol-seed | 10 | ndcg | -0.0731 | -0.0731 | withheld: insufficient repositories | 2 | 16/8/16 |
| structure-symbol-seed | 20 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 3/32/5 |
| structure-symbol-seed | 20 | recall | -0.0125 | -0.0125 | withheld: insufficient repositories | 2 | 3/32/5 |
| structure-symbol-seed | 20 | mrr | -0.1294 | -0.1294 | withheld: insufficient repositories | 2 | 10/12/18 |
| structure-symbol-seed | 20 | ndcg | -0.0833 | -0.0833 | withheld: insufficient repositories | 2 | 14/7/19 |

See `comparison.json` for per-query paired differences and quality fingerprints.
Latency comes from separate recorded runs and depends on hardware/load; it includes query encoding and fusion, but excludes startup and offline embedding.
