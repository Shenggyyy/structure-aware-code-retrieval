# Project Status and Acceptance

The repository provides an operational retrieval/evaluation system and a two-stage
QA/LLM-assessment runtime. **The first authorized live experiment finished all 120
requests with 36 invalid judge outputs.** Core implementation and the first evidence
set are delivered; judge coverage is insufficient for a reliable QA-quality ranking.
M7c supplies an offline v2 protocol candidate with per-answer schemas and archived
failure diagnostics. M7d adds judge-only execution and saved-run verification. Its
separately approved live run stopped after 13 attempts: 12 valid judgments, one
unknown outcome and 47 requests not started. The known judging cost subtotal is
US$0.08424075; the complete cost is unknown. This ordered Click-only prefix does not
complete the planned comparison or establish improved general judge reliability.
M7e adds offline preparation, approved execution and verification for a separate
follow-up covering only the 47 unstarted requests. No new calls were made in this
checkpoint; the observed v2 results remain 12 valid judgments and one unknown outcome.
Human or independent review is optional, not a completion prerequisite. Existing
labels remain provisional; automatic checks and model judgments must be described
according to what they actually measure.

## Acceptance matrix

| Area | Implemented and observed | Remaining acceptance |
| --- | --- | --- |
| Python repository parsing | Source discovery, AST symbols/ranges, structural chunks, exclusion diagnostics; SQLite indexes bind to source snapshots | Additional languages and exact dynamic analysis are outside the current scope |
| Retrieval | BM25, pinned dense embeddings, Hybrid, Symbol-aware, and bounded Structure-aware retrieval; persistent vectors and typed relation graphs | No claim that the frozen full Structure heuristic improves aggregate quality |
| Retrieval evaluation | Recall, Precision, MRR, NDCG, latency; saved rankings, query metrics, fingerprints, paired comparisons and fixed ablations | Retain sparse-label coverage limits; label changes require a new version and reruns |
| Benchmark breadth | Eight pinned repositories, 170 queries across separate development/test/public roles; source and split audits | Labels remain provisional; exposed test outcomes require a new untouched test version for future tuning |
| Systems measurements | 45 completed retrieval runs and 24 construction measurements, storage and worker peak memory | Measurements describe one interactive host, not production service guarantees |
| Repository QA | 60 live generations: 48 answers, 12 abstentions; all source audits and applicable citation ID checks passed | Automatic checks establish location/identity, not semantic truth |
| QA experiment | Twelve provisional development cases × five strategies; 120 authorized calls, complete raw archive, known usage for every call | Small development scope and same-model generator/judge limit generalization; usage-based cost is not an invoice |
| LLM evaluation | 24 accepted v1 judgments, 36 protocol failures; v2 runtime and a partial live run with 12 valid judgments, one unknown outcome and 47 not-run requests; follow-up tooling for unstarted requests | The planned comparison remains incomplete; the follow-up requires new approval and is prepared offline, with no new model outcomes or permission to retry the unknown attempt |
| Packaging and testing | Installable package, automated tests, base/CPU Dense Docker targets, offline smoke checks, Windows/Linux CI configuration | Current checkpoint's remote CI runs after the owner commits and pushes |
| Project presentation | Retrieval analysis, live QA failure analysis, raw evidence, offline saved-run verification and reproduction instructions | Retain limits and version future protocol/dataset changes |

## Verified checkpoints

- [M6c](../reports/m6c/README.md) records the frozen experiment matrix, negative and
  positive observations, construction costs, and repeatability checks. The primary
  Structure heuristic lowers aggregate NDCG@10 on expanded test candidates.
- [M7a](../reports/m7a/README.md) records offline QA preparation. The owner explicitly
  deferred live calls; test doubles are software validation, not LLM experiments.
- [M7a offline closeout](../reports/m7a-offline/README.md) verifies all sixty prepared
  requests under the revised route and freezes the LLM scoring specification.
  Final local checks: 540 tests passed, one Windows symlink test skipped, 91.80%
  combined statement/branch coverage; Ruff and distribution builds pass. No live
  generation or judging calls were made. Labels remain provisional.
- [M7b implementation](../reports/m7b/README.md) adds the combined plan, read-only
  validator, approved execution path and separate quality/usage reporting. Validation
  uses offline test doubles; it does not establish real LLM performance. Local checks:
  660 tests passed, one Windows symlink test skipped, 91.24% combined statement/branch
  coverage. The owner reports the preceding M7a closeout passed GitHub CI; this
  checkpoint's remote CI remains pending the owner's commit and push.
- [M8a](../reports/m8a/README.md) records actual CPU container builds, network-disabled
  smoke checks, pinned-model loading, and 493 passing host tests with one skip.
- The owner reports M8a's GitHub CI passed. This is distinct from locally observed
  checks and does not establish CI success for the current uncommitted checkpoint.
