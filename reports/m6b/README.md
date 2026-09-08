# M6b: Broader Draft Benchmarks and Public-Subset Audit

## Delivered checkpoint

This checkpoint expands the benchmark data and source-review tooling. It does **not**
complete independent label review or M6's formal experimental acceptance. The owner
reported M6a CI passing; M6b remote CI awaits the owner's commit/push.

| Dataset role | Repositories | Queries | Judgments | Review status |
| --- | --- | --- | --- | --- |
| Existing development seed | Requests, Click | 40 | 55 | Provisional |
| New test candidate | Flask, Rich, NetworkX, Packaging, TOMLKit | 120 | 164 | Provisional |
| Separate public adaptation | RepoQA Marshmallow | 10 | 10 | Provisional |

The original-question benchmark now has **160 questions on seven repositories**;
the complete suite has **170 questions on eight** when the public adaptation is
included. These are questions, not ranked candidate pairs or completed human reviews.

Each new test repository has four symbol, eight behavior, eight cross-file and four
test questions. All 40 cross-file questions have positive targets in at least two
files. The 120 questions record 85 families, with rationale and source hashes for every
target. Questions were authored from the inspected source before new retrieval runs.
Known positives are incomplete; all current questions are answerable, so this data
does not yet assess abstention. Shared targets and related ecosystems remain possible
dependencies despite repository URL separation.

## Frozen data and source selection

The five new releases cover web request handling, terminal rendering, graph algorithms,
package metadata and structured configuration. Indexed sizes range from **707 to
9,252 chunks**. These are corpus/storage observations, not latency or scalability
results. Full selected Python source includes tests/examples; it is not restricted to
the labeled functions. No skipped-source diagnostics occurred on the six new snapshots.

- [Generated suite audit](report.md) and [machine-readable audit](audit.json) contain
  exact commits, corpus/snapshot hashes, licenses, counts and the audit code hash.
- [Expanded draft data](../../benchmarks/expanded-v1/README.md) contain 120 questions,
  source-bound qrels, explicit family/overload selectors and the generation recipe.
- [Public adaptation](../../benchmarks/repoqa-marshmallow-v1/README.md) retains all ten
  Marshmallow descriptions from the pinned RepoQA release, with license and attribution.

The public importer verifies the compressed archive hash and the exact repository,
then checks source-file bytes, function names, UTF-8 offsets and AST line ranges.
One-based local targets include decorators. All ten public needles matched. The
original descriptions remain unchanged; their intended function targets map to grade-2
qrels. The full repository is retrieved under this project's protocol, so resulting
metrics must not be presented as original RepoQA scores or mixed into the primary
repository-question comparison.

The [suite manifest](../../benchmarks/suite-v1.json) freezes development/test/public
membership and the planned primary measures Recall@10 and NDCG@10. Audit checks reject
overlapping repository URLs/aliases, duplicate IDs or normalized question text, changed
benchmark/provenance digests, stale source indexes and invalid split roles. These checks
cannot establish semantic independence, remove source-selection bias or determine
model-training contamination.

## Review artifacts and remaining work

The committed [test review manifest](test-review-manifest.json) and
[public review manifest](public-review-manifest.json) bind the review targets to source
snapshots. Their corresponding [test status](test-review-status.json) and
[public status](public-review-status.json) record **164 + 10 pending judgments and
120 + 10 pending question reviews**. No independent review is claimed.

Local generated bundles include 130 source pages and editable reviewer templates.
They use existing qrels only, with an empty run list and the explicit
`existing_judgments_only_no_retrieval` policy. This allows initial source review before
looking at test outcomes. Broader relevance pooling, missing alternatives, uncertain
questions and disputes still need review/adjudication. New reviewed labels require a
new version and updated suite digests; existing M3–M6a data/reports remain intact.

**No retrieval or QA was executed on the new test/public datasets during M6b.**
Their quality scores, strategy ablations, model token costs, peak-memory measurements
and timing comparisons remain M6c work. Passing source checks or CI does not replace
the reviewed-label criterion.

## Reproduce and validate

From the project root, choose a new output directory:

```text
uv run --locked python scripts/run_m6b.py --prepare --output artifacts/m6b-reproduce
```

`--prepare` permits source/data downloads; omit it once artifacts exist for an entirely
offline rebuild. The workflow compares all ten regenerated benchmark files against
the committed versions, audits the suite and prepares the two review bundles. It needs
no torch, model weights, RepoQA installation or API credentials. Follow
[the benchmark guide](../../docs/benchmarks.md) to submit actual reviews.

Validation on the local Windows/Python 3.12 environment:

- Lint, formatting and wheel/source builds passed.
- **189 tests passed, one Windows symlink-privilege test skipped; coverage 91%.**
  A fresh installed-wheel base environment without torch passed the same suite.
- Two independent reconstructions and the installed wheel produced **160 byte-identical
  files**, including benchmark data, audit, source pages, templates and pending checks.
- All six new repositories were independently downloaded and indexed again. Corpus
  hashes, source targets and snapshot IDs matched, including shallow exact-commit
  preparation for Marshmallow.
- M6a regression reproduction retained its original 845-pair pool digest
  `0a160ed1812e4dbc9c0c3fafa6bc92508d1a30290ca6941e82660d104b2900b2`.

Suite digest:
`42f9000256c73dc9b9bd21f04046b41d2efcc6d79113cd839644ee55783f2e3d`.
