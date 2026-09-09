# M9a — Repository import and five-strategy previews

This checkpoint implements the first part of the repository workbench:
**import → prepare resources → ask one question → save five context previews →
reopen history**. It reuses the existing parser, retrievers and QA context/source
checks. Browser interaction and real answer generation remain M9b/M9c work.

## Observed integration checks

Windows validation used Python 3.12.14, the locked dependencies and the existing
local pinned MiniLM weights. Each source completed six CLI operations: import,
prepare, prepare again, preview, history and show. All five strategies returned
`preview`; repeated preparation reused all three resources without changing their
hashes, and reopened JSON matched the saved comparison.

| Source | Actual source version | Observation |
| --- | --- | --- |
| `tests/fixtures/sample_repo` | HEAD anchor `b92de24b9c642c2bb17b5ef5bb7a66c87ef3107f`; copied bytes identify the local source | Real MiniLM embeddings, all five contexts, cache reuse and history passed |
| Public `https://github.com/psf/requests.git` | `0e322af87745eff34caffe4df68456ebc20d9068` | Fresh HTTPS import, real MiniLM embeddings, all five contexts, cache reuse and history passed |

The local source is a synthetic fixture, while Requests is an actual public
repository. Neither question has relevance labels, and neither run generated an
answer. These checks establish workflow behavior, not retrieval quality or an
answer-quality ranking. There were **zero new LLM API calls, zero model downloads
and no new benchmark experiments**. Only the public Git import needed network.

The first public import exposed a Windows cleanup error: Git's read-only pack
files caused staging removal to fail after the snapshot had already been saved.
Cleanup now handles read-only files inside the validated owned staging directory,
records any cleanup failure separately and preserves the original operation's
outcome. A fresh public import and the entire six-command sequence passed after
that fix. The earlier staging directory was retained locally for diagnosis.

## Automated validation

The complete offline suite passed **1,019 tests with two skips** in about 8 minutes
53 seconds; both skips require unavailable Windows symlink-creation privileges.
The 158 new workbench cases account for 157 passes and one of those skips. Combined
statement/branch coverage is **91.43%**. Ruff lint/format and the offline wheel/source
distribution build passed.

The new offline tests cover URL/DNS and path validation, Git configuration
isolation, static source capture, actual source provenance, bounded inputs, cache
bindings/corruption, independent preparation/strategy failures, interruption
records, saved-history reopening without resources and CLI exit/output behavior.
Synthetic encoders in tests are explicitly marked; the checks above separately
exercise the real pinned encoder.

Run the same checks from the project root:

```text
uv run --locked --offline ruff check .
uv run --locked --offline ruff format --check .
uv run --locked --offline pytest --cov --cov-report=term-missing
uv run --locked --offline python scripts/summarize_results.py --output reports/overview --check
uv build --offline
```

See [validation.json](validation.json) for measured test totals, coverage, source
and resource identities, and the exact encoder configuration. The existing
45-run retrieval overview passed validation without changing historical reports.
Current remote CI remains pending the owner's commit and push. The existing
Windows/Linux pytest jobs collect the new tests, and the Docker build packages
the new CLI modules without dependency or port changes. Container builds were not
rerun for this checkpoint.

## Reproduce the workflow

Follow the [PowerShell startup instructions](../../docs/workbench.md), including
explicit model preparation, then choose a local source or the pinned public
Requests URL above. Use `--json` on import/preview to retain their IDs; use
`workbench history` and `workbench show RUN_ID --json` to reopen results. Model
preparation may download weights on a new machine; preview itself is offline.

The recorded CLI summaries are included in `validation.json`; full local run
artifacts remain under ignored `artifacts/` directories. History includes code
evidence and source locations without requiring those source/resource directories
to remain available. Checksums are corruption checks, not authenticity signatures.

## Remaining scope and limits

- M9a exposes CLI services only. M9b must complete browser import/status, question
  entry, five-column comparison, source expansion and saved-history interaction.
- M9c must use one answer model and common generation settings, with a new combined
  estimate and owner approval before calls. No semantic judge is enabled by default.
- Local HEAD is only an anchor for copied working-tree bytes; cleanliness is unknown.
- Imports are Python-only, public HTTPS or local, with no private authentication,
  submodule/LFS downloads or target execution. Git transfer time is bounded, but
  downloaded pack size has no hard disk quota.
- Retrieval timings are sequential local observations. Generation time, provider
  tokens and costs remain unknown; unlabeled questions have no Recall/NDCG scores.
- Provisional benchmark labels, negative retrieval findings, invalid judgments and
  historical unknown costs remain unchanged.
