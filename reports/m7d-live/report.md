# Judge-Only LLM-Assisted QA Assessment

Status: interrupted. Labels: provisional.
Execution mode: openai. New generation calls: 0.

Ordinal 0-3 model assessments, not accuracy, probabilities or human review. Means condition on scored cases; all source cases remain in coverage denominators.
Answers, automatic identity/path/line checks and source abstentions are historical observations. Their consistency is revalidated against the frozen archive; this run generates no new answers or retrieval evidence. Historical judge scores are excluded. Automatic checks do not establish semantic support.
Reference labels remain provisional; judging may flag them as inadequate or conflicting. Shared generation/judging models can introduce correlated errors. Human calibration remains an optional extension and has not been established.

| Strategy | Source cases | Dimension | Mean (0-3) | Scored | Unsure | N/A | Invalid source | Invalid judgment | Not run | Unknown outcome |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | 12 | correctness | 2.6667 | 3 | 0 | 0 | 0 | 0 | 9 | 0 |
| bm25 | 12 | completeness | 2.6667 | 3 | 0 | 0 | 0 | 0 | 9 | 0 |
| bm25 | 12 | citation_support | 3.0000 | 3 | 0 | 0 | 0 | 0 | 9 | 0 |
| dense | 12 | correctness | 3.0000 | 2 | 0 | 1 | 0 | 0 | 9 | 0 |
| dense | 12 | completeness | 2.0000 | 3 | 0 | 0 | 0 | 0 | 9 | 0 |
| dense | 12 | citation_support | 2.5000 | 2 | 0 | 1 | 0 | 0 | 9 | 0 |
| hybrid | 12 | correctness | 3.0000 | 2 | 0 | 0 | 0 | 0 | 9 | 1 |
| hybrid | 12 | completeness | 3.0000 | 2 | 0 | 0 | 0 | 0 | 9 | 1 |
| hybrid | 12 | citation_support | 3.0000 | 2 | 0 | 0 | 0 | 0 | 9 | 1 |
| structure | 12 | correctness | 3.0000 | 2 | 0 | 0 | 0 | 0 | 10 | 0 |
| structure | 12 | completeness | 3.0000 | 2 | 0 | 0 | 0 | 0 | 10 | 0 |
| structure | 12 | citation_support | 3.0000 | 2 | 0 | 0 | 0 | 0 | 10 | 0 |
| symbol | 12 | correctness | 3.0000 | 2 | 0 | 0 | 0 | 0 | 10 | 0 |
| symbol | 12 | completeness | 3.0000 | 2 | 0 | 0 | 0 | 0 | 10 | 0 |
| symbol | 12 | citation_support | 3.0000 | 2 | 0 | 0 | 0 | 0 | 10 | 0 |

## New judging usage and cost

Only new judge calls are counted. Frozen uncached-rate projections from observed usage are not invoices. Known subtotals omit missing components. Historical generation and judging costs are excluded.
An attempt without its result has unknown outcome and may be billed. Missing usage keeps token/cost totals unavailable; subtotals remain explicit. Omitted invalid source generations are distinct from eligible requests not yet run.
Eligible requests: 60; omitted source cases: 0; not run: 47; unknown outcomes: 1.

| Observed calls | Calls with unknown outcome | Input tokens | Output tokens | Cost USD | Known cost subtotal USD |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | 1 | unknown | unknown | unknown | 0.0842 |

## Matched comparisons

Candidate minus baseline on shared scored case IDs for each pair and dimension. Conditional means with different coverage are not matched comparisons. These are within-revision comparisons, not v1 versus v2 causal estimates.

| Baseline | Candidate | Dimension | Paired cases | Mean delta |
| --- | --- | --- | ---: | ---: |
| bm25 | dense | correctness | 2 | 0.5000 |
| bm25 | dense | completeness | 3 | -0.6667 |
| bm25 | dense | citation_support | 2 | -0.5000 |
| bm25 | hybrid | correctness | 2 | 0.0000 |
| bm25 | hybrid | completeness | 2 | 0.0000 |
| bm25 | hybrid | citation_support | 2 | 0.0000 |
| bm25 | structure | correctness | 2 | 0.0000 |
| bm25 | structure | completeness | 2 | 0.0000 |
| bm25 | structure | citation_support | 2 | 0.0000 |
| bm25 | symbol | correctness | 2 | 0.0000 |
| bm25 | symbol | completeness | 2 | 0.0000 |
| bm25 | symbol | citation_support | 2 | 0.0000 |
| dense | hybrid | correctness | 1 | 0.0000 |
| dense | hybrid | completeness | 2 | 1.5000 |
| dense | hybrid | citation_support | 1 | 1.0000 |
| dense | structure | correctness | 1 | 0.0000 |
| dense | structure | completeness | 2 | 1.5000 |
| dense | structure | citation_support | 1 | 1.0000 |
| dense | symbol | correctness | 1 | 0.0000 |
| dense | symbol | completeness | 2 | 1.5000 |
| dense | symbol | citation_support | 1 | 1.0000 |
| hybrid | structure | correctness | 2 | 0.0000 |
| hybrid | structure | completeness | 2 | 0.0000 |
| hybrid | structure | citation_support | 2 | 0.0000 |
| hybrid | symbol | correctness | 2 | 0.0000 |
| hybrid | symbol | completeness | 2 | 0.0000 |
| hybrid | symbol | citation_support | 2 | 0.0000 |
| structure | symbol | correctness | 2 | 0.0000 |
| structure | symbol | completeness | 2 | 0.0000 |
| structure | symbol | citation_support | 2 | 0.0000 |

## Timing boundary and retained evidence

Only new judging latency is reported, with eligible judge requests as its coverage denominator. Historical retrieval/generation latency is excluded; no new combined end-to-end or wall-clock service latency is inferred.
Exact paired case IDs, historical automatic-check coverage, abstentions, new reference-status counts and per-strategy judge usage/latency are in summary.json. Individual reference issues and raw judgments remain in records.json and results.jsonl.
No new benchmark labels or human-review claims are created by this report.
