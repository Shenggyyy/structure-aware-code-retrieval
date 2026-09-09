# Repository Workbench

The workbench adds a user workflow around the existing parser, five retrievers and
QA context builder. **M9a supports repository import, resource preparation, five
offline context previews and saved history through the CLI.** Browser comparison
and real answer generation are planned for M9b/M9c; they are not implemented here.

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
result when vectors are unavailable. No API key is required in this milestone.

## Import one repository

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

## Prepare resources and preview a question

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

## Inspect and reopen history

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
repositories/<repository-id>/       Immutable source bytes and manifest
resources/<repository-id>/          Index, vectors, graph and preparation status
runs/<run-id>/run.json               Self-contained five-strategy comparison
```

Inspect `jobs` for import errors and the resource manifest for preparation errors.
Caches bind source identity, parser configuration, encoder/model package versions
and relation settings. Mismatched or damaged cache files fail validation and are
not silently overwritten. Preserve the affected workspace for diagnosis and import
into a new workspace if a clean rebuild is needed.

## Measurements and boundaries

- The current mode is always `context_preview`; nonempty contexts have no generated
  answer. Empty contexts retain the existing `insufficient_context` outcome.
- Retrieval, context preparation, automatic validation and resource loading have
  separate timings. Shared encoder initialization is recorded once. These are
  sequential local measurements, not controlled benchmark latency comparisons.
- Generation latency, provider token usage and monetary estimates remain null;
  model API call counts are zero. Context bytes are not token usage.
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

## Delivery and next stages

The existing CPU Dense Docker image already contains the required CLI and Git.
Use [Docker preparation and persistent volumes](docker.md); mount local sources
read-only and prepare weights explicitly before running previews. The base image
can run import/index/graph operations but needs Dense dependencies for all five
strategies. No new Docker port or web dependency is needed for M9a. Existing CI
collects the new offline tests on Windows and Linux.

M9b will expose these services through a local Python HTTP layer and simple browser
assets: import status, question entry, side-by-side contexts, source expansion and
history. M9c will add one shared answering model and an explicit preflight/approval
step for the maximum five generation requests. Any proposed judge requests must
also be included in that new estimate. Earlier experiment budgets do not authorize
these calls; no judge is planned by default. Final browser workflow acceptance
remains outstanding until those stages are implemented and exercised.
