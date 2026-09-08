# Retrieval Strategy Comparison

Baseline: `hybrid-seed`; unit: `symbol`; annotation status: **provisional**.

Known-label scores; unjudged candidates score zero. Paired wins/losses are descriptive, not significance tests.

| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid-seed | 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 79.697 | 161.330 |
| hybrid-seed | 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 79.697 | 161.330 |
| hybrid-seed | 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 79.697 | 161.330 |
| hybrid-seed | 20 | 0.0300 | 0.6000 | 0.3300 | 0.3920 | 79.697 | 161.330 |
| bm25-seed | 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 31.286 | 40.401 |
| bm25-seed | 5 | 0.0600 | 0.3000 | 0.2333 | 0.2500 | 31.286 | 40.401 |
| bm25-seed | 10 | 0.0300 | 0.3000 | 0.2333 | 0.2500 | 31.286 | 40.401 |
| bm25-seed | 20 | 0.0200 | 0.4000 | 0.2424 | 0.2779 | 31.286 | 40.401 |
| dense-seed | 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 42.144 | 54.645 |
| dense-seed | 5 | 0.1000 | 0.5000 | 0.2750 | 0.3292 | 42.144 | 54.645 |
| dense-seed | 10 | 0.0700 | 0.7000 | 0.2975 | 0.3897 | 42.144 | 54.645 |
| dense-seed | 20 | 0.0350 | 0.7000 | 0.2975 | 0.3897 | 42.144 | 54.645 |
| symbol-seed | 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 330.318 | 418.015 |
| symbol-seed | 5 | 0.1000 | 0.5000 | 0.2233 | 0.2905 | 330.318 | 418.015 |
| symbol-seed | 10 | 0.0600 | 0.6000 | 0.2400 | 0.3261 | 330.318 | 418.015 |
| symbol-seed | 20 | 0.0300 | 0.6000 | 0.2400 | 0.3261 | 330.318 | 418.015 |
| structure-full | 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 79.459 | 164.450 |
| structure-full | 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 79.459 | 164.450 |
| structure-full | 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 79.459 | 164.450 |
| structure-full | 20 | 0.0250 | 0.5000 | 0.2500 | 0.3118 | 79.459 | 164.450 |
| structure-none | 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 75.611 | 166.244 |
| structure-none | 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 75.611 | 166.244 |
| structure-none | 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 75.611 | 166.244 |
| structure-none | 20 | 0.0300 | 0.6000 | 0.3300 | 0.3920 | 75.611 | 166.244 |
| structure-containment | 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 94.804 | 168.143 |
| structure-containment | 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 94.804 | 168.143 |
| structure-containment | 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 94.804 | 168.143 |
| structure-containment | 20 | 0.0300 | 0.6000 | 0.3300 | 0.3920 | 94.804 | 168.143 |
| structure-import | 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 95.350 | 192.521 |
| structure-import | 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 95.350 | 192.521 |
| structure-import | 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 95.350 | 192.521 |
| structure-import | 20 | 0.0300 | 0.6000 | 0.3300 | 0.3920 | 95.350 | 192.521 |
| structure-call | 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 89.300 | 173.670 |
| structure-call | 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 89.300 | 173.670 |
| structure-call | 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 89.300 | 173.670 |
| structure-call | 20 | 0.0300 | 0.6000 | 0.2550 | 0.3346 | 89.300 | 173.670 |
| structure-test | 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 84.937 | 158.988 |
| structure-test | 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 84.937 | 158.988 |
| structure-test | 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 84.937 | 158.988 |
| structure-test | 20 | 0.0250 | 0.5000 | 0.3250 | 0.3693 | 84.937 | 158.988 |
| structure-no-containment | 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 86.049 | 168.451 |
| structure-no-containment | 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 86.049 | 168.451 |
| structure-no-containment | 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 86.049 | 168.451 |
| structure-no-containment | 20 | 0.0250 | 0.5000 | 0.2500 | 0.3118 | 86.049 | 168.451 |
| structure-no-import | 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 101.335 | 182.205 |
| structure-no-import | 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 101.335 | 182.205 |
| structure-no-import | 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 101.335 | 182.205 |
| structure-no-import | 20 | 0.0250 | 0.5000 | 0.2500 | 0.3118 | 101.335 | 182.205 |
| structure-no-call | 1 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 99.215 | 198.836 |
| structure-no-call | 5 | 0.1000 | 0.5000 | 0.3250 | 0.3693 | 99.215 | 198.836 |
| structure-no-call | 10 | 0.0500 | 0.5000 | 0.3250 | 0.3693 | 99.215 | 198.836 |
| structure-no-call | 20 | 0.0250 | 0.5000 | 0.3250 | 0.3693 | 99.215 | 198.836 |
| structure-no-test | 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 97.119 | 191.304 |
| structure-no-test | 5 | 0.0800 | 0.4000 | 0.2333 | 0.2762 | 97.119 | 191.304 |
| structure-no-test | 10 | 0.0500 | 0.5000 | 0.2500 | 0.3118 | 97.119 | 191.304 |
| structure-no-test | 20 | 0.0300 | 0.6000 | 0.2550 | 0.3346 | 97.119 | 191.304 |
| structure-symbol-seed | 1 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 362.601 | 461.480 |
| structure-symbol-seed | 5 | 0.0800 | 0.4000 | 0.1950 | 0.2448 | 362.601 | 461.480 |
| structure-symbol-seed | 10 | 0.0600 | 0.6000 | 0.2260 | 0.3138 | 362.601 | 461.480 |
| structure-symbol-seed | 20 | 0.0300 | 0.6000 | 0.2260 | 0.3138 | 362.601 | 461.480 |

