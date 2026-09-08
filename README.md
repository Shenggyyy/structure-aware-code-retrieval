# Structure-Aware Code Retrieval and Evaluation for Repository-Level LLM Applications

A Python project investigating whether repository structure improves code retrieval
for LLM applications. The planned system compares lexical, dense, hybrid,
symbol-aware, and structure-aware retrieval, then supplies evidence to repository QA.

**Status: M2 — Python indexing and BM25 retrieval.** Scan local Python source,
extract symbols and imports, persist code chunks in SQLite, and search them with
source paths and line ranges. Dense/hybrid/structure-aware retrieval, formal
evaluation, and LLM QA are planned. No retrieval-quality improvement is claimed yet.

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

No API key, model download, GPU, or Docker installation is required for M2. The
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
search. They run offline after setup. GitHub Actions runs checks and builds on Windows
and Linux. Coverage is reported without a percentage gate. A real symlink-creation
test skips on Windows hosts without that privilege; link filtering also has a unit test.

## Repository layout

```text
src/structure_aware_retrieval/
  cli.py                      Index/search commands
  models.py                   Snapshot-scoped source objects
  ingestion.py                Filesystem scan and ignore rules
  parsing.py                  AST symbols, imports, source chunks
  indexing.py                 Atomic SQLite persistence
  tokenization.py             Identifier-aware lexical preprocessing
  retrieval.py                BM25 ranking over saved chunks
tests/                        Unit/integration tests and source fixtures
docs/                         Design, evaluation plans, smoke validation
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
