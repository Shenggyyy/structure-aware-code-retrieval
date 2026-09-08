# M6c: Fixed Retrieval Experiments

Result status: **provisional**; plan `00845048e1a4b2a002022fbe882fe72eff661e3426ebd402d7dd1f1c5cc0905d`.

Known-label metrics treat unjudged candidates as zero. Independent label review is a separate acceptance condition; completed runs do not establish reviewed quality.
Public results use the adapted full-repository protocol, not original RepoQA scoring.

## dev

| Strategy | Recall@10 | NDCG@10 | MRR@10 | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- |
| hybrid-seed | 0.8208 | 0.6450 | 0.6394 | 35.17 | 50.79 |
| bm25-seed | 0.7542 | 0.6203 | 0.6182 | 8.44 | 18.63 |
| dense-seed | 0.7833 | 0.5968 | 0.5738 | 22.14 | 30.29 |
| symbol-seed | 0.7917 | 0.5823 | 0.5610 | 70.75 | 98.99 |
| structure-full | 0.8875 | 0.5545 | 0.4647 | 42.16 | 63.17 |
| structure-none | 0.8208 | 0.6450 | 0.6394 | 35.60 | 47.90 |
| structure-containment | 0.8333 | 0.6417 | 0.6307 | 40.02 | 53.61 |
| structure-import | 0.8208 | 0.6430 | 0.6369 | 39.22 | 58.11 |
| structure-call | 0.8875 | 0.5697 | 0.4840 | 40.30 | 52.86 |
| structure-test | 0.8208 | 0.6082 | 0.5909 | 39.91 | 66.24 |
| structure-no-containment | 0.8875 | 0.5587 | 0.4691 | 41.38 | 54.50 |
| structure-no-import | 0.8875 | 0.5548 | 0.4651 | 43.95 | 71.67 |
| structure-no-call | 0.8333 | 0.6060 | 0.5834 | 45.21 | 74.30 |
| structure-no-test | 0.8875 | 0.5621 | 0.4758 | 49.46 | 80.83 |
| structure-symbol-seed | 0.8333 | 0.5719 | 0.5095 | 106.79 | 198.71 |

[Paired comparison](comparison/dev/report.md); [ablation differences](ablations/dev/report.md).

## test

| Strategy | Recall@10 | NDCG@10 | MRR@10 | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- |
| hybrid-seed | 0.7944 | 0.5947 | 0.5637 | 55.16 | 373.14 |
| bm25-seed | 0.6444 | 0.4854 | 0.4644 | 12.05 | 150.69 |
| dense-seed | 0.7292 | 0.5675 | 0.5480 | 32.42 | 171.72 |
| symbol-seed | 0.7931 | 0.5838 | 0.5438 | 105.57 | 605.54 |
| structure-full | 0.7917 | 0.5109 | 0.4409 | 54.52 | 391.98 |
| structure-none | 0.7944 | 0.5947 | 0.5637 | 46.75 | 324.86 |
| structure-containment | 0.8042 | 0.5958 | 0.5591 | 49.09 | 335.56 |
| structure-import | 0.7861 | 0.5903 | 0.5608 | 47.41 | 336.35 |
| structure-call | 0.7875 | 0.5183 | 0.4497 | 46.90 | 338.76 |
| structure-test | 0.7819 | 0.5805 | 0.5521 | 51.62 | 360.83 |
| structure-no-containment | 0.7875 | 0.5082 | 0.4403 | 52.24 | 362.42 |
| structure-no-import | 0.7917 | 0.5080 | 0.4370 | 48.86 | 348.03 |
| structure-no-call | 0.7819 | 0.5758 | 0.5449 | 55.05 | 380.37 |
| structure-no-test | 0.7917 | 0.5157 | 0.4453 | 54.63 | 389.86 |
| structure-symbol-seed | 0.7972 | 0.5234 | 0.4558 | 96.95 | 591.88 |

[Paired comparison](comparison/test/report.md); [ablation differences](ablations/test/report.md).

## public

