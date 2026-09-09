# Final Delivery Record

This record covers the owner's final delivery request after the core system,
experiments and M9 workbench were completed. It is a bounded handover, not a new
research milestone. The agreed scope closes after all three stages pass; additional
features, datasets or paid experiments require a separate request.

## Stages

| Stage | Scope | Status |
| --- | --- | --- |
| 1 | Repository audit, justified cleanup and English/Chinese GitHub homepages | Complete; local validation recorded below |
| 2 | One shared browser interface with persistent Chinese/English selection | Pending |
| 3 | Targeted final review, fixes, full verification and delivery acceptance | Pending |

The current interface is Chinese. Bilingual homepages do not imply that interface
translation or the final review has already passed. Current accepted capabilities
and historical evidence remain in [status](status.md) and [roadmap](roadmap.md).

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

## Remaining review and acceptance

Stage 2 must centralize translations while preserving question/code/answer text,
paths, identifiers, model settings, monetary values and raw historical records.
Review static asset registration in `workbench/server.py`, package contents and
the corresponding tests/CI when adding translation assets. Language switching must
not call a model or implicitly approve generation.

Stage 3 will review import and static source handling, five-strategy previews,
frozen plans and paid confirmation, unknown-request handling, answer/citation
display, history reopening, and both interface languages. It must record issues
found and fixes, not just state that no problems were found.

Final verification includes the full offline test suite, lint/format, builds,
published-result checks and browser checks in both languages. Container checks
run locally when possible; otherwise record the limitation and the existing CI
coverage (`CPU container / base` and `CPU container / dense`, including installed
runtime and network-disabled smoke checks). Neither remote CI nor unavailable
local container execution may be reported as passed without evidence.

Known research limitations remain: provisional labels, heuristic static edges,
small exposed evaluation sets, negative retrieval results, incomplete semantic
score coverage and historical unknown costs. Model opinions and automatic source
checks do not establish human-reviewed correctness. These limitations do not add
new required research work to this delivery.
