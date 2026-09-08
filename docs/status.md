# Project Status and Acceptance

The repository provides an operational retrieval/evaluation system and offline QA
workflow. **Final acceptance still needs the authorized live QA and LLM-evaluation
experiment.** Human or independent review is optional, not a completion prerequisite.
Existing labels remain provisional; automatic checks and future model judgments
must be described according to what they actually measure.

## Acceptance matrix

| Area | Implemented and observed | Remaining acceptance |
| --- | --- | --- |
| Python repository parsing | Source discovery, AST symbols/ranges, structural chunks, exclusion diagnostics; SQLite indexes bind to source snapshots | Additional languages and exact dynamic analysis are outside the current scope |
| Retrieval | BM25, pinned dense embeddings, Hybrid, Symbol-aware, and bounded Structure-aware retrieval; persistent vectors and typed relation graphs | No claim that the frozen full Structure heuristic improves aggregate quality |
| Retrieval evaluation | Recall, Precision, MRR, NDCG, latency; saved rankings, query metrics, fingerprints, paired comparisons and fixed ablations | Retain sparse-label coverage limits; label changes require a new version and reruns |
| Benchmark breadth | Eight pinned repositories, 170 queries across separate development/test/public roles; source and split audits | Labels remain provisional; exposed test outcomes require a new untouched test version for future tuning |
| Systems measurements | 45 completed retrieval runs and 24 construction measurements, storage and worker peak memory | Measurements describe one interactive host, not production service guarantees |
| Repository QA | Bounded canonical source context, citation identity/path/range validation, OpenAI adapter, request freezing and durable execution records | M7b live comparison and LLM-assisted correctness, completeness and citation-support assessment |
| QA preparation | Twelve provisional development cases × five strategies; 60 source-grounded requests prepared offline | No generated answers, actual API spend, correctness scores, or support scores exist |
| LLM evaluation | M7a supplies a versioned three-dimension scoring specification and separates automatic checks from not-run model assessments | M7b judge execution is not implemented; its model, prompt, evidence, failure rules and combined cost must be frozen before live calls |
| Packaging and testing | Installable package, automated tests, base/CPU Dense Docker targets, offline smoke checks, Windows/Linux CI configuration | Current checkpoint's remote CI runs after the owner commits and pushes |
| Project presentation | Architecture/protocol documentation, results overview, saved-evidence validation, reproduction instructions | Update conclusions and status when outstanding research acceptance is completed |

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

Historical reports retain their original measurements and completion criteria.
This page records the current automatic-evaluation acceptance policy; historical
references to required human review do not override it.

## Remaining research work

1. Implement M7b generation plus LLM-judge execution and reporting using the frozen
   [LLM scoring specification](llm-evaluation.md). Before API calls,
   present the chosen generation/judge models, request limits and **combined** cost
   estimate for explicit owner approval. The earlier 60-request generation-only
   estimate is neither a judging budget nor authorization to run.
2. Run the approved experiment with locally configured credentials. Save real
   outputs, automatic citation checks, model judgments, usage, failures and latency;
   report actual denominators and missing evidence without substituting zero or
   fabricated scores. Follow the [QA protocol](qa.md).
3. Consolidate retrieval, QA quality and costs with clear provenance and limitations.
   LLM assessment is not human ground truth or a verified true correctness rate.
   Improved Structure scores are not required; reproducible, transparent evidence is.

Existing [manual-review tools](review.md) remain available for optional investigation.
No manual-review workload or independent-review dependency is part of this route.

Engineering delivery can proceed while those items remain pending. Begin with the
[reproduction guide](reproduction.md); consult the [roadmap](roadmap.md) for milestone
scope and the owner's commit/push workflow.
