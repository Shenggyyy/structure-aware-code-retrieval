# Follow-Up LLM-Assisted QA Assessment

New batch status: complete\_with\_failures. Cumulative cohort status: incomplete.
Labels: provisional. New generation calls: 0.
New execution mode: openai. Prior execution mode: openai.

The new batch contains only previously unattempted requests. Prior judgments and unknown outcomes are retained without retry or replacement. Batch completion does not establish complete source-cohort coverage.
Ordinal 0-3 model assessments, not accuracy, probabilities or human review. Means condition on scored cases; all source cases remain in coverage denominators.
Historical answers and automatic citation ID/path/line checks are retained unchanged. Automatic checks do not establish semantic support. Original v1 judge scores and generation costs are excluded.
Reference labels remain provisional; judging may flag them as inadequate or conflicting. Shared generation/judging models can introduce correlated errors. Human calibration remains an optional extension and has not been established.

## Prior, new and cumulative judging

Prior judging covers only prior attempts; new judging covers only the follow-up request population. Cumulative usage counts each attempt once. Historical generation costs are never included. Known subtotals omit missing components; any missing usage keeps the corresponding cumulative totals unknown. Costs are projections at frozen uncached rates, not invoices or budget guarantees.
An attempt without its result has unknown outcome and may be billed. Missing usage keeps token/cost totals unavailable; subtotals remain explicit. Omitted invalid source generations are distinct from eligible requests not yet run.

| Scope | Cases | Attempts | Scored judgments | Failed | Unknown | Not run | Input tokens | Output tokens | Cost USD | Known cost subtotal USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Prior attempts | 13 | 13 | 12 | 0 | 1 | 0 | unknown | unknown | unknown | 0.0842 |
| New batch | 47 | 47 | 46 | 1 | 0 | 0 | 363899 | 17701 | 0.3526 | 0.3526 |
| Cumulative source cohort | 60 | 60 | 58 | 1 | 1 | 0 | unknown | unknown | unknown | 0.4368 |

## Cumulative ordinal scores and coverage

Cumulative scores combine the preserved parent and new batch. Read both execution modes: injected-model fixtures, including fixtures mixed with historical live results, do not establish a cumulative live evaluation.

| Strategy | Source cases | Dimension | Mean (0-3) | Scored | Unsure | N/A | Invalid source | Invalid judgment | Not run | Unknown outcome |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | 12 | correctness | 2.9000 | 10 | 0 | 1 | 0 | 1 | 0 | 0 |
| bm25 | 12 | completeness | 2.8000 | 10 | 0 | 1 | 0 | 1 | 0 | 0 |
| bm25 | 12 | citation_support | 3.0000 | 10 | 0 | 1 | 0 | 1 | 0 | 0 |
| dense | 12 | correctness | 3.0000 | 8 | 0 | 4 | 0 | 0 | 0 | 0 |
| dense | 12 | completeness | 2.4000 | 10 | 0 | 2 | 0 | 0 | 0 | 0 |
| dense | 12 | citation_support | 2.8750 | 8 | 0 | 4 | 0 | 0 | 0 | 0 |
| hybrid | 12 | correctness | 2.7778 | 9 | 0 | 2 | 0 | 0 | 0 | 1 |
| hybrid | 12 | completeness | 2.8889 | 9 | 0 | 2 | 0 | 0 | 0 | 1 |
| hybrid | 12 | citation_support | 2.6667 | 9 | 0 | 2 | 0 | 0 | 0 | 1 |
| structure | 12 | correctness | 2.9000 | 10 | 0 | 2 | 0 | 0 | 0 | 0 |
| structure | 12 | completeness | 2.9000 | 10 | 0 | 2 | 0 | 0 | 0 | 0 |
| structure | 12 | citation_support | 2.9000 | 10 | 0 | 2 | 0 | 0 | 0 | 0 |
| symbol | 12 | correctness | 2.9000 | 10 | 0 | 2 | 0 | 0 | 0 | 0 |
| symbol | 12 | completeness | 2.8000 | 10 | 0 | 2 | 0 | 0 | 0 | 0 |
| symbol | 12 | citation_support | 2.8000 | 10 | 0 | 2 | 0 | 0 | 0 | 0 |

## Matched comparisons

Candidate minus baseline on shared scored case IDs for each pair and dimension. Conditional means with different coverage are not matched comparisons. These are within-revision comparisons, not v1 versus v2 causal estimates.

| Baseline | Candidate | Dimension | Paired cases | Mean delta |
| --- | --- | --- | ---: | ---: |
| bm25 | dense | correctness | 8 | 0.1250 |
| bm25 | dense | completeness | 10 | -0.4000 |
| bm25 | dense | citation_support | 8 | -0.1250 |
| bm25 | hybrid | correctness | 9 | -0.2222 |
| bm25 | hybrid | completeness | 9 | 0.0000 |
| bm25 | hybrid | citation_support | 9 | -0.3333 |
| bm25 | structure | correctness | 10 | 0.0000 |
| bm25 | structure | completeness | 10 | 0.1000 |
| bm25 | structure | citation_support | 10 | -0.1000 |
| bm25 | symbol | correctness | 10 | 0.0000 |
| bm25 | symbol | completeness | 10 | 0.0000 |
| bm25 | symbol | citation_support | 10 | -0.2000 |
| dense | hybrid | correctness | 7 | -0.2857 |
| dense | hybrid | completeness | 9 | 0.5556 |
| dense | hybrid | citation_support | 7 | -0.2857 |
| dense | structure | correctness | 8 | -0.1250 |
| dense | structure | completeness | 10 | 0.5000 |
| dense | structure | citation_support | 8 | 0.0000 |
| dense | symbol | correctness | 8 | -0.1250 |
| dense | symbol | completeness | 10 | 0.4000 |
| dense | symbol | citation_support | 8 | -0.1250 |
| hybrid | structure | correctness | 9 | 0.2222 |
| hybrid | structure | completeness | 9 | 0.1111 |
| hybrid | structure | citation_support | 9 | 0.2222 |
| hybrid | symbol | correctness | 9 | 0.2222 |
| hybrid | symbol | completeness | 9 | 0.0000 |
| hybrid | symbol | citation_support | 9 | 0.2222 |
| structure | symbol | correctness | 10 | 0.0000 |
| structure | symbol | completeness | 10 | -0.1000 |
| structure | symbol | citation_support | 10 | -0.1000 |

## Timing and retained evidence

Latency is judge-call plus validation time. Prior latency uses prior attempts as its denominator; new latency uses follow-up requests; cumulative latency uses all eligible source requests. Missing outcomes stay missing. No combined generation latency or wall-clock service latency is inferred.
Per-scope latency, token subtotals, missing counts and exact shared case IDs are in summary.json. Parent judgments remain preserved; new raw results are in results.jsonl. No human-review or true-accuracy claim is made.
