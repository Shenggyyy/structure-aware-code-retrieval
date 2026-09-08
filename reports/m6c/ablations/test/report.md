# Retrieval Strategy Comparison

Baseline: `structure-full`; unit: `symbol`; annotation status: **provisional**.

Known-label scores; unjudged candidates score zero. Paired wins/losses are descriptive, not significance tests.

| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| structure-full | 1 | 0.2250 | 0.1792 | 0.2250 | 0.2250 | 54.519 | 391.982 |
| structure-full | 5 | 0.1683 | 0.6444 | 0.4242 | 0.4577 | 54.519 | 391.982 |
| structure-full | 10 | 0.1067 | 0.7917 | 0.4409 | 0.5109 | 54.519 | 391.982 |
| structure-full | 20 | 0.0608 | 0.9014 | 0.4468 | 0.5405 | 54.519 | 391.982 |
| structure-none | 1 | 0.4167 | 0.3528 | 0.4167 | 0.4167 | 46.752 | 324.857 |
| structure-none | 5 | 0.1783 | 0.6889 | 0.5529 | 0.5575 | 46.752 | 324.857 |
| structure-none | 10 | 0.1050 | 0.7944 | 0.5637 | 0.5947 | 46.752 | 324.857 |
| structure-none | 20 | 0.0600 | 0.8944 | 0.5693 | 0.6234 | 46.752 | 324.857 |
| structure-containment | 1 | 0.4083 | 0.3486 | 0.4083 | 0.4083 | 49.089 | 335.564 |
| structure-containment | 5 | 0.1767 | 0.6847 | 0.5450 | 0.5525 | 49.089 | 335.564 |
| structure-containment | 10 | 0.1075 | 0.8042 | 0.5591 | 0.5958 | 49.089 | 335.564 |
| structure-containment | 20 | 0.0604 | 0.8972 | 0.5638 | 0.6215 | 49.089 | 335.564 |
| structure-import | 1 | 0.4167 | 0.3528 | 0.4167 | 0.4167 | 47.412 | 336.354 |
| structure-import | 5 | 0.1767 | 0.6847 | 0.5497 | 0.5539 | 47.412 | 336.354 |
| structure-import | 10 | 0.1042 | 0.7861 | 0.5608 | 0.5903 | 47.412 | 336.354 |
| structure-import | 20 | 0.0600 | 0.8944 | 0.5672 | 0.6214 | 47.412 | 336.354 |
| structure-call | 1 | 0.2333 | 0.1833 | 0.2333 | 0.2333 | 46.903 | 338.760 |
| structure-call | 5 | 0.1767 | 0.6722 | 0.4365 | 0.4757 | 46.903 | 338.760 |
| structure-call | 10 | 0.1067 | 0.7875 | 0.4497 | 0.5183 | 46.903 | 338.760 |
| structure-call | 20 | 0.0608 | 0.9014 | 0.4566 | 0.5493 | 46.903 | 338.760 |
| structure-test | 1 | 0.4083 | 0.3403 | 0.4083 | 0.4083 | 51.619 | 360.833 |
| structure-test | 5 | 0.1750 | 0.6833 | 0.5404 | 0.5446 | 51.619 | 360.833 |
| structure-test | 10 | 0.1033 | 0.7819 | 0.5521 | 0.5805 | 51.619 | 360.833 |
| structure-test | 20 | 0.0600 | 0.8944 | 0.5583 | 0.6124 | 51.619 | 360.833 |
| structure-no-containment | 1 | 0.2250 | 0.1750 | 0.2250 | 0.2250 | 52.245 | 362.418 |
| structure-no-containment | 5 | 0.1667 | 0.6403 | 0.4221 | 0.4549 | 52.245 | 362.418 |
| structure-no-containment | 10 | 0.1058 | 0.7875 | 0.4403 | 0.5082 | 52.245 | 362.418 |
| structure-no-containment | 20 | 0.0604 | 0.8972 | 0.4462 | 0.5382 | 52.245 | 362.418 |
| structure-no-import | 1 | 0.2167 | 0.1708 | 0.2167 | 0.2167 | 48.858 | 348.029 |
| structure-no-import | 5 | 0.1700 | 0.6528 | 0.4217 | 0.4578 | 48.858 | 348.029 |
| structure-no-import | 10 | 0.1067 | 0.7917 | 0.4370 | 0.5080 | 48.858 | 348.029 |
| structure-no-import | 20 | 0.0608 | 0.9014 | 0.4429 | 0.5376 | 48.858 | 348.029 |
| structure-no-call | 1 | 0.4000 | 0.3361 | 0.4000 | 0.4000 | 55.048 | 380.369 |
| structure-no-call | 5 | 0.1700 | 0.6708 | 0.5307 | 0.5343 | 55.048 | 380.369 |
| structure-no-call | 10 | 0.1033 | 0.7819 | 0.5449 | 0.5758 | 55.048 | 380.369 |
| structure-no-call | 20 | 0.0600 | 0.8944 | 0.5509 | 0.6075 | 55.048 | 380.369 |
| structure-no-test | 1 | 0.2250 | 0.1792 | 0.2250 | 0.2250 | 54.630 | 389.861 |
| structure-no-test | 5 | 0.1750 | 0.6639 | 0.4300 | 0.4696 | 54.630 | 389.861 |
| structure-no-test | 10 | 0.1067 | 0.7917 | 0.4453 | 0.5157 | 54.630 | 389.861 |
| structure-no-test | 20 | 0.0613 | 0.9042 | 0.4515 | 0.5469 | 54.630 | 389.861 |
| structure-symbol-seed | 1 | 0.2917 | 0.2514 | 0.2917 | 0.2917 | 96.948 | 591.881 |
| structure-symbol-seed | 5 | 0.1517 | 0.6042 | 0.4326 | 0.4534 | 96.948 | 591.881 |
| structure-symbol-seed | 10 | 0.1050 | 0.7972 | 0.4558 | 0.5234 | 96.948 | 591.881 |
| structure-symbol-seed | 20 | 0.0596 | 0.8778 | 0.4612 | 0.5473 | 96.948 | 591.881 |

