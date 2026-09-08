# M6c: Expanded Retrieval Experiments and Cost Measurements

## Status and interpretation

This checkpoint implements the fixed experiment matrix and measures the existing
retrieval system on all three frozen datasets. **Labels and quality results remain
provisional.** No independent human review, improved-label release or reviewed-M6
acceptance is claimed. The owner reported M6b CI passing; M6c remote CI awaits the
owner's commit and push.

The matrix contains 15 inherited configurations per role: five main retrieval
strategies and ten additional structure ablations. The 40-query development seed,
120-query expanded test candidates and ten-query public adaptation remain separate.
The public run uses this project's full-repository symbol-retrieval protocol, not
original RepoQA scoring. All parameters, source versions and dataset membership were
frozen before inspecting the new test/public outcomes. No tuning followed those runs.

These test questions are now exposed. Future tuning needs another untouched test
version. Sparse, agent-authored positive labels can omit valid alternatives; related
question families and repositories limit independence. Higher scores need not imply
more useful LLM answers. QA evaluation remains M7 work.

## Expanded test findings

On the 120 test-candidate questions, full structure does **not** improve aggregate
known-label quality over Hybrid. Recall@10 changes from 0.7944 to 0.7917, while
NDCG@10 falls from 0.5947 to 0.5109. This is evidence against this particular frozen
reranking heuristic, not against all uses of repository structure.

The paired NDCG difference is **-0.0839**, with the existing repository-cluster
95% percentile interval **[-0.1356, -0.0381]** and 15/49/56 query wins/ties/losses.
Recall's difference is -0.0028, interval [-0.0500, 0.0444], with 6/110/4 wins/ties/losses.
These are conditional summaries over five selected repositories, not corrected
significance claims or uncertainty estimates for incomplete labels.

| Main strategy | Recall@10 | NDCG@10 | MRR@10 | Query p50 ms | Query p95 ms |
| --- | --- | --- | --- | --- | --- |
| BM25 | 0.6444 | 0.4854 | 0.4644 | 12.05 | 150.69 |
| Dense | 0.7292 | 0.5675 | 0.5480 | 32.42 | 171.72 |
| Hybrid | 0.7944 | 0.5947 | 0.5637 | 55.16 | 373.14 |
| Symbol-aware | 0.7931 | 0.5838 | 0.5438 | 105.57 | 605.54 |
| Structure (full) | 0.7917 | 0.5109 | 0.4409 | 54.52 | 391.98 |

Timing is descriptive: similar Hybrid/Structure medians do not establish zero
reranking overhead. They are separate runs on an uncontrolled interactive host.
Hybrid's judged fraction at ten is only 0.105; most retrieved symbols have no
relevance judgment. Precision@10 therefore measures agreement with sparse existing
labels, not independently reviewed precision over all retrieved candidates.

| Test category | Queries | Hybrid Recall@10 | Structure Recall@10 | Hybrid NDCG@10 | Structure NDCG@10 |
| --- | --- | --- | --- | --- | --- |
| Behavior | 40 | 0.8250 | 0.8000 | 0.5870 | 0.4907 |
| Cross-file | 40 | 0.7083 | 0.7500 | 0.5268 | 0.4995 |
| Symbol | 20 | 1.0000 | 0.9500 | 0.8359 | 0.6298 |
| Test relationships | 20 | 0.7000 | 0.7000 | 0.5049 | 0.4549 |

Cross-file questions gain some recall but lose rank quality. Direct symbol questions
show the largest mean NDCG loss. Full-structure NDCG is lower on each of the five
test repositories, with the largest decreases on TOMLKit and Rich. These categories
and families are small, selected samples, not independent generalization guarantees.

At ten results, average returned context changes from 1,219.14 to 1,232.35 lexical
tokens (a proxy, not LLM tokens). Structure examines 36.63 graph edges and boosts
12.86 non-seed symbols per query on average. It continues to score the full dense
corpus; bounded graph expansion is not an ANN or sublinear retrieval mechanism.

### Relationship ablations

| Fixed configuration | Recall@10 | NDCG@10 |
| --- | --- | --- |
| No relations (Hybrid control) | 0.7944 | 0.5947 |
| Containment only | 0.8042 | 0.5958 |
| Import only | 0.7861 | 0.5903 |
| Call only | 0.7875 | 0.5183 |
| Test relations only | 0.7819 | 0.5805 |
| Full structure without calls | 0.7819 | 0.5758 |
| Full structure | 0.7917 | 0.5109 |

Containment-only is close to Hybrid on NDCG, with a small observed recall gain.
Call-only shows a substantial rank-quality loss, and removing calls reduces the
full model's NDCG regression. These observations are consistent with the traced
caller/helper promotions below. They do not independently establish edge correctness
or a universally better weighting scheme. The complete predeclared matrix, including
every leave-one-out setting and Symbol-aware seeds, remains in the linked reports;
no test-derived configuration replaces the frozen main model.

### Source-traced successes and regressions

[Saved cases](case-analysis.json) are the three largest NDCG@10 gains and losses,
selected after scoring. They illustrate mechanisms, not a representative sample.
Every example retains the original query, designated-positive ranks and first-hit
graph evidence; unjudged neighbors must not automatically be called irrelevant.

- `networkx-10`: `number_connected_components` moves from rank 9 to 1 through a
  reverse call edge from its seeded `connected_components` implementation. The
  pinned source at `connected.py:108` counts the generator without a list.
- `rich-03`: `Measurement.get` moves from rank 7 to 1 through forward call edges
  from renderable measurement hooks.
