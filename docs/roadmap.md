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
| M3 — Evaluation | Versioned schema, approximately 40–60 reviewed questions across two real repositories, metrics, runner, JSON/CSV and Markdown reports. Test metrics against hand calculations and reproduce rankings/quality scores. | `Add reproducible retrieval evaluation pipeline` |
| M4 — Baselines | Dense, hybrid, symbol-aware strategies with shared interfaces. Pin model and preprocessing, test interfaces offline, and run real-model comparisons on the same benchmark. | `Add dense hybrid and symbol-aware retrieval` |
| M5 — Structure MVP | Typed relations, bounded expansion, reranking, ablations. Trace evidence to seeds/edges; report successes, regressions, latency, context cost. | `Add structure-aware retrieval and ablations` |
| M6 — Formal experiments | Aim for 5–8 repositories and 150–250 reviewed questions plus one public subset. Freeze held-out data; report paired differences, uncertainty, category breakdowns, scale costs. Quality takes precedence over target counts. | `Expand benchmarks and report retrieval tradeoffs` |
| M7 — QA | Context budget, model adapter, cited answers, reviewed answer-evaluation cases. Compare strategies using a fixed LLM/prompt; assess citation validity separately from support. | `Add repository QA with source citations` |
| M8 — Delivery | CPU Docker path, final docs, reports or dashboard, clean-environment reproduction. A reader can run indexing, search, QA with configured credentials, and evaluation. | `Package reproducible experiments and project documentation` |

M1 and M2 are complete, with M1–M6c CI reported passing by the owner. M3's evaluation
pipeline and 40-query source-checked seed are implemented; **independent human label
review remains pending**. The seed and its reports remain provisional until that
acceptance item is completed. M4 adds three retrieval baselines, persistent vectors,
offline tests and real-model comparisons. M5 adds relation extraction, bounded structure
reranking, 13 fixed comparison configurations and source/cost traces. M6a adds paired
repository-cluster analysis, verification of saved results and a frozen relevance pool
with manual-review templates. Its 845 candidate pairs are not 845 labeled questions:
that seed still has 40 provisional queries. M6b adds 120 source-checked draft questions
on five disjoint test-candidate repositories, plus ten adapted RepoQA Marshmallow
questions on a separate eighth repository. Generation, provenance, split audits and
source review bundles are implemented without scoring the new datasets. **Independent
review/adjudication remains outstanding**, so M6b's reviewed-label acceptance is not
complete. M6c adds the fixed 45-run matrix and construction/storage/peak-memory
profiling with explicit provisional-label opt-in. Its engineering checkpoint does
not complete independent review or reviewed-label reruns. M7a adds bounded source
context, OpenAI Responses integration, cited answers, frozen QA request preparation,
durable execution records and manual-review validation. M7b's real API comparison
and independent answer review remain pending; the prepared cases are provisional.
M8 remains planned, and human label review still gates claims of a reviewed MVP.
New remote CI runs after the owner
pushes; local checks cannot establish remote CI status.

### M6 delivery sequence

- **M6a — Audit and review tooling:** validate recorded evidence, report paired
  differences and uncertainty with explicit limits, generate and check review bundles.
  Suggested commit: `Add paired experiment analysis and benchmark review workflow`.
- **M6b — Broader frozen data:** select additional licensed pinned repositories and
  a public subset; create source-grounded questions and repository-disjoint splits;
  complete independent review/adjudication and publish versioned labels. Do not
  substitute automatically generated labels for completed human review.
  The data/tooling checkpoint uses commit message
  `Expand repository benchmarks and add a pinned RepoQA subset`; review acceptance
  is tracked separately and must not be inferred from passing CI.
- **M6c — Formal experiment suite:** rerun all strategies and fixed ablations on the
  frozen expanded benchmark, measure scale/build/storage/peak-memory costs, and report
  paired tradeoffs and limitations. Preserve previous development results.
  The provisional data/tooling checkpoint uses commit message
  `Add frozen experiment matrix and retrieval cost profiling`; broader test outcomes
  are now exposed, so later tuning needs a new untouched test version.

Each is a coherent subgoal ending with checks and an owner commit/push checkpoint.
The original M6 breadth and quality targets remain unchanged.

## MVP and final acceptance

M7 is delivered in two coherent checkpoints: **M7a** implements and validates QA
engineering offline; **M7b** runs the reviewed request bundle with an explicitly
approved model/budget, records real provider outputs/costs and completes independent
answer/citation review. No simulated provider output counts as a real experiment.

M1–M5 deliver the retrieval MVP: Python parsing/indexing, five strategies, a small
reviewed benchmark, reproducible evaluation, CLI, tests, CI, and result tables.
QA, broader experiments, and Docker remain required for the full project.

The MVP excludes web dashboards, embedding training, rerankers, graph neural networks,
multiple languages, exact whole-program analysis, incremental indexing, and
distributed services. Add complexity only for a demonstrated need.

The final project must allow a reader to install it, retrieve source evidence, and
reproduce the main quality metrics using fixed data/model/configuration versions.
Contextualize hardware-dependent latency. Include strategy and relationship ablations,
source-grounded QA, automated tests, CI, Docker, and full documentation. Conclusions
must include failures and costs; a positive improvement is not required, but
defensible evidence is.

## Deferred decisions

M4 uses pinned MiniLM on CPU and records vector size, construction time and quality;
larger code-specialized encoders and peak-memory profiling remain future experiments.
The expanded snapshot/annotation choices are recorded in [the benchmark protocol](benchmarks.md).
Introduce ANN only if M6 measurements justify it. M7 uses OpenAI Responses at the
owner's request; the model snapshot and experiment budget require explicit selection.
