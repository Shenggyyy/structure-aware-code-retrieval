# Final Delivery Record

This record covers the owner's final delivery request after the core system,
experiments and M9 workbench were completed. It is a bounded handover, not a new
research milestone. The agreed scope closes after all three stages pass; additional
features, datasets or paid experiments require a separate request.

## Stages

| Stage | Scope | Status |
| --- | --- | --- |
| 1 | Repository audit, justified cleanup and English/Chinese GitHub homepages | Complete; local validation recorded below |
| 2 | One shared browser interface with persistent Chinese/English selection | Complete; local validation recorded below |
| 3 | Targeted final review, fixes, full verification and delivery acceptance | Complete; local validation and remaining limits recorded below |

The agreed scope is formally delivered. The homepages and browser interface support
English and Chinese, and final local review is complete. Accepted capabilities and
historical evidence remain in [status](status.md) and [roadmap](roadmap.md). The owner
performs the final commit/push; no remote CI result is inferred for these changes.

## Stage 1 audit and decisions

The starting worktree was clean on `main`, at commit
`ecde9e1` (`Validate live workbench answers and preserve replayable results`). The
configured origin is the public `Shenggyyy/structure-aware-code-retrieval` repository.
No repository or ancestor `AGENTS.md` was present. Existing conventions come from
`pyproject.toml`, CLI registration, tests, Docker/CI and the maintained guides.

The audit followed references through source imports, Typer decorators, public
commands, tests, packaging, container entrypoints and reproduction scripts. A lack
of a direct function call was not treated as proof of unused code.

| Area | Evidence and decision |
| --- | --- |
| Apparent unused CLI functions | Typer decorators register public commands in `cli.py` and `workbench/cli.py`. Root and workbench help both load successfully; retain these entrypoints. |
| Two review modules | `qa/review.py` validates answer review; `evaluation/review.py` handles retrieval labels. Separate CLI commands, smoke and regression tests use them. Human review being optional does not make these interfaces obsolete. |
| Judge v1/v2, revision and follow-up code | `qa/judging.py` dispatches frozen protocols. The assessment/revision/follow-up verification chain loads old archives and preserves prior unknown outcomes. Retain each version and its tests. |
| Historical experiment scripts | `run_m5.py` and `run_m6a.py` through `run_m6c.py` reproduce different frozen suites. `docs/reproduction.md` still documents them. Retain. |
| Smoke and result aggregation | `scripts/smoke.py` is used by container CI; `scripts/summarize_results.py` checks published results in Windows/Linux CI. Retain. |
| Homepage repetition | Repeated QA batch histories, cost tables and milestone narratives made the landing page harder to use. Keep a compact evidence summary and link detailed numbers to their original reports. |
| Completion and protocol wording | Current status/roadmap repeated old checkpoint expectations. Consolidate current acceptance and historical evidence navigation; correct the Docker/manual-review boundary and the description of implemented LLM assessment. |
| Older baseline guidance | Replace future-tense M5 guidance with links to completed ablations and scale measurements; broader research remains optional. |

**No production code, public entrypoint, protocol version or historical artifact was
deleted.** There was insufficient evidence to justify such deletion. Benchmarks,
configs, reports, licenses, source provenance and user runtime data remain intact.
This audit is not a claim that every retained line is indispensable.

## Documentation ownership

| Information | Primary location |
| --- | --- |
| Goals, first run, interface and limitations | [English homepage](../README.md), [Chinese homepage](../README.zh-CN.md) |
| Browser operations, generation consent and recovery | [Workbench](workbench.md) |
| Detailed findings and evaluation limits | [Results](../RESULTS.md), linked immutable experiment reports |
| Commands and experiment reconstruction | [Reproduction](reproduction.md), [experiments](experiments.md) |
| Technical definitions | [Architecture](architecture.md), strategy and evaluation guides |
| Current acceptance and historical stages | [Status](status.md), [roadmap](roadmap.md) |
| This final three-stage handover | This file |

The homepages use the same executable quickstarts and evidence claims. Technical
guides and historical reports remain English, except for existing bilingual CV
wording. Their language is stated explicitly; no missing translations are linked.

