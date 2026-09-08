# Five-Minute Project Demonstration

Use this walkthrough to demonstrate the implemented system, then discuss the
recorded experiment. The live steps use a **three-file synthetic fixture**; real
retrieval and LLM results are inspected from saved archives. No model download,
GPU, Docker or API key is needed after installation. No command below generates a
new LLM answer or judgment.

## Prepare before presenting

Use PowerShell from the repository root with Git and uv installed. Install the
locked Python 3.12 environment beforehand; initial installation may need network
access and is outside the five-minute presentation:

```text
uv sync --locked --dev
```

Keep the same terminal for all subsequent blocks so `$demo` remains available.
Choose an empty output directory automatically each time; leave previous runs
intact. Stop if a command fails. The full setup and alternatives are in the
[reproduction guide](reproduction.md).

Opening explanation: “This project asks whether static repository structure helps
retrieve the right code for LLM questions. It compares five strategies under fixed
evaluation settings and preserves both improvements and regressions.”

## 0:20–1:10 — Run the local pipeline

```powershell
$demo = Join-Path "artifacts" ("demo-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
uv run --locked --offline python scripts/smoke.py --output "$demo"
if ($LASTEXITCODE -ne 0) { throw "Demo preparation failed; inspect its output." }
```

Expected: `status: passed`, `source_files: 3`, `repeat_quality_matches: true`,
`api_calls: 0`, `model_downloads: 0`. The existing smoke workflow runs 17 commands
covering indexing, search, relations, QA preview, repeated evaluation and comparison.
It creates and commits an isolated fixture under `$demo/repository`; it does not
commit or change the project repository. The fixture contains an intentional
runtime exception: indexing succeeds because source is parsed without importing it.

The generated optional review bundle remains `pending`; this is not a failed
acceptance check or a requirement to arrange human review.

If Windows reports `WinError 5` when publishing a temporary output directory,
stop and keep `commands.json` and `summary.json` for diagnosis. Check that the
workspace is writable and that another application is not holding output files,
then rerun with a fresh directory. Two early rehearsals hit this error and the
final walkthrough passed; the cause was not established. See the
[validation record](../reports/m8c/README.md). Do not overwrite a failed run.

## 1:10–2:10 — Retrieve source and inspect relationships

```powershell
uv run --locked --offline sacr search "calculate_checksum payload bytes" --index "$demo/index.sqlite" --top-k 3
if ($LASTEXITCODE -ne 0) { throw "BM25 search failed." }
$relations = Get-Content "$demo/graph.json" -Raw | ConvertFrom-Json
$relations.edges | Where-Object { $_.kind -eq "test" } | Select-Object kind, confidence, path, line, expression
uv run --locked --offline sacr search "calculate_checksum payload bytes" --index "$demo/index.sqlite" --strategy structure --seed-strategy bm25 --graph "$demo/graph.json" --top-k 3
if ($LASTEXITCODE -ne 0) { throw "Structure search failed." }
```

BM25 returns `client.calculate_checksum` at `client.py:27–29` first. The test edge
points from `tests/test_client.py:5` to `calculate_checksum` and is marked
`heuristic`. This is a static relationship, not measured test coverage.

The fixture's graph has containment, import and test edges. It has no resolved
ordinary call edges; unresolved references are retained. Both searches return the
same order for this query: all three lexical matches fit inside the seed budget,
so no outside neighbor is promoted. Do not present this as a retrieval improvement.
BM25 seeds keep the demo model-free; the main published Structure configuration
uses Hybrid seeds and a pinned dense encoder.

## 2:10–3:00 — Inspect bounded QA evidence and empty-context handling

```powershell
$preview = Get-Content "$demo/qa-preview/qa.json" -Raw | ConvertFrom-Json
$preview | Select-Object status, model_called
$preview.context.budget
$preview.context.evidence | Select-Object id, path, start_line, end_line
Get-Content "$demo/qa-preview/answer.md" -TotalCount 25
$empty = Get-Content "$demo/qa-empty/qa.json" -Raw | ConvertFrom-Json
$empty | Select-Object status, model_called
```

