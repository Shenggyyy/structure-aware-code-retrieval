# M7b: First Live Mini/Mini QA Experiment

Recorded on 2026-09-08. **All 120 authorized requests finished: 60 generations and
60 judgments.** The run status is `complete_with_failures`: generation passed
validation in all 60 cases, but only 24 judge outputs passed the frozen protocol.
This is real provider evidence, not a test-double demonstration. It does not
establish a reliable QA-quality ranking among retrieval strategies.

## Scope, approval and cost

The owner selected `gpt-5.4-mini-2026-03-17` for both stages and approved US$5.63
for one run. This supersedes the earlier GPT-5.4 judge proposal in
[the offline checkpoint](../m7b/README.md). The exact new preflight estimate was
**US$5.6289795**. There were no retries, replacements or extra requests.

The fixed scope is 12 provisional development questions from Requests and Click,
each evaluated with BM25, Dense, Hybrid, Symbol and Structure retrieval. Generation
allows 1,024 output tokens; judging allows 2,048. Both use reasoning effort `none`,
strict structured output, no tools, the same rubric v1 and common case references.
Both reported model IDs match the requested snapshot in every response.

| Stage | Calls | Input tokens | Output tokens | Mean API/validation latency | Cost at frozen uncached rates |
| --- | ---: | ---: | ---: | ---: | ---: |
| Generation | 60 | 141,024 | 6,481 | 1.800 s | US$0.134933 |
| Judging | 60 | 352,935 | 20,129 | 3.209 s | US$0.355282 |
| Combined | 120 | 493,959 | 26,610 | 5.061 s including preparation components | **US$0.490214** |

