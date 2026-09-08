# Structure-Aware Code Retrieval and Evaluation for Repository-Level LLM Applications

A Python project investigating whether repository structure improves code retrieval
for LLM applications. The planned system compares lexical, dense, hybrid,
symbol-aware, and structure-aware retrieval, then supplies evidence to repository QA.

**Status: M4 — retrieval baseline comparison.** Python indexing, BM25, dense, hybrid,
and symbol-aware search are available, with reproducible evaluation and comparison
reports. The 40-query Requests/Click development set remains **provisional, pending
human review**. Structure-aware graph retrieval and LLM QA remain planned.

## Quickstart

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) first. From the
repository root, run these commands in PowerShell or a POSIX shell:

```text
uv sync --locked --dev
uv run --locked sacr --help
uv run --locked sacr --version
uv run --locked sacr index tests/fixtures/sample_repo --output artifacts/sample.sqlite
uv run --locked sacr search "calculate_checksum" --index artifacts/sample.sqlite --top-k 3
```

Python **3.12** is the supported runtime, selected by `.python-version`. uv downloads
it if needed and creates `.venv/`; initial setup needs network access. CI uses uv
**0.12.5**. Commit `uv.lock` to preserve application and development dependencies.

`sacr --version` prints `sacr 0.1.0`. Running `sacr` without arguments prints help.
The equivalent module entry point is:

```text
uv run --locked python -m structure_aware_retrieval --help
```

The BM25 quickstart requires no API key, model download, GPU, or Docker. The
sample fixture is only parsed: it intentionally raises an error if executed.

## Index and search a repository

```text
uv run --locked sacr index . --output artifacts/project.sqlite
uv run --locked sacr search "build_index" --index artifacts/project.sqlite --top-k 5
uv run --locked sacr search "build_index" --index artifacts/project.sqlite --json
```

Index creation refuses an existing output. To refresh a snapshot, repeat the index
command with `--overwrite`; only an existing SACR database can be replaced. Source
changes do not update the index automatically. Search returns stored snapshot code,
even when the original files have changed or are unavailable.

Options for `sacr index`:

| Option | Default / behavior |
| --- | --- |
| `--output` | `artifacts/index.sqlite`; SQLite destination |
| `--max-chunk-lines` | 80; split long source spans into non-overlapping chunks |
| `--max-file-bytes` | 1,048,576; skip larger files with diagnostics |
| `--exclude` | Repeatable root-relative gitignore patterns, e.g. `--exclude "tests/"` |
| `--overwrite` | Atomically rebuild an existing SACR index |
| `--json` | Emit counts, snapshot provenance, config, and skipped-file diagnostics |

The scanner reads `.py` files, applies root/nested `.gitignore` rules, and always
excludes directories such as `.git`, `.venv`, `__pycache__`, `build`, and `artifacts`.
It skips links/junctions and does not import source code. Syntax/encoding/read errors
are reported; unreadable directories or ignore rules abort indexing. Unlike Git's
tracked-file behavior, ignore rules apply to all scanned files. Global ignore rules
and `.git/info/exclude` are not applied.

Search returns **chunks**, which may represent only part of a long function. Paths
are relative to the indexed root and line ranges are one-based and inclusive.
`--json` includes full chunk text, IDs, scores, and snapshot ID; text output previews
12 lines. Empty matches are successful searches with no results.

## BM25 baseline and limitations

Canonical text combines the relative path, path-qualified symbol name, normalized
signature, and original chunk code. Tokenization retains complete identifiers and
snake_case/camelCase components, case-folds text, and uses no stemming or stopwords.

The baseline uses `rank-bm25`'s **BM25Plus with k1=1.5, b=0.75, delta=0**. This explicitly
chosen variant has positive IDF even for tiny corpora; unmatched chunks score zero.
Query terms are deduplicated, and score ties use stable chunk IDs. There is no field
boosting, semantic embedding, symbol-specific reranking, or graph expansion yet.