- `packaging-13`: the grammar entry point `parse_requirement` moves from rank 12
  to 1 through module containment and the reverse edge from `_parse_requirement`.
- `rich-17`: the two designated targets move from ranks 1/2 to 8/9. Reverse call
  edges promote several measurement-hook callers above the already strong seeds.
- `tomlkit-03`: the explicitly requested `_parse_array` moves from rank 1 to 5;
  the heuristic call edge to `parse_error` helps promote that general helper.
- `networkx-02`: the requested `connected_components` moves from rank 1 to 4,
  behind related component functions promoted from other seeds.

The current policy boosts non-seed neighbors without a query-intent check while
leaving seed scores unchanged. These traces explain how useful navigation evidence
can still disrupt an accurate initial order. Preserving exact-symbol matches or
conditioning relation support on query intent are future hypotheses to evaluate on
development data and a new untouched test set, not fixes applied after this test.

## Separate public adaptation

The public adaptation has only ten Marshmallow questions, so one query changes
Recall@10 by 0.1 and repository-cluster intervals are withheld. Its ordering differs
from the original-question test role; this does not establish a general public
benchmark winner.

| Public adaptation strategy | Recall@10 | NDCG@10 | MRR@10 |
| --- | --- | --- | --- |
| BM25 | 0.3000 | 0.2500 | 0.2333 |
| Dense | 0.7000 | 0.3897 | 0.2975 |
| Hybrid | 0.5000 | 0.3693 | 0.3250 |
| Symbol-aware | 0.6000 | 0.3261 | 0.2400 |
| Structure (full) | 0.5000 | 0.3118 | 0.2500 |

## Evidence and reproduction

- [Complete metric and construction tables](report.md).
- [Frozen plan](plan.json), [split/source audit](audit/audit.json) and
  [configuration checksums](configuration-files.json).
- [Development comparison](comparison/dev/report.md),
  [expanded test comparison](comparison/test/report.md), and
  [separate public comparison](comparison/public/report.md).
- [Expanded structure ablations](ablations/test/report.md), with full structure as
  the reference. Main comparisons use Hybrid as the reference.
- `runs/<role>/<configuration>/` preserves rankings, query-level metrics, CSV and
  summaries. [Suite results](suite-results.json) retain worker memory and timing;
  [build costs](build-costs.json) retain graph/vector diagnostics and storage.

Follow [the preparation and measurement protocol](../../docs/experiments.md), then:

```text
uv run --locked --extra dense python scripts/run_m6c.py --allow-provisional --output artifacts/m6c-reproduce
```

Downloaded source, model weights, rebuilt indexes/graphs/vectors and verbose worker
logs remain under ignored `artifacts/`. Only experiment evidence is committed here.
Output configs are regenerated by the script; saved checksums refer to the local
generated files, whose relative input paths depend on the destination depth.

## Measurement environment and limits

Measured on Windows 11, Python 3.12.14, Intel Core i9-13900H, 20 logical CPUs and
approximately 16 GB installed RAM. Encoder and BLAS/OpenMP settings use four threads.
The pinned model is `all-MiniLM-L6-v2`, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, float32, 384 dimensions and 256 input tokens.
Runtime dependency versions are saved with each run and vector profile.

This was an interactive host, not an isolated performance machine. Development
checks briefly overlapped early construction work; background load and OS caches were
uncontrolled. Each of eight repositories had one fresh index, graph and vector build.
Build times include loading/imports and serialization; model download is excluded.
Construction and query timings must not be combined or read as cold-start service SLAs.

Worker peak memory includes native allocations and model weights. It excludes the
coordinator and subprocesses; it is not total machine usage or incremental allocation.
An experiment worker holds every repository in its role, whereas each construction
worker handles one repository. Heterogeneous corpora and one build sample cannot
establish asymptotic scaling or justify a distributed/ANN architecture.

All six new and two development source snapshots rebuilt without skipped-source
diagnostics. The largest, NetworkX, contains 657 indexed files and 9,252 chunks.
Its vector operation took 200.83 seconds including model loading and serialization,
with 960.43 MiB worker peak memory. Of its 9,252 document representations, 2,861
exceeded the encoder's 256-token input limit. Truncation is an observed limitation,
not proof that it caused any particular retrieval failure.

Primary quality measures remain Recall@10 and NDCG@10. Paired repository-cluster
intervals describe uncertainty conditional on these labels; they do not correct
label bias or multiple comparisons. Only the expanded test role has five contributing
repositories; development/public intervals are withheld by the existing policy.

## Local verification

- All 24 construction operations and all 45 experiment runs completed with the
  frozen package implementation hash unchanged. No source/model download occurred
  during the measured suite; all rebuilt source snapshots matched their inputs.
- [Development regression evidence](development-regression.json) confirms all 15
  development quality fingerprints exactly match the preserved M4/M5 reports.
- [Independent verification](verification.json) validates all 45 saved runs and
  confirms that disabled relations exactly reproduce Hybrid in every role. Fresh
  workers repeated all five primary strategies on the 120-query test role using the
  same rebuilt artifacts; every ranking/quality fingerprint matched. This repeats
  retrieval, not the 24 construction measurements, and excludes timing equality.
- Lint, formatting and distribution build checks passed. Source and fresh installed
  wheel environments each passed **197 tests, with one Windows symlink-privilege
  skip and 92% coverage**. The fresh base install contained no torch.
- Tests cover changed config/benchmark rejection, clean snapshot requirements,
  model-free graph/vector-profile contracts, real child-process BM25 profiling,
  failed-worker evidence, split-specific routing and rejection of mid-suite code
  changes. Synthetic orchestration tests are separate from the real runs above.
