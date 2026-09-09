# CPU Container Delivery

M8a packages the existing CLI for Linux/amd64. Docker Desktop must use Linux
containers. Python 3.12.14 and uv 0.12.5 builder images are pinned by registry digest;
application dependencies come from `uv.lock`. Debian packages and isolated build
backend requirements still resolve from package repositories, so this is not a claim
of byte-for-byte reproducible images. Builds need network access on a cold cache.

## Images and persistent data

```text
docker build --target base -t sacr:base .
docker build --target dense -t sacr:dense .
docker volume create sacr-artifacts
```

| Target | Included | Explicit runtime preparation |
| --- | --- | --- |
| `base` (default) | BM25, graph building, structure with BM25 seeds, QA, evaluation | Source snapshots/indexes; API key only for real QA |
| `dense` | Base plus locked CPU Torch and Sentence Transformers | Pinned model cache, vectors and graphs |

No model weights, downloaded repositories, API credentials, local virtual environments
or historical reports are copied into images. `.dockerignore` uses an input allowlist.
The environment is installed noneditably at `/opt/venv`; uv and development tools are
not installed in the runtime. Use `sacr` directly (the default entrypoint), or override
it with `--entrypoint python` for the included runner scripts.

The working directory is `/app`. Configs, benchmarks, scripts and a source-only test
fixture are included. Runtime UID/GID is **10001:10001**. `/app/artifacts` stores
indexes, source checkouts, model caches and generated reports; always mount it to
retain outputs. A new Docker named volume inherits the directory's ownership.

## Workbench browser and CLI

M9b's browser workflow is intended to run on the host. Follow the
[workbench startup guide](workbench.md) and use `sacr workbench serve`; its listener
binds only `127.0.0.1`, with strict request-origin checks. This checkpoint does not
add container port publishing, LAN access or a `--host` option. Publishing a Docker
port alone does not make the loopback listener reachable from a host browser.

