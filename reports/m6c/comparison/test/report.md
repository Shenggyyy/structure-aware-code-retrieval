# Retrieval Strategy Comparison

Baseline: `hybrid-seed`; unit: `symbol`; annotation status: **provisional**.

Known-label scores; unjudged candidates score zero. Paired wins/losses are descriptive, not significance tests.

| Strategy | K | Precision | Recall | MRR | NDCG | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid-seed | 1 | 0.4167 | 0.3528 | 0.4167 | 0.4167 | 55.161 | 373.142 |
| hybrid-seed | 5 | 0.1783 | 0.6889 | 0.5529 | 0.5575 | 55.161 | 373.142 |
| hybrid-seed | 10 | 0.1050 | 0.7944 | 0.5637 | 0.5947 | 55.161 | 373.142 |
| hybrid-seed | 20 | 0.0600 | 0.8944 | 0.5693 | 0.6234 | 55.161 | 373.142 |
| bm25-seed | 1 | 0.3583 | 0.2986 | 0.3583 | 0.3583 | 12.046 | 150.688 |
| bm25-seed | 5 | 0.1300 | 0.5042 | 0.4454 | 0.4382 | 12.046 | 150.688 |
| bm25-seed | 10 | 0.0825 | 0.6444 | 0.4644 | 0.4854 | 12.046 | 150.688 |
| bm25-seed | 20 | 0.0496 | 0.7403 | 0.4710 | 0.5138 | 12.046 | 150.688 |
| dense-seed | 1 | 0.4333 | 0.3778 | 0.4333 | 0.4333 | 32.418 | 171.720 |
| dense-seed | 5 | 0.1633 | 0.6403 | 0.5347 | 0.5340 | 32.418 | 171.720 |
| dense-seed | 10 | 0.0958 | 0.7292 | 0.5480 | 0.5675 | 32.418 | 171.720 |
| dense-seed | 20 | 0.0538 | 0.7986 | 0.5503 | 0.5871 | 32.418 | 171.720 |
| symbol-seed | 1 | 0.3917 | 0.3361 | 0.3917 | 0.3917 | 105.575 | 605.536 |
| symbol-seed | 5 | 0.1783 | 0.6875 | 0.5276 | 0.5459 | 105.575 | 605.536 |
| symbol-seed | 10 | 0.1042 | 0.7931 | 0.5438 | 0.5838 | 105.575 | 605.536 |
| symbol-seed | 20 | 0.0592 | 0.8722 | 0.5473 | 0.6072 | 105.575 | 605.536 |
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
| bm25-seed | 1 | precision | -0.0583 | -0.0583 | [-0.1417, 0.0250] | 5 | 12/89/19 |
| bm25-seed | 1 | recall | -0.0542 | -0.0542 | [-0.1264, 0.0194] | 5 | 12/89/19 |
| bm25-seed | 1 | mrr | -0.0583 | -0.0583 | [-0.1417, 0.0250] | 5 | 12/89/19 |
| bm25-seed | 1 | ndcg | -0.0583 | -0.0583 | [-0.1417, 0.0250] | 5 | 12/89/19 |
| bm25-seed | 5 | precision | -0.0483 | -0.0483 | [-0.0767, -0.0217] | 5 | 6/80/34 |
| bm25-seed | 5 | recall | -0.1847 | -0.1847 | [-0.2944, -0.0944] | 5 | 6/80/34 |
| bm25-seed | 5 | mrr | -0.1075 | -0.1075 | [-0.1682, -0.0435] | 5 | 20/55/45 |
| bm25-seed | 5 | ndcg | -0.1193 | -0.1193 | [-0.1852, -0.0602] | 5 | 24/49/47 |
| bm25-seed | 10 | precision | -0.0225 | -0.0225 | [-0.0342, -0.0092] | 5 | 4/87/29 |
| bm25-seed | 10 | recall | -0.1500 | -0.1500 | [-0.2167, -0.0708] | 5 | 4/87/29 |
| bm25-seed | 10 | mrr | -0.0993 | -0.0993 | [-0.1547, -0.0429] | 5 | 24/46/50 |
| bm25-seed | 10 | ndcg | -0.1093 | -0.1093 | [-0.1632, -0.0553] | 5 | 27/40/53 |
| bm25-seed | 20 | precision | -0.0104 | -0.0104 | [-0.0163, -0.0050] | 5 | 3/91/26 |
| bm25-seed | 20 | recall | -0.1542 | -0.1542 | [-0.2167, -0.0917] | 5 | 3/91/26 |
| bm25-seed | 20 | mrr | -0.0982 | -0.0982 | [-0.1514, -0.0411] | 5 | 24/38/58 |
| bm25-seed | 20 | ndcg | -0.1096 | -0.1096 | [-0.1496, -0.0728] | 5 | 28/30/62 |
| dense-seed | 1 | precision | +0.0167 | +0.0167 | [-0.0667, 0.1167] | 5 | 19/84/17 |
| dense-seed | 1 | recall | +0.0250 | +0.0250 | [-0.0569, 0.1125] | 5 | 19/84/17 |
| dense-seed | 1 | mrr | +0.0167 | +0.0167 | [-0.0667, 0.1167] | 5 | 19/84/17 |
| dense-seed | 1 | ndcg | +0.0167 | +0.0167 | [-0.0667, 0.1167] | 5 | 19/84/17 |
| dense-seed | 5 | precision | -0.0150 | -0.0150 | [-0.0383, 0.0033] | 5 | 15/83/22 |
| dense-seed | 5 | recall | -0.0486 | -0.0486 | [-0.1361, 0.0208] | 5 | 15/83/22 |
| dense-seed | 5 | mrr | -0.0182 | -0.0182 | [-0.1087, 0.0600] | 5 | 26/56/38 |
| dense-seed | 5 | ndcg | -0.0234 | -0.0234 | [-0.1069, 0.0474] | 5 | 29/48/43 |
| dense-seed | 10 | precision | -0.0092 | -0.0092 | [-0.0158, -0.0000] | 5 | 13/84/23 |
| dense-seed | 10 | recall | -0.0653 | -0.0653 | [-0.1000, -0.0167] | 5 | 13/84/23 |
| dense-seed | 10 | mrr | -0.0156 | -0.0156 | [-0.0910, 0.0538] | 5 | 27/49/44 |
| dense-seed | 10 | ndcg | -0.0272 | -0.0272 | [-0.0872, 0.0327] | 5 | 31/38/51 |
| dense-seed | 20 | precision | -0.0063 | -0.0063 | [-0.0092, -0.0029] | 5 | 4/99/17 |
| dense-seed | 20 | recall | -0.0958 | -0.0958 | [-0.1458, -0.0542] | 5 | 4/99/17 |
| dense-seed | 20 | mrr | -0.0190 | -0.0190 | [-0.0928, 0.0493] | 5 | 27/47/46 |
| dense-seed | 20 | ndcg | -0.0363 | -0.0363 | [-0.0911, 0.0184] | 5 | 31/36/53 |
| symbol-seed | 1 | precision | -0.0250 | -0.0250 | [-0.0583, 0.0167] | 5 | 14/89/17 |
| symbol-seed | 1 | recall | -0.0167 | -0.0167 | [-0.0625, 0.0153] | 5 | 14/89/17 |
| symbol-seed | 1 | mrr | -0.0250 | -0.0250 | [-0.0583, 0.0167] | 5 | 14/89/17 |
| symbol-seed | 1 | ndcg | -0.0250 | -0.0250 | [-0.0583, 0.0167] | 5 | 14/89/17 |
| symbol-seed | 5 | precision | -0.0000 | -0.0000 | [-0.0150, 0.0150] | 5 | 16/89/15 |
| symbol-seed | 5 | recall | -0.0014 | -0.0014 | [-0.0514, 0.0611] | 5 | 16/89/15 |
| symbol-seed | 5 | mrr | -0.0253 | -0.0253 | [-0.0554, 0.0071] | 5 | 32/54/34 |
| symbol-seed | 5 | ndcg | -0.0116 | -0.0116 | [-0.0351, 0.0196] | 5 | 36/47/37 |
| symbol-seed | 10 | precision | -0.0008 | -0.0008 | [-0.0042, 0.0042] | 5 | 9/101/10 |
| symbol-seed | 10 | recall | -0.0014 | -0.0014 | [-0.0319, 0.0319] | 5 | 9/101/10 |
| symbol-seed | 10 | mrr | -0.0199 | -0.0199 | [-0.0511, 0.0118] | 5 | 34/51/35 |
| symbol-seed | 10 | ndcg | -0.0109 | -0.0109 | [-0.0330, 0.0152] | 5 | 39/42/39 |
| symbol-seed | 20 | precision | -0.0008 | -0.0008 | [-0.0029, 0.0008] | 5 | 4/110/6 |
| symbol-seed | 20 | recall | -0.0222 | -0.0222 | [-0.0458, 0.0014] | 5 | 4/110/6 |
| symbol-seed | 20 | mrr | -0.0220 | -0.0220 | [-0.0498, 0.0065] | 5 | 35/46/39 |
| symbol-seed | 20 | ndcg | -0.0162 | -0.0162 | [-0.0329, 0.0008] | 5 | 40/37/43 |
| structure-full | 1 | precision | -0.1917 | -0.1917 | [-0.2583, -0.1250] | 5 | 6/85/29 |
| structure-full | 1 | recall | -0.1736 | -0.1736 | [-0.2236, -0.1250] | 5 | 6/85/29 |
| structure-full | 1 | mrr | -0.1917 | -0.1917 | [-0.2583, -0.1250] | 5 | 6/85/29 |
| structure-full | 1 | ndcg | -0.1917 | -0.1917 | [-0.2583, -0.1250] | 5 | 6/85/29 |
| structure-full | 5 | precision | -0.0100 | -0.0100 | [-0.0267, 0.0033] | 5 | 10/95/15 |
| structure-full | 5 | recall | -0.0444 | -0.0444 | [-0.0986, -0.0083] | 5 | 10/95/15 |
| structure-full | 5 | mrr | -0.1288 | -0.1288 | [-0.1789, -0.0831] | 5 | 12/59/49 |
| structure-full | 5 | ndcg | -0.0998 | -0.0998 | [-0.1478, -0.0528] | 5 | 15/55/50 |
| structure-full | 10 | precision | +0.0017 | +0.0017 | [-0.0067, 0.0108] | 5 | 6/110/4 |
| structure-full | 10 | recall | -0.0028 | -0.0028 | [-0.0500, 0.0444] | 5 | 6/110/4 |
| structure-full | 10 | mrr | -0.1228 | -0.1228 | [-0.1740, -0.0778] | 5 | 12/54/54 |
| structure-full | 10 | ndcg | -0.0839 | -0.0839 | [-0.1356, -0.0381] | 5 | 15/49/56 |
| structure-full | 20 | precision | +0.0008 | +0.0008 | [0.0000, 0.0025] | 5 | 2/118/0 |
| structure-full | 20 | recall | +0.0069 | +0.0069 | [0.0000, 0.0208] | 5 | 2/118/0 |
| structure-full | 20 | mrr | -0.1225 | -0.1225 | [-0.1710, -0.0790] | 5 | 12/50/58 |
| structure-full | 20 | ndcg | -0.0829 | -0.0829 | [-0.1216, -0.0479] | 5 | 15/45/60 |
| structure-none | 1 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 1 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 1 | mrr | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 1 | ndcg | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 5 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 5 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 5 | mrr | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 5 | ndcg | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 10 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 10 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 10 | mrr | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 10 | ndcg | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 20 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 20 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 20 | mrr | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-none | 20 | ndcg | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-containment | 1 | precision | -0.0083 | -0.0083 | [-0.0250, 0.0000] | 5 | 0/119/1 |
| structure-containment | 1 | recall | -0.0042 | -0.0042 | [-0.0125, 0.0000] | 5 | 0/119/1 |
| structure-containment | 1 | mrr | -0.0083 | -0.0083 | [-0.0250, 0.0000] | 5 | 0/119/1 |
| structure-containment | 1 | ndcg | -0.0083 | -0.0083 | [-0.0250, 0.0000] | 5 | 0/119/1 |
| structure-containment | 5 | precision | -0.0017 | -0.0017 | [-0.0067, 0.0033] | 5 | 1/117/2 |
| structure-containment | 5 | recall | -0.0042 | -0.0042 | [-0.0167, 0.0083] | 5 | 1/117/2 |
| structure-containment | 5 | mrr | -0.0079 | -0.0079 | [-0.0203, 0.0014] | 5 | 1/115/4 |
| structure-containment | 5 | ndcg | -0.0050 | -0.0050 | [-0.0161, 0.0044] | 5 | 1/114/5 |
| structure-containment | 10 | precision | +0.0025 | +0.0025 | [0.0000, 0.0075] | 5 | 2/118/0 |
| structure-containment | 10 | recall | +0.0097 | +0.0097 | [0.0000, 0.0292] | 5 | 2/118/0 |
| structure-containment | 10 | mrr | -0.0046 | -0.0046 | [-0.0144, 0.0021] | 5 | 3/110/7 |
| structure-containment | 10 | ndcg | +0.0011 | +0.0011 | [-0.0078, 0.0098] | 5 | 4/107/9 |
| structure-containment | 20 | precision | +0.0004 | +0.0004 | [0.0000, 0.0012] | 5 | 1/119/0 |
| structure-containment | 20 | recall | +0.0028 | +0.0028 | [0.0000, 0.0083] | 5 | 1/119/0 |
| structure-containment | 20 | mrr | -0.0054 | -0.0054 | [-0.0152, 0.0020] | 5 | 3/108/9 |
| structure-containment | 20 | ndcg | -0.0019 | -0.0019 | [-0.0085, 0.0031] | 5 | 5/103/12 |
| structure-import | 1 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-import | 1 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-import | 1 | mrr | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-import | 1 | ndcg | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-import | 5 | precision | -0.0017 | -0.0017 | [-0.0050, 0.0000] | 5 | 0/119/1 |
| structure-import | 5 | recall | -0.0042 | -0.0042 | [-0.0125, 0.0000] | 5 | 0/119/1 |
| structure-import | 5 | mrr | -0.0032 | -0.0032 | [-0.0061, -0.0004] | 5 | 0/116/4 |
| structure-import | 5 | ndcg | -0.0036 | -0.0036 | [-0.0073, -0.0007] | 5 | 0/114/6 |
| structure-import | 10 | precision | -0.0008 | -0.0008 | [-0.0025, 0.0000] | 5 | 0/119/1 |
| structure-import | 10 | recall | -0.0083 | -0.0083 | [-0.0250, 0.0000] | 5 | 0/119/1 |
| structure-import | 10 | mrr | -0.0028 | -0.0028 | [-0.0044, -0.0013] | 5 | 0/114/6 |
| structure-import | 10 | ndcg | -0.0044 | -0.0044 | [-0.0088, -0.0008] | 5 | 0/112/8 |
| structure-import | 20 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-import | 20 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-import | 20 | mrr | -0.0021 | -0.0021 | [-0.0039, -0.0006] | 5 | 0/114/6 |
| structure-import | 20 | ndcg | -0.0020 | -0.0020 | [-0.0041, -0.0006] | 5 | 0/112/8 |
| structure-call | 1 | precision | -0.1833 | -0.1833 | [-0.2750, -0.0917] | 5 | 6/86/28 |
| structure-call | 1 | recall | -0.1694 | -0.1694 | [-0.2403, -0.0986] | 5 | 6/86/28 |
| structure-call | 1 | mrr | -0.1833 | -0.1833 | [-0.2750, -0.0917] | 5 | 6/86/28 |
| structure-call | 1 | ndcg | -0.1833 | -0.1833 | [-0.2750, -0.0917] | 5 | 6/86/28 |
| structure-call | 5 | precision | -0.0017 | -0.0017 | [-0.0183, 0.0117] | 5 | 12/96/12 |
| structure-call | 5 | recall | -0.0167 | -0.0167 | [-0.0611, 0.0111] | 5 | 12/96/12 |
| structure-call | 5 | mrr | -0.1164 | -0.1164 | [-0.1810, -0.0594] | 5 | 12/61/47 |
| structure-call | 5 | ndcg | -0.0817 | -0.0817 | [-0.1330, -0.0304] | 5 | 15/57/48 |
| structure-call | 10 | precision | +0.0017 | +0.0017 | [-0.0050, 0.0083] | 5 | 6/110/4 |
| structure-call | 10 | recall | -0.0069 | -0.0069 | [-0.0417, 0.0278] | 5 | 6/110/4 |
| structure-call | 10 | mrr | -0.1140 | -0.1140 | [-0.1799, -0.0549] | 5 | 12/56/52 |
| structure-call | 10 | ndcg | -0.0764 | -0.0764 | [-0.1332, -0.0236] | 5 | 14/52/54 |
| structure-call | 20 | precision | +0.0008 | +0.0008 | [0.0000, 0.0025] | 5 | 2/118/0 |
| structure-call | 20 | recall | +0.0069 | +0.0069 | [0.0000, 0.0208] | 5 | 2/118/0 |
| structure-call | 20 | mrr | -0.1127 | -0.1127 | [-0.1772, -0.0552] | 5 | 12/53/55 |
| structure-call | 20 | ndcg | -0.0741 | -0.0741 | [-0.1234, -0.0301] | 5 | 15/49/56 |
| structure-test | 1 | precision | -0.0083 | -0.0083 | [-0.0333, 0.0167] | 5 | 1/117/2 |
| structure-test | 1 | recall | -0.0125 | -0.0125 | [-0.0333, 0.0083] | 5 | 1/117/2 |
| structure-test | 1 | mrr | -0.0083 | -0.0083 | [-0.0333, 0.0167] | 5 | 1/117/2 |
| structure-test | 1 | ndcg | -0.0083 | -0.0083 | [-0.0333, 0.0167] | 5 | 1/117/2 |
| structure-test | 5 | precision | -0.0033 | -0.0033 | [-0.0100, 0.0000] | 5 | 1/117/2 |
| structure-test | 5 | recall | -0.0056 | -0.0056 | [-0.0167, 0.0000] | 5 | 1/117/2 |
| structure-test | 5 | mrr | -0.0125 | -0.0125 | [-0.0375, 0.0090] | 5 | 1/110/9 |
| structure-test | 5 | ndcg | -0.0129 | -0.0129 | [-0.0327, 0.0028] | 5 | 1/108/11 |
| structure-test | 10 | precision | -0.0017 | -0.0017 | [-0.0050, 0.0000] | 5 | 0/118/2 |
| structure-test | 10 | recall | -0.0125 | -0.0125 | [-0.0375, 0.0000] | 5 | 0/118/2 |
| structure-test | 10 | mrr | -0.0116 | -0.0116 | [-0.0333, 0.0094] | 5 | 1/109/10 |
| structure-test | 10 | ndcg | -0.0142 | -0.0142 | [-0.0280, 0.0000] | 5 | 1/105/14 |
| structure-test | 20 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-test | 20 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-test | 20 | mrr | -0.0110 | -0.0110 | [-0.0334, 0.0096] | 5 | 1/108/11 |
| structure-test | 20 | ndcg | -0.0110 | -0.0110 | [-0.0261, 0.0030] | 5 | 1/104/15 |
| structure-no-containment | 1 | precision | -0.1917 | -0.1917 | [-0.2750, -0.1083] | 5 | 6/85/29 |
| structure-no-containment | 1 | recall | -0.1778 | -0.1778 | [-0.2403, -0.1153] | 5 | 6/85/29 |
| structure-no-containment | 1 | mrr | -0.1917 | -0.1917 | [-0.2750, -0.1083] | 5 | 6/85/29 |
| structure-no-containment | 1 | ndcg | -0.1917 | -0.1917 | [-0.2750, -0.1083] | 5 | 6/85/29 |
| structure-no-containment | 5 | precision | -0.0117 | -0.0117 | [-0.0267, -0.0017] | 5 | 10/94/16 |
| structure-no-containment | 5 | recall | -0.0486 | -0.0486 | [-0.1014, -0.0139] | 5 | 10/94/16 |
| structure-no-containment | 5 | mrr | -0.1308 | -0.1308 | [-0.1874, -0.0789] | 5 | 12/58/50 |
| structure-no-containment | 5 | ndcg | -0.1025 | -0.1025 | [-0.1540, -0.0511] | 5 | 15/54/51 |
| structure-no-containment | 10 | precision | +0.0008 | +0.0008 | [-0.0067, 0.0092] | 5 | 6/109/5 |
| structure-no-containment | 10 | recall | -0.0069 | -0.0069 | [-0.0500, 0.0375] | 5 | 6/109/5 |
| structure-no-containment | 10 | mrr | -0.1234 | -0.1234 | [-0.1823, -0.0714] | 5 | 12/53/55 |
| structure-no-containment | 10 | ndcg | -0.0865 | -0.0865 | [-0.1445, -0.0371] | 5 | 14/49/57 |
| structure-no-containment | 20 | precision | +0.0004 | +0.0004 | [0.0000, 0.0012] | 5 | 2/117/1 |
| structure-no-containment | 20 | recall | +0.0028 | +0.0028 | [0.0000, 0.0083] | 5 | 2/117/1 |
| structure-no-containment | 20 | mrr | -0.1230 | -0.1230 | [-0.1801, -0.0718] | 5 | 12/50/58 |
| structure-no-containment | 20 | ndcg | -0.0852 | -0.0852 | [-0.1284, -0.0443] | 5 | 14/46/60 |
| structure-no-import | 1 | precision | -0.2000 | -0.2000 | [-0.2750, -0.1250] | 5 | 6/84/30 |
| structure-no-import | 1 | recall | -0.1819 | -0.1819 | [-0.2403, -0.1250] | 5 | 6/84/30 |
| structure-no-import | 1 | mrr | -0.2000 | -0.2000 | [-0.2750, -0.1250] | 5 | 6/84/30 |
| structure-no-import | 1 | ndcg | -0.2000 | -0.2000 | [-0.2750, -0.1250] | 5 | 6/84/30 |
| structure-no-import | 5 | precision | -0.0083 | -0.0083 | [-0.0217, 0.0033] | 5 | 10/96/14 |
| structure-no-import | 5 | recall | -0.0361 | -0.0361 | [-0.0736, -0.0083] | 5 | 10/96/14 |
| structure-no-import | 5 | mrr | -0.1313 | -0.1313 | [-0.1879, -0.0831] | 5 | 12/58/50 |
| structure-no-import | 5 | ndcg | -0.0996 | -0.0996 | [-0.1475, -0.0528] | 5 | 15/54/51 |
| structure-no-import | 10 | precision | +0.0017 | +0.0017 | [-0.0067, 0.0108] | 5 | 6/110/4 |
| structure-no-import | 10 | recall | -0.0028 | -0.0028 | [-0.0500, 0.0444] | 5 | 6/110/4 |
| structure-no-import | 10 | mrr | -0.1267 | -0.1267 | [-0.1842, -0.0778] | 5 | 12/53/55 |
| structure-no-import | 10 | ndcg | -0.0867 | -0.0867 | [-0.1449, -0.0380] | 5 | 15/48/57 |
| structure-no-import | 20 | precision | +0.0008 | +0.0008 | [0.0000, 0.0025] | 5 | 2/118/0 |
| structure-no-import | 20 | recall | +0.0069 | +0.0069 | [0.0000, 0.0208] | 5 | 2/118/0 |
| structure-no-import | 20 | mrr | -0.1264 | -0.1264 | [-0.1820, -0.0790] | 5 | 12/49/59 |
| structure-no-import | 20 | ndcg | -0.0858 | -0.0858 | [-0.1309, -0.0478] | 5 | 15/44/61 |
| structure-no-call | 1 | precision | -0.0167 | -0.0167 | [-0.0417, 0.0167] | 5 | 1/116/3 |
| structure-no-call | 1 | recall | -0.0167 | -0.0167 | [-0.0375, 0.0042] | 5 | 1/116/3 |
| structure-no-call | 1 | mrr | -0.0167 | -0.0167 | [-0.0417, 0.0167] | 5 | 1/116/3 |
| structure-no-call | 1 | ndcg | -0.0167 | -0.0167 | [-0.0417, 0.0167] | 5 | 1/116/3 |
| structure-no-call | 5 | precision | -0.0083 | -0.0083 | [-0.0133, -0.0033] | 5 | 1/114/5 |
| structure-no-call | 5 | recall | -0.0181 | -0.0181 | [-0.0250, -0.0083] | 5 | 1/114/5 |
| structure-no-call | 5 | mrr | -0.0222 | -0.0222 | [-0.0447, 0.0010] | 5 | 1/104/15 |
| structure-no-call | 5 | ndcg | -0.0231 | -0.0231 | [-0.0381, -0.0079] | 5 | 1/101/18 |
| structure-no-call | 10 | precision | -0.0017 | -0.0017 | [-0.0050, 0.0000] | 5 | 0/118/2 |
| structure-no-call | 10 | recall | -0.0125 | -0.0125 | [-0.0375, 0.0000] | 5 | 0/118/2 |
| structure-no-call | 10 | mrr | -0.0187 | -0.0187 | [-0.0381, 0.0030] | 5 | 1/101/18 |
| structure-no-call | 10 | ndcg | -0.0189 | -0.0189 | [-0.0289, -0.0071] | 5 | 2/95/23 |
| structure-no-call | 20 | precision | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-no-call | 20 | recall | +0.0000 | +0.0000 | [0.0000, 0.0000] | 5 | 0/120/0 |
| structure-no-call | 20 | mrr | -0.0183 | -0.0183 | [-0.0384, 0.0032] | 5 | 1/98/21 |
| structure-no-call | 20 | ndcg | -0.0159 | -0.0159 | [-0.0280, -0.0040] | 5 | 2/90/28 |
| structure-no-test | 1 | precision | -0.1917 | -0.1917 | [-0.2750, -0.1000] | 5 | 6/85/29 |
| structure-no-test | 1 | recall | -0.1736 | -0.1736 | [-0.2403, -0.1069] | 5 | 6/85/29 |
| structure-no-test | 1 | mrr | -0.1917 | -0.1917 | [-0.2750, -0.1000] | 5 | 6/85/29 |
| structure-no-test | 1 | ndcg | -0.1917 | -0.1917 | [-0.2750, -0.1000] | 5 | 6/85/29 |
| structure-no-test | 5 | precision | -0.0033 | -0.0033 | [-0.0233, 0.0117] | 5 | 12/95/13 |
| structure-no-test | 5 | recall | -0.0250 | -0.0250 | [-0.0861, 0.0111] | 5 | 12/95/13 |
| structure-no-test | 5 | mrr | -0.1229 | -0.1229 | [-0.1860, -0.0685] | 5 | 12/60/48 |
| structure-no-test | 5 | ndcg | -0.0879 | -0.0879 | [-0.1398, -0.0359] | 5 | 15/56/49 |
| structure-no-test | 10 | precision | +0.0017 | +0.0017 | [-0.0033, 0.0067] | 5 | 5/112/3 |
| structure-no-test | 10 | recall | -0.0028 | -0.0028 | [-0.0250, 0.0222] | 5 | 5/112/3 |
| structure-no-test | 10 | mrr | -0.1184 | -0.1184 | [-0.1795, -0.0622] | 5 | 12/56/52 |
| structure-no-test | 10 | ndcg | -0.0790 | -0.0790 | [-0.1274, -0.0307] | 5 | 14/52/54 |
| structure-no-test | 20 | precision | +0.0012 | +0.0012 | [0.0000, 0.0029] | 5 | 3/117/0 |
| structure-no-test | 20 | recall | +0.0097 | +0.0097 | [0.0000, 0.0236] | 5 | 3/117/0 |
| structure-no-test | 20 | mrr | -0.1178 | -0.1178 | [-0.1797, -0.0618] | 5 | 12/52/56 |
| structure-no-test | 20 | ndcg | -0.0765 | -0.0765 | [-0.1202, -0.0357] | 5 | 14/48/58 |
| structure-symbol-seed | 1 | precision | -0.1250 | -0.1250 | [-0.2333, -0.0083] | 5 | 11/83/26 |
| structure-symbol-seed | 1 | recall | -0.1014 | -0.1014 | [-0.1917, 0.0000] | 5 | 11/83/26 |
| structure-symbol-seed | 1 | mrr | -0.1250 | -0.1250 | [-0.2333, -0.0083] | 5 | 11/83/26 |
| structure-symbol-seed | 1 | ndcg | -0.1250 | -0.1250 | [-0.2333, -0.0083] | 5 | 11/83/26 |
| structure-symbol-seed | 5 | precision | -0.0267 | -0.0267 | [-0.0550, 0.0017] | 5 | 6/92/22 |
| structure-symbol-seed | 5 | recall | -0.0847 | -0.0847 | [-0.1833, 0.0112] | 5 | 6/92/22 |
| structure-symbol-seed | 5 | mrr | -0.1203 | -0.1203 | [-0.2160, -0.0251] | 5 | 21/53/46 |
| structure-symbol-seed | 5 | ndcg | -0.1040 | -0.1040 | [-0.1862, -0.0236] | 5 | 21/49/50 |
| structure-symbol-seed | 10 | precision | -0.0000 | -0.0000 | [-0.0083, 0.0075] | 5 | 11/97/12 |
| structure-symbol-seed | 10 | recall | +0.0028 | +0.0028 | [-0.0708, 0.0626] | 5 | 11/97/12 |
| structure-symbol-seed | 10 | mrr | -0.1078 | -0.1078 | [-0.1983, -0.0173] | 5 | 28/42/50 |
| structure-symbol-seed | 10 | ndcg | -0.0713 | -0.0713 | [-0.1432, 0.0005] | 5 | 30/38/52 |
| structure-symbol-seed | 20 | precision | -0.0004 | -0.0004 | [-0.0013, 0.0000] | 5 | 3/113/4 |
| structure-symbol-seed | 20 | recall | -0.0167 | -0.0167 | [-0.0333, 0.0000] | 5 | 3/113/4 |
| structure-symbol-seed | 20 | mrr | -0.1081 | -0.1081 | [-0.1958, -0.0205] | 5 | 28/38/54 |
| structure-symbol-seed | 20 | ndcg | -0.0761 | -0.0761 | [-0.1341, -0.0181] | 5 | 30/33/57 |

See `comparison.json` for per-query paired differences and quality fingerprints.
Latency comes from separate recorded runs and depends on hardware/load; it includes query encoding and fusion, but excludes startup and offline embedding.
