# Expanded Repository Questions v1

This is a **provisional test candidate**, not an independently reviewed benchmark.
Its 120 agent-authored, source-checked questions have 164 positive symbol judgments
across five repositories. Combined with the unchanged 40-query Requests/Click seed,
the project has 160 original questions on seven repositories. The separate public
RepoQA subset is not included in that total.

| Repository | Pinned release | License | Questions | Indexed chunks |
| --- | --- | --- | --- | --- |
| Flask | 3.0.3 | BSD-3-Clause | 24 | 2,030 |
| Rich | v13.7.1 | MIT | 24 | 2,539 |
| NetworkX | networkx-3.3 | BSD-3-Clause | 24 | 9,252 |
| Packaging | 24.1 | Apache-2.0 OR BSD-2-Clause | 24 | 719 |
| TOMLKit | 0.12.5 | MIT | 24 | 707 |

Each repository has four symbol, eight behavior, eight cross-file and four test
questions. Every cross-file question has positive evidence in at least two files.
All questions currently have a designated answer; this draft does not measure
abstention or no-answer detection. Source, tests and examples remain in the full
indexed Python corpus according to the existing scanner rules.

## Authorship and limitations

Questions were written after inspecting implementations and tests at the pinned
commits, before running retrieval on these repositories. Each judgment includes a
source-based rationale. Questions favor inspectable behaviors and include wrappers
and direct symbol references; they are not a random sample of developer workloads.
Some use related targets. The 85 explicit question families document known grouping,
but do not prove that all other questions are independent. Flask also depends on
Click, so disjoint repository URLs do not imply independent ecosystems.

These labels establish known positives, not exhaustive relevance. Alternate valid
targets may be missing. No independent reviewer, negative judgment, inter-rater
agreement or statistical improvement is claimed. The five test repositories remain
unscored during M6b; `split=test` records intended use, not completed review or an
unexposed human test population. Public source may have appeared in model training.

## Files and regeneration

- `recipe.json`: immutable source commits, corpus hashes, licenses and annotation files.
- `annotations/*.json`: readable question drafts, family identifiers and explicit
  path/name targets. `start_line` disambiguates the runtime `tomlkit.items.item`
  definition from overload stubs; the builder never guesses the longest definition.
- `benchmark.json`, `queries.jsonl`, `qrels.jsonl`: evaluator-compatible versioned data.
- `provenance.jsonl`: source file/symbol hashes, recipe/draft digests and pending review.
- `freeze.json`: benchmark/provenance digests and construction counts.

From the repository root:

```text
uv run --locked python scripts/run_m6b.py --prepare --output artifacts/m6b-reproduce
```

`--prepare` permits Git/source-data downloads. Omit it after the artifacts exist to
rebuild and audit entirely offline without torch or model weights. Outputs must be
new directories. The script compares all regenerated text artifacts with this
committed version and creates a label-only review bundle. It does not execute
retrieval or change these files. Review the bundle following
[the review guide](../../docs/review.md), then publish a new version after adjudication.

Pinned upstream source and license files:
[Flask](https://github.com/pallets/flask/tree/c12a5d874c5a014495eb2db8a73f40037bc813ac),
[Rich](https://github.com/Textualize/rich/tree/7f580bdcf07a3b269a0e786b6a3aa9c804f393cf),
[NetworkX](https://github.com/networkx/networkx/tree/7fdddfa2caa8275f7862c46524b803db99ff2cde),
[Packaging](https://github.com/pypa/packaging/tree/85442b8032cb7bae72866dfd7782234a98dd2fb7),
[TOMLKit](https://github.com/python-poetry/tomlkit/tree/a96883b15f545169dd33f16160bd609d624471e3).
