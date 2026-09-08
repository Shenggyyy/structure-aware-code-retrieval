# M7a: Offline Checks and LLM Evaluation Specification

Recorded on 2026-09-08. This checkpoint completes the revised **offline** scope.
Human review is optional. M7b generation and LLM judging remain deferred, with no
live answers, model scores or API spend from this checkpoint.

## Observed validation

- Reprepared twelve provisional development cases across five strategies: **60
  requests**, each with ten packed source excerpts. All 600 evidence occurrences
  pass identity, path, physical-line and text-hash checks.
- Revalidated the frozen bundle and previewed all sixty requests using the final
  code. The checked sources are bound to the actual question and prompt payload,
  including JSON value types. No answering or judging model was called.
- Every preview has automatic source checks and a separate `llm_assessment` with
  `status: not_run` and null scores. Answer citation validity is null because there
  is no answer to check. Source validity does not establish semantic support.
- Prompt content still matches the [original M7a preparation](../m7a/README.md):
  `e39035f3d7bb4837cb26c9a4decdb1038c7b03e97535464e89391edad35689ce`.
- Final regression: **540 passed, 1 skipped**, **91.80% combined statement/branch
  coverage**. The skip concerns unavailable Windows symlink privileges. Ruff lint
  and format checks, distribution builds and the saved 45-run overview check pass.

[validation.json](validation.json) records the request and source-code fingerprints,
rubric/prompt hashes, actual test counts and scope limitations. Large local request
bundles remain in ignored `artifacts/qa/m7-offline-route-v2/`. These summaries do not
replace the complete bundle or provide live evaluation results.

## Frozen specification and costs

The [versioned rubric](../../configs/qa-judge-rubric-v1.json) defines correctness,
completeness and semantic citation support on separate ordinal 0–3 scales, with
explicit uncertainty, abstention and failure rules. M7b must implement the judge,
bind common reference evidence, and archive exact settings/messages/raw responses.

The saved generation-only projection remains **$0.91370775 USD** at the historical
configuration's rates. It excludes judging, is not actual spend or a billing cap,
and does not authorize either model. Before live calls, present both models and
their combined estimated cost for explicit approval.

Existing labels and QA references remain `provisional`. Model scores must be named
LLM-assisted assessments, never human-reviewed results or verified true accuracy.
The [current acceptance policy](../../docs/status.md) supersedes historical report
text that made independent human review a completion requirement.

## Reproduction

After the [local source/model preparation](../../docs/reproduction.md#prepare-the-qa-experiment-offline),
use a new output directory:

```text
uv run --locked --extra dense sacr prepare-qa --config configs/qa-m7.toml --output artifacts/qa/m7-offline-reproduction-001
uv run --locked pytest --cov
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked python scripts/summarize_results.py --output reports/overview --check
uv build --offline
```

Dependencies must already be cached for offline builds. No `--execute` is used.
Remote CI for this checkpoint runs after the owner commits and pushes.
