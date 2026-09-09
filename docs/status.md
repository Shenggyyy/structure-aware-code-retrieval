# Project Status and Acceptance

The original research and engineering scope is delivered, with reproducible
retrieval experiments and archived live LLM assessments. **The requested local
interactive workflow is implemented and has passed live acceptance:** M9a supplies
repository import, resource preparation, five-strategy context previews and saved
history; M9b adds the local browser interface. M9c implements frozen generation plans, explicit model/budget
approval and same-model answer comparison. The separately approved
[M9c live run](../reports/m9c-live/README.md) returned five answers from five requests,
with zero judging calls, retries or unknown outcomes. Reported usage is 15,046 input
and 1,131 output tokens; the frozen-rate estimate is US$0.016374 against a US$0.10
budget, not an invoice. Source/citation checks passed, but one unlabeled question
does not establish answer correctness or a strategy ranking. Browser checks verified
the five real answers, representative citations from each strategy, history
reopening and unchanged outcomes after server restart and page reload.
See [the M9c implementation record](../reports/m9c/README.md) for the earlier offline
checks, [M9b](../reports/m9b/README.md) for the browser foundation and
[M9a](../reports/m9a/README.md) for the underlying CLI delivery.
**All 60 v2 judge requests have now been attempted across two approved batches:**
58 judgments passed the protocol, one failed it and one historical outcome is
unknown. The [M7e live follow-up](../reports/m7e-live/README.md) completed its 47
requests with 46 valid judgments and one protocol failure, without retries or new
generations. The earlier M7d archive remains an immutable partial run.
The new batch's usage-based cost is US$0.35257875 at frozen uncached rates. Cumulative
known v2 judging cost is US$0.4368195; full usage and cost remain unknown because
the historical attempt has no saved response. These are estimates, not invoices.
The v1 experiment retains its 24 accepted judgments and 36 protocol failures.
The original engineering delivery and planned experiment attempts are complete; score
coverage is incomplete and the evidence does not establish a reliable QA ranking.
Human or independent review is optional, not a completion prerequisite. Labels
remain provisional; model scores are neither human review nor true accuracy.
The [M8c presentation checkpoint](../reports/m8c/README.md) provides a
[project brief and bilingual CV wording](project-brief.md) plus a
[verified offline demonstration](demo.md). It adds no new inference or research
scores. Those research artifacts and presentation materials remain available;
M9 extends the product workflow without changing their results or limitations.

## Acceptance matrix

| Area | Implemented and observed | Remaining acceptance |
| --- | --- | --- |
| Python repository parsing | Source discovery, AST symbols/ranges, structural chunks, exclusion diagnostics; SQLite indexes bind to source snapshots | Additional languages and exact dynamic analysis are outside the current scope |
| Retrieval | BM25, pinned dense embeddings, Hybrid, Symbol-aware, and bounded Structure-aware retrieval; persistent vectors and typed relation graphs | No claim that the frozen full Structure heuristic improves aggregate quality |
| Retrieval evaluation | Recall, Precision, MRR, NDCG, latency; saved rankings, query metrics, fingerprints, paired comparisons and fixed ablations | Retain sparse-label coverage limits; label changes require a new version and reruns |
| Benchmark breadth | Eight pinned repositories, 170 queries across separate development/test/public roles; source and split audits | Labels remain provisional; exposed test outcomes require a new untouched test version for future tuning |
| Systems measurements | 45 completed retrieval runs and 24 construction measurements, storage and worker peak memory | Measurements describe one interactive host, not production service guarantees |
| Repository QA | 60 live generations: 48 answers, 12 abstentions; all source audits and applicable citation ID checks passed | Automatic checks establish location/identity, not semantic truth |
| Initial QA experiment | Twelve provisional development cases × five strategies; 120 authorized v1 calls, complete raw archive, known usage for every call | Small development scope and same-model generator/judge limit generalization; usage-based cost is not an invoice |
| LLM evaluation | Immutable v1 results; all 60 v2 requests attempted across two batches, yielding 58 valid judgments, one invalid judgment and one historical unknown; raw records and offline verification | Keep incomplete score coverage and unknown full cost visible; model scores are not true accuracy or proof of a reliable strategy ranking |
| Packaging and testing | Installable package, automated tests, base/CPU Dense Docker targets, offline smoke checks, Windows/Linux CI configuration | Current checkpoint's remote CI runs after the owner commits and pushes |
| Project presentation | Retrieval analysis, live QA failure analysis, raw evidence, offline verification, project brief, bilingual CV wording and verified demo | Retain limits and version future protocol/dataset changes; use CV templates according to actual contributions |
| M9a workbench foundation | Local-directory/public-HTTPS snapshots; reusable index/vector/graph preparation; five context previews, per-strategy failures and self-contained history | Context previews do not contain generated answers; public imports need network and Dense needs explicitly prepared local weights |
| M9b browser workflow | Local HTTP server; import/preparation feedback, question entry, side-by-side strategy evidence, source expansion and saved history | Context previews are not generated answers; host loopback use only, one background job at a time |
| M9c same-model answers | Frozen model/request plans and total estimates; explicit approval; existing adapter reuse; separate answer archives, citations, usage and failures; offline tests and separately approved live answers | Every new paid plan needs fresh scoped approval; observed usage yields estimates rather than invoices |
| M9c live workflow acceptance | Five approved requests returned five answers; browser comparison, representative source citations, history reopening and server restart checked; zero judges/retries/unknowns | Scoped workflow accepted; one unlabeled question supplies no answer-quality ranking or true accuracy |

