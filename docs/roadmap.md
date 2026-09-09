# Development Roadmap

## Working agreement

Develop one milestone at a time. Keep delivered functionality working, add meaningful
tests, and update README and relevant documents. At completion, stop and report what
changed, why, principal files, validation, and a recommended commit message. The owner
commits and pushes. Do not begin the next milestone automatically.

At every milestone completion, provide complete copyable commands for reviewing,
staging, committing, and pushing changes. Verify the current branch and remote before
writing the push command; the owner executes these commands.

## Milestones and acceptance criteria

| Stage | Deliverable and acceptance | Suggested commit |
| --- | --- | --- |
| M1 — Foundation | Installable Python package, CLI help/version, tests, lint/format checks, Windows/Linux CI configuration, and design docs. Clean installation and build succeed. | `Initialize project tooling and architecture docs` |
| M2 — First search | Scan, AST extraction, source ranges, structural chunks, persistent index, BM25. Index a fixture and real pinned repository, restart, and return accurate paths/lines. Test exclusions, malformed files, identifiers, empty results. | `Add Python repository indexing and BM25 retrieval` |
| M3 — Evaluation | Versioned schema, approximately 40–60 source-bound questions across two real repositories, explicit provisional labels, metrics, runner and reports. Test metrics against hand calculations and reproduce rankings/quality scores. | `Add reproducible retrieval evaluation pipeline` |
| M4 — Baselines | Dense, hybrid, symbol-aware strategies with shared interfaces. Pin model and preprocessing, test interfaces offline, and run real-model comparisons on the same benchmark. | `Add dense hybrid and symbol-aware retrieval` |
| M5 — Structure MVP | Typed relations, bounded expansion, reranking, ablations. Trace evidence to seeds/edges; report successes, regressions, latency, context cost. | `Add structure-aware retrieval and ablations` |
| M6 — Formal experiments | Aim for 5–8 repositories and 150–250 source-bound questions plus one public subset. Freeze data/configuration and label provenance; report paired differences, uncertainty, category breakdowns and costs. | `Expand benchmarks and report retrieval tradeoffs` |
| M7 — QA | Bounded context, cited answers, automatic citation checks and LLM-assisted correctness/completeness/support evaluation. Freeze generation/judge settings and report real quality, failures and costs. | `Add repository QA with source citations` |
| M8 — Delivery | CPU Docker path, final docs, reports or dashboard, clean-environment reproduction. A reader can run indexing, search, QA with configured credentials, and evaluation. | `Package reproducible experiments and project documentation` |
| M9 — Interactive workbench | Extend the delivered research system into repository import, preparation, question comparison, saved history and a browser workflow; add same-model answer generation only after scoped approval. | Deliver in the M9a–M9c checkpoints below |

M1–M6 engineering and retrieval experiments are implemented: five strategies, eight
pinned repositories, 170 questions, 45 fixed runs, paired analyses, source traces
and construction/storage/peak-memory measurements. Labels remain provisional;
these scores describe agreement with the recorded sparse judgments. M6a/M6b also
provide optional manual-review tools, which do not gate completion.

M7a has an offline QA workflow, OpenAI adapter, frozen request preparation, automatic
citation checks and a fixed LLM scoring specification. M7b now implements combined
planning, common source references, generation/judge execution, durable records and
coverage/cost reporting. Its first real Mini/Mini experiment completed all 120
authorized calls, with 24 accepted judgments and 36 protocol failures. Raw evidence,
coverage and costs are preserved in the [live record](../reports/m7b-live/README.md).
M7c adds an [offline v2 protocol candidate](../reports/m7c/README.md), dynamic schemas
for exact saved answers, and replay diagnostics without new model calls.
M7d adds a [judge-only execution runtime](../reports/m7d/README.md) and read-only
saved-run verification. The separately approved [real v2 run](../reports/m7d-live/README.md)
is partial: a local interruption left 12 valid judgments, one unknown attempted
outcome and 47 requests not started. The planned 60-request comparison is unfinished.
M7e prepares a [separate follow-up scope](../reports/m7e/README.md) for those 47
unstarted requests, with offline checking, explicit approval and independent run
verification. Its implementation and proposal made no new API calls. The separately
approved [M7e live follow-up](../reports/m7e-live/README.md) completed all 47 attempts:
46 valid judgments and one protocol failure. Cumulative v2 coverage is 58 valid,
one invalid and one historical unknown, with zero requests left unstarted.
M8a supplies CPU Docker delivery; M8b supplies the validated results overview and
reproduction documentation. M8c adds the [project brief](project-brief.md), bilingual
CV wording and a [verified demonstration](demo.md) using the existing offline CLI
and saved live evidence. It adds no new model calls or retrieval-quality experiments.
Current acceptance uses automatic checks and explicitly
reported LLM assessment; independent human review is optional. See [status](status.md).
Remote CI runs after the owner pushes; local checks do not establish remote CI status.

