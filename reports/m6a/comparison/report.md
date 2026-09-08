# Retrieval Strategy Comparison

Baseline: `hybrid`; unit: `symbol`; annotation status: **provisional**.

Known-label scores; unjudged candidates score zero. Paired wins/losses are descriptive, not significance tests.

| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 33.606 | 46.917 |
| hybrid | 5 | 0.1750 | 0.7250 | 0.6279 | 0.6079 | 33.606 | 46.917 |
| hybrid | 10 | 0.1025 | 0.8208 | 0.6394 | 0.6450 | 33.606 | 46.917 |
| hybrid | 20 | 0.0625 | 0.9292 | 0.6433 | 0.6789 | 33.606 | 46.917 |
| bm25 | 1 | 0.5000 | 0.4208 | 0.5000 | 0.4833 | 7.436 | 15.470 |
| bm25 | 5 | 0.1700 | 0.6875 | 0.6062 | 0.5931 | 7.436 | 15.470 |
| bm25 | 10 | 0.0975 | 0.7542 | 0.6182 | 0.6203 | 7.436 | 15.470 |
| bm25 | 20 | 0.0588 | 0.8917 | 0.6252 | 0.6553 | 7.436 | 15.470 |
| dense | 1 | 0.4000 | 0.3417 | 0.4000 | 0.4000 | 20.867 | 29.185 |
| dense | 5 | 0.1600 | 0.6583 | 0.5542 | 0.5494 | 20.867 | 29.185 |
| dense | 10 | 0.1000 | 0.7833 | 0.5738 | 0.5968 | 20.867 | 29.185 |
| dense | 20 | 0.0550 | 0.8542 | 0.5776 | 0.6151 | 20.867 | 29.185 |
| symbol | 1 | 0.4250 | 0.3542 | 0.4250 | 0.4250 | 71.584 | 110.269 |
| symbol | 5 | 0.1500 | 0.6333 | 0.5408 | 0.5292 | 71.584 | 110.269 |
| symbol | 10 | 0.0975 | 0.7917 | 0.5610 | 0.5823 | 71.584 | 110.269 |
| symbol | 20 | 0.0600 | 0.9333 | 0.5670 | 0.6202 | 71.584 | 110.269 |
| structure-full | 1 | 0.2250 | 0.1708 | 0.2250 | 0.2250 | 41.080 | 56.953 |
| structure-full | 5 | 0.1950 | 0.7333 | 0.4483 | 0.4994 | 41.080 | 56.953 |
| structure-full | 10 | 0.1200 | 0.8875 | 0.4647 | 0.5545 | 41.080 | 56.953 |
| structure-full | 20 | 0.0650 | 0.9625 | 0.4684 | 0.5755 | 41.080 | 56.953 |

## Paired differences and uncertainty

Differences are candidate minus baseline over answerable queries. Resampling keeps all queries in a selected repository together and preserves pairing. Query-macro and equal-repository means are different estimands.
95% percentile intervals use 2000 draws, seed 0. Intervals are withheld below 5 contributing repositories (a reporting policy, not a sufficiency guarantee). Few or correlated repositories and incomplete labels limit inference; intervals do not correct label bias. No multiple-comparison correction or significance claim is made.

