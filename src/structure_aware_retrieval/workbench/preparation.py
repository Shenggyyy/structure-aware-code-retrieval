"""Prepare immutable, version-bound resources for an imported Python snapshot."""

import hashlib
import math
import re
import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path

from structure_aware_retrieval.embeddings import (
    MODEL_SPEC,
    Encoder,
    SentenceEncoder,
    build_vectors,
    load_vectors,
)
from structure_aware_retrieval.indexing import (
    BM25_CONFIG,
    PARSER_VERSION,
    SCHEMA_VERSION,
    build_index,
    load_index,
)
from structure_aware_retrieval.ingestion import EXCLUDED_DIRECTORIES
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.relations import (
    RESOLVER_CONFIG,
    build_graph,
    graph_binding,
    load_graph,
)
from structure_aware_retrieval.tokenization import TOKENIZER_VERSION
from structure_aware_retrieval.workbench.importing import load_repository
from structure_aware_retrieval.workbench.storage import (
    read_json,
    safe_path,
    workspace_root,
    write_json,
)

_STAGES = ("index", "vectors", "graph")
_STATUSES = {"queued", "running", "ready", "reused", "failed", "interrupted"}
_READY = {"ready", "reused"}
_INDEX_CONFIG = {
    "schema_version": SCHEMA_VERSION,
    "parser_version": PARSER_VERSION,
    "scanner_version": 1,
    "tokenizer_version": TOKENIZER_VERSION,
    "max_chunk_lines": 80,
    "max_file_bytes": 1_048_576,
    "exclude": [],
    "excluded_directories": sorted(EXCLUDED_DIRECTORIES),
    "bm25": BM25_CONFIG,
}