The owner subsequently requested a complete interactive workflow. M9a supplies
the CLI foundation: source import, reusable resources, five context previews and
saved history. M9b adds local browser operation; same-model generated answers remain M9c.
This new product scope does not revise the completed research evidence or treat
context previews as generated answers. See [M9a validation](../reports/m9a/README.md)
and [M9b validation](../reports/m9b/README.md).

### M6 delivery sequence

- **M6a — Audit and review tooling:** validate recorded evidence, report paired
  differences and uncertainty with explicit limits, generate and check review bundles.
  Suggested commit: `Add paired experiment analysis and benchmark review workflow`.
- **M6b — Broader frozen data:** select additional licensed pinned repositories and
  a public subset; create source-grounded questions and repository-disjoint splits;
  preserve source/annotation provenance and publish versioned provisional labels.
  Automatically generated labels must not be presented as human-reviewed labels.
  The data/tooling checkpoint uses commit message
  `Expand repository benchmarks and add a pinned RepoQA subset`.
- **M6c — Formal experiment suite:** rerun all strategies and fixed ablations on the
  frozen expanded benchmark, measure scale/build/storage/peak-memory costs, and report
  paired tradeoffs and limitations. Preserve previous development results.
  The provisional data/tooling checkpoint uses commit message
  `Add frozen experiment matrix and retrieval cost profiling`; broader test outcomes
  are now exposed, so later tuning needs a new untouched test version.

Each is a coherent subgoal ending with checks and an owner commit/push checkpoint.
The M6 breadth target is met; sparse-label limitations remain part of every conclusion.

## MVP and final acceptance

M7 is delivered in checkpoints:

- **M7a — Offline QA and specification:** validate context/source identity, paths and
  line ranges; freeze the scoring, failure and reporting rules in the
  [LLM evaluation specification](llm-evaluation.md). No paid calls are required.
- **M7b — Live QA and LLM assessment:** the judge and combined experiment runner are
  implemented and tested offline. Estimate generation **plus judging** costs, present model choices and
  request limits, and obtain explicit owner approval before API calls. Record actual
  answers, automatic citation checks, LLM correctness/completeness/support assessments,
  usage, failures and latency. No synthetic response counts as a real experiment.
- **M7c — Offline judge protocol revision:** freeze v2 without changing v1 or its
  results. Prepare dynamic request schemas from saved answers and common references;
  make full evidence IDs, claim indices and abstention constraints explicit. Validate
  bundles and diagnose archived failures offline. No API calls or v2 execution path
  are part of this checkpoint. Suggested commit:
  `Add offline v2 judge protocol preparation and replay diagnostics`.
- **M7d — Judge-only runtime:** execute checked v2 requests over saved generations
  only after exact model/plan/budget approval. Preserve source cases, journal attempts
  and results, report new costs separately, and verify saved runs offline. Test
  approval failures, protocol failures, provider errors and unknown outcomes with
  offline doubles; make no paid calls in this implementation checkpoint. Suggested
  commit: `Add approved judge-only execution and saved-run verification`.
