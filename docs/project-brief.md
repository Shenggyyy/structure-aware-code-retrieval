# Project Brief

**Structure-Aware Code Retrieval and Evaluation for Repository-Level LLM Applications**

An applied CS / AI Systems project combining information retrieval, static program
analysis, reproducible evaluation and evidence-grounded LLM question answering.
Start with the [offline demonstration](demo.md); inspect [results](../RESULTS.md)
and the [architecture](architecture.md) for supporting evidence.

## Research question and scope

Does repository structure help retrieve the code needed to answer repository-level
questions, and what quality and computational tradeoffs does it introduce?

The system compares BM25, dense, hybrid, symbol-aware and structure-aware retrieval
over the same source snapshots. It targets Python repositories, with one repository
per query. It statically reads source without executing or editing it. The project
delivers retrieval infrastructure and an evaluation pipeline; coding-agent loops,
model training and distributed serving are outside its scope.

## Engineering contributions

- **Source-aware retrieval pipeline:** extract modules, classes, functions and methods
  with Python AST; persist symbols, chunks and source identities in SQLite; return
  paths, exact line ranges and score provenance through a common retrieval interface.
- **Structure hypothesis as an executable comparison:** combine lexical and dense
  rankings, add symbol features, and test bounded one-hop relation expansion using
  containment, internal imports, resolvable calls and test/source associations.
  Frozen configurations and relation ablations make the heuristic inspectable.
- **Evaluation and QA delivery:** retain per-query rankings, Recall@K, Precision@K,
  MRR@K, NDCG@K, timing and construction costs. Build bounded cited QA contexts,
  check source identities and locations automatically, and separately record LLM
  assessments. Frozen plans, attempt journals, raw responses and archive verification
  preserve failures and missing outcomes alongside successful results.

The CLI, automated tests, Windows/Linux CI, CPU Docker targets and offline smoke
workflow support reproducible use. See [evaluation](evaluation.md),
[LLM assessment](llm-evaluation.md) and [container delivery](docker.md).

## Technology choices and tradeoffs

Python 3.12, Typer and uv keep the interface and dependency environment explicit.
The standard-library AST parser provides source structure without a runtime or
language-server dependency, but cannot resolve arbitrary dynamic Python behavior.

SQLite, JSON graphs and NPZ vectors require no external database service.
The dense baseline uses a pinned, optional CPU `all-MiniLM-L6-v2` encoder with
384-dimensional vectors and a 256-token input limit. NumPy exact search makes
scoring straightforward to inspect; it scores the full corpus and is not a
large-scale ANN implementation. The compact encoder is a baseline, not a claim
of state-of-the-art code representation.

Reciprocal rank fusion combines lexical and dense rankings without training a
reranker. Relation boosts expose why a neighbor was promoted, but can displace
stronger initial matches. Bounded graph expansion does not make the underlying
full-corpus search sublinear. See [baseline definitions](baselines.md) and
[structure retrieval](structure.md).

## Recorded experimental evidence

The [frozen retrieval matrix](../reports/m6c/README.md) contains **45 runs on eight
snapshots**, covering 1,130 indexed Python files and 20,003 chunks. The 170 questions
have separate roles; they are not one held-out test set:

| Role | Repositories | Questions |
| --- | ---: | ---: |
| Development | 2 | 40 |
| Expanded test candidates | 5 | 120 |
| Public RepoQA adaptation | 1 | 10 |

On the **120 expanded test-candidate questions**, query-macro symbol-level scores
show Hybrid Recall@10 / NDCG@10 of **0.7944 / 0.5947**, versus **0.7917 / 0.5109**
for full Structure. On the **40 cross-file questions** within that split, Structure
raises Recall@10 from **0.7083 to 0.7500**, while NDCG@10 falls from **0.5268 to
0.4995**. The result supports a coverage-versus-ranking tradeoff, not a general
structure-aware improvement. [Metrics and limitations](../RESULTS.md)

The [live QA experiment](../reports/m7b-live/README.md) generated **60 responses:
12 development questions across five strategies**, yielding 48 answers and 12
abstentions. All 60 source-evidence audits and all 48 applicable answer-citation ID
checks passed; these establish source validity, not semantic correctness.

The [cumulative v2 assessment](../reports/m7e-live/README.md) reuses those generations:
**58 of 60 judgments pass the protocol, one is invalid and one historical outcome
is unknown**. Correctness has 47 numeric scores, completeness 49 and citation support
47; remaining accepted dimensions are N/A. The final 47-call batch has a usage-based
cost estimate of **US$0.3526** at frozen uncached rates, not an invoice. Full cumulative
v2 cost remains unknown because one attempted request has no saved response.

## Limits and extensions

All relevance labels remain **provisional**; no human-reviewed ground truth or true
answer-correctness rate is claimed. Sparse judgments limit retrieval interpretation.
Expanded test outcomes are exposed, and adapted RepoQA scores are not comparable
to original RepoQA scoring. QA uses a small development cohort, a rubric revised
after examining failures, and the same model family for generation and judging.
Protocol acceptance and conditional ordinal means do not establish a reliable
QA-quality ranking.

New untouched benchmarks, evaluator calibration, optional human review and
code-specialized encoders are extensions. They do not invalidate the delivered
engineering scope or justify rewriting recorded experiments.

## Suggested CV wording

These are project-level templates. Use only statements that match your actual
contribution; describe collaboration and tool assistance when relevant. No personal
authorship history, deployment experience or publication is implied.

**English**

- Built a Python repository-retrieval pipeline comparing five strategies with AST
  parsing, SQLite indexing, static relations and source-traceable QA contexts.
- Evaluated 45 frozen retrieval runs across eight repositories and 170 questions
  with separate development/test-candidate/public roles; documented a cross-file
  recall gain alongside aggregate ranking degradation under provisional labels.
- Implemented cited QA and model-assisted evaluation with archived requests,
  source checks and usage estimates; retained 58 valid v2 judgments, one invalid
  result and one unknown outcome across 60 planned case–strategy rows
  (12 questions × five strategies).

**中文**

- 构建 Python 仓库级代码检索系统，实现 AST 解析、SQLite 索引及五种检索策略，
  将静态结构关系与可追溯的问答上下文相结合。
- 在 8 个仓库、170 个问题上完成 45 组固定配置实验，区分开发、测试候选和公开改编数据；
  在 provisional 标签下报告跨文件召回提升与整体排序退化的取舍。
- 实现带引用的问答与 LLM 辅助评测，保存请求、原始结果、来源校验和用量估算；
  12 个问题 × 5 种策略的 60 条计划评审保留 58 条有效、1 条无效及 1 条未知结果，
  明确模型评分的适用边界。
