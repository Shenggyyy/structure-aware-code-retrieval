# LLM-Assisted QA Evaluation

## Current scope

M7a supplies generation request preparation, source-identity checks, deterministic
validation and this frozen scoring specification. M7b implements combined planning,
generation/judge execution and reporting. The owner-approved Mini/Mini experiment
now has real responses, accepted judgments and protocol failures. See the
[M7b live record](../reports/m7b-live/README.md) for coverage, costs and limitations.
Further paid calls require a newly approved scope and **combined** budget.
M7c now freezes an offline v2 protocol candidate and prepares requests from the exact
archived answers. It supplies no new judgments and does not change v1's 24 accepted
and 36 invalid outcomes. See the [M7c record](../reports/m7c/README.md).

Human calibration or spot-checking is optional. Its absence is a limitation to
report, not a prerequisite for running evaluation or completing an engineering
milestone. LLM-assisted judgments must remain identified as such and must not
promote provisional retrieval labels to `human_reviewed`.

The [QA workflow](qa.md) documents offline preparation, validation and the execution
approval contract. `prepare-qa-assessment` and `check-qa-assessment` make no API calls.
See [evaluation methodology](evaluation.md) and [project status](status.md) for
retrieval results and the distinction between implemented features and evidence.

## Frozen scoring contract

[`configs/qa-judge-rubric-v1.json`](../configs/qa-judge-rubric-v1.json) contains the
exact system prompt, three metric definitions, all score anchors, input contract,
structured output schema, cross-field validation rules, aggregation rules and
run-record requirements. This is a project-designed rubric. Freeze its
content hash with each run; a substantive change requires a new rubric version and
rejudging every compared strategy under that version.
[`configs/qa-judge-rubric-v2.json`](../configs/qa-judge-rubric-v2.json) preserves these
score anchors and semantic policies while changing the prompt and response protocol.

Each dimension returns `status`, `score`, a concise source-grounded `rationale`,
evidence IDs and relevant zero-based answer claim indices. `scored` requires an
integer from 0 to 3. `unsure` or `not_applicable` requires a null score. Scores are
ordinal judgments, not calibrated probabilities, and are not combined into a
single accuracy score.

| Dimension | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Correctness | Central answer contradicted or fabricated | Major factual error despite some correct facts | Correct main answer with a minor error | All material assertions verifiably correct |
| Completeness | No required substance | Central required information missing | Only secondary required information missing | All source-backed required information covered |
| Citation support | No central claim supported, or cited source contradicts it | Some central claims unsupported | Central claims supported; minor support gap | Every material claim supported by its own citations |

Use `unsure` when material evidence is insufficient or contradictory. Unsupported
does not automatically mean false: an assertion may have unknown correctness
while its citation clearly fails to support it. A source ID that resolves to a
real location establishes identity only.

