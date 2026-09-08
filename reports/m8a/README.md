# M8a: CPU Container Delivery Validation

Recorded on 2026-09-08 using Windows/Python 3.12.14 and Docker Desktop's
Linux/amd64 engine (Docker 29.7.2). Both actual images built and ran successfully.
This checkpoint validates software delivery; all research labels remain provisional
and no paid API experiment or independent answer review was performed.

## Observed checks

| Check | Result |
| --- | --- |
| Full host regression | 493 passed, 1 skipped; 92% combined statement/branch coverage |
| Base runtime | UID 10001; installed package; no Torch, Sentence Transformers or pytest |
| Dense runtime | UID 10001; Torch 2.14.0+cpu; Sentence Transformers 5.7.0; CUDA unavailable |
| Base and Dense CLI smoke | Passed with networking disabled and read-only root filesystems |
| Persistent named volume | Base smoke passed; fresh volume inherited writable output ownership |
| Host/container agreement | Identical fixture commit, snapshot and retrieval quality fingerprints |
| Real pinned embedding | Loaded from an existing read-only cache with networking disabled |
| Five-strategy retrieval | Fresh 9 × 384 vectors and graph loaded successfully; canonical sources returned |
| QA | Source preview and local empty-context abstention; zero model/API calls |

The symlink test skips because this Windows host cannot create symlinks. Test suite
coverage measures the installed source package; the new smoke script is exercised
through subprocess integration tests. Ruff, formatting and whitespace checks pass.
Source and wheel distributions also build successfully.

## Evidence

- `containers.json`: actual image IDs, Docker-reported byte sizes, installed runtime
  checks and separate base/Dense smoke summaries. Image byte counts are engine-reported
  storage metadata, not resident memory or total disk usage including shared caches.
- `dense.json`: pinned model/dependency versions, fresh vector and graph bindings,
  five-strategy source rankings and per-strategy QA preview fingerprints.
- `host-smoke.json` and `named-volume-smoke.json`: standalone smoke observations.
- `validation.json`: check status, tool/input hashes and explicit pending remote CI.

The three-file fixture is parsed, never imported; its source intentionally raises
if executed. The smoke creates an isolated clean Git repository with fixed source
bytes and a fixture identity/date, then runs 17 commands across indexing, retrieval,
graph creation, QA, three tiny evaluations, comparison and pending review creation.
Both container targets matched this host quality fingerprint:

```text
0788f1869f84c370926272f1e7e305a47e5f7e4743c98550de4b9168dbc5dda2
```

The separate Dense acceptance used the existing MiniLM cache as a read-only mount.
Every strategy ranked `client.calculate_checksum` first for the fixture checksum
question. This is a functional fixture check, not evidence of general retrieval
quality or a structure-aware improvement. No model weights were downloaded during
runtime validation; cold image builds downloaded base images and dependencies.

## Reproduction and boundaries

See [the container guide](../../docs/docker.md) for build, mounts, source preparation,
Dense indexing and frozen evaluation commands. `scripts/smoke.py` runs offline both
on the host and in either image; choose a new output directory each time. CI now
builds both targets and repeats the network-disabled smoke after the owner pushes.
Those new remote jobs have not run for these uncommitted changes.

Python/uv image digests and application dependency versions are pinned. Debian apt
packages and isolated build backends still resolve separately, so full image IDs
need not reproduce across later builds. Historical research metrics and retrieval
implementations were preserved. M7b's real API comparison, independent label/answer
review and final evidence consolidation remain separate acceptance items.