| Strategy | K | Metric | Query mean delta | Repo mean delta | 95% interval | Repos | W/T/L |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bm25 | 1 | precision | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 6/29/5 |
| bm25 | 1 | recall | +0.0292 | +0.0292 | withheld: insufficient repositories | 2 | 6/29/5 |
| bm25 | 1 | mrr | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 6/29/5 |
| bm25 | 1 | ndcg | +0.0250 | +0.0250 | withheld: insufficient repositories | 2 | 6/29/5 |
| bm25 | 5 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 4/31/5 |
| bm25 | 5 | recall | -0.0375 | -0.0375 | withheld: insufficient repositories | 2 | 4/31/5 |
| bm25 | 5 | mrr | -0.0217 | -0.0217 | withheld: insufficient repositories | 2 | 7/23/10 |
| bm25 | 5 | ndcg | -0.0148 | -0.0148 | withheld: insufficient repositories | 2 | 10/20/10 |
| bm25 | 10 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 2/34/4 |
| bm25 | 10 | recall | -0.0667 | -0.0667 | withheld: insufficient repositories | 2 | 2/34/4 |
| bm25 | 10 | mrr | -0.0212 | -0.0212 | withheld: insufficient repositories | 2 | 8/21/11 |
| bm25 | 10 | ndcg | -0.0248 | -0.0248 | withheld: insufficient repositories | 2 | 11/18/11 |
| bm25 | 20 | precision | -0.0038 | -0.0037 | withheld: insufficient repositories | 2 | 2/34/4 |
| bm25 | 20 | recall | -0.0375 | -0.0375 | withheld: insufficient repositories | 2 | 2/34/4 |
| bm25 | 20 | mrr | -0.0181 | -0.0181 | withheld: insufficient repositories | 2 | 9/18/13 |
| bm25 | 20 | ndcg | -0.0237 | -0.0237 | withheld: insufficient repositories | 2 | 11/14/15 |
| dense | 1 | precision | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 2/33/5 |
| dense | 1 | recall | -0.0500 | -0.0500 | withheld: insufficient repositories | 2 | 2/33/5 |
| dense | 1 | mrr | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 2/33/5 |
| dense | 1 | ndcg | -0.0583 | -0.0583 | withheld: insufficient repositories | 2 | 3/32/5 |
| dense | 5 | precision | -0.0150 | -0.0150 | withheld: insufficient repositories | 2 | 4/29/7 |
| dense | 5 | recall | -0.0667 | -0.0667 | withheld: insufficient repositories | 2 | 4/29/7 |
| dense | 5 | mrr | -0.0737 | -0.0738 | withheld: insufficient repositories | 2 | 6/22/12 |
| dense | 5 | ndcg | -0.0585 | -0.0585 | withheld: insufficient repositories | 2 | 8/20/12 |
| dense | 10 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 2/34/4 |
| dense | 10 | recall | -0.0375 | -0.0375 | withheld: insufficient repositories | 2 | 2/34/4 |
| dense | 10 | mrr | -0.0656 | -0.0656 | withheld: insufficient repositories | 2 | 7/20/13 |
| dense | 10 | ndcg | -0.0483 | -0.0483 | withheld: insufficient repositories | 2 | 9/17/14 |
| dense | 20 | precision | -0.0075 | -0.0075 | withheld: insufficient repositories | 2 | 0/34/6 |
| dense | 20 | recall | -0.0750 | -0.0750 | withheld: insufficient repositories | 2 | 0/34/6 |
| dense | 20 | mrr | -0.0657 | -0.0657 | withheld: insufficient repositories | 2 | 7/20/13 |
| dense | 20 | ndcg | -0.0639 | -0.0639 | withheld: insufficient repositories | 2 | 8/15/17 |
| symbol | 1 | precision | -0.0500 | -0.0500 | withheld: insufficient repositories | 2 | 5/28/7 |
| symbol | 1 | recall | -0.0375 | -0.0375 | withheld: insufficient repositories | 2 | 5/28/7 |
| symbol | 1 | mrr | -0.0500 | -0.0500 | withheld: insufficient repositories | 2 | 5/28/7 |
| symbol | 1 | ndcg | -0.0333 | -0.0333 | withheld: insufficient repositories | 2 | 5/28/7 |
| symbol | 5 | precision | -0.0250 | -0.0250 | withheld: insufficient repositories | 2 | 4/29/7 |
| symbol | 5 | recall | -0.0917 | -0.0917 | withheld: insufficient repositories | 2 | 4/29/7 |
| symbol | 5 | mrr | -0.0871 | -0.0871 | withheld: insufficient repositories | 2 | 8/20/12 |
| symbol | 5 | ndcg | -0.0788 | -0.0788 | withheld: insufficient repositories | 2 | 9/19/12 |
| symbol | 10 | precision | -0.0050 | -0.0050 | withheld: insufficient repositories | 2 | 4/31/5 |
| symbol | 10 | recall | -0.0292 | -0.0292 | withheld: insufficient repositories | 2 | 4/31/5 |
| symbol | 10 | mrr | -0.0784 | -0.0784 | withheld: insufficient repositories | 2 | 10/17/13 |
| symbol | 10 | ndcg | -0.0627 | -0.0627 | withheld: insufficient repositories | 2 | 13/13/14 |
| symbol | 20 | precision | -0.0025 | -0.0025 | withheld: insufficient repositories | 2 | 2/34/4 |
| symbol | 20 | recall | +0.0042 | +0.0042 | withheld: insufficient repositories | 2 | 2/34/4 |
| symbol | 20 | mrr | -0.0763 | -0.0763 | withheld: insufficient repositories | 2 | 10/16/14 |
| symbol | 20 | ndcg | -0.0587 | -0.0587 | withheld: insufficient repositories | 2 | 11/11/18 |
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

See `comparison.json` for per-query paired differences and quality fingerprints.
Latency comes from separate recorded runs and depends on hardware/load; it includes query encoding and fusion, but excludes startup and offline embedding.