An index stores tokens and code, not Python pickles. Loading reconstructs BM25 term
statistics in memory once per retriever; each CLI search includes this startup cost.
M2 is an in-memory lexical baseline, not a demonstrated large-scale search engine.
Imports are recorded but not resolved; call/test relationship analysis comes later.

See the [Requests smoke validation](docs/validation/m2.md) for real-source results,
including queries where lexical ranking chooses the wrong implementation first.

## Run the evaluation

From the project root, prepare the pinned sources and run the two evaluation units:

```text
uv run --locked sacr prepare-benchmark benchmarks/seed-v1/benchmark.json
uv run --locked sacr evaluate --config configs/bm25-seed.toml --output artifacts/runs/bm25-symbol-001
uv run --locked sacr evaluate --config configs/bm25-seed-file.toml --output artifacts/runs/bm25-file-001
```

Preparation requires Git/network access on first use, clones with fixed LF checkout
settings, verifies commits, and builds indexes under `artifacts/benchmark/`. It reuses
valid existing indexes. Use `--rebuild` to rebuild them explicitly. Existing source
checkouts are never reset. Evaluation itself works offline and never fetches code.

Config paths resolve relative to the TOML file. Each run requires a **new output
directory** and produces `summary.json`, `per_query.jsonl`, `rankings.jsonl`,
`metrics.csv`, and `report.md`. A repeat with the same data/config should reproduce
the quality fingerprint; timing is hardware- and load-dependent.

The runner validates corpus hashes and source targets before retrieval, then computes
Precision@K, Recall@K, MRR@K, NDCG@K and warm p50/p95 latency for K=1,5,10,20. It reports
overall, per-repository and per-category results. Duplicate chunks are merged before
the symbol/file cutoff; file judgments use the maximum grade of labeled symbols.

Unjudged results count as nonrelevant for scoring and judgment coverage is reported.
The seed labels are sparse, agent-authored and not yet human-reviewed: scores measure
agreement with known labels, not exhaustive real-world relevance. See the
[dataset card](benchmarks/seed-v1/README.md), [evaluation protocol](docs/evaluation.md),
and [recorded M3 results](reports/m3/README.md).

## Dense, hybrid and symbol-aware retrieval

Install the optional CPU dependencies and download the pinned model once:

```text
uv sync --locked --dev --extra dense
uv run --locked --extra dense sacr prepare-model --cache artifacts/models
uv run --locked --extra dense sacr prepare-benchmark benchmarks/seed-v1/benchmark.json
uv run --locked --extra dense sacr embed --index artifacts/benchmark/indexes/requests.sqlite --output artifacts/benchmark/vectors/requests.npz
uv run --locked --extra dense sacr embed --index artifacts/benchmark/indexes/click.sqlite --output artifacts/benchmark/vectors/click.npz
uv run --locked --extra dense sacr search "prepare an HTTP request URL" --strategy hybrid --index artifacts/benchmark/indexes/requests.sqlite --vectors artifacts/benchmark/vectors/requests.npz
```

Supported `--strategy` values are `bm25` (default), `dense`, `hybrid`, and `symbol`.
Dense strategies use `--model-cache artifacts/models` by default; only `prepare-model`
allows model downloads. Search, embedding and evaluation use local model files.
`embed` requires a new output file. After changing a source index or encoder dependencies,
create new vectors and point search/configs to them; stale caches fail validation.

Run all four strategies on the same symbol-level benchmark, then compare:

```text
uv run --locked --extra dense sacr evaluate --config configs/bm25-seed.toml --output artifacts/runs/m4-bm25-001
uv run --locked --extra dense sacr evaluate --config configs/dense-seed.toml --output artifacts/runs/m4-dense-001
uv run --locked --extra dense sacr evaluate --config configs/hybrid-seed.toml --output artifacts/runs/m4-hybrid-001
uv run --locked --extra dense sacr evaluate --config configs/symbol-seed.toml --output artifacts/runs/m4-symbol-001
uv run --locked --extra dense sacr compare --run artifacts/runs/m4-bm25-001 --run artifacts/runs/m4-dense-001 --run artifacts/runs/m4-hybrid-001 --run artifacts/runs/m4-symbol-001 --output artifacts/runs/m4-comparison-001
```

