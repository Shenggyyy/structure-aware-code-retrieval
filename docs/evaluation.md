# Evaluation Protocol

M3 introduced this protocol; M4 applies it to BM25, dense, hybrid and symbol-aware
retrieval with the same symbol/file evaluation contract. The first seed
contains 40 questions and 55 source-checked judgments across Requests and Click.
Labels are agent-authored, sparse, and marked `provisional`; independent human review
is still required. The resulting development scores are not final benchmark claims.

The M2 baseline uses BM25Plus with `k1=1.5`, `b=0.75`, and `delta=0`, as recorded in
index metadata. Freeze this explicit variant before comparing later strategies.

## Dataset layers

**Fixtures:** small deterministic source repositories testing duplicate names, alias
imports, nested definitions, long functions, syntax errors, and empty results. They
validate implementation, not real-world retrieval quality.

**Reviewed benchmark:** start with approximately 40–60 questions across two fixed
Python snapshots; later target 150–250 across 5–8 repositories. Include symbol lookup,
behavioral search, cross-file flows, test discovery, and multi-evidence questions.

Store query ID, repository/snapshot, question, category, relevant source ranges or
symbols, relevance grades, and annotation rationale. Labels must be independent of
chunking policy. Preserve provenance and check licenses before redistribution.

**Public subset:** select one manageable task to test baseline generality.