def _identifier(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Resource and repository IDs must be 64 lowercase hexadecimal characters")
    return value


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _fingerprint(record: dict) -> str:
    return stable_id({key: value for key, value in record.items() if key != "fingerprint"})


def _artifact(
    workspace: Path,
    relative: str,
    binding: dict,
    build: Callable[[Path], object],
    validate: Callable[[Path], object],
) -> tuple[str, str]:
    """Reuse only matching bytes; a damaged or incomplete cache is never overwritten."""
    path = safe_path(workspace, relative)
    sidecar = relative + ".manifest.json"
    if path.exists() or safe_path(workspace, sidecar).exists():
        record = read_json(workspace, sidecar)
        if (
            record.get("schema_version") != 1
            or record.get("binding") != binding
            or not path.is_file()
            or _sha256(path) != record.get("sha256")
        ):
            raise ValueError("Resource cache checksum or binding mismatch; cache was not replaced")
        validate(path)
        return "reused", record["sha256"]
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_path(workspace, relative)
    build(path)
    validate(path)
    checksum = _sha256(safe_path(workspace, relative))
    write_json(workspace, sidecar, {"schema_version": 1, "binding": binding, "sha256": checksum})
    return "ready", checksum


def prepare_repository(
    workspace: Path,
    repository_id: str,
    *,
    model_cache: Path = Path("artifacts/models"),
    encoder: Encoder | None = None,
) -> dict:
    """Prepare each resource independently; unavailable local weights yield a partial result.

    This function never downloads a model, invokes target Git, or imports target code.
    Injected encoders are explicitly labeled as fixtures instead of production embeddings.
    """
    root = workspace_root(workspace)
    _identifier(repository_id)
    repository = load_repository(root, repository_id)
    source = safe_path(root, repository["source_directory"])
    relative_manifest = f"resources/{repository_id}/manifest.json"
    mode = "real_encoder" if encoder is None else "injected_encoder"
    record = {
        "schema_version": 1,
        "repository_id": repository_id,
        "source": deepcopy(repository["source"]),
        "resource_id": None,
        "status": "preparing",
        "execution_mode": mode,
        "index_config": deepcopy(_INDEX_CONFIG),
        "model_spec": dict(MODEL_SPEC) if encoder is None else dict(encoder.spec),
        "resolver_config": deepcopy(RESOLVER_CONFIG),
        "snapshot_id": None,
        "index": None,
        "vectors": None,
        "graph": None,
        "artifact_hashes": {},
        "stages": {
            stage: {"status": "queued", "elapsed_ms": None, "error": None} for stage in _STAGES
        },
    }

    def save() -> None:
        record["resource_id"] = stable_id(
            repository_id,
            record["index_config"],
            record["snapshot_id"],
            record["model_spec"],
            mode,
            record["resolver_config"],
        )
        record["fingerprint"] = _fingerprint(record)
        write_json(root, relative_manifest, record)

    def run_stage(stage: str, operation: Callable[[], tuple[str, str, str]]) -> None:
        record["stages"][stage]["status"] = "running"
        save()
        start = time.perf_counter()
        try:
            status, relative, checksum = operation()
            record[stage] = relative
            record["artifact_hashes"][stage] = checksum
            record["stages"][stage]["status"] = status
        except Exception as error:
            # One unavailable resource must not discard a successful independent stage.
            record["stages"][stage].update(
                status="failed", error=f"{type(error).__name__}: {error}"[:2000]
            )
        finally:
            record["stages"][stage]["elapsed_ms"] = (time.perf_counter() - start) * 1000
            save()

    index = None

    def prepare_index() -> tuple[str, str, str]:
        nonlocal index
        binding = {"repository_id": repository_id, "config": _INDEX_CONFIG}
        # Short filenames avoid Windows MAX_PATH failures; full bindings remain in sidecars.
        relative = f"resources/{repository_id}/index-{stable_id(binding)[:20]}.sqlite"
        provenance = {
            "commit": repository["source"]["commit"],
            "dirty": repository["source"].get("dirty"),
        }

        def validate(path: Path) -> None:
            loaded = load_index(path)
            config = loaded.metadata["config"]
            if {key: config.get(key) for key in _INDEX_CONFIG} != _INDEX_CONFIG or loaded.metadata[
                "git"
            ] != provenance:
                raise ValueError("Index config or source provenance mismatch")

        status, checksum = _artifact(
            root,
            relative,
            binding,
            lambda path: build_index(source, path, source_provenance=provenance),
            validate,
        )
        index = load_index(safe_path(root, relative))
        record["snapshot_id"] = index.metadata["snapshot_id"]
        record["index_summary"] = {
            key: index.metadata[key]
            for key in (
                "files_scanned",
                "files_indexed",
                "symbol_count",
                "chunk_count",
                "import_count",
                "diagnostics",
            )
        }
        return status, relative, checksum

    def prepare_vectors() -> tuple[str, str, str]:
        if index is None:
            raise ValueError("Vectors unavailable because index preparation failed")
        active_encoder = encoder if encoder is not None else SentenceEncoder(model_cache)
        record["model_spec"] = dict(active_encoder.spec)
        binding = {
            "snapshot_id": index.metadata["snapshot_id"],
            "model_spec": record["model_spec"],
            "execution_mode": mode,
        }
        relative = f"resources/{repository_id}/vectors-{stable_id(binding)[:20]}.npz"
        status, checksum = _artifact(
            root,
            relative,
            binding,
            lambda path: build_vectors(index, active_encoder, path),
            lambda path: load_vectors(path, index, active_encoder.spec),
        )
        return status, relative, checksum

    def prepare_graph() -> tuple[str, str, str]:
        if index is None:
            raise ValueError("Graph unavailable because index preparation failed")
        binding = graph_binding(index)
        relative = f"resources/{repository_id}/graph-{stable_id(binding)[:20]}.json"
        status, checksum = _artifact(
            root,
            relative,
            binding,
            lambda path: build_graph(index, path),
            lambda path: load_graph(path, index),
        )
        return status, relative, checksum

    save()
    try:
        run_stage("index", prepare_index)
        run_stage("vectors", prepare_vectors)
        run_stage("graph", prepare_graph)
    except BaseException as error:
        for stage in _STAGES:
            if record["stages"][stage]["status"] == "running":
                record[stage] = None
                record["artifact_hashes"].pop(stage, None)
                record["stages"][stage].update(
                    status="interrupted",
                    error=f"{type(error).__name__}: Resource preparation interrupted",
                )
        record["status"] = "interrupted"
        save()
        raise
    ready = sum(record["stages"][stage]["status"] in _READY for stage in _STAGES)
    record["status"] = "ready" if ready == len(_STAGES) else "partial" if ready else "failed"
    save()
    return record


def load_preparation(workspace: Path, repository_id: str) -> dict:
    """Read a confined manifest; callers check each strategy's artifact bytes separately."""
    root = workspace_root(workspace)
    _identifier(repository_id)
    record = read_json(root, f"resources/{repository_id}/manifest.json")
    if (
        record.get("schema_version") != 1
        or record.get("repository_id") != repository_id
        or record.get("fingerprint") != _fingerprint(record)
        or record.get("execution_mode") not in {"real_encoder", "injected_encoder"}
        or record.get("status") not in {"preparing", "ready", "partial", "failed", "interrupted"}
        or not isinstance(record.get("stages"), dict)
        or set(record["stages"]) != set(_STAGES)
        or not isinstance(record.get("artifact_hashes"), dict)
        or not set(record["artifact_hashes"]).issubset(_STAGES)
        or not isinstance(record.get("model_spec"), dict)
        or not isinstance(record.get("index_config"), dict)
        or not isinstance(record.get("resolver_config"), dict)
        or not isinstance(record.get("source"), dict)
    ):
        raise ValueError("Invalid preparation manifest or fingerprint")
    _identifier(record.get("resource_id"))
    source = record["source"]
    commit = source.get("commit")
    if (
        source.get("kind") not in {"local", "https"}
        or not isinstance(source.get("location"), str)
        or not source["location"]
        or not isinstance(source.get("requested_ref"), str)
        or not source["requested_ref"]
        or type(source.get("working_tree")) is not bool
        or (source.get("dirty") is not None and type(source["dirty"]) is not bool)
        or (
            commit is not None
            and (
                not isinstance(commit, str)
                or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit) is None
            )
        )
    ):
        raise ValueError("Invalid preparation source provenance")
    if record["resource_id"] != stable_id(
        repository_id,
        record["index_config"],
        record.get("snapshot_id"),
        record["model_spec"],
        record["execution_mode"],
        record["resolver_config"],
    ):
        raise ValueError("Preparation resource identity does not match its configuration")
    for stage in _STAGES:
        state = record["stages"][stage]
        if not isinstance(state, dict) or state.get("status") not in _STATUSES:
            raise ValueError("Invalid preparation stage status")
        elapsed = state.get("elapsed_ms")
        if elapsed is not None and (
            type(elapsed) not in {int, float} or not math.isfinite(elapsed) or elapsed < 0
        ):
            raise ValueError("Invalid preparation stage latency")
        if state.get("error") is not None and not isinstance(state["error"], str):
            raise ValueError("Invalid preparation stage error")
        relative = record.get(stage)
        if state["status"] in _READY:
            if not isinstance(relative, str) or not relative.startswith(
                f"resources/{repository_id}/"
            ):
                raise ValueError("Resource path does not belong to the repository")
            safe_path(root, relative)
            _identifier(record["artifact_hashes"].get(stage))
            _identifier(record.get("snapshot_id"))
        elif relative is not None or stage in record["artifact_hashes"]:
            raise ValueError("Unavailable stage cannot expose a successful resource")
    if record["status"] == "interrupted":
        if any(record["stages"][stage]["status"] == "running" for stage in _STAGES):
            raise ValueError("Interrupted preparation cannot contain a running stage")
    elif record["status"] != "preparing":
        ready = sum(record["stages"][stage]["status"] in _READY for stage in _STAGES)
        expected = "ready" if ready == len(_STAGES) else "partial" if ready else "failed"
        if record["status"] != expected or any(
            record["stages"][stage]["status"] in {"queued", "running", "interrupted"}
            for stage in _STAGES
        ):
            raise ValueError("Preparation status is inconsistent with its stages")
    return record
