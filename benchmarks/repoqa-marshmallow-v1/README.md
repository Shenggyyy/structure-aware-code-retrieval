# RepoQA Marshmallow: Retrieval Adaptation v1

This independent **public subset** uses all ten Marshmallow needles from the
[RepoQA 2024-06-23 release](https://github.com/evalplus/repoqa_release/releases/tag/2024-06-23).
RepoQA studies long-context code understanding through function descriptions;
see [the upstream project](https://github.com/evalplus/repoqa) and
[Liu et al., 2024](https://arxiv.org/abs/2406.06025).

Marshmallow was chosen before scoring because it supplies a compact, licensed,
Python-only schema/serialization corpus with all ten targets resolvable by the
existing AST parser. This is a convenience subset, not a random sample or a claim
about the complete RepoQA benchmark. Its repository is separate from development
and the five original-question test repositories.

## Adaptation and source binding

- Use upstream `marshmallow-code/marshmallow`, commit
  `b8149cec77d16357d11b08f86de3b13e6fe02fa0`.
- Preserve every selected upstream description verbatim and preserve needle order.
  Descriptions were generated in RepoQA's curation process, not newly human-authored
  or independently reviewed by this project.
- Convert each designated needle to one grade-2 symbol qrel. Other symbols remain
  unjudged; the adaptation does not establish exhaustive relevance.
- Verify the release archive SHA-256, repository commit, source-file byte hash,
  AST function name, UTF-8 byte offsets and zero-based/exclusive upstream line bounds.
  Map these to this project's one-based/inclusive bounds, including decorators.
- Retrieve over the **full indexed repository**, including tests, with original
  docstrings and comments retained. The corpus has 37 files and 2,118 chunks.
  Do not use the upstream ten needles as the candidate corpus.

This evaluates retrieval metrics, not the original model-generated function answer
or its matching criterion. It does not reproduce RepoQA's context length, dependency
ordering, needle placement, comment-removal settings or scoring protocol. Report
results separately as **RepoQA-Marshmallow retrieval adaptation**, never as an
upstream RepoQA score. Model-training overlap is unknown.

Archive SHA-256:
`c050a2ad90a7df89d9dc1f1c3b3b20683edd20a56293b35fcaae43dec115d681`.
The published release contains multiple languages; this importer selects only
Python and the exact Marshmallow repository, with an expected count of ten.

## Reproduction and optional review

`recipe.json` specifies the source. `provenance.jsonl` preserves upstream offsets,
needle identities, file/needle/description hashes and pending independent review.
The five generated data/freeze files can be rebuilt without installing RepoQA or
executing any source in the downloaded repository:

```text
uv run --locked python scripts/run_m6b.py --prepare --output artifacts/m6b-reproduce
```

Omit `--prepare` to use existing artifacts offline. See
[benchmark workflow](../../docs/benchmarks.md) for the dedicated public review bundle.
The manifest remains `annotation_status=provisional`; human review is optional and
is not a completion prerequisite. A successful source-alignment check is not semantic
label approval. Any later label improvement needs a new version and truthful provenance.

## Attribution and licensing

The adapted descriptions come from the Apache-2.0-licensed
[RepoQA data release](https://github.com/evalplus/repoqa_release).
Its license is copied in [LICENSE](LICENSE); [NOTICE](NOTICE) describes the adaptation.
Marshmallow source is separately MIT-licensed by Steven Loria and contributors;
see [its pinned license](https://github.com/marshmallow-code/marshmallow/blob/b8149cec77d16357d11b08f86de3b13e6fe02fa0/LICENSE).
The committed subset includes descriptions and source locators, not repository code.