| Candidate | Use and limitation |
| --- | --- |
| [CodeSearchNet](https://github.com/github/CodeSearchNet) | Function-level natural-language search; comment/code pairs do not constitute a cross-file benchmark. Prevent leakage from query-equivalent docstrings. |
| [CoIR](https://github.com/coir-team/coir) | Supplementary retrieval tasks; audit corpus, labels, and full-repository availability for the chosen subset. |
| [RepoBench](https://github.com/Leolty/repobench) | Cross-file retrieval reference; report natural-language adaptations separately from its code-completion task. |
| [RepoQA](https://github.com/evalplus/repoqa) | Function localization/long-context understanding; does not replace multi-evidence, open-ended QA evaluation. |

Preserve official splits for official tasks. Record subset IDs, sampling seeds,
preprocessing, and adaptations; do not equate subset scores with full-benchmark scores.

## Annotation and splits

Verify relevance against source; model-generated labels require human review. Pool
candidates from all strategies and supplement with independent source inspection.
Record unjudged candidates and judgment coverage. With incomplete labels, recall is
against known relevant items, not guaranteed true recall.

Tune on development data. Prefer repository-disjoint development and held-out test
sets; the small MVP benchmark supports exploratory conclusions. Freeze test labels
and parameters before formal comparison. Include lexical and semantic questions as
well as structural ones, rather than selecting only cases favorable to expansion.

## Metrics and units

The primary ranking unit is a source symbol, deduplicated by first occurrence after
mapping chunks to symbols. Report file-level retrieval separately. Fix source-range
mapping rules before chunking ablations.

Use K in {1, 5, 10, 20}. Grades are 0 (irrelevant), 1 (supporting), and 2
(direct evidence); grades above zero count as relevant for binary metrics.

- **Precision@K:** relevant unique results in the first K positions divided by K;
  unfilled positions count as misses.
- **Recall@K:** relevant unique results retrieved divided by all known relevant
  units for the query.
- **MRR@K:** reciprocal rank of the first relevant result up to K, or zero if absent.
- **NDCG@K:** graded gain `2^grade - 1`, discounted by `log2(rank + 1)`, normalized
  against the ideal ranking of known labels.
- **Latency:** retrieval wall time including query encoding and reranking; report
  warm p50/p95 with an explicit warm-up policy and cold start separately.

Macro-average over answerable queries and report repository/category breakdowns.
Evaluate no-answer questions separately; do not silently include undefined recall
or NDCG values. Resolve score ties with stable IDs. Test hand-calculated rankings,
duplicates, empty results, graded relevance, and fewer than K returned items.

## Fair comparisons

Share snapshots, searchable content, chunks, and output K across primary strategy
comparisons. Record model prompts and truncation. Measure expansion's extra
candidates, computation, latency, and context tokens rather than hiding costs.

Separate fixed-window versus structural chunking experiments from retrieval changes.
Run relation ablations with no edges, containment, imports, calls, and test links,
including removal of individual relation types from the complete method.

Save per-query rankings/metrics. Formal experiments report paired differences and
uncertainty, using repository-aware resampling when appropriate. Include failure
cases and stratified results; query count targets alone do not establish power.

## Reproducibility and QA extension

Capture project commit/dirty state, corpus hash, benchmark version, effective config,
model revision, dependency versions, seeds, hardware/OS, thread settings, cache
policy, and outputs. Measure index construction, size, and peak memory separately.

In M7, keep the LLM revision where available, prompt, decoding settings, and context
budget fixed. Save answers because hosted inference may not reproduce exactly.
Assess correctness, citation location validity, citation support, token use, and
end-to-end latency separately from retrieval quality.

## Executable schema (version 1)

`benchmark.json` contains exactly `schema_version`, `id`, `version`, `split`,
`annotation_status`, `repositories`, `queries_file`, and `qrels_file`. Resource paths
must stay inside the benchmark directory. Each repository records `id`, HTTPS `url`,
`ref`, immutable `commit`, source `license`, and `corpus_hash`.

Each query in `queries.jsonl` has `id`, `repository`, `category` (symbol, behavior,
cross_file, or test), `text`, and boolean `answerable`. Each `qrels.jsonl` judgment
contains `query_id`, `target`, integer `grade` (0–2), and a source-based `rationale`.

Example judgment shape:

```json
{
  "query_id": "requests-01",
  "target": {
    "path": "src/requests/cookies.py",
    "qualified_name": "src.requests.cookies.cookiejar_from_dict",
    "start_line": 521,
    "end_line": 539
  },
  "grade": 2,
  "rationale": "Builds a cookie jar from the supplied mapping."
}
```

Targets refer to entire lexical symbols including decorators, not retrieval chunk
IDs. All four locator fields must match a searchable indexed symbol. This also
distinguishes overloaded declarations and nested definitions. A hit maps through its
owning symbol; parent symbols do not automatically receive credit for child evidence.
File-level relevance is the maximum grade among judgments in that file.

The loader rejects duplicate IDs/judgments, unknown references, invalid paths/grades,
and answerability inconsistent with positive labels. No-answer questions have no
positive labels; they are excluded from quality macro-averages and counted separately
with their result-presence and timing information. The seed has no no-answer questions;
that behavior is covered by automated fixtures.

## Run configuration and artifacts

TOML config fields are `schema_version=1`, `benchmark`, `strategy="bm25"`,
`unit="symbol"` or `"file"`, `ks`, `warmup_queries`, `repeats`, `seed`, and an `indexes`
mapping from every repository ID to its database. Paths resolve beside the config.
M4 also accepts `strategy="dense"`, `"hybrid"`, or `"symbol"`, which require
`model_cache` and a `vectors` mapping with exactly the same repository IDs as `indexes`.
BM25 rejects these unused fields. Encoder and fusion parameters are fixed in code and
recorded in run metadata; the three new configs freeze the initial comparison.

The runner requires clean pinned-commit provenance and exact selected-source/ignore
hashes. This corpus check is independent of chunk sizes; the complete index settings
and snapshot ID are recorded so chunking experiments remain traceable. Skipped-source
diagnostics and missing target locators fail validation before any output is created.

For M3, every matching chunk is considered before deduplication and truncation to the
largest K. There is no hidden fixed candidate cap. First occurrence wins for each
symbol/file and ties inherit the baseline's stable chunk-ID ordering.

Queries are shuffled reproducibly per repository using the seed. The first configured
number are warmed up once, then each query is timed `repeats` times. Measurement
includes preprocessing, BM25 scoring, result materialization and unit deduplication;
metrics and serialization are excluded. Index/model loading is measured separately
and must not be described as a guaranteed cold-disk measurement. Percentiles use linear
interpolation at `(sample_count - 1) * fraction`.

Artifacts are published together into a new directory only after a successful run:

| File | Content |
| --- | --- |
| `summary.json` | Aggregate/group metrics, runtime/code/config/data provenance, quality fingerprint |
| `per_query.jsonl` | Each query's metrics, judgment counts, and raw timing samples |
| `rankings.jsonl` | Top units, source locators, scores, evidence chunk ranges, nullable judgments |
| `metrics.csv` | One query/K pair per row; undefined no-answer quality cells are blank |
| `report.md` | Human-readable tables and interpretation limits |

`judged_fraction` is judged returned units divided by actually returned units at K
(zero for empty output), averaged over queries. Explicit grade 0 is judged; absence
from qrels is unjudged and scored as zero. Precision still divides by K, including
missing result slots. Small positive-only pools can cap observable precision far
below 1, so avoid interpreting it as exhaustively adjudicated precision.

The quality fingerprint excludes timings, timestamps, and machine paths, but includes
the benchmark digest, unit/K choices, per-query quality results, and ranked evidence.
Source-code and lockfile hashes, Git dirty state, package versions, hardware and
relevant thread settings are recorded separately. Byte-identical quality fingerprints
are expected for repeated runs in the same locked environment, not bit-identical
timing or whole-report files.

## M4 comparison and costs

Dense, hybrid and symbol-aware strategies consider all dense rows (including negative
cosines) before symbol/file deduplication. Hybrid RRF uses complete BM25/dense chunk
rankings; symbol-aware adds the field-feature ranking. There is no tuned threshold or
candidate cap. Dense has no calibrated abstention mechanism, so an unknown query can
still return results. The same no-answer accounting remains active.

All methods share canonical inputs before the encoder's documented 256-word-piece
truncation. Raw chunk text and qrel mapping are unchanged. Vector metadata reports
truncated-document counts, build time, dimensions and array bytes. The model is loaded
once per experiment; its initialization is timed separately from per-query encoding,
scoring, fusion and deduplication. Existing vector artifacts are loaded, never rebuilt
silently during evaluation. BLAS is not used for dense row scoring; CPU encoding uses
four torch threads and deterministic algorithms. This does not promise bitwise
agreement across different hardware, platforms or library versions.

`sacr compare --run BASELINE --run OTHER --output NEW_DIRECTORY` validates the
benchmark digest/status, unit, K values, repository snapshots and query IDs. It writes
`report.md` and `comparison.json`, including each query's quality delta and win/tie/loss
counts (absolute tolerance 1e-12). It does not compare unlike evaluation units.
M6a additionally verifies saved quality fingerprints, query text/metadata and summary
quality; it reports paired cluster-bootstrap intervals where repository counts permit.
The two-repository seed receives descriptive differences with intervals withheld.
See [review and uncertainty protocol](review.md) for weighting, limitations and commands.
Latency values are observations from separate runs, not controlled paired timing
estimates. Read per-run hardware/startup provenance when comparing costs.

## M5 relations, ablations and context accounting

`strategy="structure"` requires a `graphs` mapping with the same repository IDs as
`indexes`. Its optional `[structure]` table defines `seed_strategy` (hybrid, symbol,
or bm25), `relations`, `seed_k`, `max_neighbors`, `max_expanded`, `max_edges`, and `alpha`.
Hybrid/symbol seeds require the M4 model/vector fields; BM25 seeds reject unused model
fields. Optional top-level `name` identifies a run in comparisons without changing
the strategy. Other strategies reject structure-specific fields.

Freeze the 11 structure configs before examining results. Together with Hybrid and
Symbol-aware baselines, `scripts/run_m5.py` runs 13 configurations on unchanged labels,
snapshots and vectors. Disabled relations must reproduce the Hybrid ranking and
quality fingerprint exactly. Single-type and leave-one-out results are exploratory;
do not select a test-set winner or rewrite labels after seeing these scores.

Graph hashes, build seconds, archive sizes, edge/confidence counts and unresolved
reason counts are recorded per repository. These counts measure extractor output,
not relation precision/recall. Provenance on every boosted evidence chunk records
the seed ID/rank/chunk, edge ID/type/direction, source path/line/expression, confidence,
weight and support. Unboosted evidence retains the baseline representation.

Per-query `retrieval_work` records seed count, examined edges, expanded non-seed
symbols and seeds hitting the edge cap. Graph work is included in retrieval latency.
Dense seeds still score all chunks; expanded symbols are already present somewhere
in the full ranking and receive additional support, not new embeddings.

`context_cost` reports per-K UTF-8 bytes, physical source lines and lexical tokens,
summing one winning evidence chunk per unique returned symbol/file. It neither
materializes whole functions/files nor applies an LLM context budget. Lexical tokens
use the existing identifier tokenizer and are explicitly a proxy. Cost fields are
excluded from the existing quality fingerprint; graph-derived scores/provenance are
included with ranked evidence. Reporting and context accounting are outside timing.

## M6a audit and label review

`scripts/run_m6a.py` reuses committed BM25/Dense M4 runs and Hybrid/Symbol/Structure M5
runs, retaining their recorded timing/provenance. It unions their top-10 symbols with
all original qrels into a snapshot-bound review pool. New candidates remain unjudged;
the original 40 questions and labels are unchanged. Candidate-pair counts must not be
reported as query counts. Full local review bundles contain source evidence and blank
decision templates; committed M6a artifacts retain metadata and the pending status.

Review checks enforce complete identities and rationales, frozen pool evidence,
query clarity, and agreement between answerability and positive reviewed targets.
These are structural checks, not proof of independent human review. New labels need
adjudication, a new benchmark version and reruns of every strategy. M6b/M6c retain
the planned wider/public datasets, held-out protocol and scale measurements.

## M6b source-checked draft suite

The explicit suite manifest now separates the existing 40-query development seed,
120 test-candidate questions on Flask/Rich/NetworkX/Packaging/TOMLKit and ten public
RepoQA Marshmallow descriptions adapted to symbol retrieval. All three manifests
remain provisional. Primary planned measures are Recall@10 and NDCG@10; review and
formal test execution remain outstanding. Exact suite membership is frozen by data
and provenance digests, not by a mutable directory name.

`audit-suite` validates repository URL disjointness, normalized exact question-text
uniqueness, source snapshots, qrel targets, intended split roles and primary-K support.
It does not score any question. `pool-labels` provides a source review bundle from
existing qrels without loading predictions. This keeps initial test-label review
separate from retrieval outcome inspection. Neither operation establishes completeness
of relevance labels; later pooled judgments need independent review and new versions.

The public adapter retains descriptions, checks archive/file hashes and exact AST
byte/line bounds, and includes decorators in target ranges. Full source including
tests/docstrings is indexed, so its retrieval metrics are not upstream RepoQA scores.
See [benchmark selection, attribution and reproduction](benchmarks.md).
