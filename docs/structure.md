# Structure-Aware Retrieval (M5)

M5 tests a bounded graph-support hypothesis over the existing retrieval baselines.
No parameters or labels are changed in response to the M5 scores. Graph generation
needs only the stored SQLite snapshot; search also uses the chosen seed strategy's
existing artifacts. No additional dependencies are introduced.

## Relation extraction

Stored source chunks reconstruct line positions; omitted whitespace-only spans become
blank lines. This is not a byte-for-byte reconstruction of the original checkout.
The AST pass maps definitions back to exact indexed ranges and builds lexical scopes.
It reads code statically, never imports it, and leaves the original index unchanged.

| Kind | Evidence | Confidence |
| --- | --- | --- |
| `containment` | Indexed parent and child definition | static |
| `import` | Resolved local module/member and import line | static |
| `call` | Resolved syntactic call, excluding the test category below | static or heuristic |
| `test` | Call from a test-named path into a non-test path | heuristic |

Test paths have a `tests` component or a filename matching `test_*.py`/`*_test.py`.
Resolved cross-boundary test calls belong only to `test`, not also `call`, so the two
ablation categories do not double-count the same observation. These links are not
measured coverage, test relevance labels, or proof that a patched target executes.

Module lookup considers the repository root and `src/`. Relative imports, aliases,
unambiguous re-exports and lexical nested functions are supported. Alias traversal
stops at cycles or 12 hops. Conflicting module roots, duplicate definitions/import
bindings, parameter/assignment shadowing, wildcard imports and missing/external names
produce unresolved records. Scope handling skips class namespaces for method free
variables. Conventional `self`/`cls` calls resolve only to the same lexical class and
are heuristic; known `staticmethod` definitions do not get that receiver assumption.

Instance type inference, inheritance/`super`, dynamic receivers, lambdas, decorator/
default/annotation/base expressions, global/nonlocal binding analysis, arbitrary
import roots and whole-program data flow are unsupported. Comprehension stores may
conservatively block a surrounding name. `static` describes a syntactic binding, not
a guarantee of runtime behavior: conditional execution, monkeypatching, decorators
and Python's dynamic semantics can invalidate an apparent relationship.

Each graph contains source/target IDs, kind, confidence, path, line and expression,
plus unresolved references and reasons. The graph hash covers binding, ordered edges
and unresolved records. Loading checks snapshot/content/resolver compatibility, edge
endpoints, source ranges, duplicate IDs and checksum. Atomic publication requires a
new filename and a local filesystem supporting hard links. Graph source/code-policy
changes require rebuilding into a new file and updating experiment paths.

## Fixed expansion policy

Default seeds are Hybrid, chosen because of its M4 development result. Symbol-aware
seeds are a separate fixed comparison. A BM25 seed option supports model-free use.

| Setting | Default |
| --- | --- |
| Unique seed symbols | 5 |
| Examined edges per seed | 64 |
| Selected distinct neighbors per seed | 8 |
| Expanded non-seed symbols across the query | 20 |
| Depth / direction | one hop / both directions |
| Alpha | 0.5 |
| Relation weights | containment 0.2, import 0.3, call 1.0, test 0.8 |
| Heuristic confidence discount | 0.5 |

Full baseline retrieval happens first. Seeds are the first unique symbols. For each
seed, merge the enabled adjacency lists by descending discounted weight, then stable
edge ID, and inspect at most 64 edges. Skip self/seed targets and targets without
baseline evidence. Repeated targets give one candidate per seed. Select candidates
by weight, baseline evidence rank and symbol ID, then apply neighbor/global caps.
Repeated call sites can consume the edge budget; cap-hit counts expose that limitation.
The global cap follows seed order rather than a global combinatorial selection.

For a selected neighbor, use only its best baseline chunk and the maximum support
across seeds, never a sum of repeated links:

```text
support(edge, seed) = relation_weight * confidence_discount * 61 / (60 + seed_rank)
score(chunk) = base_score(chunk) * (1 + alpha * max_support)
```

Seed ranks are one-based; static confidence discount is 1. All other chunks keep
their base scores. Sort by score and stable chunk ID, then apply the existing
symbol/file evaluation deduplication. No-edge and alpha-zero policies return the
unmodified base ranking. Expanded neighbors never become new seeds in that query.

The default dense-backed baseline already ranks every chunk: graph expansion means
adding bounded support outside the seed list, not avoiding corpus scoring. BM25-only
mode cannot promote zero-match symbols absent from its ranking. Source evidence stays
the query-best existing chunk; it need not contain the relationship's call/import line,
which is recorded separately in the provenance.

## Evaluation boundary

Run the [fixed suite](../scripts/run_m5.py) after graph preparation. It compares two
seed baselines, full/disabled relations, all four single types, all four removals,
and full relations with Symbol-aware seeds. The graph, budget, source snapshot and
seed config are included in run provenance; changes require new experiment outputs.

Reports contain per-query source traces, quality, warm latency, graph-work counts and
returned-context size. Lexical token counts are a size proxy, not actual LLM usage.
Use [M5 observations](../reports/m5/README.md) to assess successes and regressions.
The seed benchmark still needs human relevance review; graph edges also have no
independent precision/recall annotation yet. A quality improvement is not assumed.
