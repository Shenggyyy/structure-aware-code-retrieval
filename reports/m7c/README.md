# M7c: Offline Judge Protocol v2

Recorded on 2026-09-08. This checkpoint prepares **60 judge-only requests from the
existing M7b answers** and tests the revised protocol offline. **Zero API calls,
new answers or v2 model judgments were produced.** The original live experiment
still has 24 accepted and 36 invalid judgments; its archive and rubric v1 are unchanged.

## Change and rationale

The original schema permitted arbitrary evidence strings. Rubric v2 supplies the
full available `packed:S1` / `reference:R1` identifiers, actual claim indices and
legal scoring states in both a response catalog and a per-answer JSON schema.
Nested `anyOf` branches bind statuses to scores and abstention decisions to context
sufficiency. Score anchors and semantic grading policies remain unchanged.

The implementation uses constraints described in OpenAI's
[Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs).
Provider acceptance and future model compliance have **not** been tested by a live
v2 request. Host checks remain necessary for duplicate IDs, selected-claim citation
binding, reference/completeness consistency and source/prompt identity.

## Offline observations

Replay changes only `rubric_id` in an in-memory copy of each exposed v1 output.
It does not correct identifiers, rewrite scores or treat diagnostic copies as model
judgments. The same 60 original outputs give:

| Original v1 outcome | Cases | v2 schema accepts | Full v2 validator accepts |
| --- | ---: | ---: | ---: |
| Accepted | 24 | 24 | 24 |
| Invalid evidence identifiers | 34 | 0 | 0 |
| Invalid out-of-scope completeness state | 2 | 2 | 0 |
| Total | 60 | 26 | 24 |

The two remaining cross-field failures are `qa-click-scope-01 / bm25` and
`qa-requests-scope-01 / dense`: their usable references and scope abstentions require
N/A completeness, while the outputs report `unsure`. V2 explains this rule explicitly
and retains the host check. Do not claim that all 36 failures are schema-constrained.

These are regression diagnostics on observed development failures, **not a v2
acceptance rate or accuracy measurement**. Future model outputs could fail differently.
Labels and common references remain provisional; human calibration is optional and
has not been measured. The previous small, same-model QA comparison remains limited.

## Prepared scope and cost proposal

The candidate preserves all 12 questions × five retrieval strategies, the 60 exact
answers, their packed evidence and common reference sources. It proposes
`gpt-5.4-mini-2026-03-17`, reasoning `none`, with 2,048 maximum output tokens per judge.
No answers would be regenerated; no v1 judgment is included in the judge's input.

| Estimate component | Amount |
| --- | ---: |
| New generation calls | 0 |
| Maximum judge calls | 60 |
| Input estimate, including dynamic schemas and framing | 2,107,257 tokens |
| Maximum input estimate per request | 50,814 tokens |
| Maximum output tokens across requests | 122,880 |
| Additional generation + judging estimate | **US$2.13340275** |

The conservative estimator counts exact request-content bytes as input tokens,
plus framing and maximum output. It needs no unknown-answer reserve because answers
already exist. Prices are US$0.75 input / US$4.50 output per million tokens, checked
2026-09-08 against the official
[model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
Already incurred generation costs are excluded. This is a proposal, not a billing
cap or authorization. The previous US$5.63 approval covered the completed run only.

## Evidence and reproduction

- [plan.json](plan.json) records source hashes, v2 fingerprints, settings, request
  ordering, cost and creation provenance. `execution_authorized` is false.
- [replay.json](replay.json) preserves per-case syntax/validation diagnostics and
  hashes of the original raw outputs, without publishing new semantic scores.
- [manifest.json](manifest.json) binds these files to the unchanged M7b archive.
- [validation.json](validation.json) records this checkpoint's local software checks.

Extract the [M7b archive](../m7b-live/README.md#evidence-and-offline-reproduction) to
`artifacts/qa/m7b-replay-001`, then run:

```text
uv run --locked python scripts/prepare_qa_judge_revision.py prepare --run artifacts/qa/m7b-replay-001/run --config configs/qa-judge-revision-m7c.toml --output artifacts/qa/m7c-v2-prepared-001
uv run --locked python scripts/prepare_qa_judge_revision.py check --bundle artifacts/qa/m7c-v2-prepared-001
```

Use a new output directory if it already exists. Preparation copies and validates
the archived run before building payloads. The local bundle adds `requests.jsonl`
with exact messages/schemas and unchanged source records. Checking recomputes every
derived output, retaining the original creation provenance even on another host.
Hashes establish internal consistency, not independent provider authenticity.
New preparation may record different host/source-file hashes; compare semantic
rubric identity and diagnostics rather than demanding the same creation fingerprint.

M7c exposes no v2 execution command; the combined generation/judging runner remains
v1. A next milestone can add bounded judge-only execution, then present a final
model/scope/cost plan for explicit approval before any request. Rejudging all five
strategies under the same v2 protocol would be a new experiment, not repair of v1.

## Local validation

The CI-style `uv run --locked pytest` entry point passes **724 tests with one
Windows symlink-privilege skip**, including 44 new offline regression cases.
Combined statement/branch coverage is **91.47%** for the installed package;
standalone scripts are exercised by integration tests but excluded from that
coverage denominator. Ruff lint/format checks, distribution builds, the 45-run
retrieval overview and the complete saved-run/revision checks pass.

The owner reports that the preceding CI import fix passed remote CI. This new
checkpoint's remote CI awaits their commit/push. Linux/container checks were not
rerun locally for M7c; those jobs remain configured in the existing CI matrix.