## Verified checkpoints

- [M9c live](../reports/m9c-live/README.md) records the separately approved
  `gpt-5.4-mini-2026-03-17` scope: at most five generation requests, zero judge
  requests and US$0.10. All five requests returned `answered`; source/citation
  checks passed. Raw responses report 15,046 input and 1,131 output tokens
  (16,177 total, zero cached/reasoning tokens), implying US$0.016374 at frozen
  uncached rates. No retry or unknown outcome was recorded. Original previews
  remain unchanged. Browser checks displayed all five real answers, opened one
  representative citation per strategy, filtered/reopened the exact saved run and
  retained all five outcomes after server restart and page reload. The scoped
  interactive workflow is accepted; current remote CI follows the owner's push.
- [M9c](../reports/m9c/README.md) adds offline planning, explicit paid approval and
  durable same-model answer execution over saved contexts, with browser citations
  and history. Its implementation checks use offline providers and make no API
  calls. The linked report records actual software validation; live user-workflow
  acceptance was deferred to the separately approved live follow-up. Current remote
  CI follows the owner's commit/push.
- [M9b](../reports/m9b/README.md): broad offline regression passed 1,091 tests with
  two Windows symlink-privilege skips; the final recovery-progress refinement passed
  all 60 HTTP tests separately. Browser checks completed public/local imports, real
  MiniLM five-strategy previews, source/provenance inspection and history reopening
  after restart. Missing-model failures and literal markup rendering were exercised.
  Ruff, JavaScript syntax, distribution packaging and the 45-run overview check
  passed. No model API calls were made; M9c was pending at that checkpoint.
- [M9b](../reports/m9b/README.md) adds the local browser workflow over the M9a
  services, with server request-boundary checks, persistent background job state,
  five-strategy evidence comparison and history reopening. The linked record lists
  actual software/browser checks; these establish no new retrieval or model quality.
  Current remote CI follows the owner's commit and push.
- [M9a](../reports/m9a/README.md): 1,019 tests passed, two Windows symlink-privilege
  tests skipped, 91.43% combined statement/branch coverage. Ruff, distribution build
  and the 45-run overview check passed. Local and pinned public HTTPS imports both
  completed real-MiniLM five-strategy previews, cache reuse and history reopening.
  No LLM API call or model download was made; browser/real-answer acceptance remains
  pending the subsequent M9 checkpoints.
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
  not subsequent uncommitted changes.
- [M7e offline follow-up](../reports/m7e/README.md) freezes a verified original partial
  run and selects its 47 unstarted requests. It excludes the 12 known results and
  one unknown attempt, preserving their records and all 60 original generations.
  New execution requires separate model/plan/budget approval. The checkpoint supplies
  software tests and a prepared proposal, with zero new API calls.
