# Retrieval Strategy Comparison

Baseline: `bm25`; unit: `symbol`; annotation status: **provisional**.

Known-label development scores; unjudged candidates score zero. Paired wins/losses are descriptive, not significance tests.

| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bm25 | 1 | 0.5000 | 0.4208 | 0.5000 | 0.4833 | 7.436 | 15.470 |
| bm25 | 5 | 0.1700 | 0.6875 | 0.6062 | 0.5931 | 7.436 | 15.470 |
| bm25 | 10 | 0.0975 | 0.7542 | 0.6182 | 0.6203 | 7.436 | 15.470 |
| bm25 | 20 | 0.0588 | 0.8917 | 0.6252 | 0.6553 | 7.436 | 15.470 |
| dense | 1 | 0.4000 | 0.3417 | 0.4000 | 0.4000 | 20.867 | 29.185 |
| dense | 5 | 0.1600 | 0.6583 | 0.5542 | 0.5494 | 20.867 | 29.185 |
| dense | 10 | 0.1000 | 0.7833 | 0.5738 | 0.5968 | 20.867 | 29.185 |
| dense | 20 | 0.0550 | 0.8542 | 0.5776 | 0.6151 | 20.867 | 29.185 |
| hybrid | 1 | 0.4750 | 0.3917 | 0.4750 | 0.4583 | 32.148 | 46.038 |
| hybrid | 5 | 0.1750 | 0.7250 | 0.6279 | 0.6079 | 32.148 | 46.038 |
| hybrid | 10 | 0.1025 | 0.8208 | 0.6394 | 0.6450 | 32.148 | 46.038 |
| hybrid | 20 | 0.0625 | 0.9292 | 0.6433 | 0.6789 | 32.148 | 46.038 |
| symbol | 1 | 0.4250 | 0.3542 | 0.4250 | 0.4250 | 66.779 | 110.317 |
| symbol | 5 | 0.1500 | 0.6333 | 0.5408 | 0.5292 | 66.779 | 110.317 |
| symbol | 10 | 0.0975 | 0.7917 | 0.5610 | 0.5823 | 66.779 | 110.317 |
| symbol | 20 | 0.0600 | 0.9333 | 0.5670 | 0.6202 | 66.779 | 110.317 |

See `comparison.json` for per-query paired differences and quality fingerprints.
Latency comes from separate recorded runs and depends on hardware/load; it includes query encoding and fusion, but excludes startup and offline embedding.
