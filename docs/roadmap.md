# Development Roadmap

## Working agreement

The original research system, M9 interactive workflow and three final handover
stages are delivered. Stop within the agreed scope. Do not add feature or research
milestones automatically; further work requires a separate request.

The separately requested [FastAPI/Uvicorn HTTP migration](http-migration.md)
replaces browser routing and server transport for readability, preserving CLI,
service logic, safeguards and stored records. It is bounded maintenance after
delivery, not a new research or paid-experiment milestone. Historical M9 and
handover records below retain their original implementation and checks.

Develop one agreed stage at a time. Keep existing functionality and historical
result reading compatible, add meaningful checks, and update relevant documents.
At each checkpoint, report changes and reasons, principal files, validation,
limitations, the next agreed stage and a recommended commit message. Verify the
actual branch and remote, then provide complete PowerShell review/add/commit/push
commands. The owner commits and pushes; do not rewrite Git history.

Paid work requires a separately reviewed model, request limit, generation-plus-judge
estimate and explicit budget approval. Existing approvals do not authorize new
questions, experiments or retries. Offline tests and saved archives are the default
handover validation inputs.

## Final handover plan

| Stage | Deliverable and acceptance | Status |
| --- | --- | --- |
| 1 — Audit, cleanup and bilingual GitHub presentation | Check actual code/document references before removal; consolidate current explanations; align English `README.md` and Chinese `README.zh-CN.md` with working startup/navigation and unchanged evidence | Complete; local checks recorded |
| 2 — Bilingual browser interface | One shared interface/business flow with centralized English/Chinese messages, visible switching, persisted preference and documented fallback; translate important states and payment/error wording without modifying user content or making model calls | Complete; local tests and bilingual browser checks recorded |
| 3 — Final review and delivery | Review import → preparation → preview → approval → answers → citations → history in both languages; fix findings and record full tests, lint, formatting, build, result validation and browser checks; execute container checks when available and state actual limits | Complete; full local validation and remaining limits recorded |

Completion requires clear repository navigation, consistent bilingual homepages and
UI, preserved core behavior and experimental evidence, and a recorded final review.
[The delivery record](delivery.md) owns the audit findings and actual check results.
Do not declare localization or final review complete before its checks run. Preserve
user snapshots, caches, API configuration and workbench history throughout cleanup.
Frozen benchmarks, configurations, raw responses, source information, licenses and
reproduction files are evidence, not ordinary unused content.

Stage 2 centralizes messages in one packaged `i18n.js` catalog. Its acceptance
covers saved-choice priority, browser-language default, invalid-preference and
storage-failure handling, English/key fallback, and translated operational states.
Switching must only redraw local state: questions, source, answers and raw records
stay intact, as do edited budgets and current consent. It cannot trigger a request
or supply approval. The existing consent reset when reopening a plan remains.
These interface checks do not replace the separate Stage 3 final workflow review.

## Milestones and acceptance criteria

This table records the completed development route. Detailed historical validation
and exact experiment outcomes remain in their linked records; [status](status.md)
owns current acceptance and [RESULTS](../RESULTS.md) owns the findings summary.

| Stage | Delivered capability | Primary documentation/evidence |
| --- | --- | --- |
| M1 — Foundation | Python package, Typer CLI, tests, lint/format, Windows/Linux CI and design | [Architecture](architecture.md), [reproduction](reproduction.md) |
| M2 — First search | Static Python discovery/AST extraction, symbols/chunks/ranges, SQLite persistence and BM25 | [M2 validation](validation/m2.md) |
| M3 — Evaluation | Versioned source-bound benchmark, explicit provisional labels, metrics and saved reports | [Evaluation](evaluation.md) |
| M4 — Baselines | Pinned Dense, Hybrid and Symbol-aware strategies sharing the retrieval interface | [Baselines](baselines.md), [M4](../reports/m4/README.md) |
| M5 — Structure MVP | Typed relations, bounded expansion/reranking, provenance and ablations | [Structure](structure.md), [M5](../reports/m5/README.md) |
| M6 — Formal experiments | Broader frozen data, source/split audits, paired comparisons, ablations and construction/storage/memory measurements | [Benchmarks](benchmarks.md), [M6c](../reports/m6c/README.md) |
| M7 — Repository QA and assessment | Bounded cited contexts, automatic source checks, explicit paid planning, live generations and separately versioned model assessments | [QA](qa.md), [LLM evaluation](llm-evaluation.md) |
| M8 — Packaging and presentation | CPU containers, validated result overview, reproduction guide, project brief and offline demonstration | [Docker](docker.md), [overview](../reports/overview/report.md), [M8c](../reports/m8c/README.md) |
| M9 — Interactive workbench | Local/public-HTTPS import, resource preparation, five-strategy previews, explicit same-model generation, browser comparison and saved history | [Workbench](workbench.md), [M9c live acceptance](../reports/m9c-live/README.md) |

