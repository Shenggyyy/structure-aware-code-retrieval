# M6a: Paired Analysis and Relevance Review Audit

## Status and scope

This is the first M6 subgoal, using the **same 40 provisional development questions**
on Requests and Click. No new queries, relevance labels, retrieval runs or human
review are claimed. Broader/public benchmarks, reviewed frozen splits and scale
profiling remain required for M6 completion.

The audit reuses M4's BM25/Dense runs and M5's Hybrid/Symbol/Structure-full runs. Hybrid
is the comparison baseline. All five share the same benchmark digest, symbol unit,
K values and indexed snapshots. Recorded quality fingerprints and summary quality
were validated before analysis; retrieval parameters and historical artifacts remain
unchanged. Latency tables repeat the original measurements, not a new timing trial.

## Paired findings at K=10

Differences below are Structure-full minus Hybrid, averaged over answerable questions.
The overall difference is +0.066667 Recall, -0.174653 MRR and -0.090554 NDCG.

| Group | Questions | Recall delta | NDCG delta |
| --- | --- | --- | --- |
| All | 40 | +0.066667 | -0.090554 |
| Requests | 20 | +0.058333 | -0.168753 |
| Click | 20 | +0.075000 | -0.012355 |
| Symbol | 8 | +0.000000 | -0.094429 |
| Behavior | 16 | +0.031250 | -0.187358 |
| Cross-file | 8 | +0.270833 | +0.117037 |
| Test | 8 | +0.000000 | -0.100660 |

The repository and category rows are overlapping views of the same 40 questions,
not additional samples. On known labels, cross-file questions account for most of
the recall gain; Requests has the larger ordering regression. These observations
identify cases for review, not evidence of generalization or a reason to tune test
parameters. The M5 failure cases and source traces remain relevant.

The new comparison provides per-question differences, wins/ties/losses, query- and
repository-macro effects, and category breakdowns. **No bootstrap interval is emitted**
for this two-repository seed. The implementation requires at least five contributing
repositories as a reporting policy; five is not a statistical sufficiency guarantee.
The documented protocol resamples entire repositories with paired queries, estimates
the query-weighted mean difference and uses seeded percentile intervals. Small samples,
question-family dependence, convenience sampling, sparse labels and uncorrected
multiple comparisons remain limitations even when an interval can be computed.

See [the generated comparison](comparison/report.md) and
[machine-readable differences](comparison/comparison.json). The latter retains both
the analysis code hash and the original retrieval runtime metadata.

## Annotation coverage and concrete review output

The union of all five top-10 symbol rankings plus every existing qrel contains:

| Repository | Question/symbol pairs |
| --- | --- |
| Requests | 423 |
| Click | 422 |
| Total | 845 |

Only 55 pairs have existing judgments (54 positive, one explicit negative); **790
pairs are unjudged**. These are candidate pairs, not 845 queries or reviewed labels.
The pool is not exhaustive and cannot establish absolute recall. Its depth is 10;
even a fully reviewed pool would not imply complete labels at K=20 or for new methods.

Pool digest:
`0a160ed1812e4dbc9c0c3fafa6bc92508d1a30290ca6941e82660d104b2900b2`.

- [Pool manifest](pool-manifest.json): snapshots, questions, strategy fingerprints,
  selection policy, upstream license identifiers and counts.
- [Administrative pool](pool.jsonl): source locators, original labels and strategy
  origins. Keep this file away from reviewers while grading to reduce anchoring.
- [Initial review status](review-status.json): 845 pending judgments, 40 pending query
  checks, no completed decisions, and `ready_for_versioning=false`.

The complete local bundle also contains 40 reviewer pages with snapshot source code,
pinned links and editable JSONL decision templates. Those pages omit strategies,
ranks and old labels; the administrative files remain accessible, so this is not
enforced blinding. Source bundles stay under ignored `artifacts/`; these committed
audit files contain metadata and locators, not copied third-party source.

## Reproduction and validation

From the repository root, prepare indexes if needed, then choose a new output folder:

```text
uv run --locked sacr prepare-benchmark benchmarks/seed-v1/benchmark.json
uv run --locked python scripts/run_m6a.py --output artifacts/m6a-reproduce
```

Source preparation requires Git/network; the analysis itself runs offline without
torch, model weights or API credentials. See [the review protocol](../../docs/review.md)
for grading instructions and `sacr check-review`. The checker archives submitted
decisions and reports conflicts without changing a benchmark's labels or review status.

Two independent audit invocations produced **51 byte-identical files**, including
the comparison, frozen pool, source pages, blank templates and pending-review check.
Local lint/format checks and distribution build passed. The test suite passed with
**160 tests, one Windows symlink-privilege skip, and 92% coverage**. Tests include
hand-computed unequal-cluster weighting, deterministic bootstrap intervals, no-answer
exclusion, legacy numeric K-key hashing, corrupt reports, preserved qrels, stale source
evidence, incomplete reviews and answerability conflicts. No test fabricates a real
human reviewer; completed decisions in tests use explicitly synthetic fixtures.
The built wheel was installed in a fresh base environment without torch; the same
160 tests passed with one skip, and its real audit reproduced all 51 files byte for
byte. Wheel/source archives were checked for accidental cache and artifact inclusion.

Upstream M5 CI was reported passing by the owner. M6a remote CI is pending the owner's
commit/push. The next checkpoint is M6b: broader data selection and source-grounded
draft labels, followed by actual independent review and versioned publication.
