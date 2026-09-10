# Workbench HTTP Migration

This separately requested maintenance change replaces the standard-library HTTP
adapter with FastAPI routes and Uvicorn. It keeps the delivered retrieval, QA and
bilingual browser workflow, without creating a new research milestone. Earlier
[delivery](delivery.md) and M9 reports remain records of their own checkpoints.

## Start and update

```powershell
uv sync --locked --dev --extra dense
uv run --locked --extra dense sacr workbench serve --workspace artifacts/workbench --model-cache artifacts/models --port 8765
```

Stop an older process before restarting. Reuse its actual workspace and model
cache paths; no manifest, index, plan, answer or history conversion is needed.
For saved-history replay without Dense, omit `--extra dense` from both commands.
Use the printed loopback URL and Ctrl+C to stop. The CLI owns lifecycle setup;
reload, multiple workers, public listening and proxy deployment are not supported.

The minimal FastAPI and Uvicorn dependencies are locked without their optional
standard extras. No frontend build, account system or database service is added.
The Wheel includes the same four HTML/CSS/JS assets. Both Docker targets install
the same HTTP dependencies through their existing locked build steps; Docker port
publishing still cannot expose a listener bound only to container loopback.

## Read the implementation

Start at `workbench/cli.py` for the unchanged `serve` command and
`workbench/server.py` for explicit GET/POST routes and Uvicorn lifecycle.
`workbench/jobs.py` owns durable jobs and recovery; `workbench/security.py` owns
shared request guards, bounded body/header handling and response headers.
Routes call the existing import, preparation, comparison, storage and generation
functions; the parser and five retrieval algorithms are unchanged. Durable jobs,
single-task admission, workspace locking and interruption recovery remain
application mechanisms, not FastAPI `BackgroundTasks`.

The adapter preserves existing URL and JSON contracts, validation status codes,
body-size limits, Host/Origin and request-token checks, and security/cache headers.
Framework schema and documentation endpoints are disabled to keep the existing
surface local and unchanged. Unknown or interrupted generation attempts are never
automatically repeated. Planning remains offline, and a fresh paid request still
requires explicit model/budget approval.

A small Uvicorn header preflight is necessary because h11 can normalize duplicate
headers or trailing whitespace before FastAPI sees the ASGI request. It preserves
the workbench's stricter checks on the original header values while h11 remains
the HTTP parser. The POST admission gate derives accepted paths from FastAPI route
metadata, preserving error precedence without another manually maintained router.
Transport framing is not identical to the old server: the adapter enforces a
64 KiB aggregate-header limit and a 10-second total body-read deadline, which are
stricter resource bounds than the legacy handler. These do not increase the
existing 16,384-byte JSON body limit or permit new cross-origin access.

For example, clicking the five-strategy preview button sends JSON to
`POST /api/preview`. FastAPI selects `preview()` from its decorator. After the
shared boundary checks the origin/token and the handler validates fields,
`Jobs.submit("preview", payload)` saves and starts the existing durable task.
The HTTP response is `202` with the job record; it does not wait for all retrieval
work. The worker calls the existing `comparison.preview_question()` function,
while the browser polls `GET /api/jobs/{job_id}` and finally opens the saved run.
This preserves progress, single-job admission and saved failure outcomes.

## Validation record

Validation uses isolated workspaces and offline substitutes. No user snapshots,
caches or history are reused as writable test data; no model API call is authorized
by this migration. Checks were run locally on Windows with Python 3.12 and,
after the Docker engine became available, in Linux containers. Remote CI for
the eventual commit is separate.

