# Structure-Aware Code Retrieval and Evaluation for Repository-Level LLM Applications

A Python project investigating whether repository structure improves code retrieval
for LLM applications. The planned system compares lexical, dense, hybrid,
symbol-aware, and structure-aware retrieval, then supplies evidence to repository QA.

**Status: M1 — engineering foundation.** Package installation, CLI help/version,
tests, and CI configuration are available. Parsing, indexing, retrieval, benchmarks,
and QA are planned; no retrieval results or performance improvements are claimed yet.

## Quickstart

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) first. From the
repository root, run these commands in PowerShell or a POSIX shell:

```text
uv sync --locked --dev
uv run --locked sacr --help
uv run --locked sacr --version
```

Python **3.12** is the supported runtime, selected by `.python-version`. uv downloads
it if needed and creates `.venv/`; initial setup needs network access. CI uses uv
**0.12.5**. Commit `uv.lock` to preserve application and development dependencies.

`sacr --version` prints `sacr 0.1.0`. Running `sacr` without arguments prints help.
The equivalent module entry point is:

```text
uv run --locked python -m structure_aware_retrieval --help
```

No API key, model download, GPU, or Docker installation is required for M1.

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

Tests exercise CLI behavior and installed entry points from outside the repository.
They run offline after setup. GitHub Actions runs checks and builds on Windows and
Linux after a push or pull request. Coverage is reported without a percentage gate.

## Repository layout

```text
src/structure_aware_retrieval/  Python package and CLI
tests/                        CLI and installation smoke tests
docs/                         Architecture, roadmap, evaluation protocol
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

See [architecture](docs/architecture.md), [milestone criteria](docs/roadmap.md),
[evaluation protocol](docs/evaluation.md), and [contributor guidelines](AGENTS.md).
Each milestone ends with validation and a suggested commit message. The owner
reviews, commits, and pushes changes before development moves on.
