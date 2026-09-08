# M7e: Unattempted-Request Follow-up

Recorded on 2026-09-08. This checkpoint implements, freezes and verifies an
**offline proposal for 47 previously unattempted judge requests**. It makes zero
API calls and supplies no new live judgments. The actual v2 evidence remains
12 valid judgments, one unknown attempted outcome and 47 requests not run.
The owner reports the preceding `10e9bc2` checkpoint passed GitHub CI.

## Scope and implementation

The preparer validates and copies the entire prior revision run, including its
source answers and original request bundle. It selects requests absent from the
attempt journal, preserving their payloads and order exactly. All 13 prior attempts
are excluded, including `qa-click-13 / hybrid`, whose outcome remains unknown.
An empty result alone is never treated as proof that a request was not attempted.

The existing executor and verifier accept an explicit `--followup` mode. Execution
uses a new directory and an exact model/plan/budget binding. New journals contain
only the selected requests; all 60 source records remain, with the prior judgments
unchanged. Reports separate prior, new and cumulative usage, latency and ordinal
scores. The verifier checks the parent, inherited records, disjoint request scope,
raw results, journals and recomputed reports without credentials or requests.

This version supports one follow-up from an original interrupted or failed revision.
It rejects running/completed parents, empty remaining scopes, nested follow-ups and
existing output directories. There is no automatic retry or in-place resume. The
original interruption's cause remains unknown; its previously added diagnostic
support is retained for future failures.

## Frozen proposal and cost

| Item | Proposed scope |
| --- | --- |
| Judge | `gpt-5.4-mini-2026-03-17` |
| Rubric, prompts and schemas | Original frozen v2, unchanged |
| New generation calls | 0 |
| Maximum new judge calls | 47 |
| Prior attempts excluded | 13: 12 known, one unknown |
| Input token estimate | 1,665,265 |
| Maximum output tokens | 96,256: 47 × 2,048 |
| Additional generation + judging estimate | **US$1.68210075** |
| Proposed additional budget | **US$1.80** |

The estimate uses serialized request bytes and framing with the maximum output
allowance, following the existing conservative estimator. Reasoning remains `none`.
The uncached rates, US$0.75 input and US$4.50 output per million tokens, were rechecked
on 2026-09-08 against the official
[GPT-5.4 Mini documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
The estimate is not a billing hard cap. It excludes historical generation/judging
costs; the prior v2 known subtotal is US$0.08424075, with its full cost still unknown.

The [plan](plan.json) fixes fingerprint
`b69337459f8b22417d0d5e4cc88063c2f8d9f04d1d3571fe00592132e1313ef3`.
The [proposal](proposal.json) records the cost and budget separately from execution
consent. Preparing or checking these files does not send requests.

Even if all 47 later produce valid judgments, cumulative coverage can reach only
59 of 60, with the preserved unknown outcome. New-batch completion must not be
reported as complete cohort coverage. Cumulative full usage and cost remain unknown
where the historical attempt lacks usage. Model scores are ordinal assessments,
not human review or verified true correctness rates. Labels remain provisional.

## Reproduction and evidence

- [prepared.zip](prepared.zip) contains the frozen proposal, all exact selected
  payloads, prior run evidence and upstream attribution.
- [manifest.json](manifest.json) records archive/member hashes; [archive-check.json](archive-check.json)
  records extraction validation and selected strategy/repository counts.
- [request-manifest.json](request-manifest.json) lists all selected identities and
  exact payload hashes. The excluded identities and outcomes remain in the plan.
- [validation.json](validation.json) records local software checks separately from
  real model evidence.

Extract to a fresh directory and check offline:

```powershell
Get-FileHash reports/m7e/prepared.zip -Algorithm SHA256
Expand-Archive -LiteralPath reports/m7e/prepared.zip -DestinationPath artifacts/qa/m7e-followup-replay-001
uv run --locked python scripts/prepare_qa_judge_followup.py check --bundle artifacts/qa/m7e-followup-replay-001/prepared
```

To rebuild a proposal from the prior archive, use the
[reproduction guide](../../docs/reproduction.md#prepare-an-unstarted-request-follow-up).
Creation-host/code metadata can produce a different fingerprint on a new preparation;
checking the published bundle retains its frozen metadata. Execution parameters and
saved-run verification are documented in the [QA workflow](../../docs/qa.md#follow-up-for-unstarted-v2-requests).

A separate local transport check traversed all 47 actual prepared requests using
synthetic schema-derived outputs, with credential access and the live provider
blocked. It passed independent verification and preserved the historical unknown.
Those synthetic scores and token values are software fixtures, not new live results
or billing observations; they are not published as experiment outcomes.

## Local software validation

The complete CI-style suite passed **862 tests**, with one Windows symlink-privilege
skip. This includes 69 new regression cases for preparation, execution/verification
and reporting. Combined package statement/branch coverage is **91.77%**; standalone
scripts are exercised by integration tests but excluded from that denominator.
Ruff lint and formatting, the unchanged 45-run retrieval overview, old partial-run
verification and all 29 archive-member hashes pass. Linux/container checks were not
rerun locally; current remote CI follows the owner's next commit and push.

Source excerpts retain their Requests Apache-2.0 and Click BSD-3-Clause licenses.
All three upstream attribution files from the [prior archive](../m7d-live/README.md)
are included under `upstream-licenses/` inside this archive.
