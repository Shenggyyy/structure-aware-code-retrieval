# Repository Seed v0.1.0

An exploratory **development set**, authored and checked against source by Codex in
M3. It has **not been independently human-reviewed** and is not a held-out test set.
The manifest's `annotation_status` is `provisional`.

## Composition

| Repository | Pinned ref | Commit | Source license |
| --- | --- | --- | --- |
| [Requests](https://github.com/psf/requests/tree/0e322af87745eff34caffe4df68456ebc20d9068) | v2.32.3 | `0e322af87745eff34caffe4df68456ebc20d9068` | Apache-2.0 |
| [Click](https://github.com/pallets/click/tree/934813e4d421071a1b3db3973c02fe2721359a6e) | 8.1.8 | `934813e4d421071a1b3db3973c02fe2721359a6e` | BSD-3-Clause |

Each repository contributes 20 English questions: 4 symbol lookups, 8 behavior
questions, 4 cross-file questions, and 4 test-localization questions. All 40 questions
are answerable. The 55 judgments comprise direct evidence, supporting evidence and
one explicit irrelevant test helper. Downloaded upstream source/license files remain
in ignored `artifacts/`; this directory stores questions, locators and rationales.

## Label construction

Questions and judgments were written after inspecting the pinned implementations
and tests, before running this seed's evaluation. Source checks included the actual
control flow, nested generators, helper calls, overload implementations, and assertions
in regression tests. Each judgment records the symbol's exact path, qualified name,
decorator-inclusive range, grade, and rationale.

The runner verifies those locations exist in the indexed snapshot. That verification
does not independently prove semantic relevance. Labels are not claimed to cover
every relevant symbol, and most unjudged results have not been reviewed. Keep them
distinct from explicit negatives.

## Optional human review and limitations

Human review is not required for project completion. The current benchmark remains
provisional and supports reproducible metrics against its recorded labels. If
maintainers choose manual review, inspect questions, rationales and pooled candidates,
record missing positives/explicit negatives, and publish a new label version with
actual review provenance. Never change `annotation_status` to `human_reviewed` based
only on automatic source validation or model judgments.

Do not tune on a future held-out set or rewrite queries to improve a particular
retriever's scores. Expand to repository-disjoint development/test collections in M6.
This small set contains related question families (including overlapping behavior
and test questions), so observations are correlated and do not justify significance
or generalization claims. Some symbol queries contain explicit names; some query
categories are inherently easier at file level than at symbol level.

Use fixed LF checkouts from `sacr prepare-benchmark` to reproduce raw byte hashes.
M2's earlier Windows smoke indexes may contain CRLF and are intentionally separate.
Any source/label/protocol change requires a new benchmark version and fresh reports.

See [the executable schema and commands](../../docs/evaluation.md) and
[recorded development results](../../reports/m3/README.md).
