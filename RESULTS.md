# Retrieval Results and Limitations

This project tests whether repository structure improves code retrieval for LLM
applications. The implemented pipeline makes five retrieval strategies, relation
ablations, source traces, and computational costs reproducible. **The frozen full
structure heuristic did not improve aggregate retrieval quality over Hybrid on the
expanded test candidates.** Reporting this failure is part of the experiment.

All relevance labels and quality results remain **provisional**. Human review is
optional, and no human-reviewed labels are claimed. No live LLM answer or judge
experiment has been run. Retrieval scores and automatic source checks do not
establish answer correctness, completeness or semantic citation support.

## Evaluation scope

The frozen M6c suite contains 45 runs: five main strategies and ten additional
structure configurations on each of three separate datasets. Source snapshots,
model revision, configurations, rankings, and per-query metrics are recorded.

| Dataset role | Repositories | Queries | Judgments |
| --- | --- | ---: | ---: |
| Development | Requests, Click | 40 | 55 |
| Expanded test candidates | Flask, Rich, NetworkX, Packaging, TOMLKit | 120 | 164 |
| Public adaptation | Marshmallow | 10 | 10 |

The eight snapshots contain 1,130 indexed Python files, 17,380 symbols, and 20,003
chunks. Public questions are adapted from RepoQA to full-repository symbol retrieval;
these scores are not comparable to original RepoQA scoring. Dataset roles are not
pooled. Expanded test outcomes are now exposed; future tuning requires a new
untouched test version.

## Expanded test findings

Scores below are query-macro means at **K = 10**, with symbols as the evaluation
unit. Unjudged candidates receive zero relevance; Precision@10 is agreement with
existing sparse labels, not independently reviewed precision.

| Strategy | Recall@10 | Precision@10 | MRR@10 | NDCG@10 | Query p50 ms | Query p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BM25 | 0.6444 | 0.0825 | 0.4644 | 0.4854 | 12.05 | 150.69 |
| Dense | 0.7292 | 0.0958 | 0.5480 | 0.5675 | 32.42 | 171.72 |
| Hybrid | 0.7944 | 0.1050 | 0.5637 | 0.5947 | 55.16 | 373.14 |
| Symbol-aware | 0.7931 | 0.1042 | 0.5438 | 0.5838 | 105.57 | 605.54 |
| Structure-aware (full) | 0.7917 | 0.1067 | 0.4409 | 0.5109 | 54.52 | 391.98 |

Structure minus Hybrid changes NDCG@10 by **−0.0839**, with a paired
repository-cluster 95% percentile interval **[−0.1356, −0.0381]** and 15/49/56
query wins/ties/losses. Recall@10 changes by **−0.0028**, interval
**[−0.0500, 0.0444]**. These intervals use 2,000 draws and seed 0 across five
selected repositories; they do not correct incomplete labels or multiple comparisons.

On 40 cross-file questions, Structure increases Recall@10 from **0.7083 to 0.7500**,
while NDCG@10 decreases from **0.5268 to 0.4995**. Related-symbol promotion can find
additional designated evidence while displacing stronger initial matches. Full
Structure has lower NDCG@10 in every expanded test repository.

[Source-traced successes and regressions](reports/m6c/README.md#source-traced-successes-and-regressions)
and [saved cases](reports/m6c/case-analysis.json) explain individual promotions.
Cases were selected after scoring and are illustrative. Fixed relation ablations
are preserved; no test-derived configuration replaces the main model.

## Separate development and public results

| Strategy | Dev Recall@10 | Dev NDCG@10 | Public Recall@10 | Public NDCG@10 |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.7542 | 0.6203 | 0.3000 | 0.2500 |
| Dense | 0.7833 | 0.5968 | 0.7000 | 0.3897 |
| Hybrid | 0.8208 | 0.6450 | 0.5000 | 0.3693 |
| Symbol-aware | 0.7917 | 0.5823 | 0.6000 | 0.3261 |
| Structure-aware (full) | 0.8875 | 0.5545 | 0.5000 | 0.3118 |

Development recall gains do not carry over to the expanded test aggregate. The
ten-query, single-repository public adaptation has a different ordering and cannot
establish a general benchmark winner. Cluster intervals are withheld for development
and public roles because they contain fewer than five repositories.

## Cost and measurement limits

All 24 construction operations completed: one fresh index, graph, and vector build
per repository. On the largest corpus, NetworkX (9,252 chunks), vector construction
took **200.83 seconds** with **960.43 MiB** worker peak memory and **12.90 MiB** saved
vector artifacts. Time includes imports, model loading, construction, and serialization;
source/model downloads are excluded. Worker memory excludes the coordinator and
other processes.

Dense retrieval uses pinned `all-MiniLM-L6-v2` on CPU, 384-dimensional float32 vectors,
and a 256-token encoder input limit. Of NetworkX's document representations,
2,861 exceeded that limit. Dense retrieval scores the full corpus; bounded relation
expansion does not make retrieval sublinear.

Timing was measured on an interactive Windows host with an Intel Core i9-13900H and
four encoder/BLAS threads. Separate run medians do not establish zero Structure
overhead or a production latency guarantee. Static relationships are conservative
approximations; missing dynamic relationships and sparse relevance labels limit
the conclusions.

## Evidence and remaining work

The [generated evidence overview](reports/overview/report.md) checks all 45 saved
runs against recorded rankings, query metrics, and quality fingerprints. It reads
existing evidence without rerunning retrieval. Timing and memory are separate
recorded measurements, outside the quality fingerprints.

See the [complete experiment analysis](reports/m6c/README.md),
[reproduction guide](docs/reproduction.md), and [acceptance status](docs/status.md).
Remaining acceptance is the authorized live QA comparison and LLM-assisted assessment
of correctness, completeness and citation support, with recorded usage, failures,
latency and combined generation/judging costs. The judge is planned for M7b and has
no current scores. Model judgments will be reported as model judgments, not human
ground truth. Optional manual review is not a completion prerequisite; the current
sparse-label retrieval results retain their stated limitations.