- The owner reports the M7e tooling checkpoint (`daf6aa4`) was pushed and passed
  GitHub CI. This confirms that commit, not the current live-evidence changes.
- [M7e live follow-up](../reports/m7e-live/README.md) records 47 requests under a
  US$1.80 budget using `gpt-5.4-mini-2026-03-17`: 46 valid judgments, one protocol
  failure, no provider errors, no new unknown outcomes and no new generations.
  The batch finished as `complete_with_failures`; cumulative coverage remains
  `incomplete` because one judgment is invalid and the historical outcome is unknown.
  The new usage-based cost is US$0.35257875, and cumulative known judging cost is
  US$0.4368195. Full cumulative usage/cost remains unknown. All original answers
  and prior attempts are preserved. The report records local validation; current
  remote CI follows the owner's commit and push.

- The owner reports the M7e live-evidence checkpoint (`61e246e`) was pushed and
  passed GitHub CI. This confirms that commit, not later documentation changes.
- [M8c presentation closeout](../reports/m8c/README.md) supplies an evidence-linked
  project brief and demonstration. All five final PowerShell blocks were executed
  offline, including the 17-command fixture smoke, live searches, QA preview,
  45-run overview verification and saved live-answer inspection. No API calls or
  model downloads were made. Two earlier rehearsal attempts encountered Windows
  directory-rename errors; the record retains them and the successful final run.
  Current remote CI follows the owner's next commit and push.
- [M9a workbench foundation](../reports/m9a/README.md) adds a reusable application
  layer and `sacr workbench import`, `prepare`, `preview`, `history` and `show`.
  Imports capture Python source and provenance without executing target code;
  preparation reuses version-bound resources and retains independent stage failures.
  Each question saves all five retrieval outcomes, source context, timing and
  errors. History can reopen the saved comparison without rerunning retrieval.
  The mode is explicitly `context_preview`, with zero model API calls, no generated
  answers, null generation usage/cost and no invented relevance metrics. Local
  validation is recorded in the linked report; current remote CI follows the
  owner's commit and push.

Historical reports retain their original measurements and completion criteria.
This page records the current automatic-evaluation acceptance policy; historical
references to required human review do not override it.

## Interactive workflow acceptance

M9a–M9c complete the agreed local single-user workflow: import a Python repository,
freeze its source, prepare resources, preview five retrieval strategies, review the
fixed-model plan, explicitly approve generation, compare answers/citations and
reopen saved history. The M9c live run supplies actual provider responses in addition
to offline tests. Browser checks retained the same five answers and call count after
restart; history did not trigger another request. This does not require another
engineering milestone to declare the agreed scope complete.

New questions can use free-of-model-API context previews. Any new paid generation
requires a new reviewed plan and explicit model/budget approval; this completed
US$0.10 scope grants no continuing authorization. Unlabeled questions do not acquire
Recall/NDCG or answer-accuracy scores. Automatic source checks and optional model
assessments remain separate, and historical provisional labels and negative results
remain unchanged. The owner commits and pushes this checkpoint; remote CI status
is separate from the locally observed acceptance.

## Recommended research follow-up

1. Inspect the [cumulative v2 evidence](../reports/m7e-live/README.md), including
   58 accepted judgments, the protocol failure and the historical unknown. Report
   dimension-specific and paired-case denominators when comparing strategies;
   protocol acceptance alone does not demonstrate semantic correctness.
2. The agreed experiment scope has been attempted; recovering the historical
   unknown is not a project-completion requirement. Any further paid experiment
   requires a new model/request/plan/budget decision. Preserve old records and do
   not implicitly retry unknown attempts. Read-only verification needs no approval.
3. Improve coverage and external validation before broader answer-quality claims.
   LLM assessment is not human ground truth or a verified true correctness rate.
   Positive Structure improvements are not required; transparent evidence is.

Existing [manual-review tools](review.md) remain available for optional investigation.
No manual-review workload or independent-review dependency is part of this route.

Begin with the [reproduction guide](reproduction.md) to verify the delivered system
and recorded evidence; consult the [roadmap](roadmap.md) for milestone
scope and the owner's commit/push workflow.