### M6 delivery sequence

- **M6a:** source audits, paired analyses and optional manual-review tools.
- **M6b:** licensed pinned snapshots, broader provisional labels, separate dataset
  roles and a public RepoQA adaptation. See [benchmark provenance](benchmarks.md).
- **M6c:** frozen strategy/ablation matrix, scale measurements, source-traced
  successes and regressions. The breadth target was met; sparse labels remain a
  limitation. Exposed outcomes require a new untouched test version for future tuning.

## MVP and final acceptance

The delivered retrieval MVP includes Python parsing/indexing, five strategies,
versioned provisional benchmarks, reproducible evaluation, CLI, tests and CI.
The full agreed project adds QA, broader experiments, Docker, documentation and
the M9 browser workflow. The final handover adds bilingual access and review.

M7 was delivered through the following checkpoints:

| Checkpoint | Scope and retained evidence |
| --- | --- |
| [M7a](../reports/m7a/README.md) and [offline closeout](../reports/m7a-offline/README.md) | Offline QA, source validation, request preparation and scoring specification; no paid calls |
| [M7b implementation](../reports/m7b/README.md) and [v1 live run](../reports/m7b-live/README.md) | Combined generation/judging runtime and approved real experiment; retain all original answers, accepted judgments and protocol failures |
| [M7c](../reports/m7c/README.md) | Separate v2 protocol, exact-answer dynamic schemas and offline replay diagnostics; no rewriting v1 |
| [M7d runtime](../reports/m7d/README.md) and [partial live record](../reports/m7d-live/README.md) | Approved judge-only execution; preserve the interrupted batch, one historical unknown and its unstarted requests |
| [M7e tooling](../reports/m7e/README.md) and [live follow-up](../reports/m7e-live/README.md) | Separately approved execution of only those unstarted requests; all planned attempts are complete, while invalid/unknown coverage and unknown full cumulative cost remain |

The combined runner retains v1 semantics; judge-only v2 is a separate protocol.
Compatibility code and regression tests for these routes remain necessary.
Protocol acceptance is not true correctness. Human review is optional, and neither
recovery of the historical unknown nor a positive Structure result gates completion.
Exact coverage, dimension denominators and costs belong in
[RESULTS](../RESULTS.md) and the linked immutable experiment records.

## M8c — Presentation closeout

[The M8c record](../reports/m8c/README.md) preserves the verified offline demonstration,
including its earlier failed rehearsals. The [project brief](project-brief.md) and
[demo](demo.md) remain useful for research presentation. The current interactive
entry point is [the workbench guide](workbench.md). New bilingual homepages and UI
are part of the final handover rather than new research evidence.

## M9 — Interactive repository workbench

- **[M9a — Foundation](../reports/m9a/README.md):** copy selected local Python files
  or public HTTPS Git blobs into source-bound snapshots; prepare reusable indexes,
  vectors and graphs; save five context previews with independent failures and timing.
  Read history without rerunning retrieval. Never execute target code or dependencies.
- **[M9b — Browser](../reports/m9b/README.md):** expose the same services through a
  loopback standard-library HTTP server and packaged browser assets. Show progress,
  side-by-side source evidence, provenance and history; run one background job at a
  time without automatic resume.
- **[M9c — Answers](../reports/m9c/README.md):** freeze the exact model, context and
  requests, show total estimates and require explicit approval. Generate at most
  five answers per plan with no automatic judge, journal each attempt once, and
  preserve partial/unknown outcomes. History and citations use saved records.
- **[M9c live acceptance](../reports/m9c-live/README.md):** five approved generation
  requests produced five answers. Browser citations, saved history, restart and
  offline archive replay were checked. This is one unlabeled workflow acceptance
  case, not an answer-quality benchmark or continuing paid-call authorization.

## Deferred decisions

Private-repository authentication, additional programming languages, coding-agent loops, model
training, learned rerankers, graph neural networks, exact whole-program analysis,
incremental indexing, ANN/distributed services and new benchmark versions remain
outside this agreement. Larger code encoders, evaluator calibration and independent
review are optional extensions with separately defined scope and evidence.

A reader must be able to install the project, retrieve source evidence and reproduce
recorded quality results from fixed versions. Interpret timings with their hardware
limits; keep failures, unknown outcomes and negative results visible. After the
three handover stages pass, mark the agreed delivery complete and end this round.
