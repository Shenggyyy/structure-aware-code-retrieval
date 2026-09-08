# LLM-Assisted QA Assessment

Status: complete\_with\_failures. Labels: provisional.

Ordinal 0-3 model assessments, not accuracy, probabilities or human review. Means condition on scored cases; all planned cases remain in coverage denominators.
Human calibration is optional and has not been established.
Automatic citation checks establish identity/location, not semantic support.

| Strategy | Valid answers / planned | Dimension | Mean (0-3) | Scored | Unsure | N/A | Invalid generation | Invalid judgment | Not run | Unknown outcome |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | 10 / 12 | correctness | 3.0000 | 4 | 0 | 1 | 0 | 7 | 0 | 0 |
| bm25 | 10 / 12 | completeness | 3.0000 | 4 | 0 | 1 | 0 | 7 | 0 | 0 |
| bm25 | 10 / 12 | citation_support | 3.0000 | 4 | 0 | 1 | 0 | 7 | 0 | 0 |
| dense | 8 / 12 | correctness | 2.7500 | 4 | 0 | 0 | 0 | 8 | 0 | 0 |
| dense | 8 / 12 | completeness | 3.0000 | 4 | 0 | 0 | 0 | 8 | 0 | 0 |
| dense | 8 / 12 | citation_support | 2.7500 | 4 | 0 | 0 | 0 | 8 | 0 | 0 |
| hybrid | 10 / 12 | correctness | 2.8333 | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| hybrid | 10 / 12 | completeness | 2.8333 | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| hybrid | 10 / 12 | citation_support | 2.6667 | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| structure | 10 / 12 | correctness | 3.0000 | 3 | 0 | 1 | 0 | 8 | 0 | 0 |
| structure | 10 / 12 | completeness | 3.0000 | 3 | 1 | 0 | 0 | 8 | 0 | 0 |
| structure | 10 / 12 | citation_support | 3.0000 | 3 | 0 | 1 | 0 | 8 | 0 | 0 |
| symbol | 10 / 12 | correctness | 2.7500 | 4 | 0 | 1 | 0 | 7 | 0 | 0 |
| symbol | 10 / 12 | completeness | 2.7500 | 4 | 0 | 1 | 0 | 7 | 0 | 0 |
| symbol | 10 / 12 | citation_support | 2.7500 | 4 | 0 | 1 | 0 | 7 | 0 | 0 |

## Observed usage and cost

Frozen uncached-rate projections from observed usage, not invoices. Observed subtotals omit missing components and are not full totals.

| Stage | Observed calls | Calls with unknown outcome | Input tokens | Output tokens | Cost USD | Known cost subtotal USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| generation | 60 | 0 | 141024 | 6481 | 0.1349 | 0.1349 |
| judging | 60 | 0 | 352935 | 20129 | 0.3553 | 0.3553 |

Combined cost USD: 0.4902; known subtotal: 0.4902. Missing usage is unknown, not zero.

## Matched comparisons

Candidate minus baseline on shared scored case IDs for each pair and dimension; differing conditional means are not treated as matched samples.

| Baseline | Candidate | Dimension | Paired cases | Mean delta |
| --- | --- | --- | ---: | ---: |
| bm25 | dense | correctness | 2 | -0.5000 |
| bm25 | dense | completeness | 2 | 0.0000 |
| bm25 | dense | citation_support | 2 | -0.5000 |
| bm25 | hybrid | correctness | 4 | -0.2500 |
| bm25 | hybrid | completeness | 4 | -0.2500 |
| bm25 | hybrid | citation_support | 4 | -0.5000 |
| bm25 | structure | correctness | 2 | 0.0000 |
| bm25 | structure | completeness | 2 | 0.0000 |
| bm25 | structure | citation_support | 2 | 0.0000 |
| bm25 | symbol | correctness | 2 | -0.5000 |
| bm25 | symbol | completeness | 2 | -0.5000 |
| bm25 | symbol | citation_support | 2 | -0.5000 |
| dense | hybrid | correctness | 2 | 0.5000 |
| dense | hybrid | completeness | 2 | 0.0000 |
| dense | hybrid | citation_support | 2 | 0.5000 |
| dense | structure | correctness | 2 | 0.5000 |
| dense | structure | completeness | 2 | 0.0000 |
| dense | structure | citation_support | 2 | 0.5000 |
| dense | symbol | correctness | 1 | 0.0000 |
| dense | symbol | completeness | 1 | 0.0000 |
| dense | symbol | citation_support | 1 | 0.0000 |
| hybrid | structure | correctness | 3 | 0.0000 |
| hybrid | structure | completeness | 3 | 0.0000 |
| hybrid | structure | citation_support | 3 | 0.0000 |
| hybrid | symbol | correctness | 4 | 0.0000 |
| hybrid | symbol | completeness | 4 | 0.0000 |
| hybrid | symbol | citation_support | 4 | 0.2500 |
| structure | symbol | correctness | 2 | 0.0000 |
| structure | symbol | completeness | 2 | 0.0000 |
| structure | symbol | citation_support | 2 | 0.0000 |

Exact paired case IDs, automatic-check counts, abstentions, reference-status counts, per-strategy usage and timing coverage are retained in summary.json.
Individual reference issues and raw judgments are retained in records.json and results.jsonl.

## Timing boundary

Preparation is measured offline retrieval plus context/prompt packing. End-to-end sums those preparation times and observed generation/validation and judging times for the same case; excludes model/index loading, run orchestration, reporting and time between stages. It is not wall-clock service latency.

No new benchmark labels or human-review claims are created by this report.
