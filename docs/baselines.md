# M4 Retrieval Baselines

All strategies search the same indexed chunks and return `SearchResult` records.
The 40-query development set and M2 BM25 parameters are unchanged. Constants below
were selected before the M4 comparison; no sweep or tuning on its results was done.

## Encoder and vectors

Use [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41),
revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, Apache-2.0. This compact general
sentence encoder is a practical CPU baseline, not a claim of best code-search quality.
Its model card describes a 384-dimensional representation and 256-word-piece limit.
Its training corpus includes code-search pairs; pretraining overlap has not been audited.

Documents concatenate path, path-qualified name, signature and source code with
newlines, exactly as BM25 does before lexical tokenization. Queries are passed as
written. Both use empty prompts, float32 and L2 normalization. The model's mean-pooling
configuration is retained. Inputs are truncated at 256 tokenizer tokens including
special tokens, without splitting or averaging additional embedding windows.

Execution uses CPU, four torch threads, seed 0, deterministic algorithms and document
batch size 32. Only `prepare-model` permits download. Model loading disables remote
Python code and requests safetensors. `uv.lock` pins the optional libraries; Linux and
Windows torch wheels come from the explicit CPU index. The base install stays small.

`embed` reads saved snapshot text and writes a new compressed NPZ file. Metadata binds
ordered chunk IDs, snapshot, text hash, encoder settings and encoder package versions;
it also stores the vector checksum, build time, bytes and truncation count. Loading
rejects stale bindings, wrong shapes/dtypes, nonfinite/non-normalized rows and checksum
mismatches. Archives load with `allow_pickle=False`; original source is not needed.
Local filesystems must support hard links for atomic vector publication. Rebuilding
requires a new vector filename and an explicit config/path change.

## Ranking definitions

**BM25:** the original BM25Plus, k1=1.5, b=0.75, delta=0. Nonmatches are excluded.

**Dense:** float32 inner products over normalized rows, using NumPy `einsum` without
BLAS threading. Score every row, sort descending with stable chunk-ID ties, and return
the requested K. Negative cosine is retained; scores are not correctness probabilities.

**Hybrid:** equally weighted reciprocal rank fusion of full BM25 and dense rankings:

```text
score(chunk) = sum(1 / (60 + branch_rank(chunk)))
```

Ranks are one-based; an absent chunk contributes zero, and duplicate appearances in
a branch give only one vote. Fusion happens at chunk level before evaluation merges
symbols/files. This is not RRF over pre-deduplicated symbols.

**Symbol-aware (`symbol`):** add a third equally weighted RRF branch using this score:

```text
4 * exact_qualified_suffix + 2 * exact_name + name_token_coverage
    + 0.5 * signature_token_coverage + 0.5 * path_token_coverage
```

Exact matches are case-folded identifier matches, not arbitrary substrings. Qualified
matches require a dotted identifier at a full dotted-name boundary. Coverage is the
fraction of distinct field tokens also present in the query, using existing snake/camel
tokenization; empty fields score zero. All chunks of a symbol share its feature score.
Positive field scores form the third branch, with stable chunk-ID ties. The final
records expose each branch's rank, raw score and RRF contribution. Long symbols can
occupy multiple branch positions; that is an explicit limitation of chunk-level fusion.

## Interpretation

Symbol matching can promote common words in names and paths, so it may displace better
semantic or lexical evidence. Dense truncation can omit the relevant body of a long
function. Docstrings remain part of indexed code, and questions/labels were written
with source access. Sparse, correlated, agent-authored development labels do not support
generalization or significance claims. Do not change labels to make a strategy win.

Use [recorded results and regressions](../reports/m4/README.md) to guide M5 ablations.
M5's [graph support and ablations](structure.md) extend these baselines without
changing their definitions. Code-specialized model comparisons, ANN and large-scale
profiling remain future work.
