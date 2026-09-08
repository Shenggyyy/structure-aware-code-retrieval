# M5: Structure-Aware Retrieval and Ablations

This fixed 13-configuration experiment uses the unchanged 40-query Requests/Click
development set, M4 chunks/vectors and existing labels. Judgments remain **provisional,
agent-authored and pending independent human review**. These are measured development
tradeoffs, not a held-out result, significance test or claim of universally better retrieval.

## Main observation

Full structure support raises Recall@10 from **0.8208 to 0.8875**, but lowers MRR@10
from **0.6394 to 0.4647** and NDCG@10 from **0.6450 to 0.5545**. It recovers more known
evidence while putting worse-ranked evidence ahead of correct direct matches. Warm
p50 rises from 33.61 to 41.08 ms, and mean returned lexical tokens at K=10 rise from
997.4 to 1,062.8. This is not an overall quality improvement.

Against Hybrid, full structure improves/ties/regresses on 5/35/0 queries for Recall@10,
but 7/15/18 for NDCG@10. The unjudged-candidate and small correlated development-set
limitations still apply. Related source can be useful context without being the
correct answer to a symbol-localization question; LLM answer quality is not measured here.

## Fixed ablations

All rows use symbol-level evaluation at K=10. The final row changes the seed strategy;
other structure rows use Hybrid. No parameter sweep or post-result tuning was performed.

| Run | Recall | NDCG | Warm p50 ms | Mean lexical tokens |
| --- | --- | --- | --- | --- |
| Hybrid baseline | 0.8208 | 0.6450 | 33.61 | 997.4 |
| Symbol-aware baseline | 0.7917 | 0.5823 | 71.58 | 920.5 |
| Full structure | 0.8875 | 0.5545 | 41.08 | 1062.8 |
| No relations | 0.8208 | 0.6450 | 34.77 | 997.4 |
| Containment only | 0.8333 | 0.6417 | 42.16 | 1021.8 |
| Import only | 0.8208 | 0.6430 | 41.06 | 1003.0 |
| Call only | 0.8875 | 0.5697 | 42.22 | 1041.1 |
| Test only | 0.8208 | 0.6082 | 40.20 | 1008.8 |
| Without containment | 0.8875 | 0.5587 | 41.39 | 1038.2 |
| Without imports | 0.8875 | 0.5548 | 40.91 | 1048.8 |
| Without calls | 0.8333 | 0.6060 | 40.77 | 1038.5 |
| Without test links | 0.8875 | 0.5621 | 41.69 | 1085.2 |
| Full structure, Symbol-aware seeds | 0.8333 | 0.5719 | 75.41 | 948.4 |

Call-only matches full structure's aggregate Recall@10; removing calls loses most of
that gain. Additional types do not improve Recall@10 in this configuration and can
worsen early ordering. This is a conditional observation, not proof that those relation
types are useless. Full structure with Symbol-aware seeds improves recall relative to
its own baseline (4/36/0 paired queries), but NDCG again worsens (7/20/13). The general
comparison's paired deltas use Hybrid, so they should not be read as isolating graph
effects for the different-seed row.

See [all metrics and K values](runs/comparison/report.md) and
[per-query differences](runs/comparison/comparison.json). Separate-run latency is
hardware/load dependent; the no-edge control's timing difference is not a ranking change.

## Source-grounded cases

- `click-14`, tracing option prompting: the call at `src/click/core.py:2891` from
  `Option.prompt_for_value` promotes `src.click.termui.prompt` to rank 1. NDCG@10
  improves by 0.3927 against Hybrid.
- `requests-10`, proxy-bypass lookup: reverse support from the call at
  `src/requests/utils.py:832` promotes the caller `get_environ_proxies`, while forward
  support promotes nested/helper routines. These displace the previously first-ranked
  `should_bypass_proxies`; NDCG@10 decreases by 0.6438.
- `requests-01`, locating `cookiejar_from_dict`: reverse call/test support promotes
  callers and a test above the requested implementation. NDCG@10 decreases by 0.6131.

The relationships are inspectable, but graph proximity alone does not establish
query relevance. Unjudged neighbors are scored zero under the frozen protocol;
human review must determine which deserve additional supporting labels, independently
of whether that would improve the method's score. No labels were changed here.

## Graph and context costs

| Repository | Containment | Imports | Calls | Test links | Unresolved references | Build seconds | JSON bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Requests | 753 | 188 | 337 | 419 | 2004 | 0.142 | 841925 |
| Click | 1382 | 229 | 636 | 524 | 2540 | 0.245 | 1225936 |

Cross-boundary test calls are classified only as `test`, making call/test ablations
disjoint. Unresolved counts include imports, builtins/external calls, dynamic receivers
and conservative ambiguity/shadowing exclusions. Counts are extractor observations,
not measured graph accuracy. Build times exclude JSON serialization/publication.

Full structure examines a mean 30.3 edges and expands 12.925 non-seed symbols per query;
two seed expansions across the 40 questions hit the edge cap. Budgets are 5 seeds,
64 examined edges per seed, 8 selected neighbors per seed and 20 expanded symbols total.
Expansion is one hop; repeated evidence uses maximum support, not accumulated votes.
The baseline still scores all chunks, so this is not a full-scan scalability improvement.

Context costs sum one evidence chunk per returned symbol/file, not complete functions
or files. Lexical tokens are a volume proxy, not LLM billing tokens. The full run's mean
K=10 UTF-8 context grows from 7,189.6 to 7,673.6 bytes. Query encoding, graph work and
reranking are timed; graph/model loading and context/metric/report accounting are not.
Per-run startup, hardware, index, model and graph provenance are retained in summaries.

## Reproduction and validation

Follow [graph preparation and suite commands](../../README.md#structure-aware-retrieval).
The suite needs already-prepared local model, vector and graph files, and a new output
directory. Model-free graph extraction and BM25-seeded structure search are also supported.
For the comparison alone:

```text
uv run --locked sacr compare --run reports/m5/runs/hybrid-seed --run reports/m5/runs/structure-full --run reports/m5/runs/structure-none --output artifacts/runs/m5-main-comparison
```

All 13 configurations were repeated independently with offline flags and reproduced
exact rankings and quality fingerprints. No-relations reproduces Hybrid's M4/M5
fingerprint `c7335a38926235df83754b0c34d7409f83bfb8ddd8d6f0c88b1771ec95ef4e53`.
Full structure's fingerprint is
`7e9c330e43ddce1429d3edc8e0ef1f1b3f156e6c86c2ce653983c6a2d87281a5`.
Both graphs were re-extracted with identical graph hashes. All 1,468 recorded support
paths were checked against graph edges, directions, seed chunks, score formulas and
budgets. This verifies implementation consistency, not independent semantic correctness.

Local verification: 119 tests passed, one real-symlink test skipped on Windows, and
coverage was 92%, including an installed-wheel run in a base environment without torch.
Ruff lint/format and wheel/source builds passed. M5 remote CI runs after the owner pushes.

Recorded source/lock hashes describe the actual working implementation before the
owner's M5 commit, with dirty Git provenance. Raw runs retain timings and all top-20
ranked source evidence. Downloaded code, vectors and graph files stay in ignored
`artifacts/`; graphs are regenerated from the pinned snapshots.

The engineering retrieval MVP is implemented. Human-reviewed labels, broader
repository-disjoint experiments, graph accuracy assessment, QA and Docker delivery
remain required before the full project is complete. M6 should investigate the recall
versus ordering tradeoff without treating these development results as held-out evidence.
