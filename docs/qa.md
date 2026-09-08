# Repository QA

The active evaluation route combines deterministic checks with LLM-assisted scoring.
Human review is optional and is not a completion prerequisite. Existing retrieval
labels and QA reference points remain **provisional**; neither valid citations nor
model scores establish human-reviewed correctness or a calibrated accuracy rate.

**M7a is offline:** context preparation, answer contracts, citation checks, generation
cost projection and a frozen judge specification. **M7b remains to implement and
run the generation-plus-judging experiment.** No live answers or model scores have
been produced. See [the scoring specification](llm-evaluation.md) and
[current acceptance](status.md).

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
| `llm_assessment` | `not_run` with null scores/model/rubric in M7a; future M7b model assessment belongs here |
| `evaluation` | Legacy fields used by optional manual-review tooling; pending/null values do not block completion |

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
gold targets are excluded from the **answering** model's messages. M7b will provide
separately marked, source-backed references to the judge under the fixed specification.

The content fingerprint binds messages and case/strategy IDs; timings do not affect
it. Full plan fingerprints also bind runtime metadata and timings and can differ
between preparations. Fixed models/prompts do not guarantee bitwise identical outputs.

## Generation-only estimates and the M7b budget gate

Current `plan.json` explicitly records `cost_estimation.scope = answer_generation_only`
and `includes_llm_judging = false`. Input estimation uses UTF-8 message/schema bytes
plus a framing allowance; output estimation uses the configured maximum. This is a
conservative projection at saved uncached rates, **not a billing hard cap**. The old
60-request estimate excludes judging and must not be reused as the combined budget.

Before M7b executes, present one plan containing both proposed model snapshots,
settings, exact prompt/rubric versions, generation/judge call limits, input/output
estimates, separately verified prices and **generation + judging total cost**. Judge
input must include the generated answer and common reference evidence. Wait for the
owner to confirm the models and combined budget before sending any request.

The existing `ask --execute` and `run-qa --execute` paths perform generation only;
they neither run an LLM judge nor enforce a combined two-stage budget. They remain
available as low-level commands, but are not the completed M7b evaluation workflow.
M7a tests use synthetic provider responses and never substitute them for real results.

## Provider configuration and measurements

The existing adapter uses OpenAI Responses, strict structured output, `store=false`,
no tools, no automatic retries and a 60-second timeout. It records returned model,
request ID, raw output, status and usage. Empty evidence bypasses the API. Failed or
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

Keep retrieval/packing, generation and future judging latency separate, then report
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
