# Project Status and Acceptance

**The agreed project scope and final three-stage handover are complete.** This
includes the core research system, planned experiment attempts, M9 local browser
workflow, repository cleanup, bilingual homepages/interface and final local review.
Remaining research and platform limitations are recorded, not hidden. No new
research or feature milestone is required; Git publication remains the owner's step.

Use [RESULTS](../RESULTS.md) for experimental findings and their limitations,
[the workbench guide](workbench.md) for current operation, and [the roadmap](roadmap.md)
for delivered stages. [Final delivery](delivery.md) records the handover audit and
actual checks. Historical reports retain their original measurements, decisions and
checkpoint-specific validation.

## Acceptance matrix

| Area | Delivered and observed | Boundaries retained |
| --- | --- | --- |
| Python repository parsing | AST symbols and ranges, structural chunks, exclusions, SQLite indexes bound to source snapshots | Python only; static analysis cannot resolve all dynamic behavior |
| Retrieval | BM25, pinned Dense embeddings, Hybrid, Symbol-aware and bounded Structure-aware retrieval; persistent vectors and typed relations | No claim that the frozen full Structure heuristic improves aggregate quality |
| Retrieval evaluation | Recall, Precision, MRR, NDCG, latency, saved rankings, fingerprints, paired comparisons and fixed ablations | Sparse provisional labels measure agreement with recorded judgments; exposed test outcomes cannot become untouched tuning data |
| Benchmark and systems measurements | Eight pinned repositories, 170 questions in separate roles, 45 retrieval runs and 24 construction measurements | Selected repositories and one interactive host do not establish general performance or production guarantees |
| Repository QA and assessment | Cited answers, automatic source checks, frozen generation/judge protocols, durable request records, failure/unknown handling and offline archive verification | Source validity is not semantic correctness; LLM scores are model assessments, not human review or true accuracy |
| Recorded QA experiments | Original generations and v1 judgments preserved; all planned v2 attempts completed across two approved batches | One invalid v2 judgment and one historical unknown remain; full cumulative v2 cost and complete score coverage are unknown |
| M9 local workflow | Import a local repository or public HTTPS Git snapshot, prepare resources, preview five strategies, explicitly approve same-model answers, inspect citations and reopen history | Loopback-only, single user, one background job at a time; no automatic model downloads or paid calls |
| M9 live acceptance | Five approved requests returned five answers; browser citations, history, restart and archived replay checked | One unlabeled question establishes workflow operation, not answer quality or a strategy ranking |
| Packaging and automation | Installable package, automated tests, Windows/Linux CI, base/CPU Dense Docker targets and offline smoke checks | Local checkpoint evidence and remote CI are separate; neither is inferred for uncommitted changes |
| Project presentation | Evidence-linked findings, reproduction guide, architecture, project brief, bilingual homepages/interface, bilingual CV wording and offline demonstration | Detailed technical guides and historical reports remain English where indicated |

## Final handover

| Stage | Scope | Current state |
| --- | --- | --- |
| 1 — Repository audit and GitHub presentation | Audit references and entry points; make evidence-backed cleanup; provide aligned English and Chinese homepages; consolidate current status/navigation | Complete; local checks in the delivery record |
| 2 — Bilingual browser interface | Shared English/Chinese catalog, visible switch, saved preference and documented fallback; preserve source/questions/answers, raw records and all paid-call safeguards | Complete; local tests and bilingual browser checks in the delivery record |
| 3 — Final review and delivery | Review the complete workflow and boundaries, fix findings, run full tests/lint/format/build/result checks and browser checks; record container checks or their limits | Complete; local full-suite, archive, browser and both CPU container checks recorded |

All three stages have been verified with remaining limits recorded in
[the delivery record](delivery.md). The owner reviews, commits and pushes the final
changes; remote CI for that commit is distinct from recorded local validation.
Stop within the agreed scope: further features, research or paid experiments are
optional, separately requested work.

Stage 2 uses a single page with an **Interface language / 界面语言** selector. Valid saved choices
take priority; the first browser language selects Chinese for a `zh` prefix and
English otherwise. Storage failure does not prevent switching within the page.
The switch performs a local redraw, preserving raw content, edited budgets and
current consent without issuing requests. Reopening a plan still resets consent.
Missing messages fall back to English, then their key. See [the workbench guide](workbench.md)
for operation and [the delivery record](delivery.md) for checkpoint-specific checks.

## Verified checkpoints

The linked records are the primary sources for exact counts, prices, fingerprints,
commands and validation logs. This page does not repeat their historical CI claims
as current CI status.

| Evidence | What it establishes |
| --- | --- |
| [M6c experiment matrix](../reports/m6c/README.md), [generated overview](../reports/overview/report.md) | Frozen retrieval comparisons, negative and positive findings, ablations, construction costs and read-only verification of 45 saved runs |
| [M7a offline QA](../reports/m7a/README.md), [offline closeout](../reports/m7a-offline/README.md) | Context/source validation and frozen evaluation preparation without paid inference |
| [M7b implementation](../reports/m7b/README.md), [v1 live experiment](../reports/m7b-live/README.md) | Combined planning/runtime and the original live generations/judgments, including rejected judgments |
| [M7c protocol revision](../reports/m7c/README.md), [M7d runtime](../reports/m7d/README.md) | Separate v2 schemas, offline replay diagnostics and approved judge-only execution |
| [M7d partial live run](../reports/m7d-live/README.md) | The immutable interrupted run: known results, one unknown attempt and requests not started at that checkpoint |
| [M7e follow-up tooling](../reports/m7e/README.md), [live follow-up](../reports/m7e-live/README.md) | Execution of only the previously unstarted requests; cumulative coverage retains the invalid judgment and historical unknown |
| [M8a containers](../reports/m8a/README.md), [M8c presentation](../reports/m8c/README.md) | Observed CPU container checks and verified offline demonstrations; synthetic checks are not research scores |
| [M9a foundation](../reports/m9a/README.md), [M9b browser](../reports/m9b/README.md) | Imports, resource reuse, five context previews, source/provenance inspection and saved history |
| [M9c implementation](../reports/m9c/README.md), [M9c live acceptance](../reports/m9c-live/README.md) | Frozen plans, explicit approval, durable same-model answers, source citations, measured usage and replayable real-answer archives |

## Interactive workflow acceptance

M9a–M9c implement the agreed path: import a Python repository, freeze its source,
prepare resources, preview five strategies, review the fixed-model plan, explicitly
approve generation, compare answers/citations and reopen saved history. The
[M9c live record](../reports/m9c-live/README.md) supplements offline tests with five
actual provider responses. Reopening history or restarting the server did not
trigger another request. The handover improves access and presentation of that
existing workflow; it does not replace its implementation or rewrite its evidence.

Every new paid generation or judging scope needs its own reviewed model, request
limit, total estimate and explicit budget approval. Prior experiment approvals grant
no continuing authorization. Default context previews and saved-result inspection
make no model calls. Unknown attempts are not retried automatically; missing usage
and cost remain unknown rather than zero.

## Recommended research follow-up

The following are optional extensions, not remaining handover requirements.

All relevance labels remain **provisional**. Automatic citation/source checks
establish identity and locations, not semantic support. Model correctness,
completeness and citation-support scores remain separate from those checks and
must not be called human review or true accuracy. Preserve invalid judgments,
unknown outcomes, sparse-label limits and negative retrieval findings.

New untouched benchmarks, evaluator calibration, independent review and other
models may improve future evidence. Existing [manual-review tools](review.md) remain
available; historical references to required human review do not override the
current optional policy.
