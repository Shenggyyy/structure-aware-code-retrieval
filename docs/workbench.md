# Repository Workbench

The workbench adds a user workflow around the existing parser, five retrievers and
QA context builder. Repository import, resource preparation, five offline context
previews and saved history are available in the browser and CLI. **M9c adds frozen
generation plans, total estimates and explicitly approved same-model answers.**
Default actions remain offline previews. The
[implementation checkpoint](../reports/m9c/README.md) used offline providers; the
[separately approved live run](../reports/m9c-live/README.md) now contains five actual
answers, with no judge calls or retries. Browser answer/citation comparison, history
reopening and server restart passed, completing the scoped local workflow. Its one
unlabeled question is user-workflow evidence, not a retrieval benchmark or an
answer-correctness measurement.

## Install and prepare the embedding model

Run from the project root in PowerShell:

```powershell
uv sync --locked --dev --extra dense
uv run --locked --extra dense sacr prepare-model --cache artifacts/models
uv run --locked --extra dense sacr workbench --help
$workspace = "artifacts/workbench"
```

The explicit `prepare-model` command downloads the pinned MiniLM weights if needed.
Other preparation and query commands only load local weights. The optional Dense
dependencies are needed for all five strategies; BM25 alone can still produce a
result when vectors are unavailable. Import, preparation, previews, plans and saved
history need no API key. Only explicitly approved answer generation requires one.

## Start and use the browser

```powershell
uv run --locked --extra dense sacr workbench serve --workspace $workspace --model-cache artifacts/models --port 8765
```

