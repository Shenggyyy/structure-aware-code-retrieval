# Repository QA

The active evaluation route combines deterministic checks with LLM-assisted scoring.
Human review is optional and is not a completion prerequisite. Existing retrieval
labels and QA reference points remain **provisional**; neither valid citations nor
model scores establish human-reviewed correctness or a calibrated accuracy rate.

**M7a provides offline QA checks and the judge specification. M7b implements the
combined generation/judging workflow and records a real Mini/Mini experiment.**
The owner approved the two fixed Mini models and a US$5.63 combined budget.
See [the live evidence and failures](../reports/m7b-live/README.md),
[the scoring specification](llm-evaluation.md) and [current acceptance](status.md).
Any additional live run requires approval of its scope and combined cost.
M7c freezes a v2 judge protocol; M7d implements execution over saved answers and
offline run verification. Their implementation checkpoints made no new API calls.
The subsequent [approved v2 run](../reports/m7d-live/README.md) is partial: 12 valid
judgments, one unknown attempted outcome and 47 requests not started after a local
execution interruption. Its cause was not preserved. The planned comparison remains
incomplete; known output validity is not an answer-accuracy measurement.

## Preview a question

```text
uv run --locked sacr ask "How is calculate_checksum implemented?" --index artifacts/sample.sqlite --output artifacts/qa/sample-preview
```

This writes `qa.json` and `answer.md` without calling a model. Select `bm25`, `dense`,
`hybrid`, `symbol` or `structure` using the same index/vector/graph options as search.
BM25 needs no optional model dependencies. Use a new output directory for every run.

The context packer uses canonical indexed chunks and verifies snapshot, chunk and
symbol identities. It keeps one chunk per symbol, skips overlap, and takes complete
physical source lines under a default **16,000 UTF-8 byte** budget with ten symbols.
That budget includes evidence metadata, but excludes question, system prompt and API
framing; it is not a model-token count. Truncated tails remain explicitly identified.

## Automatic checks and separate assessment fields

Citation IDs resolve to canonical snapshot code; the answer schema does not allow
the model to invent citation paths or ranges. Paths are normalized repository-relative
POSIX paths. Absolute/drive/traversal paths, duplicate IDs, invalid integer ranges,
overlap, mismatched text hashes and inconsistent physical line counts are rejected.
The same packed-evidence validator is used before single-answer completion and when
checking frozen execution bundles. Source existence and chunk ownership are established
against the stored index during context packing, without executing the repository.

Generated answers contain exactly `status` and `claims`, with source IDs on every
claim. Malformed/duplicate fields, unknown or duplicate citations and invalid Unicode
are rejected. `insufficient_context` requires empty claims. Empty evidence abstains
locally without an API request; no citations means citation validity is not applicable.

New `qa.json` records distinguish:

| Field | Meaning |
| --- | --- |
| `automatic_checks` | Packed evidence ID/path/range checks and answer citation-ID validity; no semantic scoring |
| `llm_assessment` | A `not_run` snapshot with null scores/model/rubric in single-generation output; not rewritten by the separate combined runner |
| `evaluation` | Legacy fields used by optional manual-review tooling; pending/null values do not block completion |

Combined `records.json` joins these generation artifacts with a separate `judging`
outcome per planned case/strategy. Read `row.judging` and the combined summary for
actual LLM judgments; a nested `generation.llm_assessment.status = not_run` is not
the status of the later judging stage.

Paths and lines refer to the stored snapshot, not necessarily a changed live checkout.
Fingerprints detect inconsistent records, not maliciously reauthored evidence. Valid
IDs do not prove that a cited excerpt supports a claim. Source prose and questions
are data, not instructions; prompts do not guarantee immunity to instruction injection.

## Freeze the offline development experiment