## Paired differences and uncertainty

Differences are candidate minus baseline over answerable queries. Resampling keeps all queries in a selected repository together and preserves pairing. Query-macro and equal-repository means are different estimands.
95% percentile intervals use 2000 draws, seed 0. Intervals are withheld below 5 contributing repositories (a reporting policy, not a sufficiency guarantee). Few or correlated repositories and incomplete labels limit inference; intervals do not correct label bias. No multiple-comparison correction or significance claim is made.

| Strategy | K | Metric | Query mean delta | Repo mean delta | 95% interval | Repos | W/T/L |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bm25-seed | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| bm25-seed | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| bm25-seed | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| bm25-seed | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| bm25-seed | 5 | precision | -0.0400 | -0.0400 | withheld: insufficient repositories | 1 | 0/8/2 |
| bm25-seed | 5 | recall | -0.2000 | -0.2000 | withheld: insufficient repositories | 1 | 0/8/2 |
| bm25-seed | 5 | mrr | -0.0917 | -0.0917 | withheld: insufficient repositories | 1 | 0/7/3 |
| bm25-seed | 5 | ndcg | -0.1193 | -0.1193 | withheld: insufficient repositories | 1 | 0/7/3 |
| bm25-seed | 10 | precision | -0.0200 | -0.0200 | withheld: insufficient repositories | 1 | 0/8/2 |
| bm25-seed | 10 | recall | -0.2000 | -0.2000 | withheld: insufficient repositories | 1 | 0/8/2 |
| bm25-seed | 10 | mrr | -0.0917 | -0.0917 | withheld: insufficient repositories | 1 | 0/7/3 |
| bm25-seed | 10 | ndcg | -0.1193 | -0.1193 | withheld: insufficient repositories | 1 | 0/7/3 |
| bm25-seed | 20 | precision | -0.0100 | -0.0100 | withheld: insufficient repositories | 1 | 0/8/2 |
| bm25-seed | 20 | recall | -0.2000 | -0.2000 | withheld: insufficient repositories | 1 | 0/8/2 |
| bm25-seed | 20 | mrr | -0.0876 | -0.0876 | withheld: insufficient repositories | 1 | 0/6/4 |
| bm25-seed | 20 | ndcg | -0.1141 | -0.1141 | withheld: insufficient repositories | 1 | 0/6/4 |
| dense-seed | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| dense-seed | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| dense-seed | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| dense-seed | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| dense-seed | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| dense-seed | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| dense-seed | 5 | mrr | -0.0500 | -0.0500 | withheld: insufficient repositories | 1 | 0/8/2 |
| dense-seed | 5 | ndcg | -0.0401 | -0.0401 | withheld: insufficient repositories | 1 | 0/8/2 |
| dense-seed | 10 | precision | +0.0200 | +0.0200 | withheld: insufficient repositories | 1 | 2/8/0 |
| dense-seed | 10 | recall | +0.2000 | +0.2000 | withheld: insufficient repositories | 1 | 2/8/0 |
| dense-seed | 10 | mrr | -0.0275 | -0.0275 | withheld: insufficient repositories | 1 | 2/6/2 |
| dense-seed | 10 | ndcg | +0.0204 | +0.0204 | withheld: insufficient repositories | 1 | 2/6/2 |
| dense-seed | 20 | precision | +0.0050 | +0.0050 | withheld: insufficient repositories | 1 | 1/9/0 |
| dense-seed | 20 | recall | +0.1000 | +0.1000 | withheld: insufficient repositories | 1 | 1/9/0 |
| dense-seed | 20 | mrr | -0.0325 | -0.0325 | withheld: insufficient repositories | 1 | 2/6/2 |
| dense-seed | 20 | ndcg | -0.0024 | -0.0024 | withheld: insufficient repositories | 1 | 2/6/2 |
| symbol-seed | 1 | precision | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| symbol-seed | 1 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| symbol-seed | 1 | mrr | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| symbol-seed | 1 | ndcg | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| symbol-seed | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 1/8/1 |
| symbol-seed | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 1/8/1 |
| symbol-seed | 5 | mrr | -0.1017 | -0.1017 | withheld: insufficient repositories | 1 | 3/4/3 |
| symbol-seed | 5 | ndcg | -0.0788 | -0.0788 | withheld: insufficient repositories | 1 | 3/4/3 |
| symbol-seed | 10 | precision | +0.0100 | +0.0100 | withheld: insufficient repositories | 1 | 1/9/0 |
| symbol-seed | 10 | recall | +0.1000 | +0.1000 | withheld: insufficient repositories | 1 | 1/9/0 |
| symbol-seed | 10 | mrr | -0.0850 | -0.0850 | withheld: insufficient repositories | 1 | 3/4/3 |
| symbol-seed | 10 | ndcg | -0.0432 | -0.0432 | withheld: insufficient repositories | 1 | 3/4/3 |
| symbol-seed | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| symbol-seed | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| symbol-seed | 20 | mrr | -0.0900 | -0.0900 | withheld: insufficient repositories | 1 | 3/4/3 |
| symbol-seed | 20 | ndcg | -0.0659 | -0.0659 | withheld: insufficient repositories | 1 | 3/4/3 |
| structure-full | 1 | precision | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-full | 1 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-full | 1 | mrr | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-full | 1 | ndcg | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-full | 5 | precision | -0.0200 | -0.0200 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-full | 5 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-full | 5 | mrr | -0.0917 | -0.0917 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-full | 5 | ndcg | -0.0931 | -0.0931 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-full | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-full | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-full | 10 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-full | 10 | ndcg | -0.0574 | -0.0574 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-full | 20 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-full | 20 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-full | 20 | mrr | -0.0800 | -0.0800 | withheld: insufficient repositories | 1 | 0/6/4 |
| structure-full | 20 | ndcg | -0.0802 | -0.0802 | withheld: insufficient repositories | 1 | 0/6/4 |
| structure-none | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 5 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 5 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 10 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 10 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 20 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-none | 20 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 5 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 5 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 10 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 10 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 20 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-containment | 20 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 5 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 5 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 10 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 10 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 20 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-import | 20 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-call | 1 | precision | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-call | 1 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-call | 1 | mrr | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-call | 1 | ndcg | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-call | 5 | precision | -0.0200 | -0.0200 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-call | 5 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-call | 5 | mrr | -0.0917 | -0.0917 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-call | 5 | ndcg | -0.0931 | -0.0931 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-call | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-call | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-call | 10 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-call | 10 | ndcg | -0.0574 | -0.0574 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-call | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-call | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-call | 20 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-call | 20 | ndcg | -0.0574 | -0.0574 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-test | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 5 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 5 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 10 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 10 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-test | 20 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-test | 20 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-test | 20 | mrr | -0.0050 | -0.0050 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-test | 20 | ndcg | -0.0228 | -0.0228 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 1 | precision | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 1 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 1 | mrr | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 1 | ndcg | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 5 | precision | -0.0200 | -0.0200 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 5 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 5 | mrr | -0.0917 | -0.0917 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-containment | 5 | ndcg | -0.0931 | -0.0931 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-containment | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-containment | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-containment | 10 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-containment | 10 | ndcg | -0.0574 | -0.0574 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-containment | 20 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 20 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-containment | 20 | mrr | -0.0800 | -0.0800 | withheld: insufficient repositories | 1 | 0/6/4 |
| structure-no-containment | 20 | ndcg | -0.0802 | -0.0802 | withheld: insufficient repositories | 1 | 0/6/4 |
| structure-no-import | 1 | precision | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-import | 1 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-import | 1 | mrr | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-import | 1 | ndcg | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-import | 5 | precision | -0.0200 | -0.0200 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-import | 5 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-import | 5 | mrr | -0.0917 | -0.0917 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-import | 5 | ndcg | -0.0931 | -0.0931 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-import | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-import | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-import | 10 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-import | 10 | ndcg | -0.0574 | -0.0574 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-import | 20 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-import | 20 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-import | 20 | mrr | -0.0800 | -0.0800 | withheld: insufficient repositories | 1 | 0/6/4 |
| structure-no-import | 20 | ndcg | -0.0802 | -0.0802 | withheld: insufficient repositories | 1 | 0/6/4 |
| structure-no-call | 1 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 1 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 1 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 1 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 5 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 5 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 5 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 5 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 10 | mrr | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 10 | ndcg | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-call | 20 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-call | 20 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-call | 20 | mrr | -0.0050 | -0.0050 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-call | 20 | ndcg | -0.0228 | -0.0228 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-test | 1 | precision | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-test | 1 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-test | 1 | mrr | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-test | 1 | ndcg | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-test | 5 | precision | -0.0200 | -0.0200 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-test | 5 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 0/9/1 |
| structure-no-test | 5 | mrr | -0.0917 | -0.0917 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-test | 5 | ndcg | -0.0931 | -0.0931 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-test | 10 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-test | 10 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-test | 10 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-test | 10 | ndcg | -0.0574 | -0.0574 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-test | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-test | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-no-test | 20 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-no-test | 20 | ndcg | -0.0574 | -0.0574 | withheld: insufficient repositories | 1 | 0/7/3 |
| structure-symbol-seed | 1 | precision | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| structure-symbol-seed | 1 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| structure-symbol-seed | 1 | mrr | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| structure-symbol-seed | 1 | ndcg | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| structure-symbol-seed | 5 | precision | -0.0200 | -0.0200 | withheld: insufficient repositories | 1 | 1/7/2 |
| structure-symbol-seed | 5 | recall | -0.1000 | -0.1000 | withheld: insufficient repositories | 1 | 1/7/2 |
| structure-symbol-seed | 5 | mrr | -0.1300 | -0.1300 | withheld: insufficient repositories | 1 | 2/5/3 |
| structure-symbol-seed | 5 | ndcg | -0.1244 | -0.1244 | withheld: insufficient repositories | 1 | 2/5/3 |
| structure-symbol-seed | 10 | precision | +0.0100 | +0.0100 | withheld: insufficient repositories | 1 | 1/9/0 |
| structure-symbol-seed | 10 | recall | +0.1000 | +0.1000 | withheld: insufficient repositories | 1 | 1/9/0 |
| structure-symbol-seed | 10 | mrr | -0.0990 | -0.0990 | withheld: insufficient repositories | 1 | 2/5/3 |
| structure-symbol-seed | 10 | ndcg | -0.0555 | -0.0555 | withheld: insufficient repositories | 1 | 2/5/3 |
| structure-symbol-seed | 20 | precision | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-symbol-seed | 20 | recall | +0.0000 | +0.0000 | withheld: insufficient repositories | 1 | 0/10/0 |
| structure-symbol-seed | 20 | mrr | -0.1040 | -0.1040 | withheld: insufficient repositories | 1 | 2/5/3 |
| structure-symbol-seed | 20 | ndcg | -0.0782 | -0.0782 | withheld: insufficient repositories | 1 | 2/5/3 |

See `comparison.json` for per-query paired differences and quality fingerprints.
Latency comes from separate recorded runs and depends on hardware/load; it includes query encoding and fusion, but excludes startup and offline embedding.
