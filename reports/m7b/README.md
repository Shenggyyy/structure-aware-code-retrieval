# M7b: QA Generation and LLM-Assisted Evaluation Runtime

This historical offline checkpoint is followed by the owner-approved, lower-cost
[Mini/Mini live experiment](../m7b-live/README.md). Its original proposal below was
superseded before execution; the live record preserves the actual approval and outcomes.

Recorded on 2026-09-08. The two-stage execution path is implemented and validated
offline. **No live generation or judging calls were made. Model and combined-budget
approval are pending; no real answers, model scores or API spend are reported.**

## Implemented behavior

- Freeze both models, request settings, rubric, common source references, input
  hashes, request order and combined cost before execution.
- Require the exact plan fingerprint, both model IDs and sufficient combined budget.
  Validate the copied bundle before calling either provider. Each stage receives
  at most one attempt; provider failures stop the run without automatic retries.
- Keep automatic citation ID/path/line validation separate from 0–3 model assessments
  of correctness, completeness and semantic citation support. Preserve uncertainty,
  abstentions, invalid responses and missing results in the reported denominators.
- Archive credential-free request payloads, raw responses, model metadata, usage,
  latency and durable attempt/result records. Unknown billed usage remains unknown.
- Compare strategies on shared scored cases and report paired coverage alongside
  scores. These are model judgments, not human review or verified true accuracy.

## Proposed live experiment

The existing 12 provisional Requests/Click development cases across five strategies
produce 60 answer requests and up to 60 judgments. Each case uses the same pinned
source references across strategies; retriever labels/ranks are omitted from judge
messages. The fixed rubric remains `repository-qa-judge-rubric-v1`.

| Stage | Proposed model | Maximum calls | Output tokens/call | Estimated USD |
| --- | --- | ---: | ---: | ---: |
| Generation | `gpt-5.4-mini-2026-03-17` | 60 | 1,024 | $0.922528 |
| Judging | `gpt-5.4-2026-03-05` | 60 | 2,048 | $15.687423 |
| Combined | Both stages | 120 | — | **$16.609950** |

Both stages explicitly set reasoning effort to `none`. Prices frozen on 2026-09-08
are $0.75/$4.50 per million input/output tokens for
[GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini), and
$2.50/$15.00 for [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4).
The prepared judge input estimates remain below the documented 272K premium threshold.

The conservative estimator counts one token per message/schema/settings UTF-8 byte,
adds 4,096 framing tokens per call, and reserves another 65,536 bytes for each
generated answer sent to the judge. It includes maximum output tokens and assumes
no cached-input discount. **The proposed owner budget is US$20, not a billing hard
cap or authorization.** Actual token counts and costs must be recorded after approval.

Prepared plan fingerprint:

```text
18bdcaf157d5e9d511aae165250e65fe6a9200879a2f2ff252294b55d5145457
```

The generation content fingerprint remains
`e39035f3d7bb4837cb26c9a4decdb1038c7b03e97535464e89391edad35689ce`.
See [cost-proposal.json](cost-proposal.json) for settings, estimates and provenance.

## Offline reproduction and validation

After preparing the source indexes and M7a generation bundle as described in the
[QA protocol](../../docs/qa.md), use a fresh output directory:

```text
uv run --locked sacr prepare-qa-assessment --bundle artifacts/qa/m7-prepared --config configs/qa-assessment-m7.toml --output artifacts/qa/m7b-prepared-001
uv run --locked sacr check-qa-assessment --bundle artifacts/qa/m7b-prepared-001
```

The recorded local run used the equivalent M7a bundle at
`artifacts/qa/m7-offline-route-v2`. These commands make no API calls.
Runtime fingerprints can differ across machines;
inspect and approve the exact locally prepared plan. Full messages and source
references stay under ignored `artifacts/`; committed summaries cannot replace an
executable bundle. The CLI's separate execution command requires explicit approval
flags and `--execute`; see the [execution protocol](../../docs/qa.md).

Local Windows/Python 3.12 validation: **660 tests passed, one symlink-privilege test
skipped, 91.24% combined statement/branch coverage**. Tests use offline doubles and
cover reference binding, strict judgment parsing, budget/model gates, partial runs,
known and unknown usage, and paired reporting. See [validation.json](validation.json)
for lint, packaging and saved-evidence checks. Current remote CI awaits the owner's
commit and push; prior CI success does not establish this checkpoint's result.

## Limits and remaining acceptance

Reference points and relevance labels remain provisional. Each draft reference point
is linked to the case's candidate source evidence, not a verified sentence-level
alignment. Source inclusion and hash checks establish identity, not semantic truth.
The small development set and related generator/judge models limit generalization;
ordinal scores are uncalibrated. Human review remains an optional extension.

Next: obtain explicit approval for both models and the combined budget, run the
frozen experiment, then analyze observed scores, failures, costs and coverage.
Final research acceptance remains pending that real evidence.