Usage is available for all 120 calls; there are no unknown outcomes or missing token
counts. Generation reports 1,792 cached input tokens, and both stages report zero
reasoning tokens. Costs above apply the frozen $0.75/$4.50 per million input/output
rates to all tokens, including cached input; they are **usage-based projections,
not an invoice**. Rates come from the official
[GPT-5.4 Mini page](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

The estimate was conservative: it reserved the full 65,536-byte answer ceiling for
each judge request, counted input bytes as tokens and budgeted maximum outputs.
Observed use was substantially lower. The timing sum includes frozen offline
retrieval/packing plus generation and judging; it excludes loading, checkpoint I/O,
orchestration and gaps between stages, and is not service wall-clock latency.

## Outcomes and automatic checks

- Generation: **48 answered, 12 model abstentions**, zero invalid answers and zero
  provider errors. All ten scope-control instances abstained; Dense also abstained
  on two development cases provisionally labeled answerable. Expected-status agreement is not
  a correctness measurement.
- Source evidence IDs, paths and line ranges: **60/60 valid**.
- Answer citation IDs: **48/48 checked answers valid**. The 12 abstentions have no
  claim citations; they are not assigned perfect citation-support scores.
- Judge output: **24/60 accepted, 36/60 invalid**. There are no skipped or unrun
  requests. Invalid judge outputs have null semantic results, not zero scores.

| Strategy | Answered / 12 | Accepted judgments / 12 | Invalid judgments | Correctness mean (scored n) | Completeness mean (scored n) | Citation support mean (scored n) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BM25 | 10 | 5 | 7 | 3.00 (4) | 3.00 (4) | 3.00 (4) |
| Dense | 8 | 4 | 8 | 2.75 (4) | 3.00 (4) | 2.75 (4) |
| Hybrid | 10 | 6 | 6 | 2.83 (6) | 2.83 (6) | 2.67 (6) |
| Structure | 10 | 4 | 8 | 3.00 (3) | 3.00 (3) | 3.00 (3) |
| Symbol | 10 | 5 | 7 | 2.75 (4) | 2.75 (4) | 2.75 (4) |

These are **conditional ordinal 0–3 means on different subsets**, not accuracy
rates. Each dimension has only 21 scored rows out of 60 planned. Correctness and
support also have three N/A rows; completeness has two N/A and one unsure row.
The [machine-readable summary](summary.json) and [generated report](report.md)
retain all denominators. Three accepted abstentions were judged appropriate;
the other nine abstentions have invalid judgments, not inferred semantic scores.

Hybrid and Structure share only three scored cases per dimension. All three are
ties at 3; this tiny, selected subset establishes neither improvement nor
equivalence. Do not rank strategies from their unmatched conditional means.

## Judge failures and limitations

The frozen validator's first reported errors were:

| Error | Count |
| --- | ---: |
| Unknown or duplicate evidence IDs in correctness | 26 |
| Unknown or duplicate evidence IDs in completeness | 5 |
| Unknown or duplicate evidence IDs in packed-context sufficiency | 3 |
| Out-of-scope abstention completeness must be N/A | 2 |

An observed failure pattern is output such as `S1` where the judge protocol requires
`packed:S1` (or `reference:R1` for independent references). The prompt explicitly
requests these namespaces, but its JSON schema allows arbitrary strings. Successful
structured JSON therefore does not imply valid evidence references. We did not
normalize these IDs, alter the rubric, salvage individual scores from rejected
outputs or rerun failures after seeing the results.

Only 40% of judgments are accepted. Missing assessments can depend on question,
answer or strategy, so their removal can bias the remaining means. A useful next
step is an offline, versioned protocol revision that makes evidence IDs explicit in
the schema and clarifies abstention status constraints, tested on these archived
failures. This is evaluator engineering on exposed development data; a later paid
comparison needs fresh approval and a clearly identified protocol version.

Labels and reference points remain provisional. The generator and judge use the
same model, introducing correlated-error and self-preference risks. A 12-question
development set and uncalibrated model scores do not establish general repository
QA accuracy. Optional human calibration is still an extension, not a prerequisite.

## Evidence and offline reproduction

- [plan.json](plan.json), [approval.json](approval.json): exact settings, source,
  reference/rubric hashes, request ordering, models and approved budget.
- [case-results.json](case-results.json): every planned case/strategy outcome,
  accepted dimension scores and first judge-validation error.
- [summary.json](summary.json), [report.md](report.md): separate automatic and
  semantic results, coverage, matched case IDs, reported usage and timing.
- [run.zip](run.zip): exact request/response journals, all raw provider outputs,
  prepared source contexts, references, rubric and the source code that executed
  the run. The executing source hashes match the recorded approval metadata.
- [manifest.json](manifest.json): archive/member SHA-256 hashes, run fingerprints
  and offline validation observations. The configured credential is absent from
  every archived file; authentication headers are not recorded.

Archived excerpts retain their upstream ownership. Requests is pinned to
`0e322af87745eff34caffe4df68456ebc20d9068` under
[Apache-2.0](licenses/requests-LICENSE), with its [NOTICE](licenses/requests-NOTICE).
Click is pinned to `934813e4d421071a1b3db3973c02fe2721359a6e` under
[BSD-3-Clause](licenses/click-LICENSE.txt). These files are also included under
`upstream-licenses/` in the archive. The excerpts are selected for evaluation,
not modified upstream files or a claim of upstream endorsement.

The archive is approximately 3.7 MB. Extract it to a fresh directory and verify the
stored evidence without credentials or network requests:

```powershell
Expand-Archive -LiteralPath reports/m7b-live/run.zip -DestinationPath artifacts/qa/m7b-replay-001
uv run --locked python scripts/verify_qa_assessment.py --run artifacts/qa/m7b-replay-001/run
```

Offline verification replays validation and recomputes the saved summaries; it does
not regenerate model outputs. Hashes establish internal consistency, not independent
proof of provider authenticity. Exact inputs cannot guarantee identical future API
responses. Use [the QA protocol](../../docs/qa.md) to prepare a new experiment;
the saved approval does not authorize repeating this paid run.

The immutable archived `run/report.md` has one presentation mistake: its final note
places individual reference issues in `summary.json`. They are actually stored in
`records.json` and `results.jsonl`; the summary has reference-status counts. The
current report renderer corrects this wording without changing the saved scores.
Local software checks: **679 tests passed, one Windows symlink-privilege test
skipped, 91.25% combined statement/branch coverage**. Ruff, offline distribution
builds, all 45 saved retrieval runs and verification of the extracted live archive
passed. The wheel's 41 Python files match current source. These offline tests made
no additional API calls. Details are in [validation.json](validation.json);
this checkpoint's remote CI awaits the owner's commit and push.
