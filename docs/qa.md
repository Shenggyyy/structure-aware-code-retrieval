# Repository QA

M7a implements question answering over a stored Python snapshot. The owner selected
OpenAI API. The first engineering checkpoint is offline: no generated answer, accuracy
score, or independent human review is implied by passing tests or preparing requests.

## Context and answers

`sacr ask QUESTION --index INDEX --output NEW_DIRECTORY` previews context without a
model. Select `bm25`, `dense`, `hybrid`, `symbol`, or `structure` with the same model,
vector and graph options as `search`. BM25 requires no optional dependencies.

The context packer consumes ranked chunks, uses canonical indexed code and verifies
snapshot/chunk/symbol identities. It keeps the first chunk per symbol, skips overlap,
and takes the longest complete-line prefix that fits. Lower-ranked smaller chunks
may fill the remaining space. Defaults: ten symbols, 16,000 UTF-8 bytes, including
JSON evidence metadata. This is a byte budget, not a tokenizer measurement. Question,
system prompt and API framing add input overhead; long-symbol tails can be omitted.

Generated JSON contains `status` and `claims`; each claim contains `text` and source
IDs such as `S1`. Abstention is `insufficient_context` with empty claims. The validator
rejects malformed/duplicate fields, unknown or duplicate citations, invalid Unicode,
and claims without sources. References render beside canonical paths, line ranges and
source excerpts. A valid ID only establishes source identity, never semantic support.
Source comments and docstrings are treated as untrusted data. Prompt instructions
reduce injection risk but cannot guarantee that a model follows them.

## OpenAI setup and single-question generation

Provide `OPENAI_API_KEY` through your local environment/secret manager. Never commit
it, paste it in an issue, or put it in experiment configs. `.env` is ignored by Git
but is not automatically loaded. To set a session value in PowerShell without echoing
it or writing it into shell history, run interactively:

```powershell
$qaSecret = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $qaSecret).Password
Remove-Variable qaSecret
```

New environment settings are visible only to processes that inherit them; an already
running desktop session may need restarting. With your own index and a new output:

```text
uv run --locked sacr ask "How is calculate_checksum implemented?" --index artifacts/sample.sqlite --output artifacts/qa/sample-answer --model gpt-5.4-mini-2026-03-17 --execute
```

`--execute` sends the question and selected source to `https://api.openai.com/v1/responses`
and may incur charges. The adapter uses strict structured output, `store=false`,
no tools, no retries and a 60-second request timeout. It records reported model,
request ID, usage and completion status. `store=false` is an API setting, not a
claim about all provider retention. Empty evidence bypasses the API. Refused,
incomplete and malformed provider responses are recorded as errors, with unknown
usage where unavailable. Failed attempts may still have been billed.

## Frozen development experiment

`configs/qa-m7.toml` proposes `gpt-5.4-mini-2026-03-17`, 1,024 maximum output tokens,
the same context/prompt policy for all five strategies, and twelve provisional cases:
ten source-backed questions from Requests/Click plus two private-deployment scope
controls. No expanded/test/public question is used to tune QA behavior.

Prepare the development source indexes, embedding cache, vectors and graphs using
the [QA preparation prerequisites](reproduction.md#prepare-the-qa-experiment-offline).
Then prepare offline:

```text
uv run --locked --extra dense sacr prepare-qa --config configs/qa-m7.toml --output artifacts/qa/m7-prepared
```

The new bundle includes `plan.json`, exact `requests.jsonl`, source `previews/`, and
separate `cases.json` reviewer references. Preparation validates the development
benchmark digest, unchanged questions, all positive source targets, compatible
snapshots, model/vector/graph hashes and actual retrieval strategies. Reference
points, expected statuses and gold targets never enter the model messages.

The content fingerprint depends on prompts and case/strategy IDs; timing does not
affect it. Integrity fingerprints also bind saved runtime metadata and measured
timings, so the full plan need not match across machines/runs. OpenAI generation is
not bitwise deterministic even with a pinned model and identical prompts.

Inspect the bundle before approving a paid run. Once a model and budget are approved:

```text
uv run --locked sacr run-qa --bundle artifacts/qa/m7-prepared --output artifacts/qa/m7-run --budget-usd 2 --execute
```

The runner recomputes the frozen cost projection before calling the provider. Pricing
uses standard uncached rates from the config; input estimation counts one token per
UTF-8 content/schema byte plus a framing allowance, and output uses the configured
maximum. **The budget check is an estimate gate, not a billing hard cap.** Missing
provider usage stays unknown. Failed/uncertain attempts are never automatically retried.
Execution reserves its output first and journals attempts/results; an existing directory
cannot be resumed or overwritten. Inspect partial records before explicitly starting
any new run, since a new directory can repeat billable calls.

## Answer evaluation and review

Execution reports status counts, citation identity checks, abstention on the two
scope controls, provider token counts and single-run timing. Automatic empty-context
abstention is distinguishable from model abstention. Timings separate stored retrieval/
packing from generation; they exclude loading and bundle-validation startup and are
not repeated latency benchmarks. Scope-control agreement is not answer correctness.

Human reviewers use the source evidence and provisional reference points. Assess
factual correctness and semantic citation support separately; omissions caused by
context selection differ from unsupported model statements. Valid source IDs, an
answered status or agreement with a draft answerability label do not grant correctness.
The generated review template stays pending. Copy it to a judgments file, complete
the rubric, then validate it without modifying the original run:

- Set each reviewed row's `status` to `submitted`, with a nonblank `reviewer` and `notes`.
- For answered cases, use `correctness`: `pass` (required facts correct), `partial`
  (some required facts missing), or `fail` (materially incorrect). Use `citation_support`:
  `supported` only when every claim is supported by its cited excerpts, otherwise `unsupported`.
- For abstentions, correctness is `pass` or `fail` based on available evidence;
  citation support is `not_applicable`. Failed generation uses `not_applicable` for both.
- Keep untouched rows `pending` with null judgments. Do not change binding fingerprints.

```powershell
Copy-Item artifacts/qa/m7-run/review-template.json artifacts/qa/m7-judgments.json
```

```text
uv run --locked sacr check-qa-review --run artifacts/qa/m7-run --judgments artifacts/qa/m7-judgments.json --output artifacts/qa/m7-reviewed
```

The checker binds judgments to archived answers/context, preserves submitted notes,
and keeps semantic metrics unknown until all recorded outcomes are reviewed. Reports
separate overall and per-strategy quality; not-run and unknown outcomes remain visible
even when reviews of available answers are complete. Reviewer identity and
independence are self-attested, not authenticated. A reviewed QA report does not
automatically promote the underlying provisional retrieval labels.

## Sources

- [OpenAI Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create)
- [GPT-5.4 mini model and pricing](https://developers.openai.com/api/docs/models/gpt-5.4-mini)

Model snapshot and listed rates were checked on 2026-09-08; confirm rates before a
later paid run. No new SDK/service dependency is required by the adapter.
