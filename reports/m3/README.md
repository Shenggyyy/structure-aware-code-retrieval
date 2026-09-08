# M3: BM25 Development Evaluation

These are measured results from the 40-query [seed dataset](../../benchmarks/seed-v1/README.md),
not estimates. Its 55 source-checked judgments are **agent-authored and provisional**;
independent human review is still pending. This is a development baseline, not a
held-out benchmark or evidence that structure-aware retrieval improves quality.

## Recorded results

Macro averages over 40 answerable queries, using known positive labels:

| Evaluation unit | Precision@10 | Recall@10 | MRR@10 | NDCG@10 | Warm p50 / p95 (ms) |
| --- | --- | --- | --- | --- | --- |
| Symbol | 0.0975 | 0.7542 | 0.6182 | 0.6203 | 8.044 / 15.866 |
| File | 0.1200 | 1.0000 | 0.8187 | 0.8640 | 3.914 / 7.380 |

Both rows use the same BM25 retrieval strategy. File-level evaluation collapses
symbols into files and changes the target, so its higher scores are **not a strategy
improvement**. A correct file can still contain an incorrectly ranked function.
Only 10% of returned symbol results at K=10 have explicit judgments; unjudged results
score zero. Low precision therefore cannot be interpreted as exhaustive irrelevance.

See the [symbol report](bm25-symbol/report.md) and [file report](bm25-file/report.md)
for all K values and repository/category breakdowns. Each directory also contains
`summary.json`, `per_query.jsonl`, `rankings.jsonl`, and `metrics.csv`, including raw
timings and source locations. Ranking artifacts contain metadata, not upstream code.

## Failure examples

- `requests-02`: the explicitly requested `PreparedRequest.prepare_url` ranks 18th;
  a similarly named, explicitly irrelevant test helper ranks second.
- `click-01`: `CliRunner.invoke` is absent from the top 20 even though the query
  names it. The containing class ranks second; that is not the requested method.
- `click-14`: the two option methods rank 7th and 10th, while the interactive
  `prompt` implementation ranks 13th. Recall@10 is only 2/3 for the labeled chain.

These cases motivate testing symbol matching and relation expansion in later stages.
They do not establish that those methods will help. Freeze this version and compare
new strategies on the same inputs; add human-reviewed pooled judgments separately.

## Reproduce

From the repository root after `uv sync --locked --dev`:

```text
uv run --locked sacr prepare-benchmark benchmarks/seed-v1/benchmark.json
uv run --locked sacr evaluate --config configs/bm25-seed.toml --output artifacts/runs/m3-symbol-reproduce
uv run --locked sacr evaluate --config configs/bm25-seed-file.toml --output artifacts/runs/m3-file-reproduce
```

Use a new output directory for every run. Compare `quality_fingerprint` in the new
and checked-in summaries; timestamps, index load time and retrieval latency vary.

| Unit | Expected quality fingerprint |
| --- | --- |
| Symbol | `490a2b5d836d280ab8cb657f41d6705fd4b45ebcafff201200b28c8f6f2b4d50` |
| File | `b8c697958b829f0acd366a4f73602b89b5f10a89415eed65d95161e40397b249` |

M3 validation reproduced the symbol rankings and quality metrics after a fresh
download and index rebuild in a separate directory. A repeated file-level run also
matched exactly. Each query was timed three times after two warmup queries per
repository, with seed 0. Windows 11, Python 3.12.14, 20 logical CPUs, and the locked
packages were used; full runtime details are in the summaries. Timing includes
preprocessing, scoring, materialization and deduplication, but excludes loading and
metric/report generation. This is a small-corpus measurement, not a scale claim.

Reports were generated before the owner's M3 commit. Accordingly, implementation
provenance records the preceding commit and `dirty: true`, together with the actual
Python source hash and lockfile hash. Do not replace that history with an invented
clean commit. Cross-platform reproduction has not yet been demonstrated.

Local checks: 75 tests passed, one real-symlink test skipped on Windows, 91% coverage;
Ruff lint/format and wheel/source builds passed. Remote CI runs after the owner pushes.