`docs/assets/workbench.jpg` is an unmodified browser screenshot of the published
M9c live Requests run opened as history. It shows saved answers, not a new paid
generation, a translated response or a semantic assessment. Only public source
information is visible; local repository selectors and credentials are not shown.

## Stage 1 validation

Recorded on 2026-09-09, before the owner's commit/push:

| Check | Actual result |
| --- | --- |
| Homepage parity | All four command/layout blocks and all 34 link targets match between English and Chinese; scope, result claims and language availability were reviewed in both versions |
| Current-document navigation | 288 local links and heading anchors across 21 current Markdown documents passed; no broken local target was found |
| Display privacy | Current documents contain no personal absolute directory or credential patterns; the screenshot was visually checked and shows only the public saved run |
| Offline regression | `tests/test_delivery.py` and `tests/workbench/test_live_archive.py`: five passed in 6.68 seconds |
| CLI entrypoints | Root and workbench `--help` both passed; registered commands remain available |
| Lint and formatting | `uv run --locked --offline ruff check .` and `ruff format --check .` passed |
| Published results | The existing overview validator passed for all 45 saved runs without rewriting them |
| Build | `uv build --offline` produced wheel and source distribution; both homepages and screenshot are present byte-for-byte in the source distribution, and the wheel retains its browser assets and English README metadata |
| Browser walkthrough | Fresh archive-only workspace, server without `OPENAI_API_KEY`: history search opened five saved answers, and Dense S2 opened `src/requests/models.py:409–481` |
| Preservation check | Git diff confirms no changes to `src/`, tests, scripts, benchmarks, configs, reports, dependency/build configuration or Docker/CI files |

The work uses existing archives and offline tests. **New model requests and model
downloads: zero.** Fresh validation outputs were isolated under ignored `artifacts/`;
existing user workspaces and caches were not cleaned or overwritten.

Full-suite and bilingual browser review belong to Stage 3 and were not claimed for
this documentation checkpoint. No new container build or remote CI run was executed;
the existing CI covers both CPU container targets after the owner pushes. Historical
full-suite and live-acceptance records remain evidence of their own checkpoints.

## Stage 2 implementation and findings

This stage starts from `845c370` on `main`. One `i18n.js` catalog serves the existing
HTML and application logic. It covers navigation, forms, progress, previews,
generation plans, consent, saved answers, citations, history and errors. No core
retrieval, generation or archive protocol was redesigned or deleted.

The visible language selector stores `en` or `zh-CN` locally. A valid saved choice
takes priority; otherwise the first browser language selects Chinese for a `zh`
prefix and English for other languages. Blocked storage still permits switching
within the page. Missing translations fall back to English, then the message key.

Switching redraws cached data without fetching or translating user content. Questions,
code, answers, identifiers and raw JSON stay unchanged; edited budgets and current
consent survive a switch. Reopening a plan retains the existing consent reset.
Text and substituted values use safe DOM text operations. Known operational errors
have bilingual explanations; unmapped technical diagnostics retain their original
text with a localized wrapper.

Review found and fixed three issues: redrawing repository choices initially selected
a repository after the user had deliberately cleared the selection, and some fixed
generation approval errors lacked Chinese explanations; a few dictionary lookups
also treated prototype-named unknown fields as messages. Regression checks now
cover empty selection preservation, important budget/model/key/plan errors and
safe fallback for unusual status/check names.
Responsive rules allow longer English labels and local scrolling for tables,
comparison cards and source code. The new asset is registered with the server,
checked in the package and included in the CI container asset assertion.

## Stage 2 validation

Recorded on 2026-09-09, before the owner's commit/push:

| Check | Actual result |
| --- | --- |
| Workbench regression | `test_server.py`, `test_server_generation.py` and `test_live_archive.py`: 95 tests passed, including the new static asset route |
| Translation contracts | `test_i18n.py` passed all 11 Node subtests: defaults/storage/fallback, catalog and placeholder parity, DOM safety, critical errors, and application redraw preserving data, consent, source details and empty repository selection |
| Browser behavior | Existing published Requests archive opened in both languages; Dense S2 showed unchanged source at `src/requests/models.py:409–481`; language persisted after reload |
| No-request switch | Instrumented server request counts remained at nine GETs and zero POSTs across a language switch; original question, answer claims and actual configuration matched exactly |
| Offline workflow | Isolated test workspace: local fixture import, resource preparation/reuse, five previews, cost planning, insufficient-budget rejection, explicit consent, five synthetic answers, citation viewing and history search/reopen worked |
| Failure and rendering | An offline unknown-outcome fixture retained unknown usage/costs, one unknown attempt and three unstarted strategies in both languages; invalid HTTP repository URL showed a translated rejection; HTML-shaped answer text rendered literally with no injected image |
| Responsive browser check | 1440×1000 and 390×844: reviewed both languages, long confirmation text, buttons and citation dialogs; narrow layouts use local scrolling without page-wide horizontal overflow; no browser warning/error logs observed |
| Homepage and navigation | Four command/layout blocks and 34 link targets match across the two homepages; 290 local links and 20 heading anchors across 20 current top-level documents passed |
| Delivery regression | `test_delivery.py`: three tests passed; the final combined run with `test_i18n.py` passed four pytest tests |
| Lint and formatting | Ruff check and format check passed; Node syntax checks passed for both application and translation scripts |
| Build and assets | `uv build --offline` succeeded; wheel contains the four exact static assets, and source distribution includes the same assets, bilingual homepages and Node contract tests |
| Published results | Existing overview validator passed for all 45 saved runs; no report artifacts were rewritten |

Browser generation used an injected test model and fixture encoder, with the real
OpenAI call method disabled. Synthetic answers are explicitly marked as offline
tests and report zero real API calls. This is software validation, not a new model
experiment or retrieval-quality measurement. Published archives were read without
modification; validation data stayed under ignored `artifacts/`, apart from source
tests. User workspaces, model caches and API configuration were not overwritten.

Node is needed for the frontend contract tests, not for serving the workbench.
Local pytest skips these tests if Node is absent; CI explicitly checks Node before
running them. An already-running Python server must be restarted to register the
new asset; existing histories remain readable. Full-suite and container execution
are deferred to Stage 3; no remote CI result is claimed for this uncommitted stage.

## Stage 3 review and findings

Review started from a clean `main` at `94cab19`. It covered public HTTPS and local
imports, static source capture, version/cache bindings, five-strategy previews,
generation plans and explicit approval, unknown attempts, safe browser rendering,
citations, history/restart, bilingual behavior, packaging and experiment evidence.
The implementation was inspected alongside tests, CLI entrypoints, Docker/CI and
current guides. Independent backend and documentation reviews informed this record.

| Finding | Resolution and evidence |
| --- | --- |
| Failed or interrupted import steps could appear completed | The browser now retains the terminal status on the last attempted import phase. A regression test failed before the fix and passed afterward in both languages; the browser confirmed that rejected HTTP sources show validation failure. |
| Reproduction guide described implemented browser generation as future work | Updated the current guide to describe saved cost plans and explicit model/request/budget approval. |
| Architecture called 58/60 cumulative score coverage | Corrected this to protocol acceptance; numeric score coverage differs by assessment dimension. Original records and scores were not edited. |
| Completion statements described Stage 2 as current | Final homepages, workbench guide, status and roadmap are reconciled with the bounded handover after final validation. Optional extensions remain separate. |
| One local browser import encountered a filesystem error | The failure stayed visible and no retry happened automatically. Direct diagnostic imports, an explicit UI re-import and eight isolated imports with concurrent progress reads succeeded. The original cause remains unknown. |

No backend change was justified by the review. Public addresses are validated and
pinned for Git; credentials, redirects, hooks and target-code execution stay
disabled. Source/resource integrity checks, single-use plans, durable request
journals and unknown-outcome recovery remain in place. These inspections and tests
are bounded evidence, not a guarantee that all defects have been found.

The filesystem diagnostic confirmed that service reads/writes share a process
lock. A deliberately held external file handle can block atomic replacement on
Windows, but this does not identify the cause of the observed browser failure.
No speculative storage retry, background model retry or broad refactor was added.

