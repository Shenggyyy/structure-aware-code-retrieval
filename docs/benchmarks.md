# Benchmark Expansion and Freeze Protocol

## Current suite

`benchmarks/suite-v1.json` binds three separately reported datasets to exact benchmark
and annotation-provenance digests. The primary planned quality measures are Recall@10
and NDCG@10; Precision, MRR, other K values and cost measurements remain secondary.
These choices preserve the M5 tradeoff instead of choosing a new winning metric.

| Role | Source | Repositories | Queries | Independent review |
| --- | --- | --- | --- | --- |
| Development | Existing Requests/Click seed | 2 | 40 | Pending |
| Test candidate | Flask, Rich, NetworkX, Packaging, TOMLKit | 5 | 120 | Pending |
| Public adaptation | RepoQA Marshmallow | 1 | 10 | Pending |

The original-question benchmark totals 160 queries across seven repositories. The
public adaptation adds ten separate queries, bringing the suite to 170 on eight.
The roadmap target is **reviewed** questions; this draft meets the intended breadth
but does not satisfy the independent-review acceptance criterion.

Repository URL disjointness and normalized exact-text uniqueness are enforced by
`sacr audit-suite`. This prevents accidental split overlap and renamed repository
aliases but cannot detect every fork, paraphrase, related ecosystem or pretraining
overlap. The expanded questions record 85 known families. All current questions are
answerable with designated positive targets; no-answer evaluation remains a dataset
gap. Sparse positives and agent-authored question style can bias all quality scores.

## Prepare and reproduce

From the project root, in a base environment:

```text
uv sync --locked --dev
uv run --locked python scripts/run_m6b.py --prepare --output artifacts/m6b-reproduce
```

The explicit `--prepare` flag permits downloading pinned source checkouts and the
checksum-verified RepoQA archive. Source selection uses the existing scanner, retaining
tests and examples rather than only labeled functions. Git refs containing an exact
40-character commit use a shallow fetch of that commit into a new checkout; existing
checkouts are only inspected. Neither upstream packages nor code are executed.

Without `--prepare`, the script is offline and requires the prepared indexes and
archive. It rebuilds both new datasets, compares all five generated files per dataset
against committed artifacts, audits the frozen suite, and creates two source review
bundles. It refuses an existing output directory. Optional dense dependencies and
weights are not needed. If preparation is interrupted, select a fresh artifact
destination or inspect the incomplete checkout; the tool never resets it automatically.

Useful independent commands:

```text
uv run --locked sacr audit-suite --suite benchmarks/suite-v1.json --output artifacts/suite-audit
uv run --locked sacr pool-labels --config configs/bm25-expanded-test.toml --output artifacts/expanded-review
uv run --locked sacr pool-labels --config configs/bm25-repoqa-public.toml --output artifacts/public-review
```

The BM25 configs are ordinary experiment configurations used here to locate the
benchmark and indexes. Auditing and `pool-labels` do not execute those experiments.
Actual test/public retrieval is deferred during M6b to avoid using the new scores
to revise questions or strategy parameters.

## Review and publish

Open the generated `test-review/review.md` and `public-review/review.md`. They provide
source pages and editable judgment/query templates following [the review protocol](review.md).
The expanded bundle initially covers its 164 designated positive targets; the public
bundle covers ten needles. These are label-only reviews, not full ranked candidate
pools. Unlisted alternatives and relevance completeness require additional source
inspection and, later, blinded pooling across all fixed strategies.

```text
uv run --locked sacr check-review --bundle artifacts/m6b-reproduce/test-review --judgments artifacts/m6b-reproduce/test-review/judgments.jsonl --queries artifacts/m6b-reproduce/test-review/queries.jsonl --output artifacts/expanded-submission-01
```

A zero exit status means the validator ran; inspect `ready_for_versioning` and
conflicts. The validator does not authenticate humans or enforce reviewer independence.
Keep reviewer submissions, disputed cases and adjudications. Publish reviewed labels
as a **new benchmark version**, update the suite's explicit digests and preserve the
old files. Do not silently edit a frozen manifest to read `human_reviewed`.

## Subsequent experiments

M6c still needs the five fixed strategies, relationship ablations and scale profiling
over the expanded corpora. Tune only on development data; freeze configuration before
test runs. Compute paired uncertainty over repositories and respect the M6a small-sample
limits. Report the public adaptation separately. Report failures, sparse-label coverage,
context/token proxies, build/storage/peak-memory costs and hardware-dependent timing.

Source validation, corpus-size counts and reproducible question files are M6b's
engineering deliverables. They are not new quality measurements, semantic approval,
or completion of M6's formal-experiment acceptance criteria.
