[English](README.md) | [简体中文](README.zh-CN.md)

# Structure-Aware Code Retrieval and Evaluation for Repository-Level LLM Applications

**Does repository structure help retrieve the right code for LLM questions?**
This Python CS / AI Systems project compares BM25, Dense, Hybrid, Symbol-aware and
Structure-aware retrieval, then uses the retrieved evidence for cited repository QA.
It combines a local browser workbench with reproducible experiments and saved results.

The agreed scope is delivered: the core system, experiment pipeline, M9 browser
workflow, bilingual homepages and bilingual interface. Final review and local
verification are complete; research limitations remain explicit. Further features
or experiments are optional, separately requested work. See [status](docs/status.md)
and the [delivery record](docs/delivery.md) for checks and remaining limitations.

## What you can do

- Import a public HTTPS Git repository or local Python directory, record its source
  version, and prepare reusable indexes, vectors and a static relationship graph.
- Ask one question and compare five retrieval strategies under shared settings.
  Inspect ranked code, file paths, line numbers, scores and relationship provenance.
- Preview contexts without a model API, or explicitly approve one shared answering
  model and budget to generate separate answers from those contexts.
- Compare citations, latency, reported tokens and cost estimates; reopen saved
  history without repeating retrieval or generation.
- Reproduce Recall@K, Precision@K, MRR, NDCG, latency and structure ablations using
  versioned benchmarks, configurations and offline verification.

## Interface

![Five-strategy comparison showing saved Requests answers in the local workbench](docs/assets/workbench.jpg)

Actual browser view of the [archived Requests run](reports/m9c-live/README.md).
This is a saved result, not a new generation or a correctness score. The original
question and model answers remain unchanged. Evidence controls open the saved code
and line numbers; narrower screens can scroll the five columns horizontally. This
Stage 1 screenshot retains the Chinese interface from that checkpoint. The current
page offers **Interface language / 界面语言** selection between English and 简体中文.

## Workbench quickstart

Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Use PowerShell; Python 3.12 is selected by `.python-version` and uv can install it.

```powershell
git clone https://github.com/Shenggyyy/structure-aware-code-retrieval.git
cd structure-aware-code-retrieval
uv sync --locked --dev --extra dense
uv run --locked --extra dense sacr prepare-model --cache artifacts/models
uv run --locked --extra dense sacr workbench serve --workspace artifacts/workbench --model-cache artifacts/models --port 8765
```

