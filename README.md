# Structure-Aware Code Retrieval and Evaluation for Repository-Level LLM Applications

A Python research and engineering project asking: **does repository structure help
retrieve the right code for repository-level LLM questions?** It compares BM25,
dense, hybrid, symbol-aware and structure-aware retrieval, with reproducible
evaluation, source traces, cost measurements and a cited QA pipeline.

The system reads local Python snapshots statically. Each query targets one repository.
It does not execute or edit the indexed code. The focus is retrieval and evaluation;
coding-agent loops, model training and distributed serving are outside its scope.

**Latest checkpoint: M9c — real same-model answers in the repository workbench.**
The new [repository workbench](docs/workbench.md) imports local Python directories
or public HTTPS Git repositories, freezes source versions, prepares existing indexes,
vectors and graphs, and compares five-strategy contexts in a browser. Inspect code
and source locations, watch preparation state, and reopen saved history. The
workbench now prepares a frozen generation plan and total estimate, then requires
explicit model and budget confirmation before answering from the five contexts.
The [separately approved live run](reports/m9c-live/README.md) returned five answers
from five generation requests, with zero judge calls, retries or unknown outcomes.
Reported usage was 15,046 input and 1,131 output tokens, implying **US$0.016374** at
the plan's frozen uncached rates, under the approved US$0.10 budget. This is a cost
estimate, not an invoice. Browser checks verified all five answers, representative
citations for each strategy, history reopening and unchanged results after server
restart. **The scoped local import-to-answer-comparison workflow is implemented and
observed.** One unlabeled question establishes no strategy-quality ranking or
answer-correctness rate. See [acceptance status](docs/status.md) and
[M9c implementation](reports/m9c/README.md) for the preceding offline checkpoint.

Start with the [project brief](docs/project-brief.md) or follow the
[five-minute demonstration](docs/demo.md) to inspect the system and saved evidence.
All five retrievers, evaluation, QA tooling and CPU Docker delivery are implemented.
The retrieval matrix contains 45 runs on eight snapshots and 170 questions. The
[live QA experiment](reports/m7b-live/README.md) supplies 60 real generations.
The [latest model-assisted assessment](reports/m7e-live/README.md) retains **58 valid
v2 judgments, one invalid judgment and one historical unknown out of 60 planned
rows**. All planned requests have been attempted. Original answers, v1 results and
the earlier partial v2 run remain archived unchanged.

The follow-up made 47 judge calls with no retries or new generations. Its usage
implies US$0.35257875 at frozen uncached rates; cumulative known v2 judging cost is
US$0.4368195, while full cost remains unknown. These are estimates, not invoices.
The earlier research engineering and experiment attempts are delivered. **Labels remain
provisional; the small development set and incomplete score coverage do not
establish a reliable QA-quality ranking.** Model assessments are not human review
or true accuracy.
See [acceptance status](docs/status.md) and the
[LLM evaluation specification](docs/llm-evaluation.md). Human review is optional.

## What the experiments show

On 120 expanded test-candidate questions from five repositories, the frozen full
Structure heuristic does not improve aggregate quality over Hybrid:

| Strategy | Recall@10 | NDCG@10 |
| --- | ---: | ---: |
| BM25 | 0.6444 | 0.4854 |
| Dense | 0.7292 | 0.5675 |
| Hybrid | 0.7944 | 0.5947 |
| Symbol-aware | 0.7931 | 0.5838 |
| Structure-aware (full) | 0.7917 | 0.5109 |

On the 40 cross-file questions, Structure improves Recall@10 from 0.7083 to 0.7500
while lowering NDCG@10. These are provisional symbol-level, query-macro scores with
sparse judgments. Development and public-adaptation results are reported separately.
Exposed test outcomes must not be reused for tuning a claimed held-out comparison.

Read [results and limitations](RESULTS.md) for all metrics, paired uncertainty,
latency, memory, failure cases and the outstanding research work. The
[generated overview](reports/overview/report.md) validates and summarizes all 45
saved runs without loading a model or rerunning retrieval.

In the original v1 experiment on 12 QA questions across five strategies, the generator returned 48
answers and 12 abstentions. Answer citation IDs passed all 48 applicable checks,
but only 24/60 judge outputs passed the v1 assessment protocol. Reported
tokens imply **US$0.490214 at frozen uncached rates**, not an invoice. The
[QA failure analysis and raw archive](reports/m7b-live/README.md) explain the
evidence-ID/status failures and preserve them without repair or retries.

The later v2 assessment reuses those answers and accepts 58/60 judgments, with
dimension-specific N/A scores, one invalid judgment and one historical unknown.
Structure minus Hybrid has mean ordinal deltas of +0.2222/+0.1111/+0.2222 for
correctness/completeness/citation support on nine shared scored cases; against
BM25 the deltas are 0/+0.1/−0.1 on ten cases. These small, exposed development
comparisons do not show a consistent advantage or reverse the retrieval finding.
See [the cumulative report](reports/m7e-live/README.md) for exact denominators and
limits. Higher protocol acceptance is not improved true accuracy.

