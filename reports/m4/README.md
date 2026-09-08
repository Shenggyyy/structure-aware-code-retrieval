# M4: Four Retrieval Baselines

Measured on the unchanged [40-query Requests/Click development set](../../benchmarks/seed-v1/README.md).
Its 55 judgments remain **provisional and pending independent human review**. M4 adds
working baselines and evidence about their tradeoffs; it does not claim a final model
comparison, significance, or generalization to unseen repositories.

## Main results

Symbol-level macro averages over 40 answerable queries:

| Strategy | Precision@10 | Recall@10 | MRR@10 | NDCG@10 | Warm p50 / p95 (ms) |
| --- | --- | --- | --- | --- | --- |
| BM25 | 0.0975 | 0.7542 | 0.6182 | 0.6203 | 7.436 / 15.470 |
| Dense | 0.1000 | 0.7833 | 0.5738 | 0.5968 | 20.867 / 29.185 |
| Hybrid | 0.1025 | 0.8208 | 0.6394 | 0.6450 | 32.148 / 46.038 |
| Symbol-aware | 0.0975 | 0.7917 | 0.5610 | 0.5823 | 66.779 / 110.317 |

Hybrid has the highest Recall@10 and NDCG@10 in this run, with higher latency than
BM25. Dense increases recall slightly but lowers MRR and NDCG. The symbol heuristic
raises Recall@20 to 0.9333 while hurting top-ranked quality and adding feature-scoring
cost. More signals do not automatically produce a better ranking.

Relative to BM25, Recall@10 improves/ties/regresses on 4/34/2 queries for Hybrid and
6/28/6 for both Dense and Symbol-aware. NDCG@10 changes are 11/18/11 for Hybrid and
11/14/15 for Symbol-aware. Counts are descriptive; correlated questions and incomplete
labels preclude interpreting them as significance tests. Only roughly 10% of returned
top-10 symbols are explicitly judged, so observed precision is not exhaustive.

## Successes and regressions

- Hybrid improves `requests-15` (multipart upload implementation) by 0.5693 NDCG@10
  and `click-12` (normalized subcommand lookup) by 0.5000.
- Hybrid regresses `click-08` (case-insensitive choices) by 0.5000 and `click-15`
  (exception handling and error output) by 0.4447.
- Symbol-aware improves `click-19` (numeric-range tests) by 1.0000 but regresses
  `click-05` (the output helper) by 1.0000 NDCG@10. Matching metadata can displace
  relevant code; no feature weights or benchmark labels were changed after these runs.

These are observations against the existing labels, not independently verified
explanations of every miss. Inspect [paired query deltas](comparison/comparison.json)
and each strategy's `rankings.jsonl` to review source evidence and branch scores.
M5 should test seed selection and relationship ablations, including regressions.

## Index and execution costs

The pinned MiniLM encoder uses CPU, float32, 384 dimensions, 256 tokenizer tokens,
document batch size 32 and four torch threads. Canonical text is identical across
methods before encoder truncation; no alternative chunking was introduced.

| Repository | Chunks | Truncated chunks | Encoding/build seconds | Vector array bytes | Archive bytes |
| --- | --- | --- | --- | --- | --- |
| Requests | 867 | 134 (15.46%) | 15.133 | 1,331,712 | 1,269,145 |
| Click | 1,771 | 193 (10.90%) | 25.724 | 2,720,256 | 2,591,688 |

Build seconds cover text preparation, token-length counting and encoding, excluding
model startup and archive serialization. The initial model load took about 6.35 seconds
including imports; per-experiment startup observations are recorded in each summary.
Archive and array sizes are not process peak-memory measurements. Those measurements
and large-repository throughput remain future work.

Retrieval timings include fresh query encoding, full scoring, fusion and symbol/file
deduplication, excluding model/index startup and metric/report writing. No query-vector
cache is used. Each repository warms two queries; all queries are shuffled with seed 0
and measured three times. Windows 11/Python 3.12.14 and the locked CPU packages were
used. Separate strategy processes share the machine, so latency differences are
observed costs, not controlled paired estimates.

## Artifacts and reproduction

The [generated comparison](comparison/report.md) shows every K. The [BM25](bm25/report.md),
[Dense](dense/report.md), [Hybrid](hybrid/report.md) and [Symbol-aware](symbol/report.md)
directories contain full summaries, per-query metrics, rankings, CSV and Markdown.
Vector arrays/model weights remain ignored under `artifacts/`; no downloaded code or
weights are committed.

Follow the [README commands](../../README.md#dense-hybrid-and-symbol-aware-retrieval).
For a comparison of these already-recorded runs, no optional model install is needed:

```text
uv run --locked sacr compare --run reports/m4/bm25 --run reports/m4/dense --run reports/m4/hybrid --run reports/m4/symbol --output artifacts/runs/m4-recorded-comparison
```

The BM25 quality fingerprint remains identical to M3. Independent offline process
repeats of all three new strategies reproduced their exact rankings and quality
fingerprints; latency and timestamps differed. Recorded runs use the pre-M4 commit with dirty
working-tree provenance and the actual source/lock hashes, because the owner commits
after milestone validation. Cross-platform numerical equivalence is not claimed.

The general sentence encoder's pretraining overlap is not audited; it is not a
code-specialized model-selection study. Human label review remains an explicit open
acceptance item inherited from M3. See [baseline definitions](../../docs/baselines.md)
for fixed parameters, failure modes and the next experiment boundaries.

## Local verification

Ruff lint/format checks and wheel/source builds passed. The built wheel was installed
into a separate base environment with no torch or Sentence Transformers: 97 tests
passed, one real-symlink test skipped on Windows, and coverage was 91%. That installation
also reproduced the comparison from recorded runs without model dependencies. Build
archives were inspected to exclude downloaded artifacts and local caches. Real-model
tests used the locked optional environment and offline flags; remote CI has not run
for M4 until the owner pushes.
