# M7e Live Follow-Up: Completed Attempts and Cumulative Evidence

Recorded 2026-09-09. This checkpoint completes the approved 47-request follow-up
using `gpt-5.4-mini-2026-03-17`. All 47 responses were saved: **46 judgments passed
the protocol and one failed it**. There were no provider errors or new unknown
outcomes. No answers were regenerated and no requests were retried.

Across the original partial v2 run and this follow-up, all 60 planned requests
have been attempted: **58 valid judgments, one invalid judgment and one historical
unknown outcome**. The new batch is `complete_with_failures`; the cumulative
cohort remains `incomplete`. Completing the engineering and planned experiment
attempts does not imply complete score coverage or reliable semantic accuracy.
Labels remain **provisional**. Human review is an optional extension.

## Frozen scope and provenance

- Executing source commit: `daf6aa4`; the owner reported that checkpoint passed CI.
- Approved new budget: **US$1.80**; frozen preflight estimate: US$1.68210075.
  The budget is an execution guard based on estimates, not a provider billing cap.
- Plan fingerprint:
  `b69337459f8b22417d0d5e4cc88063c2f8d9f04d1d3571fe00592132e1313ef3`.
- The follow-up selects only the 47 previously unattempted requests from
  [the M7e prepared plan](../m7e/README.md). All 13 prior attempts, including the
  unknown one, were excluded from execution and retained unchanged.
- The original 60 generations, packed contexts, automatic citation checks and
  provisional references remain unchanged. This adds judging evidence only.
- All 59 saved v2 responses report the requested Mini snapshot. Provider revision
  identifiers were not returned. Frozen prompts, rubric, schemas and raw responses
  are included in the archive.

## Attempts, usage and cost

| Scope | Attempts | Saved responses | Valid judgments | Invalid | Unknown | Known cost subtotal (USD) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prior v2 batch | 13 | 12 | 12 | 0 | 1 | 0.08424075 |
| New follow-up | 47 | 47 | 46 | 1 | 0 | 0.35257875 |
| Cumulative v2 | 60 | 59 | 58 | 1 | 1 | 0.43681950 |

No eligible requests remain unattempted. The new batch has fully observed usage:
363,899 input tokens, 17,701 output tokens and 381,600 total tokens; 28,160 input
tokens were reported as cached and zero output tokens as reasoning. Mean judge
call plus validation latency was **3,413.61 ms** across 47 requests. This measures
neither answer-generation latency nor end-to-end wall-clock service latency.