## Workbench quickstart

Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/), then
run from this project root in PowerShell:

```powershell
uv sync --locked --dev --extra dense
uv run --locked --extra dense sacr prepare-model --cache artifacts/models
uv run --locked --extra dense sacr workbench serve --workspace artifacts/workbench --model-cache artifacts/models --port 8765
```

Dependency/model installation may download files. Subsequent previews load local
weights and require no API key. They show retrieved evidence, not generated answers.
Open [the local workbench](http://127.0.0.1:8765/) while the command is running. Enter
a public HTTPS Git URL or a local path, import and prepare it, select the repository,
then submit a question. Compare the five columns and expand evidence to inspect
source lines; use history to reopen a saved comparison without rerunning it.
For optional answers, first inspect the generated plan's model, request limit and
total estimate. Paid execution requires separate confirmation; starting the server,
previewing contexts and opening history never generate answers automatically.
The server reads `OPENAI_API_KEY` only from its local environment when executing an
approved plan. Do not paste keys into the browser or commit them.
The [startup guide](docs/workbench.md) covers browser controls, pinned versions,
generation approval, failure recovery and the retained CLI commands. See
[M9c live evidence](reports/m9c-live/README.md) for the approved generation run and
[M9c validation](reports/m9c/README.md) for the preceding offline implementation checks;
earlier browser/import validation remains in [M9b](reports/m9b/README.md) and
[M9a](reports/m9a/README.md).

## Minimal fixture quickstart

Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/), then
run these commands in PowerShell or a POSIX shell:

```text
git clone https://github.com/Shenggyyy/structure-aware-code-retrieval.git
cd structure-aware-code-retrieval
uv sync --locked --dev
uv run --locked sacr --help
uv run --locked sacr index tests/fixtures/sample_repo --output artifacts/sample.sqlite
uv run --locked sacr search "calculate_checksum" --index artifacts/sample.sqlite --top-k 3
uv run --locked sacr ask "How is calculate_checksum implemented?" --index artifacts/sample.sqlite --output artifacts/qa/sample-preview
```

Python **3.12** is selected by `.python-version`; uv installs it if necessary. Initial
dependency installation needs network access. The fixture commands need no model,
API key, GPU or Docker. Source is only parsed; QA defaults to an evidence preview
and makes no API call. Search returns paths, one-based inclusive line ranges and
stored code chunks. Use `--json` for full text, identifiers and score components.

Indexes are snapshots: refresh with an explicit `index --overwrite` and rebuild
dependent vectors/graphs. Experiments and QA bundles require new output paths.

Run the complete offline delivery smoke, or verify the published retrieval overview:

```text
uv run --locked python scripts/smoke.py --output artifacts/smoke-host-001
uv run --locked python scripts/summarize_results.py --output reports/overview --check
```

The smoke creates an isolated Git fixture and checks indexing, graph retrieval,
QA preview, evaluation repeatability and review preparation. It measures software
behavior on synthetic data, not real retrieval or answer quality.

## Reproduce and explore

