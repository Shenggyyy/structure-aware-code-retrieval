# QA Development Cases

`cases.json` contains 12 provisional development cases: five source-grounded
questions and one scope-abstention control for each of Requests and Click. The
ten answerable questions preserve their `seed-v1` wording and all positive qrel
targets, including supporting targets with grade 1. Each repository contributes
one symbol, one behavior, two cross-file, and one test question.

This small, deliberately selected set exercises QA behavior; it is not an
independent test set or a representative estimate of repository QA quality.
Selection used only the Requests/Click development corpus, without consulting
the expanded test set or public RepoQA subset. All reference points are
agent-authored drafts checked against source, not independently human-reviewed
answers.

## Source Binding

The referenced retrieval benchmark digest binds questions, judgments, and
repository metadata. Requests is pinned to
`0e322af87745eff34caffe4df68456ebc20d9068`; Click is pinned to
`934813e4d421071a1b3db3973c02fe2721359a6e`. Source targets use exact paths,
qualified names, and inclusive one-based line ranges. Both existing indexes
were validated against the benchmark before drafting the reference points.
Keep these labels versioned with the pinned source; do not silently carry line
references forward to newer upstream revisions.

## Evaluation Rubric

M7a freezes the [LLM evaluation specification](../../docs/llm-evaluation.md) and
strengthens automatic source checks. M7b implements LLM-assisted evaluation of
real answers; the [Mini/Mini live record](../../reports/m7b-live/README.md) preserves
accepted judgments and protocol failures. Labels remain provisional. Assess generated answers against the
actual supplied context and pinned source:

- **Correctness:** assess material assertions against source. Insufficient
  evidence leaves correctness uncertain; missing citation support alone does not
  prove an assertion false.
- **Completeness:** compare coverage with common, source-backed reference evidence
  for the case, separately from the context selected by each retriever. Optional
  explanatory detail is not required for a simple location question. The provisional
  reference points are evidence to check, not authoritative answers.
- **Citation support:** verify that the cited visible lines support their
  associated claims. A valid source identifier and in-range line numbers prove
  citation identity, not semantic support or answer correctness. Record missing
  support separately from incorrect claims.
- **Abstention:** the two controls require unavailable private deployment
  information. Expect `insufficient_context` with `claims: []`, without invented
  timeout values or application commands. Record the missing evidence in the
  evaluation rationale; the answer output contract does not include an abstention
  explanation. Do not infer global absence of a library capability. For
  source-grounded cases, distinguish retrieval/context omissions from model
  failure to use evidence. Report automatic empty-evidence abstention separately
  from model-generated abstention.

Report controls separately from answerable cases. Future model assessments must
record evaluator model/prompt/evidence provenance, rationale, errors and cost; they
are not human-reviewed accuracy or verified true correctness. Manual review is an
optional investigation tool, not a requirement. If used, record reviewer identity,
rationale and unresolved disagreements separately.

## Label Leakage Prevention

Only the question and retrieved code context belong in the answering-model request.
Never send `reference_points`, `source_targets`, `expected_status`, or the
selection rationale to the answering model or use them to seed retrieval. These fields
are evaluation-only; the separate evaluator-input contract is defined in the scoring
specification. Keep prompt/model development confined to this development set;
freeze changes before evaluating a new untouched test version.
