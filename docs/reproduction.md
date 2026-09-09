# Reproduction Guide

Run commands from the repository root. The examples work in PowerShell and POSIX
shells. Use a **new output path** for each experiment, graph, vector archive or QA
bundle; tools preserve existing artifacts rather than silently replacing them.
See [current findings and acceptance](../RESULTS.md) and the
[recorded results overview](../reports/overview/report.md) before interpreting scores.

For the new end-user flow, start with [Repository Workbench](workbench.md): import a
local directory or pinned public HTTPS Git repository, prepare existing resources,
run five offline context previews and reopen saved comparisons. Its workspace
reuses validated resources; the experiment commands below retain their separate
output-preservation rules. Run `uv run --locked --extra dense sacr workbench serve`
and open the printed loopback URL for the bilingual browser interface. Optional
answer generation uses a saved cost plan and requires explicit approval of its
model, request limit and budget before any model request.

## Install and verify locally

Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```text
git clone https://github.com/Shenggyyy/structure-aware-code-retrieval.git
cd structure-aware-code-retrieval
uv sync --locked --dev
uv run --locked sacr --help
uv run --locked sacr --version
uv run --locked sacr index tests/fixtures/sample_repo --output artifacts/sample.sqlite
uv run --locked sacr search "calculate_checksum" --index artifacts/sample.sqlite --top-k 3
uv run --locked sacr ask "How is calculate_checksum implemented?" --index artifacts/sample.sqlite --output artifacts/qa/sample-preview
uv run --locked python scripts/smoke.py --output artifacts/smoke-host-001
```

Python 3.12 is selected by `.python-version`; uv downloads it if necessary. Initial
installation needs network access. Subsequent fixture commands need no network,
model weights, API key, GPU or Docker. The fixture is parsed, never imported; it
intentionally raises if executed. QA preview saves evidence without generating an
answer. The separate smoke creates its own isolated Git fixture and checks indexing,
search, relations, QA preview, repeated evaluation, comparison and review preparation.

`sacr` without arguments prints help; `python -m structure_aware_retrieval` is the
equivalent module entry point. See [Docker reproduction](docker.md) for base and
optional CPU Dense images, persistent volumes and container smoke checks.

## Inspect saved results without retrieval

The overview script reads `reports/m6c` by default and writes a fresh
`artifacts/overview` directory:

```text
uv run --locked python scripts/summarize_results.py
uv run --locked python scripts/summarize_results.py --output reports/overview --check
```

Generation validates the 45 recorded runs and creates a compact JSON/Markdown
overview. Choose another new `--output` directory to regenerate it. Existing
experiment artifacts are preserved. `--check` is read-only: it validates the saved
evidence and compares the expected overview with the committed output, without
overwriting either. After locked installation, both modes need no network, model
weights, source checkouts or API key. They do not rerun retrieval; latency and memory
remain separately recorded measurements, outside the quality fingerprints.

## Index and search your repository

```text
uv run --locked sacr index . --output artifacts/project.sqlite
uv run --locked sacr search "build_index" --index artifacts/project.sqlite --top-k 5
uv run --locked sacr search "build_index" --index artifacts/project.sqlite --json
```

An index is a saved source snapshot. Search still returns its stored code if the
original checkout changes or disappears. Refresh explicitly with `index --overwrite`;
only an existing SACR database can be replaced. Rebuild dependent vectors and graphs
after a snapshot change; stale bindings fail validation.

| Index option | Default or behavior |
| --- | --- |
| `--output` | `artifacts/index.sqlite`; SQLite destination |
| `--max-chunk-lines` | 80; split long source spans without overlap |
| `--max-file-bytes` | 1,048,576; larger files produce skip diagnostics |
| `--exclude` | Repeatable root-relative gitignore pattern, e.g. `--exclude "tests/"` |
| `--overwrite` | Atomically rebuild an existing SACR index |
| `--json` | Counts, provenance, configuration and skipped-file diagnostics |