The images retain all workbench CLI commands. Rebuild the chosen target after
source changes, use the Dense image for all five strategies, and mount the same
artifact volume for import, preparation, preview and history. Prepare model weights
explicitly with `prepare-model` before a preview. Public HTTPS imports require
network access; local repository mounts can be read-only. The CLI workflow is in
[the workbench guide](workbench.md#cli-import-one-repository).

Browser assets ship inside the Python package and need no Node build or dependency
change. Existing image source copying and offline CI collection include the M9b
code/tests. [M9b validation](../reports/m9b/README.md) records checks actually run;
historical container measurements below retain their original checkpoint scope.

## Offline smoke

```text
docker run --rm --network none sacr:base --help
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts --entrypoint python sacr:base scripts/smoke.py --output artifacts/smoke-001
```

The smoke copies three source fixture files with fixed LF line endings and creates
a separate local Git repository/commit inside its new output. It uses an explicit
fixture identity/date and disables inherited Git configuration/hooks. The program
only parses the source, which intentionally raises if imported. It runs indexing,
BM25 and structure retrieval, graph creation, QA preview and empty-evidence abstention,
three tiny retrieval evaluations, a comparison and a pending review pool. Repeated
BM25 runs must have identical quality fingerprints. These fixture results are software
checks, not research benchmark scores or generated QA answers.

`summary.json` and `commands.json` retain the checks and subprocess outputs. A failed
run preserves diagnostics. Existing output directories are refused. To inspect a
saved summary, mount the named volume read-only:

```text
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts,readonly --entrypoint python sacr:base -m json.tool artifacts/smoke-001/summary.json
```

The same smoke can run on the host after locked installation:

```text
uv run --locked python scripts/smoke.py --output artifacts/smoke-host-001
```

Container CI builds both image targets, checks their runtime dependencies, then runs
the smoke with `--network none`, a read-only root filesystem and writable temporary
mounts. It does not download weights or call an LLM. Real Dense validation is a separate
step using the pinned model, as described below.

## Your own repository

Use an absolute source path and mount it read-only. In PowerShell:

```powershell
$sourcePath = (Get-Location).Path
docker run --rm --network none --mount "type=bind,source=$sourcePath,target=/source,readonly" --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:base index /source --output artifacts/project.sqlite
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:base search "build_index" --index artifacts/project.sqlite
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:base ask "How is build_index implemented?" --index artifacts/project.sqlite --output artifacts/project-preview
```

`index` captures stored source; later queries use that snapshot. Refresh explicitly
with `index --overwrite`. New vector, graph, QA and evaluation outputs require new paths.

On Linux, a host output bind mount must be writable by the container user. Either
use the named volume above or run with the host UID/GID and a writable HOME, for example
`--user "$(id -u):$(id -g)" -e HOME=/tmp`. Avoid broad permission changes. Different
ownership of a source Git mount can make Git withhold commit/dirty metadata: general
search still works, but strict benchmark evaluation rejects missing provenance. Prefer
benchmark preparation inside the container-owned volume. When an explicitly trusted
mount needs Git metadata, scope Git's `safe.directory` setting to that exact path;
do not disable ownership checks globally.

## Reproduce retrieval experiments

Prepare the existing development benchmark and run BM25:

```text
docker run --rm --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:base prepare-benchmark benchmarks/seed-v1/benchmark.json
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:base evaluate --config configs/bm25-seed.toml --output artifacts/runs/docker-bm25-001
```

Only preparation needs network access. For all five strategies, prepare the pinned
embedding model once in the Dense image, then create vectors and graphs offline:

```text
docker run --rm --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:dense prepare-model --cache artifacts/models
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:dense embed --index artifacts/benchmark/indexes/requests.sqlite --output artifacts/benchmark/vectors/requests.npz
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:dense embed --index artifacts/benchmark/indexes/click.sqlite --output artifacts/benchmark/vectors/click.npz
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:dense graph --index artifacts/benchmark/indexes/requests.sqlite --output artifacts/benchmark/graphs/requests.json
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:dense graph --index artifacts/benchmark/indexes/click.sqlite --output artifacts/benchmark/graphs/click.json
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:dense evaluate --config configs/structure-full.toml --output artifacts/runs/docker-structure-001
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts --entrypoint python sacr:dense scripts/run_m5.py --output artifacts/runs/docker-m5-001
docker run --rm --network none --mount type=volume,src=sacr-artifacts,dst=/app/artifacts sacr:dense prepare-qa --config configs/qa-m7.toml --output artifacts/qa/docker-m7-prepared
```

Configs resolve paths relative to their own TOML file. Preserve the documented
`artifacts/benchmark` layout or supply an appropriate config. Windows absolute paths
are not Linux paths. Source corpus hashes bind raw bytes; LF/CRLF differences can
invalidate an index for evaluation. Built-in benchmark preparation uses fixed checkout
settings. Vector archives also bind exact encoder dependency versions: build vectors
inside the chosen runtime and preserve the existing validation rules when moving data.

For broader M6c runs, follow [the experiment prerequisites](experiments.md), using
`--entrypoint python` for scripts and the Dense image for model operations. Historical
report analysis requires an additional read-only mount of the repository's `reports/`
at `/app/reports`, because prior results are deliberately omitted from images.

## Real QA and remaining acceptance

Real QA requires network access, an explicit model/budget and credentials supplied
at runtime. Pass a locally configured key with `-e OPENAI_API_KEY`; never put its
value in a Dockerfile, build argument or command history. Follow [the QA protocol](qa.md)
to inspect requests and use `run-qa --execute`. The current M8a stage performs no paid
API calls. Container validation does not complete M7b or independent human review.

References: [uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/),
[Python official image](https://hub.docker.com/_/python),
[Docker bind mounts](https://docs.docker.com/engine/storage/bind-mounts/).
