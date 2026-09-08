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

## Manual Review Rubric

Review generated answers against the actual supplied context and pinned source:

- **Correctness:** mark each substantive claim as correct, incorrect, or
  unsupported. Check whether the answer directly addresses the question and
  covers the relevant reference points; optional explanatory detail is not
  required for a simple location question.
- **Citation support:** verify that the cited visible lines support their
  associated claims. A valid source identifier and in-range line numbers prove
  citation identity, not semantic support or answer correctness. Record missing
  support separately from incorrect claims.
- **Abstention:** the two controls require unavailable private deployment
  information. Expect `insufficient_context` with `claims: []`, without invented
  timeout values or application commands. Record the missing evidence in the
  review rationale; the model output contract does not include an abstention
  explanation. Do not infer global absence of a library capability. For
  source-grounded cases, distinguish retrieval/context omissions from model
  failure to use evidence. Report automatic empty-evidence abstention separately
  from model-generated abstention.

Record reviewer identity, rationale, disagreements, and adjudication before
claiming reviewed accuracy. Report controls separately from answerable cases.

## Label Leakage Prevention

Only the question and retrieved code context belong in the model request.
Never send `reference_points`, `source_targets`, `expected_status`, or the
selection rationale to the model or use them to seed retrieval. These fields
are evaluation-only. Keep prompt/model development confined to this development
set; freeze changes before evaluating independently reviewed test data.
