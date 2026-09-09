# M9b — Local browser repository workbench

M9b connects the existing workbench services to a local browser interface:
**import → prepare → enter a question → compare five contexts → inspect source →
reopen history**. It does not generate answers or perform LLM judging. The remaining
same-model answer workflow is M9c, with a new model/request/budget approval before
any paid execution.

## Implementation

- Python's standard-library HTTP server and three packaged HTML/CSS/JavaScript
  assets; no web framework, frontend build tool, database service or account system.
- A single background task per workspace, durable import/preparation/preview
  progress, explicit partial outcomes, and restart recovery without automatic retry.
- Five side-by-side strategy columns, actual source commits, common context
  settings, evidence IDs, code with line numbers, score components and typed
  relation provenance. History can reopen CLI-created and browser-created records.
- Loopback-only binding, exact Host/Origin and request-token checks, bounded JSON
  requests, fixed asset routes, no request-content logging, and text-only rendering
  of repository content. There is no answer-generation endpoint or API-key form.

## Observed browser checks

The actual browser was driven through the UI on Windows, using already cached
MiniLM weights. No HTTP request was substituted for the user-facing import or
preview actions in these checks.

| Case | Observed result |
| --- | --- |
| Fresh public Requests import | HTTPS URL and commit `0e322af87745eff34caffe4df68456ebc20d9068` entered in the form; 38 captured files, index/vectors/graph ready |
| Refresh during preparation | The existing background task and vector preparation status reappeared without another submission |
| Five-strategy preview | One question, all five real retrievers and the real pinned encoder; five completed context previews, no generated answers |
| Source inspection | Structure-aware evidence S1 opened `src/requests/models.py`, lines 295–310; the code, rank, score components and call relationship at line 297 were visible |
| Save, filter and reopen | History listed the same run; filtering selected its question; reopening and server restart retained the original run ID, measurements and evidence, with the historical-result label |
| Local static fixture | A one-file Python fixture containing a top-level exception imported and prepared successfully without execution |
| Markup in question/code | Literal image/script strings appeared as text; no injected image/script nodes or JavaScript dialog appeared |
| Missing embedding weights | Separate workspace retained index/graph preparation, displayed vector failure, and saved the available BM25 result alongside four failed strategies |

The public-repository and markup-fixture previews used the real encoder. The
missing-model case deliberately used a nonexistent model cache. These are workflow
and failure-handling checks on unlabeled questions, not retrieval-quality results.
Provider tokens, generation latency and monetary estimates remain unknown;
**new LLM API calls and new model downloads are zero**. Only the public Git import
required a network download. Historical benchmark artifacts remain unchanged.

## Automated validation

The broad offline suite passed **1,091 tests with two Windows symlink-privilege
skips** in about 9 minutes 29 seconds. After its collection, a final restart-progress
consistency fix and two additional cases were checked with **all 60 HTTP tests
passing**. These overlapping test counts are not additive. Ruff lint/format,
JavaScript syntax and the final wheel/source-distribution build passed.

New offline tests exercise HTTP import/preparation/preview/history with a labeled
synthetic encoder, packaged asset routes, partial failures, request validation,
workspace locking, interruption callbacks, restart recovery, corruption preservation
and CLI startup. Test encoders validate software behavior, not model quality.

Validation uncovered Windows file-sharing conflicts between polling reads and
atomic JSON replacement. A shared process lock now serializes those state reads
and writes. Rejected POST bodies are drained within byte/time bounds to avoid a
Windows connection reset hiding a rejection response. Shutdown retains the
workspace lock until the worker stops, and initial progress callbacks now enter
the services' interruption guards. These failures were fixed and covered by tests.

The measured totals and browser run identities are recorded in
[validation.json](validation.json). Ruff, JavaScript syntax checking, distribution
building and the existing 45-run overview check are part of this checkpoint's
verification. Container CI now verifies all three assets exist in the installed
package; container images were not rebuilt locally in this milestone. Remote CI
is pending the owner's commit and push.

## Reproduce

```powershell
uv sync --locked --dev --extra dense
uv run --locked --extra dense sacr prepare-model --cache artifacts/models
uv run --locked --extra dense sacr workbench serve --workspace artifacts/workbench --model-cache artifacts/models --port 8765
```

Open `http://127.0.0.1:8765/` and follow the [startup guide](../../docs/workbench.md).
Prepare weights explicitly on a new machine; starting the server itself performs
no download or retrieval. Use a free port and a local writable workspace. Run only
one browser server for that workspace and avoid concurrent CLI mutations.

```text
uv run --locked --offline ruff check .
uv run --locked --offline ruff format --check .
uv run --locked --offline pytest --cov --cov-report=term-missing
uv run --locked --offline python scripts/summarize_results.py --output reports/overview --check
uv build --offline
```

M9b's browser listener is for host-local use and is not exposed through Docker or
a reverse proxy. Existing container CLI workflows remain supported. Private Git,
multiple languages, target-code execution, distributed serving and automatic
semantic judging are outside this checkpoint. Provisional labels, negative
research findings and historical unknown outcomes retain their original meaning.