The cost projection uses the frozen uncached rates of US$0.75/M input and
US$4.50/M output tokens, consistent with the
[official model pricing](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
checked on 2026-09-09. It deliberately does not subtract the cached-input discount.
These are usage-based projections, not invoices. The invalid response is included
in usage and cost. Cumulative known usage is 470,931 tokens; **full cumulative
usage and cost remain unknown**, because the historical attempt has no saved
response. Original generation and v1 judging costs are excluded from these v2
subtotals and remain documented in [M7b](../m7b-live/README.md).

## Preserved protocol failure

The new invalid result is `qa-requests-scope-01 / bm25`. Its response passes the
frozen JSON schema, but the host validator rejects completeness=`unsure` for an
out-of-scope abstention with a usable reference. The fixed rule requires
`not_applicable`: **“Out-of-scope abstention completeness must be N/A.”**

The whole judgment remains invalid; no individual dimension is salvaged. The
historical `qa-click-13 / hybrid` attempt remains unknown. Neither record is
replaced, retried or silently removed from the denominator. This demonstrates
that schema-valid structured output can still violate cross-field scoring rules.

## Model assessments and denominators

Scores are ordinal **0–3 model assessments**, not probabilities, true correctness
rates or human review. Means condition on numerically scored cases. Each strategy
has 12 planned cases; accepted judgments can still contain N/A dimensions.

| Strategy | Valid judgments / planned | Correctness mean (n) | Completeness mean (n) | Citation support mean (n) |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 11 / 12 | 2.9000 (10) | 2.8000 (10) | 3.0000 (10) |
| Dense | 12 / 12 | 3.0000 (8) | 2.4000 (10) | 2.8750 (8) |
| Hybrid | 11 / 12 | 2.7778 (9) | 2.8889 (9) | 2.6667 (9) |
| Structure | 12 / 12 | 2.9000 (10) | 2.9000 (10) | 2.9000 (10) |
| Symbol | 12 / 12 | 2.9000 (10) | 2.8000 (10) | 2.8000 (10) |

Overall correctness has 47 numeric scores and 11 N/A dimensions; completeness has
49 numeric scores and nine N/A dimensions; citation support has 47 numeric scores
and 11 N/A dimensions. Every dimension also retains one invalid and one unknown
case. There are no accepted `unsure` dimensions. Overall conditional means are
2.8936, 2.7551 and 2.8511 respectively.

On the nine shared numerically scored cases, Structure minus Hybrid has mean
deltas of +0.2222 correctness, +0.1111 completeness and +0.2222 citation support.
Against BM25 on ten shared cases, the respective deltas are 0, +0.1 and −0.1.
These descriptive comparisons show **no consistent advantage across baselines**.
The [generated report](report.md) and [summary](summary.json) preserve all pairs,
coverage categories and shared case IDs.

The judge marks nine abstentions appropriate and two unnecessary; one other
abstention has the invalid judgment. All 58 accepted judgments mark the supplied
references usable, with three also recording reference issues. These are model
opinions, not validation of the provisional labels. Automatic citation ID, path
and line checks establish source identity and location; semantic support is a
separate model-assessed dimension.

## Interpretation and limits

Protocol acceptance changed from 24/60 in v1 to 58/60 in cumulative v2. Of the
original 36 invalid judgments, all 36 now pass v2; among the 24 originally accepted
ones, 22 pass v2, one is invalid and one has an unknown outcome. This is a
descriptive change in protocol coverage on exposed cases, **not improved true
accuracy, a controlled causal comparison or a reason to mix v1 and v2 scores**.

The QA cohort contains only 12 provisional development questions across Click
and Requests, evaluated with five retrieval strategies. The rubric was revised
after inspecting these cases; generation and judging share a model family;
scores cluster near the ceiling; N/A and missing outcomes change denominators.
There is no human calibration or untouched QA test set. The results support
debugging and a reproducible example of model-assisted assessment, not a general
ranking of answer quality.

The broader retrieval result also remains unchanged: the frozen full Structure
heuristic lowers aggregate NDCG@10 relative to Hybrid on the expanded test split.
See the [retrieval overview](../overview/report.md) and
[M6c experiments](../m6c/README.md). Small conditional QA score differences do not
reverse that retrieval finding. Transparent negative and incomplete observations
are part of the delivered project.

## Reproduce and inspect

[run.zip](run.zip) contains 90 members: the complete new run, parent and original
source provenance, frozen requests, raw responses, exact executing implementation
and upstream licenses. Its SHA256 is
`329f9dfcdc3e70ac923fc02c8b0121b3de1d03d4746c10363025b0a0e8c33385`.
[manifest.json](manifest.json) records every member's size and hash.
[case-results.json](case-results.json) is a compact 60-case index;
[approval.json](approval.json) and [plan.json](plan.json) retain execution scope.

Run from the repository root with an unused extraction directory:

```powershell
uv sync --locked --dev
uv run --locked python -m zipfile -e reports/m7e-live/run.zip artifacts/qa/m7e-live-replay-001
uv run --locked python scripts/verify_qa_judge_revision.py --followup --run artifacts/qa/m7e-live-replay-001/run
```

Verification is offline and does not require an API key. A successful verifier
can report `complete_with_failures`: it verifies the recorded experiment,
including its invalid judgment, without claiming every response was usable.
See [the reproduction guide](../../docs/reproduction.md) for other checkpoints.

## Software and archive validation

This checkpoint changes documentation and evidence, with no application-source
change. Targeted follow-up execution/reporting tests passed: **48 passed**. The
new archive was extracted and independently verified; all 90 member hashes match.
All 60 original generations and all 13 prior records are unchanged. The original
M7b/M7d run archives and M7e prepared archive also retain their published hashes.
Ruff lint/format, the unchanged 45-run retrieval overview and offline distribution
builds are recorded in [validation.json](validation.json).

The previous M7e tooling checkpoint recorded 862 tests passed, one Windows symlink
skip and 91.77% combined statement/branch coverage. That full suite and local
container checks were not rerun for this documentation/evidence checkpoint. The
owner reported `daf6aa4` passed remote CI; this checkpoint's remote CI follows the
owner's commit and push.

The agreed engineering and experiment-attempt scope is delivered. Preserving an
invalid score, a historical unknown and provisional labels is required reporting,
not an obligation to keep running paid experiments or arrange human review.
Future benchmark expansion, judge calibration or protocol revisions are optional
new work and must preserve this archive.