Initial dependency/model installation and public repository import need network
access. Previews use local CPU model weights and require no API key or GPU. Keep
this terminal running and open [the local workbench](http://127.0.0.1:8765/).
Stop it with Ctrl+C; choose another `--port` if needed.

Use **Interface language / 界面语言** to switch the shared interface. A saved choice takes priority;
otherwise the first browser language selects Chinese when it starts with `zh`, and
English in other cases. The choice persists when browser storage is available.
Switching changes interface wording only: questions, code, answers and raw records
keep their original text, with no network request or paid action from the switch.

1. Enter a public HTTPS Git URL or local directory. For a remote source, an exact
   commit in the ref field makes the version reproducible; `HEAD` resolves the
   current version. Local paths refer to the server's filesystem.
2. Select **Import and prepare / 导入并准备**, then inspect source identity and
   parsing, vector and graph status. Imported repository code is read statically;
   its dependencies, install scripts and tests are not executed.
3. Enter a question and select **Preview all five strategies / 运行五策略预览**. Compare code
   evidence; missing or failed strategies remain visible rather than being invented.
4. For optional answers, prepare a plan and review its model, request limit and total
   estimate. Explicitly confirm paid generation and budget. Configure
   `OPENAI_API_KEY` only in the server's local environment before starting it;
   restart the server after environment changes. Never enter the key in the page.
5. Open answer citations to inspect source. Use **History / 历史记录** to reopen
   the saved comparison. Reopening or refreshing does not repeat paid requests.

Starting the server, importing, previewing, planning and viewing history do not
call an answering model. Approved generation sends the question and selected code
context to the provider. The default workflow requests no LLM judge. Unknown
request outcomes are preserved without automatic retries; costs are estimates,
not invoices. See the [full startup and recovery guide](docs/workbench.md).

## View saved answers without model installation

From this project root, the following separate quickstart uses the published
archive. It requires neither an API key nor embedding weights after installation:

```powershell
uv sync --locked --dev
$replay = Join-Path "artifacts" ("workbench-demo-" + [guid]::NewGuid().ToString("N"))
Expand-Archive -LiteralPath reports/m9c-live/run.zip -DestinationPath $replay
uv run --locked --offline sacr workbench serve --workspace "$replay" --port 8765
```

Open the local workbench, choose **History / 历史记录**, and open **How are request URLs
prepared?** The displayed API call count belongs to the historical run; viewing it
makes no new request. The [archive guide](reports/m9c-live/README.md#portable-offline-replay)
includes integrity verification. For a model-free indexing/search/evaluation example,
use the [offline demonstration](docs/demo.md).

## What the experiments show

| Evidence | Finding and interpretation |
| --- | --- |
| [Retrieval results](RESULTS.md) | 45 runs on eight snapshots and 170 questions. Full Structure did not improve aggregate quality over Hybrid on expanded test candidates. Cross-file recall improved while ranking quality declined. |
| [Model-assisted assessment](reports/m7e-live/README.md) | The cumulative v2 protocol accepts 58 judgments, rejects one and retains one historical unknown out of 60 planned rows. Protocol acceptance is not true correctness. |
| [Browser acceptance](reports/m9c-live/README.md) | Five strategies returned five real answers to one approved question; citations, usage, history and restart were checked. This validates a workflow, not a strategy ranking. |

Detailed metrics, denominators, costs, negative results and uncertainty live in
those linked reports, rather than being repeated here. The
[generated overview](reports/overview/report.md) summarizes validated saved runs.

## Limits

Python only, one repository per question, public HTTPS or local sources, and a
single-user server bound to `127.0.0.1`. There is no private-repository authentication,
coding agent, model training or distributed service. Static relationships are
heuristics; exact vector search and BM25 still score the full corpus.

Relevance labels remain **provisional**. Sparse labels, small exposed evaluation
sets and incomplete semantic-score coverage limit generalization. Do not tune on
exposed test results and call them held out. Automatic citation ID/path/line checks
are separate from model semantic assessments; neither is human-reviewed ground
truth. Unlabeled interactive questions display no Recall, NDCG or correctness rate.
Identical answers across strategies are valid. Human review is optional.

## Architecture and repository layout

The existing pipeline is **snapshot → Python AST → SQLite index / local vectors /
static graph → retrieval → bounded context → cited QA**. Evaluation uses the same
retrieval contracts with frozen benchmarks. See [architecture](docs/architecture.md).

```text
src/structure_aware_retrieval/  Parser, indexes, retrieval, evaluation, QA, workbench
tests/                        Offline tests and synthetic fixtures
benchmarks/ + configs/         Versioned inputs, provenance and fixed settings
scripts/                      Experiment runners, verification and smoke checks
reports/                      Historical evidence and generated results overview
docs/                         Technical guides, protocols and delivery records
artifacts/                    Ignored local snapshots, caches and saved user runs
Dockerfile + .github/          CPU containers and Windows/Linux CI
```

## Documentation

Both homepages cover the same scope and quickstarts. Deeper guides and historical
reports below are currently in English; the project brief also includes Chinese
CV wording. No separate translated technical guide is implied.

| Purpose | Main document |
| --- | --- |
| Browser import, preview, paid confirmation and history | [Workbench](docs/workbench.md) |
| CLI reproduction and experiment commands | [Reproduction](docs/reproduction.md), [frozen experiments](docs/experiments.md) |
| Findings, scope and evaluation limits | [Results](RESULTS.md), [benchmarks](docs/benchmarks.md), [evaluation](docs/evaluation.md) |
| System and strategy definitions | [Architecture](docs/architecture.md), [baselines](docs/baselines.md), [structure](docs/structure.md) |
| QA, semantic assessment and optional human review | [QA](docs/qa.md), [LLM evaluation](docs/llm-evaluation.md), [review tools](docs/review.md) |
| Present the project or inspect saved evidence | [Project brief](docs/project-brief.md), [offline demo](docs/demo.md) |
| CPU containers and persistent workspaces | [Docker](docs/docker.md) |
| Accepted scope, historical stages and final handover | [Status](docs/status.md), [roadmap](docs/roadmap.md), [delivery](docs/delivery.md) |

## Development and contribution

```powershell
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest --cov --cov-report=term-missing
uv run --locked python scripts/summarize_results.py --output reports/overview --check
uv build
```

Use four spaces, type annotations, `snake_case` functions/modules, `PascalCase`
classes and `test_*.py` tests. Ruff uses a 100-character limit; format with
`uv run --locked ruff format .`. Add `--extra dense` to uv commands when retaining
optional Dense dependencies. Tests are offline after installation; coverage is
reported without a percentage gate. CI also builds both CPU container targets and
runs their installed-runtime smoke checks without networking.

Browser localization tests use Node.js on `PATH`, without npm dependencies. Run
`uv run --locked pytest tests/workbench/test_i18n.py` for those contracts; pytest
skips them locally if Node is unavailable. CI explicitly checks Node availability
before testing. Serving the workbench does not require Node.

Keep code, tests and documentation aligned; commit `uv.lock` with dependency changes.
Preserve historical results, licenses and provenance. Keep user data in ignored
`artifacts/` and credentials out of Git. Use focused imperative commits and describe
behavior, validation and experimental comparability in PRs. The owner reviews,
commits and pushes each stage. Final delivery closes the agreed scope; future
features or experiments require a separate request.