## Stage 3 validation

Recorded on 2026-09-09; remote CI is not inferred from local checks.

| Check | Actual result |
| --- | --- |
| Full offline suite | `uv run --locked --offline pytest --cov --cov-report=term-missing --cov-report=xml`: 1178 passed, two skipped in 668.75 seconds; reported Python coverage 91%; all 11 Node contract subtests passed |
| Skip reasons | `tests/test_ingestion.py:60` and `tests/workbench/test_importing.py:149` require symlink creation unavailable on this Windows host; the existing Ubuntu CI runs the same suite on Linux |
| Backend regression | Import/storage/preparation/comparison/generation tests: 155 passed, one Windows symlink-creation test skipped because the host could not create that link; mocked junction/path guards passed |
| Published evidence | Retrieval overview verified all 45 saved runs; M7b assessment, M7d revision, M7e follow-up and M9c workbench archive validators passed without changing records |
| Archive integrity | Four ZIP checksums and all 235 member sizes/hashes matched their manifests; failure, invalid and unknown outcomes remained present |
| Container execution | Base and CPU Dense images built locally; both installed-runtime checks passed as UID 10001 with read-only filesystems and networking disabled; both 17-command CLI smokes passed, with no model download or API call |
| Browser workflow | Bilingual import/preparation, five previews, plan/budget/consent, synthetic answers, citations and history/reload completed; reopening cleared consent, and trying a consumed plan was rejected without another generation |
| Browser boundaries | Failed import status, bilingual required-field errors, safe literal rendering, missing usage/costs and unknown/unstarted outcomes were checked; switching preserved raw question/answer/configuration and left server counts unchanged at 39 GETs and five POSTs |
| Browser layout | Both languages checked at 1440×1000 and 390×844, including citations from all five archived strategies; narrow source blocks scroll locally, with no page-wide horizontal overflow or browser warning/error logs |
| Restart and history | Restarted the isolated server, reopened the saved five-answer run and compared question/claims/configuration; all five saved run-file hashes remained unchanged |
| Lint, format and syntax | Ruff check/format and both browser JavaScript syntax checks passed |
| Distributions | Final offline wheel and source distribution built; all four static assets matched source, both homepages and Node contracts were included in the source distribution, and runtime data was excluded |
| Documentation | 289 local links and 20 heading anchors across 20 current documents passed; homepage four code blocks and 34 link targets matched; no personal Windows directory or credential pattern was found |

Browser validation uses isolated fixture workspaces, a synthetic encoder and an
injected answer model; the real provider method is disabled. Published live answers
are read only as saved history. This stage authorizes no paid experiment. Synthetic
outputs remain labeled `offline_test`; they cannot establish answer correctness or
retrieval quality. User workspaces, caches and API configuration remain untouched.

## Delivery boundary and remaining limitations

Local Docker checks cover the same installed-runtime and offline CLI smoke boundaries
as `CPU container / base` and `CPU container / dense` in CI. The Dense check validates
CPU dependencies, not a new embedding experiment. After the static-only progress fix,
both images were rebuilt and their restricted runtime checks repeated; installed
script and README hashes matched the final working tree. The earlier 17-command
smokes were retained without repeating unrelated CLI tests. No paid calls or model
downloads were made. Browser automation covered the local Chromium interface; this does not
claim exhaustive browser, operating-system or accessibility coverage.

The observed unreproduced file error remains a known limitation of this validation.
Use a writable local workspace; file-locking or concurrent external changes can
still prevent an operation. The service records errors, and retries require an
explicit user action; unknown model requests must never be retried automatically.
Git downloads have time limits but no hard downloaded-pack disk quota.

Known research limitations remain: provisional labels, heuristic static edges,
small exposed evaluation sets, negative retrieval results, incomplete semantic
score coverage and historical unknown costs. Model opinions and automatic source
checks do not establish human-reviewed correctness. These limitations do not add
new required research work to this delivery.

No further development milestone is scheduled. Additional datasets, methods,
manual assessment, broader deployment or paid experiments are optional extensions,
not missing requirements of this handover.
