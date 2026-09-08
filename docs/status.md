# Project Status and Acceptance

Updated for the M8b engineering and evidence-consolidation checkpoint. The repository
provides an operational retrieval/evaluation system and offline QA workflow.
**Final research acceptance is still pending.** Passing software checks does not
replace independent relevance or answer review.

## Acceptance matrix

| Area | Implemented and observed | Remaining acceptance |
| --- | --- | --- |
| Python repository parsing | Source discovery, AST symbols/ranges, structural chunks, exclusion diagnostics; SQLite indexes bind to source snapshots | Additional languages and exact dynamic analysis are outside the current scope |
| Retrieval | BM25, pinned dense embeddings, Hybrid, Symbol-aware, and bounded Structure-aware retrieval; persistent vectors and typed relation graphs | No claim that the frozen full Structure heuristic improves aggregate quality |
| Retrieval evaluation | Recall, Precision, MRR, NDCG, latency; saved rankings, query metrics, fingerprints, paired comparisons and fixed ablations | Independent relevance review and adjudication; reviewed-label reruns |
| Benchmark breadth | Eight pinned repositories, 170 queries across separate development/test/public roles; source and split audits | Labels remain provisional; exposed test outcomes require a new untouched test version for future tuning |
| Systems measurements | 45 completed retrieval runs and 24 construction measurements, storage and worker peak memory | Measurements describe one interactive host, not production service guarantees |
| Repository QA | Bounded canonical source context, citations, OpenAI adapter, request freezing, durable execution records, review tooling | M7b live API comparison and independent answer/citation-support review |
| QA preparation | Twelve provisional development cases × five strategies; 60 source-grounded requests prepared offline | No generated answers, actual API spend, correctness scores, or support scores exist |
| Packaging and testing | Installable package, automated tests, base/CPU Dense Docker targets, offline smoke checks, Windows/Linux CI configuration | Current checkpoint's remote CI runs after the owner commits and pushes |
| Project presentation | Architecture/protocol documentation, results overview, saved-evidence validation, reproduction instructions | Update conclusions and status when outstanding research acceptance is completed |

## Verified checkpoints

- [M6c](../reports/m6c/README.md) records the frozen experiment matrix, negative and
  positive observations, construction costs, and repeatability checks. The primary
  Structure heuristic lowers aggregate NDCG@10 on expanded test candidates.
- [M7a](../reports/m7a/README.md) records offline QA preparation. The owner explicitly
  deferred live calls; test doubles are software validation, not LLM experiments.
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

Historical reports retain the status recorded when their checkpoint was produced.
This page tracks later owner-reported progress without rewriting that evidence.

## Remaining research work

1. Complete independent source-first relevance review and adjudication using the
   [review workflow](review.md). Publish versioned labels and rerun the frozen
   strategies; preserve provisional results for comparison.
2. Resume M7b when the owner chooses to run it: approve the fixed model and budget,
   configure credentials locally, validate the prepared requests, and record real
   provider outputs, usage, failures, and latency. Follow the [QA protocol](qa.md).
3. Review answer correctness and source support independently of citation identity.
   Keep incomplete or disputed judgments visible and report actual denominators.
4. Consolidate the reviewed retrieval and QA findings before claiming the full
   research project is complete. Improved Structure scores are not an acceptance
   requirement; reproducible and defensible conclusions are.

Engineering delivery can proceed while those items remain pending. Begin with the
[reproduction guide](reproduction.md); consult the [roadmap](roadmap.md) for milestone
scope and the owner's commit/push workflow.