Leave this PowerShell process running and open [http://127.0.0.1:8765/](http://127.0.0.1:8765/).
The command prints its local URL. Use a different `--port` if 8765 is occupied.
Stop the server with Ctrl+C when finished. Starting the server does not download a
repository, prepare model weights, run retrieval or call an answering model.

The visible **Interface language / 界面语言** selector offers **English** and **简体中文** on the
same page. An existing valid saved preference takes priority. Otherwise the first
browser language selects Chinese when it begins with `zh`; other languages use
English. Invalid saved values are ignored. A browser that blocks storage still
allows switching for the open page, but the choice may not survive a refresh.

Language switching redraws local interface wording without fetching data, running
retrieval or calling a model. It preserves question input, source code, model
answers, paths, IDs, monetary values and raw JSON. Technical error details remain
in their original language beside translated user-facing explanations. An edited
generation budget and current paid-consent checkbox are not reset or approved by
switching language; reopening or refreshing a plan still resets paid consent.

1. Enter a **public HTTPS Git URL** or a **local directory path**. Local paths refer
   to the server's filesystem; relative paths resolve from the project directory
   where the server was launched. For HTTPS, set an exact commit in the ref field
   for repeatable source selection, or keep `HEAD` to resolve its current version.
2. Choose **Import and prepare / 导入并准备**. Download/capture, parsing, vector and graph state
   remain visible, including failures. Only one background job runs at a time;
   reload the page to reconnect rather than starting duplicate jobs. Existing
   snapshots and valid resources are reused under the same M9a rules.
3. Select an imported repository. Inspect the saved commit/source information and
   resource state, then enter a question. The shared `top_k` and context byte limit
   apply to all five retrieval strategies.
4. Choose **Preview all five strategies / 运行五策略预览**. Five columns display separate outcomes, ranked hits,
   source evidence, score details and available structure provenance. Expand code
   evidence to see its saved path and one-based line numbers. Evidence IDs refer to
   packed context; a preview has no generated answer or answer citation.
5. Open a run from **History / 历史记录**. The saved comparison and its source evidence are loaded
   without retrieval, encoding or access to the original source. The UI distinguishes
   this saved view from a preview just completed in the current browser session.

Every preview is saved automatically. Browser history uses the same workspace and
records as `workbench history`/`show`, including previews created through the CLI.
Reloading or restarting the server does not repeat work. Unfinished server jobs are
marked interrupted at restart; resource stages or saved strategy results already
written remain available. Explicitly prepare or preview again when a fresh attempt
is needed. An abrupt termination cannot recover work that was never saved.

One browser server owns each workspace. Use a different workspace for a second
server, and wait for the active browser job to finish before writing to the same
workspace through CLI commands. The browser's read-only history access remains
available while a task runs.

Missing Dense dependencies or weights leave vector preparation failed; unaffected
resources and strategy outcomes stay visible. Install the optional dependencies and
run `prepare-model` in PowerShell, then explicitly prepare the repository again.
Do not use a preview's missing generation time, tokens or cost as a zero-cost model
measurement: those values remain unknown and the model API call count is zero.

The server binds **only `127.0.0.1`**. It uses local packaged HTML/CSS/JavaScript, no
external assets or web framework. Host/origin checks and a per-process request token
protect the local API; this token is unrelated to an OpenAI key. Keep the page on
the printed origin rather than placing it behind a proxy or exposing it to a LAN.
The server has no credentials form, user accounts or automatic LLM judge. Generation
requires the separate plan and confirmation flow below. Repository content and
generated answers are rendered as text rather than executable
HTML. Existing benchmark findings remain in [RESULTS](../RESULTS.md), separate from
unlabeled interactive questions.

## Optional answers: review before paid execution

First save a context preview. In the browser, choose **Review this cost plan /
查看本次费用方案** and review the model, per-strategy eligibility, exact request
count and combined estimate. Planning does not call OpenAI.

Preparing a plan updates the browser URL to `#plan=PLAN_ID`. Bookmark or copy that
URL to reopen the same frozen plan after closing or refreshing the tab, while the
server uses the same workspace. Reopening reads the saved plan and original preview;
it creates no new plan and makes no model request. Paid consent is reset to unchecked
each time the plan opens. An already consumed plan remains single-use; use history
to open its saved answers rather than attempting generation again.

The preset is shared by every eligible strategy:

| Setting | Frozen value |
| --- | --- |
| Answer model | `gpt-5.4-mini-2026-03-17` |
| Reasoning effort | `none` |
| Maximum output per request | 1,024 tokens |
| Generation requests | At most five, one for each eligible strategy |
| LLM judge requests | Zero |
| Frozen uncached rates | US$0.75 input / US$4.50 output per million tokens |

Rates were checked on 2026-09-09 against the
[official model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
The saved plan binds the rates, request payloads, source context and generation
settings. Its estimate covers generation plus the zero proposed judging requests.
Input estimation uses message/schema/settings UTF-8 bytes plus a 4,096-token framing
allowance, with the full output cap; it is a conservative proxy, not an exact
tokenizer count. Strategies with missing retrieval or empty evidence are ineligible
and make no request. The plan displays that reduced scope explicitly.
It is an estimate rather than an invoice or a provider-enforced spending cap; a
budget check cannot guarantee the eventual bill. Existing research budgets do not
authorize this new plan.

To execute, explicitly confirm the exact model ID and a positive US-dollar budget
covering the displayed estimate, acknowledge paid generation, then choose
**Approve and generate answers / 确认并生成回答**. No preselected consent or automatic execution
follows planning. The server must inherit a locally configured `OPENAI_API_KEY`;
configure it before starting the server and restart
the server if its environment changes. The key is never submitted to the browser,
saved with the plan or written to the archive. Approved requests send the question
and frozen code context to OpenAI, including source copied from a local directory.

Each strategy keeps its own answer or failure alongside the original retrieval
evidence. Citation controls open saved code and line numbers. The same model and
limits do not force answers to differ: identical answers are valid outcomes. Missing
or failed retrieval cannot become a fabricated answer. Generated results display
actual generation latency and reported provider tokens; unavailable measurements
remain unknown. Usage-based estimates use the plan's frozen rates, not a guessed
invoice. No LLM judge or semantic correctness score is requested by this workflow.

A plan executes once. Attempts and raw responses are saved locally as they happen;
an attempted request with no durable response stays unknown. There is no automatic
retry, resume, or regeneration when history opens. Preserve failed, interrupted and
unknown outcomes before deciding on any separately scoped work. Historical previews
remain unchanged; answer runs are separate saved comparisons. The browser labels
current generation, reopened saved results and offline validation separately.
Unknown transport outcomes stop the remaining requests, which stay `not_run`.
Recorded refusal/incomplete responses and invalid answer formats retain their
provider data while subsequent strategies can continue. Explicitly creating a new
plan from the same preview is a new scope requiring its own paid confirmation; it
does not repair or erase any previous attempt.

The same workflow is available in PowerShell. First create and inspect a plan from
an existing preview ID:

```powershell
$previewRunId = Read-Host "Saved context-preview run ID"
$plan = uv run --locked --extra dense sacr workbench plan $previewRunId --workspace $workspace --json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Generation planning failed." }
$plan | Select-Object plan_id, model, request_limit, judge_calls, estimated_cost_usd
$plan.strategies | Select-Object strategy, status, estimated_cost_usd
```

Only after reviewing and approving this exact scope, run the following opt-in block.
It can produce paid requests; this is not part of the offline quickstart:

```powershell
if (-not (Test-Path Env:OPENAI_API_KEY)) { throw "Configure the API key locally before execution." }
$approvedBudgetUsd = [double](Read-Host "Approved total budget in US dollars")
uv run --locked --extra dense sacr workbench generate $plan.plan_id --workspace $workspace --budget-usd $approvedBudgetUsd --confirm-model "gpt-5.4-mini-2026-03-17" --confirm-paid
```

CLI approval errors fail before calls; non-complete execution prints its saved
outcomes and returns a nonzero exit code. Use `workbench history` and `show RUN_ID`
to inspect them rather than repeating `generate`. The
[M9c implementation record](../reports/m9c/README.md) preserves the offline checks;
the [separate live record](../reports/m9c-live/README.md) contains the approved five
requests and raw outcomes. All five returned `answered`; reported usage was 15,046
input and 1,131 output tokens, with a US$0.016374 frozen-rate estimate against the
US$0.10 approved budget. No judge, retry or unknown response was recorded. Valid
source/citation checks do not establish semantic correctness.

## CLI: import one repository

Choose **one** source. For a local Python directory or Git working tree:

```powershell
$repository = uv run --locked --extra dense sacr workbench import "." --workspace $workspace --json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Import failed; inspect the error and workspace jobs." }
```

For a public HTTPS Git repository, use an exact commit for repeatable imports:

```powershell
$repository = uv run --locked --extra dense sacr workbench import "https://github.com/psf/requests.git" --ref 0e322af87745eff34caffe4df68456ebc20d9068 --workspace $workspace --json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Import failed; inspect the error and workspace jobs." }
```

Inspect the returned identity:

```powershell
$repository.repository_id
$repository.source | Format-List
```

HTTPS imports record the actual fetched commit. Branches, tags and `HEAD` are also
accepted, but mutable refs are resolved again on each import. A repeated exact-commit
import validates and reuses an existing matching snapshot without downloading it.

Local imports copy current files and record HEAD when available. That commit is
only an anchor: `working_tree: true` and `dirty: null` do not claim a clean checkout.
The saved file hashes identify what was actually analyzed, including local edits.
A directory without Git metadata has a null commit. Importing again after a source
change creates a different repository identity; existing snapshots stay intact.

Only selected Python files and applicable `.gitignore` files are frozen. The source
tree is never imported, checked out into an executable workspace, or installed.
Do not change the local tree during import if a consistent working-tree capture is
needed. The stored snapshot is independent of subsequent changes to the original.

## CLI: prepare resources and preview a question

```powershell
uv run --locked --extra dense sacr workbench prepare $repository.repository_id --workspace $workspace
```

The command records index, vector and graph stages separately. A stage is `ready`
when newly built or `reused` after validating existing bytes and configuration.
Missing model weights fail the vector stage while leaving the index and graph
available. Install/prepare the model and explicitly run preparation again to finish.
`partial` and `failed` commands return a nonzero exit code after printing their
saved state. A caught Ctrl+C records `interrupted`; no automatic retry is performed.

```powershell
$run = uv run --locked --extra dense sacr workbench preview $repository.repository_id "How are request URLs prepared?" --workspace $workspace --top-k 10 --max-context-bytes 16000 --json | ConvertFrom-Json
$run.results | Select-Object strategy, status
$run.run_id
```

Use a question relevant to the selected repository. One invocation runs BM25,
Dense, Hybrid, Symbol-aware and Structure-aware, with the same question and context
settings. Structure uses the existing default Hybrid seeds. The archived settings
include the actual encoder specification, fusion constants, symbol weights and
structure configuration.

Every strategy keeps its own outcome. An unavailable vector resource does not
become a fake Dense answer; an invalid graph does not erase BM25 or other unaffected
results. `preview_complete` means all strategies finished previewing, not that an
answer was generated. A partial comparison is still saved and can be reopened.

Each successful row stores ranked hits with code, paths, one-based inclusive line
ranges, score components and available relation provenance. It saves the first
`top_k` hits plus any additional chunks selected by the existing context packing
policy; `ranked_candidates` records the full ranking size. The context uses up to
`top_k` distinct symbols and the exact UTF-8 byte budget. Scores from different
retrieval methods are not calibrated against each other.

## CLI: inspect and reopen history

```powershell
$run.results[0].hits | Select-Object rank, qualified_name, path, start_line, end_line
$run.results[0].qa.context.evidence | Select-Object id, path, start_line, end_line
uv run --locked --extra dense sacr workbench history --workspace $workspace
uv run --locked --extra dense sacr workbench show $run.run_id --workspace $workspace --json
```

`show` checks and reads the saved record without redoing retrieval or loading a
model. Records include source/commit information, configuration and code evidence;
they can be reopened even after the original source or prepared resources disappear.
Damaged history appears as `unreadable`, rather than silently disappearing. Checksums
detect accidental corruption; they are not signatures authenticating third-party data.

The workspace contains:

```text
jobs/<job-id>.json                    Import stages and errors
web-jobs/<job-id>.json                Browser jobs and persisted progress
repositories/<repository-id>/       Immutable source bytes and manifest
resources/<repository-id>/          Index, vectors, graph and preparation status
runs/<run-id>/run.json               Self-contained five-strategy comparison
generation-plans/<plan-id>/plan.json Frozen preview, payloads, model and total estimate
generation-plans/<plan-id>/execution/ Permanent single-use claim and execution lock
```

Inspect `web-jobs` for browser task progress, `jobs` for import errors and the
resource manifest for preparation errors.
Generation run records retain per-strategy attempt state, raw output/provider
envelope, response IDs and normalized QA results. Keep these local archives for
review; they can contain the selected repository's source and questions.
Caches bind source identity, parser configuration, encoder/model package versions
and relation settings. Mismatched or damaged cache files fail validation and are
not silently overwritten. Preserve the affected workspace for diagnosis and import
into a new workspace if a clean rebuild is needed.

## Measurements and boundaries

- `context_preview` has no generated answer; empty contexts retain the existing
  `insufficient_context` outcome. Approved answers use `model_generation`; injected
  test providers are labeled `offline_test` and do not count as live evidence.
- Retrieval, context preparation, automatic validation and resource loading have
  separate timings. Shared encoder initialization is recorded once. These are
  sequential local measurements, not controlled benchmark latency comparisons.
- Previews have null generation latency, provider token usage and cost, with zero
  API calls. Answer runs retain observed generation measurements and unknown values;
  known token/cost subtotals never stand in for missing full totals. Context bytes
  are not token usage.
- New questions have no relevance judgments: Recall, NDCG and answer-correctness
  metrics are not invented. Existing [benchmark results](../RESULTS.md) remain a
  separate, unchanged experiment with provisional labels and negative findings.
- Automatic citation/source checks verify identity and locations. They do not
  score correctness, completeness or semantic citation support.

Public import accepts conservative HTTPS DNS-host URLs on port 443. Credentials,
redirects, query strings, encoded paths, IP literals and private/non-public DNS
answers are rejected. A checked public address is pinned through Git's
`http.curloptResolve`; Git must support that option. Ambient credentials, proxy
settings, hooks, templates and repository-controlled filters are not used. Remote
files are read from Git blobs; submodules, LFS retrieval, symlinks and junctions are
not followed. The indexer also never executes target code or dependencies.

Source capture is limited to 10,000 selected files, 1 MiB per selected file, 50 MiB
total, 100,000 directory/tree entries and bounded depth/time. Git transfer time is
bounded, but this version has no hard disk quota on the downloaded Git pack. Keep
workspaces on a local writable filesystem under the user's control. The service
does not sandbox unrelated processes concurrently modifying local files.

## Delivery and acceptance

The existing CPU Dense Docker image already contains the required CLI and Git.
Use [Docker preparation and persistent volumes](docker.md); mount local sources
read-only and prepare weights explicitly before running previews. The base image
can run import/index/graph operations but needs Dense dependencies for all five
strategies. M9b's browser server is intended to run on the host; container port
exposure is not added in this checkpoint. Container CI now also checks that the
installed package contains all four browser assets, including the shared `i18n.js`
translation catalog. Existing CI collects the offline
tests on Windows and Linux, and package builds include the local browser assets
without a frontend build.

The browser localization contract tests use Node.js on `PATH` with no npm packages.
Run `uv run --locked pytest tests/workbench/test_i18n.py` to check them locally;
pytest skips this test when Node is unavailable. CI runs `node --version` and
JavaScript syntax checks before pytest, so missing Node fails CI rather than
silently skipping this coverage. The workbench server itself does not need Node.

M9b exposes the existing services through Python's standard-library HTTP server and
simple browser assets: import status, question entry, side-by-side contexts, source
expansion and history. See [M9b validation](../reports/m9b/README.md) for observed
checks and limits. M9c implements shared-model plans and explicit approval for at
most five generation requests, without adding a judge. Its offline tests validate
software behavior, not model correctness or real billing. The separately approved
[M9c live acceptance](../reports/m9c-live/README.md) verified five actual answers,
representative citations for all five strategies, token/cost display, saved-history
reopening and unchanged results after server restart. The agreed local workflow is
complete; no additional engineering stage is required automatically.

Final handover is complete: the shared English/Chinese interface, preference
behavior and final workflow review have passed local validation. See
[delivery](delivery.md) for actual checks, fixes and remaining limitations.
Localization does not change or add research measurements.

Existing experiment approvals, including this completed US$0.10 run, do not
authorize new questions or retries. Prepare and review a new plan before any new
paid generation. Offline previews, source inspection, saved-plan reopening and
answer history remain available without model calls. Keep all earlier raw evidence,
provisional labels and negative research results unchanged.
