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

M1–M6 engineering and retrieval experiments are implemented: five strategies, eight
pinned repositories, 170 questions, 45 fixed runs, paired analyses, source traces
and construction/storage/peak-memory measurements. Labels remain provisional;
these scores describe agreement with the recorded sparse judgments. M6a/M6b also
provide optional manual-review tools, which do not gate completion.

M7a has an offline QA workflow, OpenAI adapter, frozen request preparation and durable
execution records, shared offline citation checks and a frozen
LLM scoring specification. M7b's live answer comparison and LLM judge are not yet
implemented as a combined evaluation workflow and have no real experimental scores.
M8a supplies CPU Docker delivery; M8b supplies the validated results overview and
reproduction documentation. Current acceptance uses automatic checks and explicitly
reported LLM assessment; independent human review is optional. See [status](status.md).
Remote CI runs after the owner pushes; local checks do not establish remote CI status.

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

M7 is delivered in two checkpoints:

- **M7a — Offline QA and specification:** validate context/source identity, paths and
  line ranges; freeze the scoring, failure and reporting rules in the
  [LLM evaluation specification](llm-evaluation.md). No paid calls are required.
- **M7b — Live QA and LLM assessment:** implement the judge and combined experiment
  runner. Estimate generation **plus judging** costs, present exact model choices and
  request limits, and obtain explicit owner approval before API calls. Record actual
  answers, automatic citation checks, LLM correctness/completeness/support assessments,
  usage, failures and latency. No synthetic response counts as a real experiment.

The prior 60-request estimate covers generation only; it is not an approved combined
budget. Live calls remain deferred. LLM scores must be labeled as model assessments,
with unknown or failed cases explicit, not verified true correctness rates.

The owner deferred live API calls after M7a. **M8a** delivered base and CPU Dense
containers, reproducible delivery checks and usage documentation. **M8b** consolidated
recorded evidence and project presentation, including an automatically checked
overview and a dedicated reproduction guide. These checkpoints did not close M7b.
Once the remaining live evaluation is completed, update the findings and acceptance
matrix in a separate checkpoint. Engineering delivery must not be presented as proof that
structure-aware retrieval improves answer quality.

M1–M5 define the implemented retrieval MVP: Python parsing/indexing, five strategies,
a versioned source-bound benchmark with explicit provisional labels, reproducible
evaluation, CLI, tests, CI and result tables. QA, broader experiments and Docker are
also required for the full project. Optional manual review may improve future data;
it is not a prerequisite for either MVP or final acceptance.

The MVP excludes web dashboards, embedding training, learned/cross-encoder rerankers,
graph neural networks, multiple languages, exact whole-program analysis, incremental indexing, and
distributed services. Add complexity only for a demonstrated need.

The final project must allow a reader to install it, retrieve source evidence, and
reproduce the main quality metrics using fixed data/model/configuration versions.
Contextualize hardware-dependent latency. Include strategy and relationship ablations,
source-grounded QA, automated tests, CI, Docker, and full documentation. Conclusions
must include failures and costs; a positive improvement is not required, but
defensible evidence is.

## Deferred decisions

M4 uses pinned MiniLM on CPU and records vector size, construction time and quality;
M6c adds peak-memory profiling. Larger code-specialized encoders remain future experiments.
The expanded snapshot/annotation choices are recorded in [the benchmark protocol](benchmarks.md).
Introduce ANN only if M6 measurements justify it. M7 uses OpenAI Responses at the
owner's request; generation/judge model snapshots and the combined experiment budget
require explicit approval before live calls.