The scanner reads `.py` files and root/nested `.gitignore` rules, excludes build/cache
directories, and skips symlinks and junctions. Ignore patterns apply even to tracked
files; global Git ignores and `.git/info/exclude` are not used. Syntax, encoding and
file-read failures are reported; unreadable directories or ignore files abort indexing.
No source is executed. See [snapshot and parser contracts](architecture.md).

Search returns chunks, which can cover only part of a long symbol. Paths are relative
to the indexed root; line ranges are one-based and inclusive. Qualified names follow
source paths, not inferred runtime import roots. JSON includes source text, IDs,
scores and snapshot identity; text output previews twelve lines. Empty matches are
successful results. BM25 reconstructs in-memory term statistics when loaded;
single-command startup is separate from warm retrieval latency in experiment reports.

## Reproduce the development BM25 baseline

```text
uv run --locked sacr prepare-benchmark benchmarks/seed-v1/benchmark.json
uv run --locked sacr evaluate --config configs/bm25-seed.toml --output artifacts/runs/bm25-symbol-001
uv run --locked sacr evaluate --config configs/bm25-seed-file.toml --output artifacts/runs/bm25-file-001
```

Preparation downloads pinned Requests/Click source commits on first use, with fixed
LF checkout settings, then validates or builds indexes under `artifacts/benchmark/`.
Existing checkouts are inspected, never reset; `--rebuild` explicitly rebuilds indexes.
Evaluation is offline and validates source/label identity before retrieving.

TOML paths resolve relative to the configuration file. Each run writes `summary.json`,
`per_query.jsonl`, `rankings.jsonl`, `metrics.csv` and `report.md`. Quality is scored at
K=1,5,10,20 after deduplicating symbols or files. Repeated runs should reproduce quality
fingerprints; hardware-dependent timing and runtime metadata need not match. The
40-query seed has **provisional, sparse labels**. Automatic source checks do not
establish exhaustive semantic relevance; human review is optional.
Read the [evaluation protocol](evaluation.md) for metrics, denominators and limitations.

## Prepare dense retrieval and compare baselines

Retain optional dependencies with `--extra dense` on subsequent uv commands:

```text
uv sync --locked --dev --extra dense
uv run --locked --extra dense sacr prepare-model --cache artifacts/models
uv run --locked --extra dense sacr prepare-benchmark benchmarks/seed-v1/benchmark.json
uv run --locked --extra dense sacr embed --index artifacts/benchmark/indexes/requests.sqlite --output artifacts/benchmark/vectors/requests.npz
uv run --locked --extra dense sacr embed --index artifacts/benchmark/indexes/click.sqlite --output artifacts/benchmark/vectors/click.npz
uv run --locked --extra dense sacr search "prepare an HTTP request URL" --strategy hybrid --index artifacts/benchmark/indexes/requests.sqlite --vectors artifacts/benchmark/vectors/requests.npz
```

`prepare-model` explicitly downloads the pinned MiniLM model; all other model
operations use local files. The default cache is `artifacts/models`. Vectors bind
the snapshot, canonical chunk text, encoder settings and dependency versions. Use new
archives after changing those inputs. MiniLM uses CPU and truncates long input to 256
word pieces; see [model, tokenization and fusion definitions](baselines.md).

Compare BM25, Dense, Hybrid and Symbol-aware retrieval on identical symbol labels:

```text
uv run --locked --extra dense sacr evaluate --config configs/bm25-seed.toml --output artifacts/runs/baselines-bm25-001
uv run --locked --extra dense sacr evaluate --config configs/dense-seed.toml --output artifacts/runs/baselines-dense-001
uv run --locked --extra dense sacr evaluate --config configs/hybrid-seed.toml --output artifacts/runs/baselines-hybrid-001
uv run --locked --extra dense sacr evaluate --config configs/symbol-seed.toml --output artifacts/runs/baselines-symbol-001
uv run --locked --extra dense sacr compare --run artifacts/runs/baselines-bm25-001 --run artifacts/runs/baselines-dense-001 --run artifacts/runs/baselines-hybrid-001 --run artifacts/runs/baselines-symbol-001 --output artifacts/runs/baselines-comparison-001
```