- **M7d live — Partial execution evidence:** preserve the approved v2 run's exact
  requests, raw known responses and all planned rows after interruption. Keep the
  unknown attempt and unstarted requests explicit, report known cost subtotals
  without inventing a full total, and verify the archive offline. Archive delivery
  does not complete the 60-request experiment or establish a strategy comparison.
- **M7e — Unstarted-request follow-up:** independently verify and freeze the original
  partial v2 run, then select only requests absent from its attempt journal. Preserve
  known and unknown prior outcomes; retain exact model, rubric and request payloads.
  Require a new plan fingerprint, approval and output directory for execution. Report
  historical, new and cumulative measurements separately, keeping unknown usage
  unknown. Test the workflow offline and publish a cost proposal before any calls.
  The first version allows one follow-up from an original revision run, without
  nested follow-ups or retrying prior attempts. Suggested commit:
  `Add bounded follow-up judging for unstarted requests`.
- **M7e live — Experiment closeout:** execute the separately approved 47-request
  scope, archive exact inputs and outputs, verify the saved follow-up offline and
  report historical/new/cumulative coverage. All 47 attempts produced records:
  46 valid judgments and one protocol failure. Preserve the historical unknown
  and unknown full cost. This completes the agreed attempts and evidence delivery,
  while incomplete score coverage remains a research limitation.