| Strategy | Recall@10 | NDCG@10 | MRR@10 | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- |
| hybrid-seed | 0.5000 | 0.3693 | 0.3250 | 79.70 | 161.33 |
| bm25-seed | 0.3000 | 0.2500 | 0.2333 | 31.29 | 40.40 |
| dense-seed | 0.7000 | 0.3897 | 0.2975 | 42.14 | 54.65 |
| symbol-seed | 0.6000 | 0.3261 | 0.2400 | 330.32 | 418.01 |
| structure-full | 0.5000 | 0.3118 | 0.2500 | 79.46 | 164.45 |
| structure-none | 0.5000 | 0.3693 | 0.3250 | 75.61 | 166.24 |
| structure-containment | 0.5000 | 0.3693 | 0.3250 | 94.80 | 168.14 |
| structure-import | 0.5000 | 0.3693 | 0.3250 | 95.35 | 192.52 |
| structure-call | 0.5000 | 0.3118 | 0.2500 | 89.30 | 173.67 |
| structure-test | 0.5000 | 0.3693 | 0.3250 | 84.94 | 158.99 |
| structure-no-containment | 0.5000 | 0.3118 | 0.2500 | 86.05 | 168.45 |
| structure-no-import | 0.5000 | 0.3118 | 0.2500 | 101.34 | 182.20 |
| structure-no-call | 0.5000 | 0.3693 | 0.3250 | 99.22 | 198.84 |
| structure-no-test | 0.5000 | 0.3118 | 0.2500 | 97.12 | 191.30 |
| structure-symbol-seed | 0.6000 | 0.3138 | 0.2260 | 362.60 | 461.48 |

[Paired comparison](comparison/public/report.md); [ablation differences](ablations/public/report.md).

## Offline construction costs

One fresh worker per operation. Seconds include imports, input loads, model loading where needed, construction and serialization. Source/model downloads are excluded.

| Role | Repository | Operation | Seconds | Peak MiB | Artifact MiB |
| --- | --- | --- | --- | --- | --- |
| dev | requests | index | 0.84 | 38.48 | 2.62 |
| dev | requests | graph | 0.29 | 45.76 | 0.80 |
| dev | requests | vectors | 45.90 | 692.08 | 1.21 |
| dev | click | index | 1.14 | 34.68 | 4.27 |
| dev | click | graph | 0.44 | 51.59 | 1.17 |
| dev | click | vectors | 42.85 | 690.04 | 2.47 |
| test | flask | index | 1.09 | 34.81 | 4.76 |
| test | flask | graph | 0.39 | 51.96 | 1.21 |
| test | flask | vectors | 44.74 | 694.53 | 2.83 |
| test | rich | index | 2.33 | 37.78 | 8.08 |
| test | rich | graph | 0.82 | 81.36 | 2.78 |
| test | rich | vectors | 58.28 | 730.18 | 3.54 |
| test | networkx | index | 9.50 | 56.15 | 35.95 |
| test | networkx | graph | 3.53 | 283.87 | 11.50 |
| test | networkx | vectors | 200.83 | 960.43 | 12.90 |
| test | packaging | index | 0.61 | 33.07 | 2.23 |
| test | packaging | graph | 0.29 | 41.87 | 0.70 |
| test | packaging | vectors | 21.59 | 686.19 | 1.00 |
| test | tomlkit | index | 0.52 | 33.07 | 1.75 |
| test | tomlkit | graph | 0.26 | 39.76 | 0.72 |
| test | tomlkit | vectors | 18.05 | 674.30 | 0.99 |
| public | marshmallow | index | 0.55 | 39.39 | 4.93 |
| public | marshmallow | graph | 0.57 | 57.46 | 1.63 |
| public | marshmallow | vectors | 38.80 | 702.16 | 2.96 |

Peak memory is the OS process lifetime high-water mark including native/model allocations and imports, excluding child processes. It is not incremental allocation or a sum across repositories. OS caches are uncontrolled; one build sample and heterogeneous repositories do not establish asymptotic scalability.

Query latency includes encoding, ranking, deduplication and fusion after warmup; it excludes startup and construction. Each experiment loads all repositories in its role into one worker, so its peak is not a per-repository memory measurement. See suite-results.json for experiment lifetime peaks and wall times.