The first run is the comparison reference. Incompatible snapshots, labels, evaluation
units or K values are rejected. Per-query differences remain available alongside
aggregates; an observed winner is conditional on the benchmark and its labels.

## Add relations and reproduce structure ablations

After preparing the preceding development indexes, model and vectors:

```text
uv run --locked --extra dense sacr graph --index artifacts/benchmark/indexes/requests.sqlite --output artifacts/benchmark/graphs/requests.json
uv run --locked --extra dense sacr graph --index artifacts/benchmark/indexes/click.sqlite --output artifacts/benchmark/graphs/click.json
uv run --locked --extra dense sacr search "rewind a request body during redirects" --strategy structure --index artifacts/benchmark/indexes/requests.sqlite --vectors artifacts/benchmark/vectors/requests.npz --graph artifacts/benchmark/graphs/requests.json --json
uv run --locked --extra dense sacr evaluate --config configs/structure-full.toml --output artifacts/runs/structure-full-001
uv run --locked --extra dense python scripts/run_m5.py --output artifacts/runs/structure-suite-001
```

Graphs use stored snapshot code. Structure defaults to Hybrid seeds;
`--seed-strategy bm25` permits structure search without vectors or model dependencies.
The fixed thirteen-run suite includes seed baselines, full/disabled structure, each
relation type, leave-one-out ablations and Symbol-aware seeds. It records comparisons
and source traces. Interrupted runs remain inspectable; retry with a new suite path.

Relations include containment, supported imports, static calls and test-to-source
calls. Uncertain bindings remain unresolved; test edges are not runtime coverage.
One-hop expansion has explicit budgets and reweights the full baseline ranking.
It does not make the underlying full-corpus search sublinear. See the
[graph and reranking policy](structure.md) and [recorded ablations](../reports/m5/README.md).

## Optional source-review bundles

These existing tools support manual label improvement. They are not required for
project completion; the current QA evaluation route is [specified separately](llm-evaluation.md).

After preparing the development source indexes, reproduce the saved-result audit
and pending candidate pool without an embedding model:

```text
uv run --locked python scripts/run_m6a.py --output artifacts/m6a-audit
```

The script reads committed M4/M5 results, checks fingerprints, compares paired
differences and prepares a pool of 845 question/symbol pairs. All decisions start
pending; see the [grading and validation workflow](review.md).

To reproduce the expanded datasets, split audit and source-review bundles:

```text
uv run --locked python scripts/run_m6b.py --prepare --output artifacts/m6b-reproduce
```

`--prepare` permits pinned source/archive downloads. Omit it once those inputs are
available for offline data regeneration and review preparation. This command performs
no retrieval or model calls; see the [benchmark preparation protocol](benchmarks.md).
Neither workflow supplies independent relevance judgments.

## Reproduce the expanded experiment matrix