See the [M7b implementation record](../reports/m7b/README.md) and
[offline preparation commands](qa.md#prepare-and-check-the-combined-experiment).

The prior 60-request estimate covers generation only; it is not an approved combined
budget. The later Mini/Mini approval covered one completed US$5.63-budget run.
The subsequent US$2.20 approval covered at most 60 v2 Mini judgments over existing
answers; only 13 attempts were journaled before the partial run stopped.
The separate US$1.80 approval covered the 47 previously unstarted Mini judgments;
all 47 now have recorded outcomes, without retrying any prior attempt.
LLM scores must be labeled as model assessments,
with unknown or failed cases explicit, not verified true correctness rates.

The owner deferred live API calls after M7a. **M8a** delivered base and CPU Dense
containers, reproducible delivery checks and usage documentation. **M8b** consolidated
recorded evidence and project presentation, including an automatically checked
overview and a dedicated reproduction guide. These checkpoints did not close M7b.
M7b now supplies the first live results and updates the findings and acceptance
matrix. Its 40% judge acceptance rate prevents a strong QA comparison. M7c completes
the offline, versioned protocol revision; it does not establish improved live reliability.
M7d implements bounded judge-only execution and saved-run verification over the saved
answers. Its implementation tests make no API calls. The subsequent approved live
run yielded 12 valid judgments from the ordered prefix, one unknown attempted
outcome and 47 requests not started. Its known cost subtotal is US$0.08424075; full
cost remains unknown. Preserve this partial evidence alongside v1. Additional paid
attempts require an explicitly scoped decision; there is no automatic retry or resume.
M7e implements that separate decision path for the 47 unstarted requests and leaves
all 13 prior attempts untouched. Its live follow-up produced 46 valid judgments and
one protocol failure, bringing cumulative accepted coverage to 58/60. New-batch
cost is US$0.35257875 and cumulative known judging cost is US$0.4368195 at frozen
uncached rates. The historical unknown keeps full cumulative usage/cost unknown.
The original engineering and experiment attempts are delivered; a missing historical
outcome and optional human review do not require indefinite additional milestones.
The existing combined runner remains v1. Incomplete score coverage and provisional
labels remain limitations, and delivery does not prove Structure improves answers.

M1–M5 define the implemented retrieval MVP: Python parsing/indexing, five strategies,
a versioned source-bound benchmark with explicit provisional labels, reproducible
evaluation, CLI, tests, CI and result tables. QA, broader experiments and Docker are
also required for the full project. Optional manual review may improve future data;
it is not a prerequisite for either MVP or final acceptance.

The original retrieval MVP excludes web dashboards, embedding training, learned/cross-encoder rerankers,
graph neural networks, multiple languages, exact whole-program analysis, incremental indexing, and
distributed services. The later M9 scope explicitly adds a browser interface;
the other exclusions remain in place. Add complexity only for a demonstrated need.

The final project must allow a reader to install it, retrieve source evidence, and
reproduce the main quality metrics using fixed data/model/configuration versions.
Contextualize hardware-dependent latency. Include strategy and relationship ablations,
source-grounded QA, automated tests, CI, Docker, and full documentation. Conclusions
must include failures and costs; a positive improvement is not required, but
defensible evidence is.

## M8c — Presentation closeout

The original engineering and planned experiment scope is complete. This presentation
checkpoint connects it to the original application-portfolio goal: a concise
project brief, English/Chinese CV templates with evidence links, and a five-minute
PowerShell walkthrough. The demonstration separates synthetic software checks from
saved real retrieval results and model assessments; it does not turn fixture
scores or protocol acceptance into accuracy claims.

Acceptance: execute the documented offline commands, inspect the archived answer
and citations, check local document links, and retain the provisional-label and
negative-result limits. Record successful and failed rehearsals in the
[M8c validation record](../reports/m8c/README.md). No new service, dependency, model
call or benchmark version is required. Suggested commit:
`Add project brief and verified offline demonstration`.

Further research, features or detailed architecture teaching are separate follow-up
work, rather than automatic additional milestones needed to declare completion.

## M9 — Interactive repository workbench

The owner requested this extension after research and presentation delivery.
Reuse the existing parser, indexes, retrieval strategies, context packing and QA
adapter. A user should import a repository, prepare its resources, ask a question,
compare strategies and reopen the same saved results. Preserve the fixed research
benchmarks and historical experiment artifacts; ad hoc repository questions are
unlabeled unless separately included in a versioned evaluation dataset.

- **M9a — CLI foundation, implemented:** import current local Python files or a
  public HTTPS Git snapshot with recorded source identity. Prepare and reuse
  version-bound indexes, vectors and relations. Save all five context previews
  under common question/context settings, keeping each strategy's failures and
  timings visible. Reopen self-contained history without repeating retrieval.
  No target code, dependency installation or model API call is executed. Public
  imports need network; model weights must already be prepared locally. Context
  previews contain source evidence, not generated answers or measured relevance.
  Acceptance checks and observed runs are in the
  [M9a record](../reports/m9a/README.md). Suggested commit:
  `Add repository workbench imports and five-strategy previews`.
- **M9b — Browser workflow, implemented:** expose the same services through a
  loopback-only standard-library HTTP server and local HTML/CSS/JavaScript. Show
  import/preparation state, accept a question, compare the five strategy contexts
  side by side, expand source lines, surface failures and reopen saved history.
  Run one background job at a time and retain state without automatic resume.
  Keep the CLI path and avoid model downloads or API calls from the browser.
  Acceptance covers the browser flow, offline server tests, packaged assets and
  existing checks; observed outcomes are in [M9b validation](../reports/m9b/README.md).
  Suggested commit: `Add local browser workflow for five-strategy context comparison`.
- **M9c — Same-model answer comparison, pending:** freeze one answer-model
  configuration and shared generation limits across the five retrieval contexts.
  Produce a reviewable estimate for generation and any planned judging, with a
  bounded request scope before paid execution. Execute only after model/budget
  approval. Save actual answers,
  automatic citation checks, token usage, estimated cost, latency and failures.
  Keep LLM-assisted semantic scores separately labeled if judging is included;
  never infer true accuracy from model scores or valid citation locations.

The original research deliverables remain complete. The new full product workflow
requires M9c as well as the delivered M9a/M9b foundation; a browser context preview
does not satisfy browser-based answer comparison. Complete each checkpoint,
validate existing behavior and stop for the owner's commit/push before proceeding.

## Deferred decisions

M4 uses pinned MiniLM on CPU and records vector size, construction time and quality;
M6c adds peak-memory profiling. Larger code-specialized encoders remain future experiments.
The expanded snapshot/annotation choices are recorded in [the benchmark protocol](benchmarks.md).
Introduce ANN only if M6 measurements justify it. M7 uses OpenAI Responses at the
owner's request; generation/judge model snapshots and the combined experiment budget
require explicit approval before live calls.