The first `--run` is the comparison baseline. Different labels, snapshots, units or
K values are rejected; paired quality differences are saved per query.
See [M4 results](reports/m4/README.md) and [model/fusion details](docs/baselines.md).
The compact MiniLM model truncates long chunks to 256 word pieces; this is measured
in vector metadata. Symbol features are heuristics and can reduce retrieval quality.

## Development checks

```text
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest --cov --cov-report=term-missing
uv build
```

Use `uv run --locked ruff format .` to apply formatting. `uv build` creates a wheel
and source archive in `dist/` without publishing. Build-system requirements are
resolved separately in an isolated build environment; `uv.lock` locks application
and development packages.

Tests cover ignore rules, AST ranges/encodings, nested scopes, chunk bounds, SQLite
round trips and failed replacements, hand-calculated BM25 scores, and separate-process
search. Evaluation tests cover hand-calculated metrics, data rejection, no-answer
separation, deduplication, reproducible reports and atomic output failure. All tests
run offline after setup; real-source preparation is never part of the test suite.
GitHub Actions runs checks and builds on Windows
and Linux. Coverage is reported without a percentage gate. A real symlink-creation
test skips on Windows hosts without that privilege; link filtering also has a unit test.
CI's base installation does not download torch or model weights. Synthetic encoders
test cosine ranking, cache invalidation, RRF, symbol features, CLI integration and
cross-strategy reports offline. Real-model validation is recorded separately in M4.
Use `uv run --locked --extra dense ...` to retain optional dependencies while developing
with the model; `uv sync --locked --dev` restores the smaller base environment.

## Repository layout

```text
src/structure_aware_retrieval/
  cli.py                      Index, search, benchmark preparation, evaluation
  models.py                   Snapshot-scoped source objects
  ingestion.py                Filesystem scan and ignore rules
  parsing.py                  AST symbols, imports, source chunks
  indexing.py                 Atomic SQLite persistence
  tokenization.py             Identifier-aware lexical preprocessing
  retrieval.py                BM25 ranking over saved chunks
  embeddings.py               Pinned CPU encoder and persistent vector artifacts
  strategies.py               Shared interface, dense, hybrid and symbol retrieval
  evaluation/                 Dataset/config validation, metrics, runner, reports
tests/                        Unit/integration tests and source fixtures
docs/                         Design, evaluation plans, smoke validation
benchmarks/seed-v1/            Pinned corpus manifest, 40 queries, source judgments
configs/                      Reproducible symbol/file experiment settings
reports/m3/                   Selected real BM25 runs and their limitations
reports/m4/                   Four-strategy runs, paired comparison and analysis
.github/workflows/             Windows/Linux CI
pyproject.toml                Package metadata and tool configuration
uv.lock                       Locked application/development dependencies
```

Add future modules when their milestones begin. Keep downloaded repositories,
indexes, models, and intermediate results under ignored `artifacts/`. Keep
credentials in environment variables or ignored `.env` files.

## Scope and development route

The initial target is one fixed Python repository snapshot per query, with English
benchmark questions. Evaluate retrieval independently of LLM answers. The planned
system statically reads indexed code without executing or modifying it.

| Milestone | Deliverable |
| --- | --- |
| M1 | Package, CLI, checks, and design documentation |
| M2 | Python parsing, persistent indexing, BM25 search |
| M3 | Benchmark format, metrics, experiment runner |
| M4 | Dense, hybrid, symbol-aware retrieval |
| M5 | Structure-aware retrieval and ablations; retrieval MVP |
| M6 | Broader benchmarks, scale measurements, experimental analysis |
| M7 | Repository QA with source citations and answer evaluation |
| M8 | Docker, reproducible delivery, final result presentation |

See [architecture](docs/architecture.md), [milestone criteria and contribution workflow](docs/roadmap.md),
and [evaluation protocol](docs/evaluation.md).
Each milestone ends with validation and a suggested commit message. The owner
reviews, commits, and pushes changes before development moves on.
