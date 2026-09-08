# M7d: Bounded Judge-Only Execution

Recorded on 2026-09-08. This milestone implements execution and independent offline
verification of the frozen v2 judge requests. **No live API calls or new model
assessments were made.** M7b's 24 accepted / 36 invalid judgments and M7c's offline
diagnostics remain unchanged. Software tests are not evidence of v2 judge reliability.

## Delivered behavior

- `scripts/run_qa_judge_revision.py` requires an explicit execution flag, the exact
  plan fingerprint, matching judge model and a finite positive budget covering the
  complete estimate. The output directory must be new.
- It copies and rechecks the prepared bundle before making calls. Each request uses
  its saved answer, original context/references and exact dynamic schema. Original
  generations remain verbatim; historical judge scores are excluded from new results.
- The request journal is flushed before each call. Results, raw responses and provider
  usage are retained. Invalid judgments remain unscored and do not trigger retries.
  Provider errors stop the run; interruption preserves an unknown attempt where needed.
- Reports retain all source-case denominators, automatic identity checks, abstentions,
  score coverage and comparisons on shared scored cases. New token usage, cost and
  latency cover judging only. Historical generation costs and timing are excluded.
- `scripts/verify_qa_judge_revision.py` independently checks the frozen source,
  approval, exact ordered requests, result journals, raw response envelopes, v2
  validation and recomputed summaries/reports without accessing the provider.

The existing combined generation/judge runner remains v1. M7c's prepared README is
a historical offline artifact and is preserved byte-for-byte; this milestone adds
its separate executor. Prepared proposals always retain `execution_authorized=false`;
an authorized invocation creates a separate `approval.json` in the new run.

## Failure and measurement boundaries

No automatic retries, resume or overwrite are implemented. A failed request may be
billed. Missing usage or an attempt without a result keeps total cost unknown while
retaining known subtotals. A disk failure can leave an archive that fails consistency
checks; do not silently repair it or repeat calls under the old approval.

Returned model IDs and any provider revision metadata are retained separately from
the requested snapshot. Hashes establish internal consistency, not independent
provider authenticity. Model grades are ordinal assessments, not human review or
true accuracy. Labels remain provisional and human calibration is optional.

## Concrete proposal for a later real run

[proposal.json](proposal.json) binds the candidate to the checked M7c request plan:

| Item | Proposal |
| --- | --- |
| Judge model | `gpt-5.4-mini-2026-03-17` |
| New generation calls | 0; reuse all 60 archived answers |
| Maximum judge calls | 60; 12 questions × five retrieval strategies |
| Protocol | Frozen rubric v2, per-answer schema, reasoning `none` |
| Maximum output | 2,048 tokens per request |
| Combined additional generation + judging estimate | **US$2.13340275** |
| Suggested approval budget | **US$2.20**, not a billing hard cap |
| Approval status | **Not approved; no calls made** |

The estimate counts exact saved-answer request bytes, schema/settings and framing
as conservative input tokens, plus maximum output. Historical generation costs are
excluded. The US$0.75 input / US$4.50 output rates per million tokens were rechecked
on 2026-09-08 against the official
[GPT-5.4 Mini page](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
The earlier US$5.63 authorization applied only to the completed M7b run.

Rejudge every strategy under the same version if this proposal is approved. Do not
combine newly accepted v2 grades with retained v1 grades to fill gaps. Actual v2
schema acceptance, completion, score coverage and model quality remain unmeasured.

## Reproduction and validation

The [workflow](../../docs/qa.md#judge-only-v2-execution) documents execution parameters
with placeholders for a separately approved run. The plan and saved results can be
checked without credentials:

```text
uv run --locked python scripts/prepare_qa_judge_revision.py check --bundle artifacts/qa/m7c-v2-prepared-001
uv run --locked python scripts/verify_qa_judge_revision.py --run PATH_TO_SAVED_JUDGE_RUN
```

Local software checks are recorded in [validation.json](validation.json). Unit and
integration tests cover approval rejection, immutable source copying, changing inputs,
exact schemas, durable journals, failure stopping, unknown usage, omitted sources,
altered archives and isolated Python CLI imports. Test factories cannot return live
OpenAI adapters and provider/credential access is blocked in tests.

The full CI-style test command passed **784 tests with one Windows symlink-privilege
skip**, including 60 new regression cases. A separate local transport check walked
all 60 actual archived inputs with synthetic schema-derived responses and passed the
independent verifier. Those responses are explicitly `injected_models` fixtures;
their scores and usage are not model evaluation or billing observations.

The owner reports M7c passed GitHub CI. M7d's remote CI awaits their commit and push.
This checkpoint does not rerun local Linux/container checks; the existing CI matrix
continues to provide those jobs.
