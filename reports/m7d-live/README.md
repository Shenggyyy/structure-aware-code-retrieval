# M7d Live: Partial v2 Judge Experiment

Recorded on 2026-09-08. **The authorized 60-case run was interrupted after 13
journaled attempts: 12 results are saved, one outcome is unknown, and 47 requests
were not run.** All 12 saved judgments pass v2 validation. This is a partial real
experiment, not completion of the planned comparison. No request was retried or
resumed, and no new answers were generated.

## Scope and preserved evidence

The owner approved `gpt-5.4-mini-2026-03-17`, up to 60 judge requests and a US$2.20
budget against the [frozen proposal](../m7d/proposal.json). The input estimate was
US$2.13340275. All 60 answers, their source contexts and common provisional references
are identical to the original M7b experiment. Judging uses rubric v2, reasoning
`none`, per-answer strict schemas and a 2,048-token output limit.

The completed prefix contains all five strategies for `qa-click-04` and `qa-click-08`,
then BM25 and Dense for `qa-click-13`. The next request, `qa-click-13 / hybrid`, has
an attempt record but no saved response. Its outcome and possible charge are unknown.
No Requests cases or scope-control cases have a saved v2 judgment in this run.

| Strategy | Source cases | Accepted v2 judgments | Unknown outcome | Not run |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 12 | 3 | 0 | 9 |
| Dense | 12 | 3 | 0 | 9 |
| Hybrid | 12 | 2 | 1 | 9 |
| Structure | 12 | 2 | 0 | 10 |
| Symbol | 12 | 2 | 0 | 10 |
| Total | 60 | 12 | 1 | 47 |

The 12 responses report the requested model snapshot; provider revision metadata
is unavailable in each. They contain 11 scored correctness/support dimensions and
one N/A abstention; completeness has 12 scored dimensions. There are no `unsure`
dimensions among the known results. Every dimension retains one unknown and 47
not-run cases in its planned denominator.

| Dimension | Scored / planned | N/A | Conditional mean, 0–3 |
| --- | ---: | ---: | ---: |
| Correctness | 11 / 60 | 1 | 2.9091 |
| Completeness | 12 / 60 | 0 | 2.6667 |
| Citation support | 11 / 60 | 1 | 2.9091 |

These are ordinal model assessments, not probabilities, true correctness rates or
human review. All known assessments mark the references usable; one existing Dense
abstention is judged unnecessary. The [summary](summary.json) preserves per-strategy
counts and shared scored case IDs. This short, ordered Click-only prefix cannot
support a strategy ranking or a representative v2 reliability estimate.

On precisely these 12 answer/strategy pairs, v1 had six accepted and six invalid
judgments; v2 has 12 saved accepted judgments. This is a descriptive observation on
exposed development cases, not a causal accuracy improvement. The original complete
v1 outcome remains 24 accepted / 36 invalid; do not mix its scores with v2 scores.

## Known usage and unknown total

| Measurement | Known 12 results |
| --- | ---: |
| Input tokens | 84,733 |
| Output tokens | 4,598 |
| Total tokens | 89,331 |
| Cached / reasoning tokens | 0 / 0 |
| Cost subtotal at frozen uncached rates | **US$0.08424075** |
| Mean judge-and-validation latency | 4,074.71 ms |
| Observed judge-and-validation time sum | 48,896.49 ms |

**Full token usage and full cost remain unknown.** The subtotal excludes the unknown
13th outcome and all historical generation/judging costs; it is not an invoice.
The frozen prices are US$0.75 input and US$4.50 output per million tokens from the
[official model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
The approved budget is an estimate gate, not a billing hard cap. Latency values cover
only known judging and validation, not full experiment or service wall-clock time.

## Interruption and diagnostic limit

The original CLI caught the exception and printed only a generic execution error.
It did not preserve the exception class, operation phase or traceback. Therefore
**the triggering cause cannot be established from this archive**. Offline validation
of the pending prepared request succeeds. Short elapsed time between the last attempt
record and interruption does not prove that no request was sent or billed.

The exact executing code was preserved before adding safe diagnostics for future
runs. Future unexpected exceptions can record type, phase and code locations without
raw exception arguments, credentials or local variables. That improvement neither
recovers the missing response nor establishes that the original cause is fixed.
The original run and its unknown outcome are not rewritten.

## Local software validation

After adding diagnostics, the full offline suite passed **793 tests**, with one
Windows symlink-privilege skip. Package statement/branch coverage is **91.62%**;
standalone scripts are exercised by integration tests but excluded from that
coverage denominator. Nine new regression cases cover failure phases, preservation
of the original exception and omission of sensitive exception text. Ruff lint and
format checks pass, as does verification of the unchanged 45-run retrieval overview.
All 79 archive member hashes and the extracted partial run passed independent
checks. These software checks made no API calls. Current remote CI awaits the
owner's commit and push; Linux/container checks were not rerun locally.

## Archive and offline reproduction

- [run.zip](run.zip): immutable partial run, all frozen source inputs, raw known
  responses and journals, exact executing code, dependencies/configs and attribution.
- [manifest.json](manifest.json): archive/member SHA256 values, source fingerprints,
  observed/unknown counts and offline verification. The archive is about 6.0 MB.
- [plan.json](plan.json), [approval.json](approval.json): frozen request scope and
  the authorized invocation. The former remains an offline proposal; the latter
  records execution consent without claiming identity verification.
- [case-results.json](case-results.json), [summary.json](summary.json),
  [report.md](report.md): every source case, coverage, new scores, usage and timing.
- [validation.json](validation.json): current software and archive checks.

```powershell
Expand-Archive -LiteralPath reports/m7d-live/run.zip -DestinationPath artifacts/qa/m7d-live-replay-001
uv run --locked python scripts/verify_qa_judge_revision.py --run artifacts/qa/m7d-live-replay-001/run
```

Use a fresh extraction directory. Verification needs no credentials or API calls and
does not recover missing responses. It checks internal consistency, not independent
provider authenticity. The configured API credential was checked in memory and is
absent from the archived files; authentication headers are not recorded.

Excerpts retain upstream ownership: Requests at
`0e322af87745eff34caffe4df68456ebc20d9068` uses [Apache-2.0](licenses/requests-LICENSE)
and its [NOTICE](licenses/requests-NOTICE); Click at
`934813e4d421071a1b3db3973c02fe2721359a6e` uses [BSD-3-Clause](licenses/click-LICENSE.txt).
All attribution files are also inside the archive. Labels remain provisional and
human calibration optional. A complete 60-case v2 comparison is still unfinished;
any further paid work must explicitly address the preserved unknown attempt.