Prepare [development indexes, model, vectors and graphs](reproduction.md#prepare-the-qa-experiment-offline),
then run:

```text
uv run --locked --extra dense sacr prepare-qa --config configs/qa-m7.toml --output artifacts/qa/m7-prepared
```

The config contains a historical generation-model proposal, 1,024 maximum output
tokens and twelve provisional development cases across five strategies: ten
Requests/Click questions and two deployment-scope controls. It is not approval of a
model or budget. QA tuning does not use the expanded or public test questions.

The bundle contains `plan.json`, exact `requests.jsonl`, source `previews/` and separate
`cases.json` references. It validates source targets, snapshot/model/vector/graph
bindings, questions and retrieval strategies. Reference points, expected status and
gold targets are excluded from the **answering** model's messages. M7b supplies
separately marked, source-backed references to the judge under the fixed specification.

The content fingerprint binds messages and case/strategy IDs; timings do not affect
it. Full plan fingerprints also bind runtime metadata and timings and can differ
between preparations. Fixed models/prompts do not guarantee bitwise identical outputs.

## Prepare and check the combined experiment

Use the existing generation bundle and the same Requests/Click indexes:

```text
uv run --locked sacr prepare-qa-assessment --bundle artifacts/qa/m7-prepared --config configs/qa-assessment-m7-mini.toml --output artifacts/qa/m7b-prepared
uv run --locked sacr check-qa-assessment --bundle artifacts/qa/m7b-prepared
```

Both commands are offline and read no API key. Preparation copies the generation
inputs and rubric, resolves reference source and freezes the settings, estimate and
plan fingerprint. Checking the completed bundle needs no indexes or model weights
and changes no files. Use a new preparation path; prior artifacts are preserved.

Reference source includes all canonical chunks within each exact target, including
chunks owned by nested definitions. Every provisional reference point links to the
case's candidate source set. This is not verified sentence-to-source alignment.
The references are identical across strategies and never enter generation messages.
Inspect `references.json` alongside the generated plan before approving the run.

The recorded run uses [qa-assessment-m7-mini.toml](../configs/qa-assessment-m7-mini.toml):

| Stage | Recorded model | Max output tokens | Reasoning effort | Input / output USD per million tokens |
| --- | --- | ---: | --- | --- |
| Generation | `gpt-5.4-mini-2026-03-17` | 1,024 | `none` | 0.75 / 4.50 |
| Judging | `gpt-5.4-mini-2026-03-17` | 2,048 | `none` | 0.75 / 4.50 |

Standard uncached rates are frozen as of 2026-09-08 from the official
[GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini) page.
The exact combined estimate was US$5.6289795. The earlier GPT-5.4 judge proposal is
preserved in [the offline checkpoint](../reports/m7b/README.md); it was superseded
before any calls. The saved approval covers one run, not future invocations.
Verify prices and prepare a new plan when changing inputs or settings.

## Combined budget and execution approval

The original generation `plan.json` records `cost_estimation.scope = answer_generation_only`
and `includes_llm_judging = false`. Input estimation uses UTF-8 message/schema bytes
plus a framing allowance; output estimation uses the configured maximum. This is a
conservative projection at saved uncached rates, **not a billing hard cap**. The old
60-request estimate excludes judging and must not be reused as the combined budget.

The combined estimator counts model-visible message UTF-8 bytes plus serialized
schema/settings and framing. It additionally reserves the full **65,536-byte valid
answer ceiling** as judge input, plus both stages' maximum output tokens. This can
greatly exceed typical usage; it is not a tokenized prediction or billing hard cap.

Before any new paid experiment executes, present its plan containing both proposed model snapshots,
settings, exact prompt/rubric versions, generation/judge call limits, input/output
estimates, separately verified prices and **generation + judging total cost**. Judge
input must include the generated answer and common reference evidence. Wait for the
owner to confirm the models and combined budget before sending any request.

After approval, `run-qa-assessment` requires all of these flags:

| Flag | Required value |
| --- | --- |
| `--bundle` | The checked combined bundle |
| `--output` | A new run directory; no overwrite or resume |
| `--generation-model`, `--judge-model` | Both exact approved IDs from the plan |
| `--approve-plan` | The exact approved `plan_fingerprint` |
| `--budget-usd` | The approved budget covering the combined estimate |
| `--execute` | Explicitly enable requests after approval |

Missing execution consent, model/fingerprint mismatches and inadequate budgets make
no calls. Local empty-context abstentions bypass generation; invalid generation
skips judging. Provider errors stop the run, preserving partial results. Additional
attempts require a separately approved scope; there are no automatic retries.

The existing `ask --execute` and `run-qa --execute` paths perform generation only;
they neither run an LLM judge nor enforce a combined two-stage budget. They remain
available as low-level commands, but do not replace `run-qa-assessment` for M7b.
Offline tests use synthetic provider responses and never substitute them for real results.

## Combined run outputs

| File | Contents |
| --- | --- |
| `approval.json` | Approved models, plan fingerprint, budget and execution mode |
| `prepared/` | Copied generation inputs, common references, rubric and combined plan |
| `attempts.jsonl` | Durable pre-call events with exact credential-free request payloads and hashes |
| `results.jsonl` | Stage-result events, including unsuccessful outputs and available provider metadata |
| `records.json` | Every planned case/strategy with separate `generation` and `judging` results; absent outcomes remain null |
| `summary.json`, `report.md` | Automatic checks, ordinal dimensions, coverage, paired case IDs, abstentions, stage costs and timing |

An attempted request without a result has an unknown outcome, distinct from a
request never started. The latter remains in planned-case denominators. A valid
abstention receives no perfect correctness/support score. Means condition on scored
cases; matched comparisons use shared scored case IDs, with coverage visible.

## Judge-only v2 execution

First [prepare and check a v2 bundle from saved answers](reproduction.md#prepare-judge-protocol-v2-from-saved-answers).
This freezes exact answer-specific messages, schemas and judge settings. The current
M7c proposal contains 60 judge requests and zero new generation calls; its saved
estimate is US$2.13340275 at frozen rates, not a billing hard cap. The owner approved
one scope using `gpt-5.4-mini-2026-03-17` and US$2.20; its [partial execution
record](../reports/m7d-live/README.md) preserves 13 attempts and 12 known results.
That record is not permission to restart or retry requests. Confirm the exact model,
request scope and budget for additional paid attempts.

After approval, replace every uppercase placeholder with its approved value:

```text
uv run --locked python scripts/run_qa_judge_revision.py --bundle CHECKED_BUNDLE --output NEW_RUN_DIRECTORY --judge-model APPROVED_MODEL --approved-plan APPROVED_PLAN_FINGERPRINT --budget-usd APPROVED_BUDGET_USD --execute
```

The model and fingerprint must match the checked bundle; the finite budget must
cover its estimate. `--execute` is mandatory. Missing or mismatched approval makes
no requests. The combined `run-qa-assessment` command remains v1 and cannot execute
this v2 bundle. Configure the key locally only after approval.

The new run copies its checked input under `prepared/` and writes `approval.json`,
`attempts.jsonl`, `results.jsonl`, `records.json`, `summary.json` and `report.md`.
All source case/strategy rows remain present. Their `generation` objects are reused
verbatim; `judging` stores only the new v2 outcome. Invalid source generations skip
judging, and old v1 judgments never fill missing v2 results or enter model messages.
Original generations, references and provisional labels remain unchanged.

Requests use the saved per-answer payloads with no automatic retries. Invalid judge
outputs are archived and later requests continue; provider errors stop the run.
An interrupted attempt may have an unknown result and cost. New output directories
are required: there is no overwrite or resume. Repeating requests requires a new
approved scope. Reports distinguish historical generation measurements from new
judging costs and latency, retaining coverage and unknown usage explicitly.
The execution command returns a nonzero status for protocol or provider failures;
inspect the saved report even when every planned request was attempted.
Unexpected execution exceptions now also attempt to write `interruption.json` with
the exception type, phase, request/count metadata, numeric OS codes and traceback
locations. It omits exception messages, arguments, source lines and local variables.
This best-effort diagnostic cannot recover an unknown model response and does not
retroactively identify the cause of the archived partial run.

Verify a saved judge-only run without credentials or API calls:

```text
uv run --locked python scripts/verify_qa_judge_revision.py --run SAVED_RUN_DIRECTORY
```

The verifier checks bundle and source bindings, approval, request journals, outcomes
and summaries without modifying them. These are consistency checks, not proof of
semantic correctness or provider authenticity. M7d's offline test responses remain
software fixtures. The separate live prefix has 12 valid judgments out of 60 planned
rows, with one unknown outcome and 47 not-run requests. Its US$0.08424075 known cost
subtotal excludes unknown usage and is not a full-run cost or invoice. See the
[archive reproduction commands](reproduction.md#verify-the-partial-live-v2-archive).

## Provider configuration and measurements

The existing adapter uses OpenAI Responses, strict structured output, `store=false`,
no tools, no automatic retries and a 60-second timeout. It records returned model,
request/response IDs, any reported revision, bounded raw response envelopes, text,
status and usage. Incomplete/refused responses retain partial text and known usage
when supplied. Empty evidence bypasses generation. Failed or
uncertain attempts may be billable; missing usage is unknown rather than zero.
`store=false` is an API setting, not a claim about all provider retention.

Provide `OPENAI_API_KEY` locally only when an approved live run is ready. Do not
commit it or paste it into chat/configs. `.env` is ignored but not automatically read.
An interactive PowerShell session can set it without recording the value in history:

```powershell
$qaSecret = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $qaSecret).Password
Remove-Variable qaSecret
```

An existing desktop session must inherit the environment setting. Execution reserves
new output paths and journals attempted/completed requests; it never silently resumes
or overwrites an old run. New runs can repeat paid calls and need explicit scope.

Keep offline retrieval/packing, generation and judging latency separate, then report
end-to-end measurement boundaries. Preserve generation and judge token usage and cost
estimates separately and together. Unknown billed usage prevents a complete total;
known subtotals require coverage counts. Scope-control agreement and answer status
counts are automatic observations, not factual answer correctness.

## Optional human review

Existing `review-template.json` and `check-qa-review` remain available for optional
calibration or spot checks. They accept human decisions bound to archived answer and
context fingerprints. Never pass LLM judgments off as those human submissions.

For a completed generation run, copy its template, fill actual human judgments and
validate to a new output:

```text
uv run --locked sacr check-qa-review --run artifacts/qa/m7-run --judgments artifacts/qa/m7-judgments.json --output artifacts/qa/m7-reviewed
```

Submitted rows need a reviewer and notes. Correctness is `pass`, `partial` or `fail`;
citation support is `supported` or `unsupported` for answered cases. Abstentions and
failures use the template's documented not-applicable rules; untouched rows stay
pending. This legacy checker withholds its manual semantic aggregates until those
submissions are complete, but that does not gate automated/model evaluation or
project completion. Reviewer identity and independence are self-attested.

For M7b, report **LLM-assisted correctness, completeness and citation-support scores**
with per-dimension coverage, uncertainty and failures. The [fixed rubric](llm-evaluation.md)
defines these outputs; human calibration remains an optional extension.
