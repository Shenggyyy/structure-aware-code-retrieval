# M9c — Same-model answer comparison

This checkpoint implements **saved five-strategy preview → offline cost plan →
explicit approval → answer comparison → citation inspection → saved history**.
It reuses the existing QA adapter, prompt/source audit, response validation,
conservative input estimator and usage accounting. New code coordinates these
operations for arbitrary repository questions without inventing benchmark labels.

Implementation and offline validation are delivered. **New real model calls are
zero.** The separately approved live acceptance run remains pending within M9c;
synthetic browser responses are not real answer-quality or billing evidence.

## Implementation and boundaries

- A frozen plan binds the original preview, source snapshot, five prompts, common
  settings, exact Responses payloads, model snapshot and dated prices. Planning
  needs no API key. The initial preset is `gpt-5.4-mini-2026-03-17`, reasoning
  `none`, at most 1,024 output tokens per request and no semantic judge.
- CLI and HTTP execution require an explicit confirmation, the exact planned
  model and a positive budget covering the estimate. Server credentials come only
  from `OPENAI_API_KEY`; there is no key field in the browser. Opening history,
  previews or plans never generates an answer.
- Each plan has a permanent atomic execution claim. Each request attempt is
  persisted before calling the existing no-retry provider. Completed answers are
  saved before the next request. Unknown outcomes stop the remaining calls;
  restart recovery does not resume execution. Invalid answers with known responses
  can retain their error and allow independent strategies to continue.
- A new self-contained child run retains retrieval evidence/provenance, source
  checks, answers, raw responses, response identifiers, timings and available
  usage. The original preview stays unchanged. Missing usage makes full cost
  unknown; reported token subtotals are not substituted for missing totals.
- Browser text rendering handles model output as data. Validated answer claims
  link to the saved source lines and retrieval relation provenance. Preview,
  model-generation and injected-test modes have separate labels. New unlabeled
  questions have no Recall, NDCG, correctness score or invented semantic assessment.

## Observed browser checks

An isolated local harness disabled `OpenAIModel.complete` and injected a synthetic
provider. It copied an existing Requests preview, retaining the real five retrieval
contexts and source commit `0e322af87745eff34caffe4df68456ebc20d9068`.
No new repository import or embedding-model download was needed.

| Check | Observed outcome |
| --- | --- |
| Plan and consent | Exact model, five request estimates and zero judging requests displayed; execution button disabled before consent and with an insufficient budget |
| Five answers | Five identical synthetic responses preserved as returned, with explicit offline-test labels and zero real API calls |
| Answer citation | Structure-aware answer S1 opened `src/requests/models.py:295–310`; saved call relation at line 297 and score components remained available |
| Untrusted output | Literal `<img ...>` markup displayed as text, with no injected image nodes or JavaScript dialog |
| Missing usage and interrupted response | First answer retained with unknown token/cost fields; second outcome unknown; remaining three strategies not run; no fabricated answers or zero-filled costs |
| History and restart | Saved success and interrupted runs reopened with their original IDs and historical/synthetic labels, without repeating generation |
| Actual workbench | Existing public Requests preview reopened; an unconsumed real-generation plan was created through the browser, with consent unchecked and execution disabled |

The final successful synthetic run is `c0816efa3509430680a2ce25744b0076`;
the synthetic unknown-outcome run is `d3756dbc547341aa86a1139134eab36d`.
They live in ignored local artifacts, not published benchmark results.

## Automated validation

The full suite passed **1,174 tests**, with **two Windows symlink-privilege skips**,
in about **9 minutes 28 seconds**. The **81 new tests** comprise 30 generation-core,
32 HTTP-generation and 19 CLI cases. Overall branch-aware coverage is approximately
91%; Ruff, JavaScript syntax, the 45-run retrieval overview and package checks passed.

New offline coverage includes frozen-plan integrity, source/configuration binding,
budget/model/key gates, concurrent claims, missing usage, invalid responses,
interrupted and active execution recovery, HTTP consent/security, server shutdown
and CLI commands. See [validation.json](validation.json) for final recorded counts.
Existing benchmark artifacts and their provisional/negative/unknown outcomes were
not modified.

```powershell
uv run --locked --offline ruff check .
uv run --locked --offline ruff format --check .
node --check src/structure_aware_retrieval/workbench/static/app.js
uv run --locked --offline pytest --cov --cov-report=term-missing
uv run --locked --offline python scripts/summarize_results.py --output reports/overview --check
uv build --offline
```

The wheel includes the generation module and all three browser assets. No new
runtime dependency or frontend build was added. Existing Windows/Linux CI collects
the new tests; existing container checks verify installed assets. Docker images
were not rebuilt locally, and remote CI awaits the owner's commit and push.

## Pending live acceptance proposal

The saved Requests question is **How are request URLs prepared?** Its original
preview ID is `cc4c1c7c20ad48558b06af28d89ece64`. The unconsumed plan ID is
`e74fbce9735446779c6917e42059da57`, stored locally under
`artifacts/wb-m9b/generation-plans/`.

| Item | Proposed scope |
| --- | --- |
| Answer model | `gpt-5.4-mini-2026-03-17` |
| Generation / judging requests | At most 5 / 0 |
| Common output limit / reasoning | 1,024 tokens / `none` |
| Input / output rates per million tokens | US$0.75 / US$4.50, checked 2026-09-09 |
| Combined conservative estimate | Approximately US$0.085 |
| Proposed budget | US$0.10; not an invoice or provider-enforced spending cap |

Prices and snapshot support were verified against the
[official model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
The estimate counts UTF-8 message/schema/settings bytes plus a framing allowance
as a conservative input proxy, with full output limits at uncached rates. It is
not an exact tokenizer count. No LLM judging is planned. A new approval is required
before any live execution; historical experiment budgets do not apply.

After approval, the remaining acceptance checks are actual provider outcomes,
browser citation inspection, recorded usage/latency and reopening the saved run.
Model or network failures must remain visible, rather than being retried to obtain
better-looking results. See the [startup and CLI guide](../../docs/workbench.md).