- [The generated overview](../reports/overview/report.md) consolidates saved retrieval
  evidence; it does not generate new retrieval or QA outcomes.
- M8b local validation: 515 tests passed and one Windows symlink-privilege test
  skipped; combined statement/branch coverage was 92%. Ruff lint/format checks and
  offline wheel/source-distribution builds passed. The overview's 22 new tests cover
  evidence/configuration/model mismatches and stale output.
- The same 45-run overview passed `--check` on Windows and in the newly built Linux
  base image (`sacr:base-m8b`) with networking disabled, a read-only root filesystem
  and a read-only report mount. Current remote CI remains pending the owner's push.
- [M7b live experiment](../reports/m7b-live/README.md) completes the owner-approved
  Mini/Mini scope: 60 generations, 60 judgments, no retries or provider errors.
  It preserves 36 invalid judgments and reports US$0.49021425 at frozen uncached
  rates from fully observed usage. This is a completed experiment with failures,
  not evidence of a dependable semantic evaluator or improved Structure answers.
  Final local validation: 679 passed, one symlink-privilege skip, 91.25% combined
  statement/branch coverage; Ruff, distribution builds and extracted-run verification
  pass. Current remote CI remains pending the owner's commit and push.
- The owner reports the subsequent standalone-verifier import fix passed GitHub CI.
  This confirms the preceding pushed checkpoint, not the current uncommitted changes.
- [M7c offline protocol](../reports/m7c/README.md) preserves v1, the archived answers,
  references and provisional labels. It freezes v2 and prepares source-bound dynamic
  schemas with a read-only checker. Archived-output replay is a protocol diagnostic,
  not new inference or repaired scores. The report records current local validation;
  remote CI follows the owner's next commit and push.
- The owner reports the M7c checkpoint passed GitHub CI. This confirms the preceding
  pushed checkpoint, not later uncommitted changes.
- [M7d judge-only runtime](../reports/m7d/README.md) reuses saved generations and
  executes only newly approved judge requests, retaining failures, unknown outcomes
  and all planned source cases. It adds offline verification of complete and partial
  runs. That implementation checkpoint used test doubles and made no paid request
  or new model assessment. Its report records local checks.
- [M7d partial live run](../reports/m7d-live/README.md) records the owner-approved
  `gpt-5.4-mini-2026-03-17` judge-only scope: at most 60 requests and US$2.20, with no
  new generation calls. A local execution interruption left 13 attempted requests,
  12 recorded valid judgments, one unknown outcome and 47 requests not started. Its
  cause was not preserved. All 60 original generation records remain unchanged;
  the 12 known responses report the requested model. The known cost subtotal is
  US$0.08424075 at frozen uncached rates; the unknown attempt prevents a complete
  usage/cost total. No retry or resume was performed. The report records current
  local validation; the partial experiment is not a completed 60-request comparison.
- The owner reports the partial-live archive and interruption-diagnostics checkpoint
  (`10e9bc2`) was pushed and passed GitHub CI. This confirms that preceding commit,
  not the current M7e changes.
- [M7e offline follow-up](../reports/m7e/README.md) freezes a verified original partial
  run and selects its 47 unstarted requests. It excludes the 12 known results and
  one unknown attempt, preserving their records and all 60 original generations.
  New execution requires separate model/plan/budget approval. The checkpoint supplies
  software tests and a prepared proposal, with zero new API calls; current remote CI
  follows the owner's next commit and push.

Historical reports retain their original measurements and completion criteria.
This page records the current automatic-evaluation acceptance policy; historical
references to required human review do not override it.

## Recommended research follow-up

1. Inspect the archived partial v2 run and its unknown outcome. The 12 known results
   cover all strategies for two Click cases and BM25/Dense for one more Click case;
   Requests and the later cases have no new recorded judgments. Preserve all v1
   evidence and keep these partial denominators visible.
2. Any additional paid attempts need an explicitly scoped decision covering the
   exact model, requests, plan and budget. The runner has no automatic retry or
   resume; do not repeat the unknown attempt implicitly. Read-only archive checking
   needs no new approval. The [M7e proposal](../reports/m7e/README.md) isolates the 47
   unstarted requests while reusing their exact frozen payloads and saved answers.
   Even 47 later recorded outcomes would leave one historical unknown outcome and
   unknown cumulative full usage/cost; accepted-score coverage must also be reported.
3. Improve coverage and external validation before broader answer-quality claims.
   LLM assessment is not human ground truth or a verified true correctness rate.
   Positive Structure improvements are not required; transparent evidence is.

Existing [manual-review tools](review.md) remain available for optional investigation.
No manual-review workload or independent-review dependency is part of this route.

Begin with the [reproduction guide](reproduction.md) to verify the delivered system
and recorded evidence; consult the [roadmap](roadmap.md) for milestone
scope and the owner's commit/push workflow.
