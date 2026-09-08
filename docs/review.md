# Optional Benchmark Review and Paired Analysis

## Scope

Manual review is an optional extension, not a project completion requirement. The
current evaluation route combines reproducible retrieval/source checks with the
planned [LLM-assisted QA assessment](llm-evaluation.md). It leaves existing relevance
labels provisional and does not claim human-reviewed ground truth.

M6a adds an audit workflow before broader formal experiments. It uses the existing
40-query development set, not a new held-out benchmark. None of its commands change
qrels, tune retrieval parameters, verify a person's identity, or declare labels human
reviewed. M6b supplies wider **provisional** data and a
[source-review workflow before retrieval](benchmarks.md). M6c records the fixed
expanded experiment matrix and scale measurements. The procedures below remain
available if maintainers choose to collect manual labels; their pending status does
not block the automatic-evaluation route.

## Reproduce the audit

From the repository root, prepare the pinned indexes if they are absent, then use a
new output directory. This workflow needs neither model weights nor an API key:

```text
uv run --locked sacr prepare-benchmark benchmarks/seed-v1/benchmark.json
uv run --locked python scripts/run_m6a.py --output artifacts/m6a-audit
```

Only source preparation needs Git/network; analysis and pool generation use saved
indexes and committed M4/M5 runs offline. Existing output directories are refused.
For another benchmark, pass its experiment config and compatible recorded runs:

```text
uv run --locked sacr pool --config configs/bm25-seed.toml --run reports/m5/runs/hybrid-seed --run reports/m5/runs/structure-full --depth 10 --output artifacts/custom-review
```

The config supplies the benchmark and index locations; it does not rerun its
retrieval strategy. Symbol-level runs must share the benchmark, snapshots, query
identities and K values. Depth cannot exceed the largest stored K.

## Pool and review procedure

The pool is the union of each submitted run's top-depth unique symbols plus **all**
existing qrels, including explicit negatives and positives absent from the rankings.
Deduplication is per question/target pair. Unjudged candidates retain a null old label;
they are not automatically graded zero. Every target is checked against its snapshot.

1. Open the generated `review/review.md` and its per-question pages. They show the
   question, source locator, snapshot code and a pinned GitHub source link. Candidate
   order uses hashed IDs; strategy names, ranks and old labels are omitted from the
   reviewer pages and decision templates. Avoid the administrative `pool.jsonl` while
   grading. This reduces anchoring but is not access-controlled blinding.
2. Edit `review/judgments.jsonl`. Set `grade` to 2 (direct answer), 1 (useful support),
   0 (irrelevant), or `"unsure"` (adjudication required). Null means pending. Supply a
   reviewer identifier and a source-based rationale for every submitted decision.
3. Edit `review/queries.jsonl` for every question, including those with no candidates.
   Set `clear` to true/false and `answerable` to true/false or `"unsure"`, with reviewer
   and rationale. Answerability concerns the repository, not just the retrieved pool.
   Inspect wider source before declaring no answer. Record missing targets and unclear
   questions for a revised pool; do not force an incomplete pool to pass validation.
4. If collecting multiple reviews, resolve uncertain/conflicting cases explicitly. Preserve each
   submission in a separate output directory. This tool validates a submission; it
   does not implement reviewer consensus, inter-rater agreement or identity checks.
5. Validate the edited files:

```text
uv run --locked sacr check-review --bundle artifacts/m6a-audit/review --judgments artifacts/m6a-audit/review/judgments.jsonl --queries artifacts/m6a-audit/review/queries.jsonl --output artifacts/m6a-submission-01
```

The output archives the decisions and `review-status.json`, containing pending/unsure
counts, answerability conflicts, label changes and content digests. Exit code zero
means validation completed, **not** approval; inspect `ready_for_versioning`. Readiness
requires every decision complete, clear questions and agreement between reviewed
answerability and positive qrels. Original files and annotation status remain intact.

Checksums detect accidental edits or mixed versions; they are not signatures proving
authorship. Frozen `manifest.json`, `pool.jsonl` and `evidence.jsonl` must remain
unchanged. Only the two decision templates are editable. Source is reconstructed from
stored chunks with original line positions and nested definitions; omitted whitespace
becomes blank lines. Local generated source stays under ignored `artifacts/`; preserve
upstream licenses when distributing source bundles separately.

## Paired statistics

```text
uv run --locked sacr compare --run reports/m5/runs/hybrid-seed --run reports/m5/runs/structure-full --bootstrap-samples 2000 --bootstrap-seed 0 --output artifacts/paired-analysis
```

For each K and quality metric, compute candidate-minus-baseline differences over the
same answerable queries. No-answer queries remain outside quality means. The report
includes wins/ties/losses, query-macro mean differences, equal-repository mean
differences, and repository/category breakdowns. These two means differ when query
counts per repository differ.

The seeded cluster bootstrap samples R repositories with replacement from R observed
repositories, retaining all paired queries within each selected repository. Each
replicate divides selected cluster sums by selected query counts; it does not average
repository means. The interval uses the 2.5th/97.5th percentiles with linear
interpolation. The default is 2,000 replicates and seed 0. Paired categories use only
repositories represented in that category.

Intervals are withheld below five contributing repositories. This is a conservative
project reporting policy, not a statistical sufficiency threshold. Even above five,
few or correlated repositories, convenience sampling, repeated question families and
incomplete labels limit interpretation. Intervals do not repair label bias, establish
generalization or account for multiple strategy/K/category comparisons. Results are
exploratory unless a separate analysis protocol and held-out data were frozen first.

The reader rejects duplicate IDs, mismatched query metadata/text, invalid metrics,
stale quality fingerprints and inconsistent summary quality. It restores integer K
keys when checking legacy fingerprints. Comparison JSON records both the current
analysis code hash (normalized newlines) and the original retrieval runtime metadata.
Timing remains an observation from the original runs, not newly paired timing.

## Optional new labels without rewriting history

Keep `seed-v1` and M3–M5 reports unchanged. Once review and adjudication are actually
finished, publish new benchmark and pool versions with the decision records and
review provenance; rerun **all** strategies on the same new labels. Adding judgments
can change both numerators and denominators, so scores across label versions are not
directly comparable. A top-10 pool remains incomplete for top-20 evaluation and
for unseen retrieval strategies. Broaden the pool or report its coverage explicitly.

Select repository-disjoint development/test splits before tuning. Freeze question
families, snapshots, labels, model, parameters and primary metrics before test runs.
Do not call the current development data held-out because a new report was generated.
