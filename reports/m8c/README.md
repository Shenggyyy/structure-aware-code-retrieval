# M8c Presentation Closeout

Recorded 2026-09-09 against application source `61e246e`, which the owner reports
passed GitHub CI. This checkpoint packages the delivered engineering and experiments
for an application portfolio. It changes documentation only: **zero API calls,
zero model downloads and no new research scores**.

## Deliverables

- [Project brief](../../docs/project-brief.md): research question, implemented
  contributions, technology tradeoffs, evidence, limitations and three English
  plus three Chinese CV templates. The templates must reflect actual contributions.
- [Five-minute demonstration](../../docs/demo.md): copyable PowerShell blocks for
  a synthetic offline pipeline, real saved retrieval findings, and an archived
  cited LLM answer with its separate model assessment.
- README, roadmap and acceptance status link these materials. Structure documentation
  now describes human review as optional, consistent with current acceptance.

The brief retains the 40/120/10 dataset roles, the negative aggregate Structure
finding, and the distinction between 58 protocol-valid judgments and true accuracy.
No new completion gate or paid experiment is introduced.

## Observed validation

All **five final PowerShell blocks** were extracted from the demo document and
executed in order after the existing locked installation. The first block runs
the existing 17-command smoke. Final outputs confirm three indexed files,
repeatable quality fingerprints, identical BM25/Structure ordering for the example,
608 bytes of QA context, and empty-context handling without model calls.

The walkthrough also checks the unchanged 45-run retrieval overview, extracts the
M7e live archive, verifies it offline, and displays the stored
`qa-click-04 / bm25` answer, `S1`/`S10` source locations and v2 correctness assessment.
The verifier's `complete_with_failures` describes preserved experimental outcomes,
not a software-check failure. Its cumulative cohort still includes an invalid
judgment and historical unknown.

Two earlier full-walkthrough attempts failed at Windows directory publication with
`WinError 5`: one at `comparison`, one at `review`. A direct smoke before them and
another direct smoke after them passed; the final walkthrough with a shorter fresh
directory also passed. Inspection found no demonstrated open-handle or relative-path
defect. **The cause remains unresolved; shorter paths are not a proven fix.**
No application retry or publication behavior was changed. Failure records are
retained in [validation.json](validation.json), with workspace prefixes redacted.
This records five smoke invocations: three passed and two failed.

The validation record also captures local link checks, Ruff and distribution
build results. No new automated tests were needed for this documentation change,
and the full pytest suite and Docker builds were not rerun. The previous engineering
baseline remains [M7e's recorded checks](../m7e/validation.json); this checkpoint's
remote CI follows the owner's commit and push.

The project and presentation materials are ready for review. Future model choices,
new benchmarks, feature additions or systematic teaching are separate follow-up
work. Published experimental evidence remains unchanged.