Follow the complete [source preparation and fixed-matrix protocol](experiments.md#reproduction)
for eight snapshots, 170 questions and 45 runs. It prepares pinned sources and the
public archive, then rebuilds indexes, graphs and vectors in a new suite directory.
Only explicit input/model preparation needs network access; measured retrieval is offline.

Keep the 40 development, 120 expanded test-candidate and ten public-adaptation
questions separate. All labels remain provisional, requiring `--allow-provisional`.
The test outcomes are exposed; further tuning needs a fresh untouched test version.
See [benchmark freeze and attribution](benchmarks.md), [optional review instructions](review.md)
and [M6c measurements](../reports/m6c/README.md). Published reports preserve quality,
paired differences, failures, source traces and construction/storage/memory costs.

## Prepare the QA experiment offline

Complete these sections first: [development source preparation](#reproduce-the-development-bm25-baseline),
[model and vector preparation](#prepare-dense-retrieval-and-compare-baselines), and
[graph creation](#add-relations-and-reproduce-structure-ablations). QA preparation
needs the shared indexes, model, vectors and graphs in the documented
`artifacts/benchmark` layout; the evaluation and ablation runs are optional.

```text
uv run --locked --extra dense sacr prepare-qa --config configs/qa-m7.toml --output artifacts/qa/m7-prepared
```

This freezes twelve development cases across five strategies: sixty exact requests,
source previews, provenance and a generation-only cost projection. Evaluation reference
points remain separate from answering-model messages. Preparation makes no API call
and establishes no answer quality.

## Prepare the combined QA and LLM assessment

After the generation bundle above exists, freeze the common reference source,
generation/judge settings and combined estimate, then validate them offline:

```text
uv run --locked sacr prepare-qa-assessment --bundle artifacts/qa/m7-prepared --config configs/qa-assessment-m7-mini.toml --output artifacts/qa/m7b-prepared
uv run --locked sacr check-qa-assessment --bundle artifacts/qa/m7b-prepared
```

Preparation reads the configured Requests/Click indexes; checking the resulting
bundle needs neither indexes nor model weights. Both commands make no API calls.
Inspect the new bundle's `README.md`, `plan.json` and `references.json` before approval.
The model proposals are configuration, not permission to run them. The earlier
60-request generation estimate does not include judging.

The implemented `run-qa-assessment` command requires both approved model IDs, the
exact combined plan fingerprint, combined budget, a new output directory and
`--execute`. Obtain explicit owner approval before invoking it. See
[the approval and output contract](qa.md#combined-budget-and-execution-approval), the
[LLM scoring specification](llm-evaluation.md) and [M7b live record](../reports/m7b-live/README.md).
That record also provides an offline archive-validation path; it requires no API key
and does not repeat paid requests.

## Prepare judge protocol v2 from saved answers

First extract and verify the [saved M7b archive](../reports/m7b-live/README.md) under
`artifacts/qa/m7b-replay-001`, so its assessment run is at the path below. Then prepare
the revised requests and check the new bundle:

```text
uv run --locked python scripts/prepare_qa_judge_revision.py prepare --run artifacts/qa/m7b-replay-001/run --config configs/qa-judge-revision-m7c.toml --output artifacts/qa/m7c-v2-prepared-001
uv run --locked python scripts/prepare_qa_judge_revision.py check --bundle artifacts/qa/m7c-v2-prepared-001
```

Choose a fresh output directory for every preparation. These commands read saved
answers and common references; they need no API key, source checkout, index or model
weights. Inspect the generated bundle and [M7c report](../reports/m7c/README.md) for
exact messages, dynamic schemas, provenance, replay diagnostics and the cost proposal.
An estimate is not execution approval.

Replay only retags the rubric identifier in diagnostic copies of v1 outputs; it does
not repair them or generate v2 scores. The original archive and provisional labels
remain unchanged. M7c preparation is offline and the legacy combined runner remains
v1. M7d adds a separate execution path for the prepared v2 requests, requiring new
explicit model, scope and budget approval.

## Execute and verify a judge-only run

Inspect the checked bundle's exact payloads, model, `plan_fingerprint` and estimate.
Obtain owner approval before executing the [judge-only command](qa.md#judge-only-v2-execution).
It reuses archived generations; it does not rerun retrieval or generate answers.
Choose a new run directory. The runner neither resumes nor overwrites earlier runs.

Once a judge-only run exists, verify it offline:

```text
uv run --locked python scripts/verify_qa_judge_revision.py --run artifacts/qa/m7d-run-001
```

The verifier needs only the saved run and installed project dependencies, with no
credentials, source checkout, model weights or network. It checks the copied bundle,
approval, journals, results and summaries; it neither sends requests nor changes
recorded results. The [M7d report](../reports/m7d/README.md) records software checks,
while the [later live record](../reports/m7d-live/README.md) preserves a partial
real run. M7c's archived generated README describes
its original offline checkpoint; the current execution contract is in the QA guide.

## Verify the partial live v2 archive

The [partial v2 archive](../reports/m7d-live/README.md) contains 13 attempted judge
requests, 12 recorded valid judgments, one unknown outcome and 47 requests not
started. It preserves the original generations and makes no claim that the planned
60-request comparison finished. Check the report's archive hash, then extract into
a fresh directory in PowerShell:

```powershell
Get-FileHash reports/m7d-live/run.zip -Algorithm SHA256
Expand-Archive -LiteralPath reports/m7d-live/run.zip -DestinationPath artifacts/qa/m7d-live-replay-001
uv run --locked python scripts/verify_qa_judge_revision.py --run artifacts/qa/m7d-live-replay-001/run
```

These commands do not call a model, need credentials or resume the run. Inspect
`run/records.json`, `run/summary.json` and the request/result journals for coverage
and known usage. The 13th attempt has no saved response, so its usage and the complete
new judging cost remain unknown; the known subtotal is US$0.08424075. Verification
checks the saved evidence's internal consistency, not the missing response or the
semantic correctness of model judgments.

## Prepare an unstarted-request follow-up

After extracting and checking the partial archive above, prepare a new bundle:

```text
uv run --locked python scripts/prepare_qa_judge_followup.py prepare --run artifacts/qa/m7d-live-replay-001/run --output artifacts/qa/m7e-followup-prepared-001
uv run --locked python scripts/prepare_qa_judge_followup.py check --bundle artifacts/qa/m7e-followup-prepared-001
```

These offline commands freeze the verified prior run and select only its 47 requests
without attempt-journal entries. The 12 known results and one unknown outcome are
preserved and excluded from new requests. The exact saved answers, references, model,
v2 rubric and selected payloads remain unchanged; no source checkout, model weights,
credentials or network are needed. Inspect the new plan fingerprint and cost estimate
alongside the [M7e proposal](../reports/m7e/README.md). Preparation is not execution
approval and does not create new LLM results.

Execution requires a new approved model/plan/budget scope and the explicit `--followup`
flag; see the [execution contract](qa.md#follow-up-for-unstarted-v2-requests).
Once that separate run exists, verify it without credentials or requests:

```text
uv run --locked python scripts/verify_qa_judge_revision.py --followup --run artifacts/qa/m7e-followup-run-001
```

The new run retains the prior evidence and reports its historical, new and cumulative
measurements separately. Even if every selected request later has a result, the
original unknown attempt keeps cumulative full cost unknown. Fresh paths are
mandatory; this first version rejects running/completed parents, empty remaining
scopes and follow-ups of follow-ups. The original M7e tooling checkpoint was offline;
the later live archive below preserves the separately approved execution.

## Verify the live follow-up archive

The [M7e live archive](../reports/m7e-live/README.md) includes the new batch and its
frozen prior run. All 47 new requests have recorded outcomes: 46 valid judgments
and one protocol failure. Cumulative coverage is 58 valid judgments, one invalid
judgment and one historical unknown out of 60 planned rows. Compare the archive
hash with the report, then extract into a fresh directory in PowerShell:

```powershell
Get-FileHash reports/m7e-live/run.zip -Algorithm SHA256
Expand-Archive -LiteralPath reports/m7e-live/run.zip -DestinationPath artifacts/qa/m7e-live-replay-001
uv run --locked python scripts/verify_qa_judge_revision.py --followup --run artifacts/qa/m7e-live-replay-001/run
```

Verification checks the saved inputs, approval, historical/new request journals,
results and recomputed summaries without credentials, network or model calls.
Inspect the separate historical, new and cumulative measurements in the report.
The new batch's known cost is US$0.35257875 at frozen uncached rates; cumulative
known judging cost is US$0.4368195. Full cumulative usage/cost remains unknown,
and neither archive consistency nor protocol acceptance establishes semantic truth.

## Development checks

```text
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest --cov --cov-report=term-missing
uv build
```

Use the `uv run --locked pytest` entry point above to match CI. `python -m pytest`
also adds the working directory to Python's import path and can conceal accidental
imports from uninstalled directories such as `scripts/`. Tests of standalone
scripts should load them by file path or invoke their CLI from an isolated process.

Add `--extra dense` to `uv run` if retaining optional dependencies in this environment.
Tests run offline after installation; synthetic encoders/provider responses test
software behavior rather than real retrieval or answer quality. Coverage is reported
without a percentage gate. `uv build` creates distributions without publishing;
build-backend dependencies resolve separately from the application lockfile.
See [the contribution and milestone workflow](roadmap.md).