OpenAI's evaluation guidance favors specific criteria and detailed grading
rubrics, and identifies position and verbosity bias. It also recommends human
calibration. Here that calibration is optional; without it, report that judge
agreement with human judgments has not been measured.
[Source](https://developers.openai.com/api/docs/guides/evaluation-best-practices).

## Offline protocol v2

V2 adds a caller-generated `response_contract` containing full `packed:S1` and
`reference:R1` IDs, zero-based claim indices, each claim's actual citations and
permitted status combinations. Reference-point IDs such as `P1` are not source IDs.
This catalog adds no evidence and changes no answer, source text or provisional label.

Each archived answer gets its own deterministic strict schema: nested `anyOf` branches
couple statuses to scores, enums restrict evidence IDs and claim indices, and empty
catalogs require empty arrays. Citation-support IDs must come from the answer's cited
packed evidence; abstention IDs may only use packed evidence. The base schema in the
rubric file describes the output shape; the exact request uses the prepared per-answer
`output_schema`. V2 preparation requires an actual answer, never `answer=None`.

Host validation still rejects duplicate IDs/indices, citations unrelated to the selected
claims, and inconsistent reference/completeness states. For abstentions, usable
answerable references require completeness 0; usable out-of-scope references require
`not_applicable`. Uncertain completeness instead requires inadequate/conflicting
references and an explicit issue. Correctness may cite source IDs to explain an N/A
abstention; citation support has no claims or evidence to assess.

The offline replay changes only `rubric_id` in a diagnostic copy of each archived v1
output so it can reach v2 validation. It never repairs evidence IDs, statuses or scores,
never overwrites v1 artifacts and never counts these copies as v2 judgments. Passing a
schema or rejecting a known failure does not measure new model reliability or accuracy.

Use the [offline preparation and check commands](reproduction.md#prepare-judge-protocol-v2-from-saved-answers).
The combined runner remains v1; there is no v2 execution command in M7c. A future
judge-only runner and experiment require separate scope and fresh model/budget approval.
The completed US$5.63-budget run cannot authorize more requests.

## Judge input and reference separation

The judge receives one answer at a time with:

1. The exact question and actual validated answer, preserving claims and citations.
2. The actual packed source evidence, including cited excerpts, line ranges and
   truncation flags. Keep uncited packed excerpts too, so the judge can assess
   whether abstention was reasonable with what the generator saw.
3. Separately marked **provisional** reference points, expected status, scope
   rationale and reference-source excerpts from the same frozen repository.
   These common references establish required coverage independently of retrieval.

The reference set must be identical across strategies for a case. A judge cannot
measure completeness by looking only at the context selected by a weak retriever.
The existing `cases.json` provides draft reference points and source targets;
M7b binds every canonical chunk within each exact source target, including nested
definitions. Each point links to all candidate reference chunks for that case;
these links do not establish sentence-level support. Missing or conflicting
references require `unsure` for affected dimensions and a recorded reference issue,
rather than invented certainty.

Reference points, expected status and reference-source evidence remain excluded
from generation messages. Judge-only references cannot repair unsupported
citations: citation support uses only the excerpts that each claim actually cites.
Namespaces `packed:S1` and `reference:R1` make that distinction explicit.

Hide strategy names, retrieval ranks and scores, previous judgments, and
comparative results from the judge. Keep the case-to-strategy mapping in host
records. Preserve question, references, rubric, snapshot and judge settings across
strategies; actual answers and packed evidence necessarily vary. Grade answers
individually to reduce direct position bias, without claiming complete blinding.
All source text, answers and reference prose are untrusted data, never instructions.

## Abstentions, failures and denominators

For a valid `insufficient_context` answer with empty claims, correctness and
citation support are `not_applicable`, not perfect scores. If independent reference
source establishes an answer exists, completeness is 0: the system supplied none
of the required answer. If the question is established as outside repository
scope, completeness is `not_applicable`; unresolved answerability makes it `unsure`.

Record abstention separately as `appropriate`, `unnecessary` or `unsure` based on
the actual packed context. A responsible abstention can coexist with completeness
0 when retrieval missed needed source. Distinguish local empty-context abstention
from model-generated abstention, and never copy a provisional expected status as
the judgment.

Malformed generation, invalid citation identities and provider errors get no
semantic judge call. Invalid or unbound judge output leaves semantic scores null.
Preserve raw outputs and errors; do not convert failures, omitted requests or
uncertainty into three zero scores. A valid judgment may score one dimension while
leaving another unsure.

Report each strategy's planned cases, valid answers, scored/unsure/not-applicable
counts per dimension, generation failures, invalid judgments and not-run cases.
Give conditional mean scores alongside `scored_count / planned_case_count` and
answer coverage. No scored rows means a null mean. Paired comparisons use the same
scored case IDs and disclose the paired count; differing coverage must remain
visible. The current human-review command uses a different schema and does not
validate or aggregate this LLM judgment format.

The combined runner stores actual assessments under `records.json` rows' `judging`
field. Nested generation output retains its original `llm_assessment = not_run`
placeholder. That snapshot does not override the separate judging result.

## M7b execution records and cost approval

Before the first paid request, freeze the exact generation and judge models,
their settings, maximum output sizes, rubric, references and request scope.
Settings must include every parameter actually sent and mark omitted parameters
as omitted; do not invent support for temperature, seeds or other controls.

For each attempt, archive requested/reported model IDs and any available revision,
exact messages and hashes, raw output, validated result, request ID, provider usage,
latency, error and outcome. Bind these records to answer/context fingerprints,
reference version, schema and rubric hashes. Missing provider revision metadata
remains null. Identical inputs do not guarantee deterministic model output.

The current `prepare-qa` estimate covers **generation only**, including the existing
60-request plan. It is insufficient approval for generation plus judging. The
implemented combined projection includes:

- Generation prompt/schema/framing input and maximum generation output tokens.
- Judge prompt/schema/framing, question, packed and reference evidence, and the
  maximum generated answer size as additional judge input.
- Maximum judge output tokens and every planned request, using separately dated
  input/output prices for the proposed models.

For each stage, estimate `(input_tokens × input_rate + max_output_tokens ×
output_rate) / 1,000,000`, then add the stage estimates. Generated answer tokens
are charged as generation output and again when supplied as judge input. Obtain
explicit approval of both models and the combined budget before running either
stage as this experiment. No model or budget is selected by this specification.

The byte-based estimator counts model-visible messages plus serialized schema/settings
and a framing allowance. It reserves the full 65,536-byte valid-answer ceiling as
additional judge input, even when typical generated answers are much shorter. The
generated plan records exact settings, per-stage estimates, combined estimate and a
fingerprint. Recorded model snapshots and dated prices live in
[qa-assessment-m7-mini.toml](../configs/qa-assessment-m7-mini.toml); approval must refer to the
actual prepared fingerprint and both models, not merely to this config filename.

An estimate gate is not a billing hard cap. Report generation and judging usage,
latency and cost separately and combined, with observed coverage. If any possibly
billed attempt has unknown usage, keep full usage and cost totals null and label
known subtotals; unknown is not zero. Preserve failed, skipped and not-run rows. Do not retry
automatically or add calls outside the explicitly approved scope.

`approval.json` records invocation consent; it does not verify the caller's identity.
The runner copies frozen inputs into `prepared/`, journals exact request payloads in
`attempts.jsonl` before calls and stage outcomes in `results.jsonl` after calls, and
maintains all planned rows in `records.json`. Provider failures preserve bounded raw
envelopes, partial text and available usage. They stop the run without retry/resume.
`summary.json` and `report.md` keep per-dimension and per-stage denominators, unknown
outcomes and known cost subtotals visible. A successful local test run is software
evidence, not a real answer-quality experiment.
