# Fixed Experiment Matrix and Cost Protocol

## Scope

M6c reuses the existing five retrieval strategies and M5 relationship ablations.
`evaluation/experiments.py` freezes 15 configurations before any query is executed:
Hybrid, BM25, Dense, Symbol-aware, full structure, no relations, four single-relation
settings, four leave-one-out settings, and structure with Symbol-aware seeds.
All settings come from the existing TOML files; the wider test scores are not used
to adjust weights, seeds, graph budgets, encoder choice or primary metrics.

Each configuration runs separately on development (40 queries), expanded test
candidates (120) and the public adaptation (10). These **45 runs are not 45
independent benchmarks**. Roles are never pooled into a single headline quality score.
The same repository is selected for each query across all strategies.

All current labels remain provisional. By default the script refuses these labels;
`--allow-provisional` explicitly permits draft experiments and records that choice.
This flag does not replace independent review or make the suite's reviewed-label
acceptance complete. Once outcomes are visible, the test candidate set must be
described as exposed; future tuning requires another untouched test version.

## Reproduction

From the repository root, with Git and Python 3.12:

```text
uv sync --locked --dev --extra dense
uv run --locked --extra dense python scripts/run_m6b.py --prepare --output artifacts/m6b-inputs
uv run --locked --extra dense sacr prepare-model --cache artifacts/models
uv run --locked --extra dense python scripts/run_m6c.py --allow-provisional --output artifacts/m6c-reproduce
```

Choose new output directories. Preparation and `prepare-model` may download pinned
inputs. M6c itself is offline: it requires the existing validated SQLite indexes,
their original clean source checkouts and the local pinned model. It rebuilds eight
indexes, eight graphs and eight vector archives inside the new output directory.
Existing artifacts, labels and earlier reports are preserved. Upstream source is
parsed, never imported or executed. No API key or GPU is needed.

The script runs sequentially and prints the current build/experiment. Runtime varies
with hardware and corpus size. A failed worker retains `job.json`, `worker.log` and
`failure.json`; an interrupted suite lacks final `suite-results.json`. Inspect the
failure and use a fresh output directory after fixing its cause. Automatic resume
or reuse of partial measurements is deliberately not implemented.

## Freeze and evidence

`plan.json` records the suite digest, inherited strategy settings, source snapshots,
model specification, implementation hash, lockfile hash, role/order and cost protocol.
Generated TOML configs bind those settings to the rebuilt artifacts;
`configuration-files.json` records their normalized-text checksums. Before each run,
the worker checks config and benchmark identity, and the coordinator rejects an
implementation change during the suite. Index/vector/graph loaders retain their
existing source and checksum validation.

Each run saves the existing metrics CSV, per-query metrics, rankings, runtime data
and quality fingerprint. `comparison/<role>/` uses Hybrid as the common reference;
`ablations/<role>/` uses full structure as the reference. Recall@10 and NDCG@10 remain
primary. Other K values, Precision, MRR, categories and returned-context proxies are
secondary. Intervals use the existing paired repository-cluster bootstrap: 2,000
draws, seed 0, withheld below five contributing repositories. Five heterogeneous
repositories do not guarantee reliable coverage. Intervals do not correct missing
labels, source-selection bias or multiple comparisons.

Reproduction should compare rankings and quality fingerprints, not byte equality of
timing reports. Construction timestamps, Git dirty state, machine information and
timing can differ. Different native-library/platform behavior can also affect float
scores; retain the locked environment and investigate mismatches rather than silently
replacing old results.

## Timing, storage and memory

Every construction operation and experiment uses a fresh Python worker. The wrapper
sets OMP, MKL and OpenBLAS thread environment variables to four; the encoder also
uses its existing four-thread CPU setting. Worker logs and profiles remain local.

`operation_seconds` includes operation-specific imports, input loading, construction
or evaluation, and artifact serialization. Vector construction therefore includes
loading the model; its nested `build_seconds` excludes model loading and is not the
same measure. `worker_wall_seconds` additionally includes process startup, profiling
and shutdown. Builds have one sample per operation, with uncontrolled filesystem/OS
caches. These measurements are observations, not cold-cache or asymptotic benchmarks.

Warm retrieval p50/p95 comes from the existing runner: two warmup queries per
repository, three repetitions per measured query, fixed shuffled query order. It
includes query encoding, ranking, fusion and unit deduplication; startup, offline
construction and report generation are excluded. The worker loads all repositories
for its role, so its memory peak is not a single-repository retrieval measurement.

Peak memory is the worker's OS lifetime high-water mark, including Python, native
libraries, model weights and imports, excluding child processes. Windows uses
[PeakWorkingSetSize](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters);
Linux/macOS use [resource.getrusage](https://docs.python.org/3.12/library/resource.html)
with platform unit conversion. This is neither an allocation delta nor private
memory; values from different OS methods should not be equated directly. The
profiler adds no dependency and does not poll sampled RSS or use `tracemalloc`.

Storage fields count serialized SQLite, compressed vectors and graph JSON files.
They exclude source clones, shared model cache and experiment outputs. Vector
profiles also retain float32 payload size and pre-truncation document counts.
Lexical context tokens remain a proxy, not LLM billing tokens. No answer correctness,
API token usage or end-to-end QA latency is measured until M7.

## Review after retrieval

Keep the M6b source-first reviews separate from later outcome-informed pooling. To
create a broader blinded pool, pass all fixed run directories for one role to
`sacr pool`; never combine public and original-question labels. Reviewers must check
missing alternatives, misleading questions and sparse positives. Preserve submissions,
adjudicate disagreements, publish a new label version and rerun every strategy.
Neither this experiment script nor CI supplies independent human judgments.