The preview contains source IDs and locations, uses 608 of the 16,000 UTF-8 byte
budget, and reports `model_called: false`. It is a context preview, not a generated
answer. The unmatched query returns `insufficient_context` without calling a model.
Source identity and location checks do not establish semantic correctness.

## 3:00–4:00 — Show reproducibility and the real retrieval finding

```powershell
$first = Get-Content "$demo/bm25-first/summary.json" -Raw | ConvertFrom-Json
$repeat = Get-Content "$demo/bm25-repeat/summary.json" -Raw | ConvertFrom-Json
$first.quality_fingerprint -eq $repeat.quality_fingerprint
Get-Content "$demo/comparison/report.md" -TotalCount 14
uv run --locked --offline python scripts/summarize_results.py --output reports/overview --check
if ($LASTEXITCODE -ne 0) { throw "Published overview verification failed." }
```

The fingerprint comparison returns `True`; latency may differ. The synthetic
benchmark's perfect recall comes from two answerable fixture questions and is not
research evidence. The overview command instead
validates **45 saved real retrieval runs**, without rerunning them or loading models.

Open [RESULTS.md](../RESULTS.md): on 120 expanded test-candidate questions, Hybrid
NDCG@10 is 0.5947 and full Structure is 0.5109. On 40 cross-file questions, Structure
improves Recall@10 from 0.7083 to 0.7500 while lowering NDCG@10. Explain the observed
coverage-versus-ranking tradeoff; do not claim general superiority. The 170 total
questions have separate development, test-candidate and public-adaptation roles,
and all relevance labels remain provisional.

## 4:00–5:00 — Inspect an archived real answer and its assessment

```powershell
uv run --locked --offline python -m zipfile -e reports/m7e-live/run.zip "$demo/live"
if ($LASTEXITCODE -ne 0) { throw "Archive extraction failed." }
uv run --locked --offline python scripts/verify_qa_judge_revision.py --followup --run "$demo/live/run"
if ($LASTEXITCODE -ne 0) { throw "Archived experiment verification failed." }
$records = Get-Content "$demo/live/run/records.json" -Raw | ConvertFrom-Json
$example = $records | Where-Object { $_.case_id -eq "qa-click-04" -and $_.strategy -eq "bm25" }
$example.generation.answer | ConvertTo-Json -Depth 6
$example.generation.context.evidence | Where-Object { $_.id -in @("S1", "S10") } | Select-Object id, path, start_line, end_line
$example.judging.judgment.correctness | ConvertTo-Json -Depth 6
```

This explicitly selected example is a previously generated answer about Click's
`Context.ensure_object`, with citations `S1` and `S10`. The saved v2 model assessment
is separate from automatic location checks. This is archive inspection, not new
inference or an unbiased case selection.

Successful verification prints `complete_with_failures`: all 47 follow-up results
were saved, including one invalid judgment. Cumulative v2 coverage is **58 valid,
one invalid and one historical unknown out of 60 planned case–strategy rows**.
Numeric-score denominators differ by dimension. These are ordinal model opinions,
not human review or a true correctness rate. See the
[complete report](../reports/m7e-live/README.md) for the unchanged raw evidence,
known usage, unknown full cumulative cost and evaluation limits.

Close with: “The deliverable is a reproducible retrieval and evaluation system.
The structure heuristic exposed a recall–ranking tradeoff, and the LLM assessment
pipeline makes protocol failures and missing results visible.”

## After the demonstration

Use the [project brief and bilingual CV wording](project-brief.md) for a concise
description. To run Dense/Hybrid on prepared real snapshots or rebuild the full
benchmark, follow [reproduction](reproduction.md) and [experiments](experiments.md).
Those longer runs are outside this short walkthrough. The main engineering scope
is complete; additional models, benchmark versions or paid calls are separate work.
