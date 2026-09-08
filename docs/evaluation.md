# Evaluation Protocol

This is the planned protocol. M2 has a BM25 implementation and real-repository smoke
checks, but no labeled benchmark or quality metrics. Finalize executable schemas and
metric edge cases in M3 before comparing strategies. Smoke queries verify functionality
and expose examples; they do not establish Recall, Precision, MRR, or NDCG.

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

Use K in {1, 5, 10, 20}. Proposed grades are 0 (irrelevant), 1 (supporting), and 2
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
