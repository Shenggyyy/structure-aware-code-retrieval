# M9c — Live workbench acceptance

The owner approved one saved Requests question, **How are request URLs prepared?**,
with `gpt-5.4-mini-2026-03-17`, at most **five generations**, **zero judges** and a
**US$0.10 budget**. The browser submitted the frozen plan once. All five strategies
returned answers; no requests were retried and no outcomes are unknown.

This completes the scoped local import-to-answer-comparison workflow together
with [M9a](../m9a/README.md), [M9b](../m9b/README.md) and the earlier
[M9c implementation](../m9c/README.md). One unlabeled question validates the user
workflow; it does not establish answer correctness or a strategy ranking.

## Approved inputs and recorded outcomes

- Source: `https://github.com/psf/requests.git`, commit
  `0e322af87745eff34caffe4df68456ebc20d9068`.
- Original preview: `cc4c1c7c20ad48558b06af28d89ece64`.
- Frozen plan: `e74fbce9735446779c6917e42059da57`; fingerprint
  `aaca5e28861cfa28179cbcdbea8b6574e9a6db72169299d3744f96ff803dd7f4`.
- Saved answer run: `46384c67593d438ea2009bf537f36667`, completed
  `2026-09-09T01:19:55.264309+00:00`.
- Shared settings: top 10 results, the original frozen contexts/prompts,
  reasoning `none`, at most 1,024 output tokens per request. The archive retains
  the full retrieval, context, model and request configuration.
- Combined conservative estimate before approval: **US$0.08499975**. Frozen
  uncached prices: US$0.75 per million input tokens and US$4.50 per million output
  tokens. No judging cost was proposed or incurred by this workflow.

| Strategy | Input tokens | Output tokens | Saved retrieval ms | Generation ms | Usage-based cost estimate (USD) |
| --- | ---: | ---: | ---: | ---: | ---: |
| BM25 | 2,365 | 170 | 2.708 | 3,676.181 | 0.00253875 |
| Dense | 3,876 | 249 | 20.090 | 2,912.524 | 0.00402750 |
| Hybrid | 2,735 | 237 | 15.279 | 2,713.262 | 0.00311775 |
| Symbol-aware | 3,335 | 203 | 35.707 | 2,949.236 | 0.00341475 |
| Structure-aware | 2,735 | 272 | 15.805 | 3,247.541 | 0.00327525 |

Total reported usage is **15,046 input + 1,131 output = 16,177 tokens**; cached
and reasoning tokens are zero. The frozen-rate projection is **US$0.016374**,
not an invoice. All five responses supplied usage. The sequential generation run
took 15,731.709 ms including local overhead. Retrieval times come from the saved
preview, not a new retrieval measurement during generation; these single-run
timings are not a performance benchmark.

## Browser acceptance and offline audit

Observed browser checks covered:

1. Reopen the exact approved plan through `#plan=PLAN_ID`, including after reload;
   consent remains unchecked until explicitly selected. This small frontend fix
   avoids creating a replacement plan when a tab closes.
2. Submit once with the approved model and budget; display five real answers,
   reported usage, timings and costs, with five responses and zero unknowns.
3. Open a representative answer citation from every strategy: BM25/Symbol-aware
   `models.py:313–333`, Dense `models.py:409–481`, and Hybrid/Structure-aware
   `models.py:295–310`, all under `src/requests/`.
4. Filter history by run ID, reopen the saved record, restart the server and reload;
   the same five answers and historical request count remain unchanged.
5. Extract the portable archive into a fresh workspace with no source checkout,
   indexes or model weights. Open its historical answers in the browser and inspect
   Dense S2 at `src/requests/models.py:409–481` from the saved source snapshot.

The [read-only verifier](verify.py) rechecks original preview/plan bindings, exact
prompts, source-location checks, citation IDs, raw provider responses, token totals
and frozen-rate costs. It verifies that the consumed plan is refused before any
provider call. The [audit result](audit-result.json) preserves its output.
These checks establish stored identities and accounting consistency, not semantic
support. No LLM judging or human correctness labels were added; earlier provisional,
negative and unknown experiment records remain unchanged.

## Portable, offline replay

[run.zip](run.zip) contains the byte-preserved preview, frozen plan, permanent
execution claim and answer run, including raw provider responses and saved code.
It also includes unchanged Requests LICENSE and NOTICE files from the same commit.
No API key, complete repository checkout or model weights are included. The
consumed claim prevents executing this plan again.

The [manifest](manifest.json) records archive/member hashes and sizes. Archive
SHA-256: `323c0e5db15e3ff64c46034bf11c297d55c71820bd2ead82f69cbe16b2b75e9c`.
[approval.json](approval.json) records the owner's exact scope.

From the project root, use a new destination directory; do not overwrite an existing
workspace. Install the normal project dependencies first if necessary:

```powershell
uv sync --locked --dev
Expand-Archive -LiteralPath reports/m9c-live/run.zip -DestinationPath artifacts/m9c-live-replay
uv run --locked --offline python reports/m9c-live/verify.py --workspace artifacts/m9c-live-replay
uv run --locked --offline sacr workbench show 46384c67593d438ea2009bf537f36667 --workspace artifacts/m9c-live-replay
uv run --locked --offline sacr workbench serve --workspace artifacts/m9c-live-replay --port 8766
```

Open `http://127.0.0.1:8766/#run=46384c67593d438ea2009bf537f36667` in a browser.
Viewing and verification require no API key, Dense extra, model download or source
checkout. The displayed five API calls describe the historical run; replay makes
zero new model calls. Importing a new repository or generating a new answer is
separate work, with normal resource preparation and new model/budget approval.

## Software validation

This follow-up passed 32 HTTP-generation regression tests and two new archive
tests. The latter verify read-only replay with model calls forbidden and reject
token metadata tampering even after a run fingerprint is recomputed. Ruff,
JavaScript syntax, the unchanged 45-run overview and distribution checks passed;
details are in [validation.json](validation.json).

The earlier implementation's full suite had 1,174 passes and two Windows symlink
skips. That full suite was not repeated for this frontend/report follow-up; the
existing Windows/Linux CI automatically includes the two new offline tests after
the owner's commit and push. No Docker rebuild or new remote CI result is claimed.

```powershell
uv run --locked --offline ruff check .
uv run --locked --offline ruff format --check .
node --check src/structure_aware_retrieval/workbench/static/app.js
uv run --locked --offline pytest tests/workbench/test_server_generation.py tests/workbench/test_live_archive.py -q
uv run --locked --offline python scripts/summarize_results.py --output reports/overview --check
uv build --offline
```