| Check | Observed result |
| --- | --- |
| Dependency lock/sync | Minimal FastAPI 0.141.1 and Uvicorn 0.52.4 installed; all 51 previously locked package versions unchanged |
| HTTP smoke | Passed from the editable development environment and a fresh noneditable, base-only Python 3.12.14 Wheel installation; rebuilt/reinstalled and repeated after the final HTTP fixes |
| Installed package boundaries | CLI option help, actual FastAPI route registration, four static assets over real HTTP, empty history, session state, Host/Origin rejection, absent documentation endpoints, shutdown and workspace reopening passed |
| Distribution contents | sdist/Wheel built; final Wheel server/jobs/security modules and all four asset bytes match source; HTTP runtime dependencies and sdist migration docs/smoke script included |
| Browser workflow | Passed in an isolated workspace: local import/preparation, five-strategy preview, offline plan/confirmation with a synthetic model, five answers, source lines, English/Chinese switching, history reopen and reload; five synthetic calls, zero real API calls |
| Published results | Existing overview validator checked all 45 saved runs; frozen reports and benchmark/configuration records remain unchanged |
| Documentation | 201 local linked paths exist; English/Chinese README links match across 35 entries |
| Docker | Passed on Docker Engine 29.7.2, linux/amd64: both base and dense images built; installed runtime checks, HTTP smoke and each 17-command offline CLI smoke passed |
| Linux CLI shutdown | The existing POSIX CLI SIGTERM regression body passed against the installed base image: startup from another directory, loopback HTTP response, clean signal exit and workspace reopening |

The fresh environment needed a one-time download of locked dependencies before
its offline runtime check; no model weights were downloaded. Both container CI
targets now run the installed HTTP smoke as well as their existing runtime and
algorithm checks. Their equivalent checks passed locally after the engine was
started; this does not claim that a future GitHub CI run has already passed.

The initial Docker attempt was blocked by an unavailable engine. The follow-up
on 2026-09-10 used separate `sacr:http-migration-base` and
`sacr:http-migration-dense` image tags, without changing the Dockerfile or runtime
code. Both images ran as UID 10001 from `/opt/venv`, with no pytest installed.
Base excludes Torch and sentence-transformers; Dense imports CPU-only Torch and
sentence-transformers successfully. The HTTP smoke served all four packaged
assets and checked routes, session, history, access restrictions, shutdown and
workspace reopening. Each CLI smoke completed 17 commands with matching repeated
quality fingerprints. These are synthetic workflow checks, not new retrieval
quality or live Dense-model experiments.

All container checks used `--network none`, `--read-only` and isolated writable
tmpfs directories. No API key or user workspace was passed into a container;
there were zero model API calls and zero model-weight downloads. Build-time
package/image downloads are separate from these offline runtime checks. The
original Windows symlink skips remain platform limitations; no full Linux pytest
suite was run in these runtime images.

`scripts/smoke_workbench.py` performs the package/HTTP check in an isolated child
with `-I`, a temporary current directory, no API key and offline model flags.
Use `--require-installed` with a noneditable Wheel or container installation to
reject an editable checkout accidentally standing in for the installed package.
Ruff lint and formatting, both JavaScript syntax checks and `git diff --check`
passed. The focused HTTP/generation/CLI checks passed, with the POSIX CLI signal
test skipped on Windows. Its test body subsequently passed in the Linux base
container; the Linux CI job also remains configured to exercise it.
The full offline regression run completed with **1,254 passed and three skipped**
in 633.74 seconds. The skips were two unavailable Windows symlink operations and
the POSIX CLI SIGTERM test. Ten additional trailing-header-whitespace cases passed
after that suite had collected; seven targeted lifecycle checks passed again
against the final single-worker/shutdown changes. The 23 direct ASGI cases are
included in the full run. These are local results, not a claim that the future
GitHub CI run has already passed.

The compatibility review found and fixed unknown-POST error precedence and
trailing-header-whitespace normalization before final package verification.
Direct ASGI tests additionally check bounded streams, timeouts, duplicate JSON,
error redaction and the same access guards without relying on a socket transport.

One browser fixture import initially failed with a filesystem error; the UI
retained that failure and an explicit manual retry completed. The cause was not
established. No automatic import or generation retry was added. Browser model
responses and usage values were synthetic and clearly labeled; they are not new
research results. These checks do not establish correctness on every OS/browser
or exercise a new paid provider request.