| Task | Guide |
| --- | --- |
| Import a repository, compare five contexts in a browser and reopen history | [Workbench startup](docs/workbench.md) |
| Estimate and explicitly approve five same-model answers from saved contexts | [Workbench generation](docs/workbench.md#optional-answers-review-before-paid-execution) |
| Present the project and its defensible findings | [Project brief and CV wording](docs/project-brief.md), [offline demonstration](docs/demo.md) |
| Index your repository and compare five strategies | [Commands and preparation](docs/reproduction.md) |
| Inspect model, tokenization and fusion settings | [Baseline definitions](docs/baselines.md) |
| Understand typed edges, expansion and ablations | [Structure retrieval](docs/structure.md) |
| Rebuild the eight-repository, 45-run experiment | [Frozen matrix and measurement protocol](docs/experiments.md#reproduction) |
| Understand labels, splits, metrics and attribution | [Benchmarks](docs/benchmarks.md), [evaluation](docs/evaluation.md) |
| Inspect optional manual relevance-review tools | [Review workflow](docs/review.md) |
| Prepare QA requests and inspect automatic citation checks | [QA setup and evaluation](docs/qa.md) |
| Inspect real LLM assessments, failures and costs | [Live QA evidence](reports/m7b-live/README.md), [scoring specification](docs/llm-evaluation.md) |
| Prepare and verify the revised judge protocol offline | [M7c checkpoint](reports/m7c/README.md), [commands](docs/reproduction.md#prepare-judge-protocol-v2-from-saved-answers) |
| Reassess saved answers after approval and verify the run offline | [M7d checkpoint](reports/m7d/README.md), [judge-only workflow](docs/qa.md#judge-only-v2-execution) |
| Inspect the partial real v2 run and its unknown outcome | [Partial v2 evidence](reports/m7d-live/README.md), [offline archive check](docs/reproduction.md#verify-the-partial-live-v2-archive) |
| Prepare only unstarted judgments and inspect the new cost proposal | [M7e checkpoint](reports/m7e/README.md), [follow-up workflow](docs/qa.md#follow-up-for-unstarted-v2-requests) |
| Inspect all v2 attempts and verify the follow-up archive | [M7e live evidence](reports/m7e-live/README.md), [offline archive check](docs/reproduction.md#verify-the-live-follow-up-archive) |

Dense retrieval uses optional CPU Sentence Transformers dependencies and a pinned
`all-MiniLM-L6-v2` model. Explicit source/model preparation may download inputs;
retrieval and evaluation read prepared local artifacts. SQLite, NPZ vectors and JSON
graphs require no external database service. Exact vector search and BM25 score the
full corpus; bounded graph expansion does not make that search sublinear.

QA packs canonical source evidence under a **16,000 UTF-8 byte** default limit and
requires supplied source IDs for answer claims. Generating answers requires explicit
`--execute`, a model and local `OPENAI_API_KEY`; see the QA guide before execution.
The 12-case, five-strategy experiment has [saved live responses and judgments](reports/m7b-live/README.md).
Valid citation identifiers alone do not establish correctness or source support.
M7b implements separate generation and judging stages. Prepare and check their common
references, frozen settings and combined estimate offline using the
[QA workflow](docs/qa.md). Both proposed models and the combined budget require explicit
owner approval before any additional API calls. Saved results can be verified offline.
The combined runner remains on rubric v1. M7c prepares v2 requests from saved answers;
M7d adds judge-only execution with explicit model, plan and budget approval. It reuses
the original answers and makes no generation calls. Its approved v2 run stopped after
13 attempts. M7e's separately approved follow-up completed the other 47 attempts,
excluding all prior attempts. Reports distinguish historical, new and cumulative
coverage: 58 accepted judgments, one protocol failure and one historical unknown.
Unknown outcomes retain unknown usage/cost without automatic retry or resume.
This evidence does not establish better answer quality or a reliable QA ranking;
additional calls still require owner approval.

## Docker

With Docker running in Linux-container mode:

```text
docker build --target base -t sacr:base .
docker run --rm --network none sacr:base --help
docker volume create sacr-artifacts
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts --entrypoint python sacr:base scripts/smoke.py --output artifacts/smoke-001
```

The runtime runs as UID/GID 10001. The optional `dense` target adds CPU embedding
dependencies; prepare model weights separately. After building, the base smoke needs
no network or credentials. See [container reproduction](docs/docker.md) and
[recorded host/container validation](reports/m8a/README.md).

## Architecture and repository layout

```mermaid
flowchart LR
    R[Python snapshot] --> P[Scan and AST parse]
    P --> I[SQLite symbols and chunks]
    I --> V[Optional vectors]
    I --> G[Static relation graph]
    I --> T[Five retrieval strategies]
    V --> T
    G --> T
    T --> Q[Bounded context and cited QA]
    B[Frozen benchmarks and configs] --> E[Experiment runner]
    E --> T
    E --> M[Metrics, traces and reports]
```

```text
src/structure_aware_retrieval/  Parser, indexes, retrievers, evaluation/ and qa/
  workbench/                  Import, resources, previews, local server and browser assets
tests/                        Offline unit/integration tests and small fixtures
benchmarks/                   Versioned manifests, questions, judgments, provenance
configs/                      Fixed strategy, ablation and QA configurations
scripts/                      Experiment runners, smoke and saved-results overview
reports/                      Recorded evidence; overview/ is generated
docs/                         Architecture, protocols, reproduction and acceptance
artifacts/                    Ignored local snapshots, indexes, models and outputs
Dockerfile                    Base and optional CPU Dense runtime targets
.github/workflows/ci.yml       Windows/Linux checks and Linux container smoke
```

The [architecture document](docs/architecture.md) explains source identity, shared
retrieval contracts and evaluation boundaries. Historical reports retain their
original checkpoint status; [current status](docs/status.md) tracks later progress.

## Development and contribution

```text
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest --cov --cov-report=term-missing
uv run --locked python scripts/summarize_results.py --output reports/overview --check
uv build
```

Use four-space indentation, type annotations and Ruff's 100-character line limit.
Name modules/functions in `snake_case`, classes in `PascalCase`, and tests `test_*.py`.
Run `uv run --locked ruff format .` to format. Retain optional dependencies with
`--extra dense` on uv commands when developing with the model. Tests run offline
after installation; coverage is reported without a percentage gate. CI also builds
both CPU container targets and runs their smoke checks with networking disabled.

Keep source, tests and protocol documentation aligned; commit `uv.lock` with dependency
changes. Store downloaded inputs and intermediate outputs under ignored `artifacts/`;
keep credentials out of Git. Preserve recorded experiments when publishing new runs.
Use focused commits with imperative messages, such as `Add saved-result overview validation`.
PRs should explain the behavior change, validation and any effect on experimental
comparability. Follow the [milestone workflow](docs/roadmap.md): the owner reviews,
commits and pushes each completed checkpoint.
