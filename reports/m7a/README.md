# M7a: Offline Repository QA Preparation

Recorded on 2026-09-08. This checkpoint implements the QA pipeline and prepares
real-source requests. **No OpenAI calls were made, no answers were generated, and
no QA correctness/support scores exist.** The owner chose to defer paid execution.

## Observed preparation

- Twelve provisional development cases on Requests and Click: ten source-backed
  questions plus two unavailable private-deployment information controls.
- Five inherited retrieval strategies, twelve requests each, **60 requests total**.
- Every context contains ten unique symbols. Evidence JSON sizes range from **2,589
  to 15,966 UTF-8 bytes**, below the fixed 16,000-byte budget.
- One evidence excerpt was budget-truncated in each of Hybrid, Symbol and Structure;
  none were budget-truncated in BM25 or Dense. All source truncation preserves full lines.
- All contexts are nonempty, including the scope controls. Retrieval alone therefore
  does not establish that a question is answerable.
- Proposed fixed model: `gpt-5.4-mini-2026-03-17`; at most 1,024 output tokens per call.
  Conservative projected spend: **$0.91370775 USD**, using the frozen standard rates
  and byte-based input estimate. This is not actual spend or a billing guarantee.

Two real preparations reproduced the same prompt content fingerprint:

```text
e39035f3d7bb4837cb26c9a4decdb1038c7b03e97535464e89391edad35689ce
```

Full integrity fingerprints also include measured timing/runtime data and need not
match across preparations. Preparation timings are single passes, not performance
benchmarks. Existing M3–M6c results and retrieval algorithms were not modified.

## Evidence and reproduction

- `plan.json`: final prepared configuration, snapshots, code/input hashes and cost assumptions.
- `requests-summary.json`: all sixty prompt/context fingerprints and context counts.
- `preparation.json`: compact observations, explicit zero calls and pending review status.

After following the README's M4/M5 source/model/vector/graph preparation steps:

```text
uv run --locked --extra dense sacr prepare-qa --config configs/qa-m7.toml --output artifacts/qa/m7-prepared
```

This creates the full messages, source previews and separate reviewer references.
Compare the returned plan's `content_fingerprint` with the value above. Large local
bundles remain under ignored `artifacts/`; committed summaries are not executable
substitutes for the full request bundle. The execution loader verified the final
bundle offline without reading credentials or calling a model.

## Validation and limits

Final local Windows/Python 3.12 regression: **490 passed, 1 skipped**, **92% combined
statement/branch coverage**. The skip is unavailable symlink creation on this host.
Tests cover source budgets and identities, strict answer/citation validation,
malformed/refused/incomplete API responses, preserved billing uncertainty, durable
partial runs, label leakage, stable prompts, and manual-review binding/denominators.
Fake model responses are used only for software tests; they are not QA results.

Ruff, formatting and whitespace checks pass. Source and wheel distributions build;
all 35 packaged Python files match source. An isolated wheel installation with only
locked base dependencies passes help, BM25 search and QA preview; Torch and Sentence
Transformers are absent. Archives exclude caches, downloaded artifacts and credentials.
See `validation.json` for the check summary. New remote Windows/Linux CI runs after
the owner pushes; local validation does not establish remote CI success.

M7b still requires explicit model/budget approval, real provider responses, and
independent correctness/citation review. The reviewed retrieval-label acceptance
items from earlier milestones also remain pending. See the [QA protocol](../../docs/qa.md).