## Paired differences and uncertainty

Differences are candidate minus baseline over answerable queries. Resampling keeps all queries in a selected repository together and preserves pairing. Query-macro and equal-repository means are different estimands.
95% percentile intervals use 2000 draws, seed 0. Intervals are withheld below 5 contributing repositories (a reporting policy, not a sufficiency guarantee). Few or correlated repositories and incomplete labels limit inference; intervals do not correct label bias. No multiple-comparison correction or significance claim is made.

| Strategy | K | Metric | Query mean delta | Repo mean delta | 95% interval | Repos | W/T/L |
| --- | --- | --- | --- | --- | --- | --- | --- |
| structure-none | 1 | precision | +0.1917 | +0.1917 | [0.1250, 0.2583] | 5 | 29/85/6 |
| structure-none | 1 | recall | +0.1736 | +0.1736 | [0.1250, 0.2236] | 5 | 29/85/6 |
| structure-none | 1 | mrr | +0.1917 | +0.1917 | [0.1250, 0.2583] | 5 | 29/85/6 |
| structure-none | 1 | ndcg | +0.1917 | +0.1917 | [0.1250, 0.2583] | 5 | 29/85/6 |
| structure-none | 5 | precision | +0.0100 | +0.0100 | [-0.0033, 0.0267] | 5 | 15/95/10 |
| structure-none | 5 | recall | +0.0444 | +0.0444 | [0.0083, 0.0986] | 5 | 15/95/10 |
| structure-none | 5 | mrr | +0.1288 | +0.1288 | [0.0831, 0.1789] | 5 | 49/59/12 |
| structure-none | 5 | ndcg | +0.0998 | +0.0998 | [0.0528, 0.1478] | 5 | 50/55/15 |
| structure-none | 10 | precision | -0.0017 | -0.0017 | [-0.0108, 0.0067] | 5 | 4/110/6 |
| structure-none | 10 | recall | +0.0028 | +0.0028 | [-0.0444, 0.0500] | 5 | 4/110/6 |
| structure-none | 10 | mrr | +0.1228 | +0.1228 | [0.0778, 0.1740] | 5 | 54/54/12 |
| structure-none | 10 | ndcg | +0.0839 | +0.0839 | [0.0381, 0.1356] | 5 | 56/49/15 |
| structure-none | 20 | precision | -0.0008 | -0.0008 | [-0.0025, 0.0000] | 5 | 0/118/2 |
| structure-none | 20 | recall | -0.0069 | -0.0069 | [-0.0208, 0.0000] | 5 | 0/118/2 |
| structure-none | 20 | mrr | +0.1225 | +0.1225 | [0.0790, 0.1710] | 5 | 58/50/12 |
| structure-none | 20 | ndcg | +0.0829 | +0.0829 | [0.0479, 0.1216] | 5 | 60/45/15 |
| structure-containment | 1 | precision | +0.1833 | +0.1833 | [0.1083, 0.2583] | 5 | 28/86/6 |
| structure-containment | 1 | recall | +0.1694 | +0.1694 | [0.1153, 0.2236] | 5 | 28/86/6 |
| structure-containment | 1 | mrr | +0.1833 | +0.1833 | [0.1083, 0.2583] | 5 | 28/86/6 |
| structure-containment | 1 | ndcg | +0.1833 | +0.1833 | [0.1083, 0.2583] | 5 | 28/86/6 |
| structure-containment | 5 | precision | +0.0083 | +0.0083 | [-0.0033, 0.0267] | 5 | 15/94/11 |
| structure-containment | 5 | recall | +0.0403 | +0.0403 | [-0.0028, 0.0972] | 5 | 15/94/11 |
| structure-containment | 5 | mrr | +0.1208 | +0.1208 | [0.0715, 0.1732] | 5 | 48/60/12 |
| structure-containment | 5 | ndcg | +0.0948 | +0.0948 | [0.0448, 0.1448] | 5 | 49/56/15 |
| structure-containment | 10 | precision | +0.0008 | +0.0008 | [-0.0050, 0.0075] | 5 | 5/111/4 |
| structure-containment | 10 | recall | +0.0125 | +0.0125 | [-0.0250, 0.0500] | 5 | 5/111/4 |
| structure-containment | 10 | mrr | +0.1182 | +0.1182 | [0.0703, 0.1705] | 5 | 54/54/12 |
| structure-containment | 10 | ndcg | +0.0850 | +0.0850 | [0.0384, 0.1350] | 5 | 56/50/14 |
| structure-containment | 20 | precision | -0.0004 | -0.0004 | [-0.0025, 0.0012] | 5 | 1/117/2 |
| structure-containment | 20 | recall | -0.0042 | -0.0042 | [-0.0208, 0.0083] | 5 | 1/117/2 |
| structure-containment | 20 | mrr | +0.1171 | +0.1171 | [0.0700, 0.1683] | 5 | 57/51/12 |
| structure-containment | 20 | ndcg | +0.0810 | +0.0810 | [0.0417, 0.1220] | 5 | 59/47/14 |
| structure-import | 1 | precision | +0.1917 | +0.1917 | [0.1250, 0.2583] | 5 | 29/85/6 |
| structure-import | 1 | recall | +0.1736 | +0.1736 | [0.1250, 0.2236] | 5 | 29/85/6 |
| structure-import | 1 | mrr | +0.1917 | +0.1917 | [0.1250, 0.2583] | 5 | 29/85/6 |
| structure-import | 1 | ndcg | +0.1917 | +0.1917 | [0.1250, 0.2583] | 5 | 29/85/6 |
| structure-import | 5 | precision | +0.0083 | +0.0083 | [-0.0033, 0.0250] | 5 | 15/94/11 |
| structure-import | 5 | recall | +0.0403 | +0.0403 | [0.0014, 0.0972] | 5 | 15/94/11 |
| structure-import | 5 | mrr | +0.1256 | +0.1256 | [0.0806, 0.1756] | 5 | 49/58/13 |
| structure-import | 5 | ndcg | +0.0962 | +0.0962 | [0.0502, 0.1431] | 5 | 50/54/16 |
| structure-import | 10 | precision | -0.0025 | -0.0025 | [-0.0108, 0.0050] | 5 | 3/111/6 |
| structure-import | 10 | recall | -0.0056 | -0.0056 | [-0.0444, 0.0333] | 5 | 3/111/6 |
| structure-import | 10 | mrr | +0.1200 | +0.1200 | [0.0765, 0.1693] | 5 | 53/54/13 |
| structure-import | 10 | ndcg | +0.0795 | +0.0795 | [0.0373, 0.1263] | 5 | 55/50/15 |
| structure-import | 20 | precision | -0.0008 | -0.0008 | [-0.0025, 0.0000] | 5 | 0/118/2 |
| structure-import | 20 | recall | -0.0069 | -0.0069 | [-0.0208, 0.0000] | 5 | 0/118/2 |
| structure-import | 20 | mrr | +0.1204 | +0.1204 | [0.0777, 0.1680] | 5 | 58/49/13 |
| structure-import | 20 | ndcg | +0.0809 | +0.0809 | [0.0469, 0.1195] | 5 | 60/45/15 |
| structure-call | 1 | precision | +0.0083 | +0.0083 | [-0.0167, 0.0333] | 5 | 2/117/1 |
| structure-call | 1 | recall | +0.0042 | +0.0042 | [-0.0208, 0.0292] | 5 | 2/117/1 |
| structure-call | 1 | mrr | +0.0083 | +0.0083 | [-0.0167, 0.0333] | 5 | 2/117/1 |
| structure-call | 1 | ndcg | +0.0083 | +0.0083 | [-0.0167, 0.0333] | 5 | 2/117/1 |
| structure-call | 5 | precision | +0.0083 | +0.0083 | [0.0033, 0.0133] | 5 | 5/115/0 |
| structure-call | 5 | recall | +0.0278 | +0.0278 | [0.0097, 0.0458] | 5 | 5/115/0 |
| structure-call | 5 | mrr | +0.0124 | +0.0124 | [-0.0044, 0.0257] | 5 | 8/109/3 |
| structure-call | 5 | ndcg | +0.0181 | +0.0181 | [0.0112, 0.0264] | 5 | 10/108/2 |
| structure-call | 10 | precision | +0.0000 | +0.0000 | [-0.0025, 0.0025] | 5 | 1/118/1 |
| structure-call | 10 | recall | -0.0042 | -0.0042 | [-0.0250, 0.0125] | 5 | 1/118/1 |
| structure-call | 10 | mrr | +0.0088 | +0.0088 | [-0.0096, 0.0247] | 5 | 9/107/4 |
| structure-call | 10 | ndcg | +0.0074 | +0.0074 | [-0.0008, 0.0164] | 5 | 15/102/3 |
| structure-call | 20 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-call | 20 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-call | 20 | mrr | +0.0098 | +0.0098 | [-0.0085, 0.0249] | 5 | 11/105/4 |
| structure-call | 20 | ndcg | +0.0088 | +0.0088 | [-0.0019, 0.0179] | 5 | 20/97/3 |
| structure-test | 1 | precision | +0.1833 | +0.1833 | [0.0917, 0.2667] | 5 | 27/88/5 |
| structure-test | 1 | recall | +0.1611 | +0.1611 | [0.0986, 0.2236] | 5 | 27/88/5 |
| structure-test | 1 | mrr | +0.1833 | +0.1833 | [0.0917, 0.2667] | 5 | 27/88/5 |
| structure-test | 1 | ndcg | +0.1833 | +0.1833 | [0.0917, 0.2667] | 5 | 27/88/5 |
| structure-test | 5 | precision | +0.0067 | +0.0067 | [-0.0117, 0.0267] | 5 | 15/95/10 |
| structure-test | 5 | recall | +0.0389 | +0.0389 | [-0.0042, 0.0958] | 5 | 15/95/10 |
| structure-test | 5 | mrr | +0.1163 | +0.1163 | [0.0560, 0.1765] | 5 | 46/63/11 |
| structure-test | 5 | ndcg | +0.0869 | +0.0869 | [0.0285, 0.1454] | 5 | 47/59/14 |
| structure-test | 10 | precision | -0.0033 | -0.0033 | [-0.0108, 0.0033] | 5 | 2/112/6 |
| structure-test | 10 | recall | -0.0097 | -0.0097 | [-0.0444, 0.0250] | 5 | 2/112/6 |
| structure-test | 10 | mrr | +0.1112 | +0.1112 | [0.0535, 0.1689] | 5 | 50/59/11 |
| structure-test | 10 | ndcg | +0.0696 | +0.0696 | [0.0174, 0.1219] | 5 | 52/54/14 |
| structure-test | 20 | precision | -0.0008 | -0.0008 | [-0.0025, 0.0000] | 5 | 0/118/2 |
| structure-test | 20 | recall | -0.0069 | -0.0069 | [-0.0208, 0.0000] | 5 | 0/118/2 |
| structure-test | 20 | mrr | +0.1115 | +0.1115 | [0.0546, 0.1684] | 5 | 55/54/11 |
| structure-test | 20 | ndcg | +0.0720 | +0.0720 | [0.0281, 0.1159] | 5 | 57/49/14 |
| structure-no-containment | 1 | precision | +0.0000 | +0.0000 | [-0.0250, 0.0250] | 5 | 1/118/1 |
| structure-no-containment | 1 | recall | -0.0042 | -0.0042 | [-0.0250, 0.0125] | 5 | 1/118/1 |
| structure-no-containment | 1 | mrr | +0.0000 | +0.0000 | [-0.0250, 0.0250] | 5 | 1/118/1 |
| structure-no-containment | 1 | ndcg | +0.0000 | +0.0000 | [-0.0250, 0.0250] | 5 | 1/118/1 |
| structure-no-containment | 5 | precision | -0.0017 | -0.0017 | [-0.0050, 0.0000] | 5 | 0/119/1 |
| structure-no-containment | 5 | recall | -0.0042 | -0.0042 | [-0.0125, 0.0000] | 5 | 0/119/1 |
| structure-no-containment | 5 | mrr | -0.0021 | -0.0021 | [-0.0125, 0.0104] | 5 | 1/117/2 |
| structure-no-containment | 5 | ndcg | -0.0027 | -0.0027 | [-0.0106, 0.0055] | 5 | 1/117/2 |
| structure-no-containment | 10 | precision | -0.0008 | -0.0008 | [-0.0025, 0.0000] | 5 | 0/119/1 |
| structure-no-containment | 10 | recall | -0.0042 | -0.0042 | [-0.0125, 0.0000] | 5 | 0/119/1 |
| structure-no-containment | 10 | mrr | -0.0006 | -0.0006 | [-0.0125, 0.0121] | 5 | 2/116/2 |
| structure-no-containment | 10 | ndcg | -0.0027 | -0.0027 | [-0.0107, 0.0057] | 5 | 3/114/3 |
| structure-no-containment | 20 | precision | -0.0004 | -0.0004 | [-0.0013, 0.0000] | 5 | 0/119/1 |
| structure-no-containment | 20 | recall | -0.0042 | -0.0042 | [-0.0125, 0.0000] | 5 | 0/119/1 |
| structure-no-containment | 20 | mrr | -0.0005 | -0.0005 | [-0.0125, 0.0121] | 5 | 3/115/2 |
| structure-no-containment | 20 | ndcg | -0.0023 | -0.0023 | [-0.0101, 0.0064] | 5 | 7/109/4 |
| structure-no-import | 1 | precision | -0.0083 | -0.0083 | [-0.0250, 0.0000] | 5 | 0/119/1 |
| structure-no-import | 1 | recall | -0.0083 | -0.0083 | [-0.0250, 0.0000] | 5 | 0/119/1 |
| structure-no-import | 1 | mrr | -0.0083 | -0.0083 | [-0.0250, 0.0000] | 5 | 0/119/1 |
| structure-no-import | 1 | ndcg | -0.0083 | -0.0083 | [-0.0250, 0.0000] | 5 | 0/119/1 |
| structure-no-import | 5 | precision | +0.0017 | +0.0017 | [0.0000, 0.0050] | 5 | 1/119/0 |
| structure-no-import | 5 | recall | +0.0083 | +0.0083 | [0.0000, 0.0250] | 5 | 1/119/0 |
| structure-no-import | 5 | mrr | -0.0025 | -0.0025 | [-0.0125, 0.0050] | 5 | 1/118/1 |
| structure-no-import | 5 | ndcg | +0.0001 | +0.0001 | [-0.0092, 0.0097] | 5 | 1/118/1 |
| structure-no-import | 10 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-no-import | 10 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-no-import | 10 | mrr | -0.0039 | -0.0039 | [-0.0125, 0.0008] | 5 | 1/118/1 |
| structure-no-import | 10 | ndcg | -0.0028 | -0.0028 | [-0.0094, 0.0008] | 5 | 2/116/2 |
| structure-no-import | 20 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-no-import | 20 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-no-import | 20 | mrr | -0.0039 | -0.0039 | [-0.0125, 0.0008] | 5 | 1/118/1 |
| structure-no-import | 20 | ndcg | -0.0028 | -0.0028 | [-0.0094, 0.0008] | 5 | 2/116/2 |
| structure-no-call | 1 | precision | +0.1750 | +0.1750 | [0.0833, 0.2667] | 5 | 26/89/5 |
| structure-no-call | 1 | recall | +0.1569 | +0.1569 | [0.0903, 0.2236] | 5 | 26/89/5 |
| structure-no-call | 1 | mrr | +0.1750 | +0.1750 | [0.0833, 0.2667] | 5 | 26/89/5 |
| structure-no-call | 1 | ndcg | +0.1750 | +0.1750 | [0.0833, 0.2667] | 5 | 26/89/5 |
| structure-no-call | 5 | precision | +0.0017 | +0.0017 | [-0.0150, 0.0233] | 5 | 13/96/11 |
| structure-no-call | 5 | recall | +0.0264 | +0.0264 | [-0.0167, 0.0889] | 5 | 13/96/11 |
| structure-no-call | 5 | mrr | +0.1065 | +0.1065 | [0.0415, 0.1716] | 5 | 44/65/11 |
| structure-no-call | 5 | ndcg | +0.0767 | +0.0767 | [0.0168, 0.1365] | 5 | 45/61/14 |
| structure-no-call | 10 | precision | -0.0033 | -0.0033 | [-0.0108, 0.0033] | 5 | 2/112/6 |
| structure-no-call | 10 | recall | -0.0097 | -0.0097 | [-0.0444, 0.0250] | 5 | 2/112/6 |
| structure-no-call | 10 | mrr | +0.1041 | +0.1041 | [0.0430, 0.1653] | 5 | 49/60/11 |
| structure-no-call | 10 | ndcg | +0.0650 | +0.0650 | [0.0136, 0.1165] | 5 | 51/56/13 |
| structure-no-call | 20 | precision | -0.0008 | -0.0008 | [-0.0025, 0.0000] | 5 | 0/118/2 |
| structure-no-call | 20 | recall | -0.0069 | -0.0069 | [-0.0208, 0.0000] | 5 | 0/118/2 |
| structure-no-call | 20 | mrr | +0.1042 | +0.1042 | [0.0439, 0.1645] | 5 | 53/56/11 |
| structure-no-call | 20 | ndcg | +0.0670 | +0.0670 | [0.0219, 0.1122] | 5 | 55/52/13 |
| structure-no-test | 1 | precision | +0.0000 | +0.0000 | [-0.0250, 0.0250] | 5 | 1/118/1 |
| structure-no-test | 1 | recall | +0.0000 | +0.0000 | [-0.0250, 0.0250] | 5 | 1/118/1 |
| structure-no-test | 1 | mrr | +0.0000 | +0.0000 | [-0.0250, 0.0250] | 5 | 1/118/1 |
| structure-no-test | 1 | ndcg | +0.0000 | +0.0000 | [-0.0250, 0.0250] | 5 | 1/118/1 |
| structure-no-test | 5 | precision | +0.0067 | +0.0067 | [0.0017, 0.0117] | 5 | 4/116/0 |
| structure-no-test | 5 | recall | +0.0194 | +0.0194 | [0.0028, 0.0417] | 5 | 4/116/0 |
| structure-no-test | 5 | mrr | +0.0058 | +0.0058 | [-0.0082, 0.0208] | 5 | 6/110/4 |
| structure-no-test | 5 | ndcg | +0.0119 | +0.0119 | [0.0035, 0.0237] | 5 | 8/109/3 |
| structure-no-test | 10 | precision | +0.0000 | +0.0000 | [-0.0050, 0.0050] | 5 | 2/116/2 |
| structure-no-test | 10 | recall | +0.0000 | +0.0000 | [-0.0375, 0.0375] | 5 | 2/116/2 |
| structure-no-test | 10 | mrr | +0.0044 | +0.0044 | [-0.0107, 0.0201] | 5 | 7/108/5 |
| structure-no-test | 10 | ndcg | +0.0048 | +0.0048 | [-0.0043, 0.0154] | 5 | 10/105/5 |
| structure-no-test | 20 | precision | +0.0004 | +0.0004 | [0.0000, 0.0012] | 5 | 1/119/0 |
| structure-no-test | 20 | recall | +0.0028 | +0.0028 | [0.0000, 0.0083] | 5 | 1/119/0 |
| structure-no-test | 20 | mrr | +0.0047 | +0.0047 | [-0.0115, 0.0208] | 5 | 7/108/5 |
| structure-no-test | 20 | ndcg | +0.0065 | +0.0065 | [-0.0014, 0.0162] | 5 | 12/103/5 |
| structure-symbol-seed | 1 | precision | +0.0667 | +0.0667 | [-0.0167, 0.2083] | 5 | 23/82/15 |
| structure-symbol-seed | 1 | recall | +0.0722 | +0.0722 | [-0.0014, 0.1959] | 5 | 23/82/15 |
| structure-symbol-seed | 1 | mrr | +0.0667 | +0.0667 | [-0.0167, 0.2083] | 5 | 23/82/15 |
| structure-symbol-seed | 1 | ndcg | +0.0667 | +0.0667 | [-0.0167, 0.2083] | 5 | 23/82/15 |
| structure-symbol-seed | 5 | precision | -0.0167 | -0.0167 | [-0.0400, 0.0067] | 5 | 13/83/24 |
| structure-symbol-seed | 5 | recall | -0.0403 | -0.0403 | [-0.1361, 0.0458] | 5 | 13/83/24 |
| structure-symbol-seed | 5 | mrr | +0.0085 | +0.0085 | [-0.0822, 0.0940] | 5 | 41/40/39 |
| structure-symbol-seed | 5 | ndcg | -0.0042 | -0.0042 | [-0.0752, 0.0665] | 5 | 41/37/42 |
| structure-symbol-seed | 10 | precision | -0.0017 | -0.0017 | [-0.0183, 0.0100] | 5 | 13/94/13 |
| structure-symbol-seed | 10 | recall | +0.0056 | +0.0056 | [-0.1000, 0.0792] | 5 | 13/94/13 |
| structure-symbol-seed | 10 | mrr | +0.0150 | +0.0150 | [-0.0725, 0.0966] | 5 | 47/31/42 |
| structure-symbol-seed | 10 | ndcg | +0.0126 | +0.0126 | [-0.0704, 0.0853] | 5 | 51/28/41 |
| structure-symbol-seed | 20 | precision | -0.0013 | -0.0012 | [-0.0037, 0.0000] | 5 | 3/111/6 |
| structure-symbol-seed | 20 | recall | -0.0236 | -0.0236 | [-0.0542, 0.0000] | 5 | 3/111/6 |
| structure-symbol-seed | 20 | mrr | +0.0144 | +0.0144 | [-0.0673, 0.0953] | 5 | 47/27/46 |
| structure-symbol-seed | 20 | ndcg | +0.0068 | +0.0068 | [-0.0556, 0.0703] | 5 | 48/24/48 |

See `comparison.json` for per-query paired differences and quality fingerprints.
Latency comes from separate recorded runs and depends on hardware/load; it includes query encoding and fusion, but excludes startup and offline embedding.
