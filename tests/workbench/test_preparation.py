"""Resource preparation is offline, snapshot-bound, reusable, and failure-isolated."""

import json
from pathlib import Path

import numpy as np
import pytest

from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.workbench.importing import import_repository
from structure_aware_retrieval.workbench.preparation import load_preparation, prepare_repository
from structure_aware_retrieval.workbench.storage import read_json, write_json


class FixtureEncoder:
    def __init__(self, revision="fixture-v1", dimensions=2):
        self.spec = {
            "id": "fixture-only",
            "revision": revision,
            "dimensions": dimensions,
            "max_seq_length": 8,
        }
        self.calls = 0

    def encode(self, texts):
        self.calls += 1
        values = np.zeros((len(texts), self.spec["dimensions"]), dtype=np.float32)
        values[:, 0] = 1
        return values

    def token_lengths(self, texts):
        return [len(text.split()) for text in texts]


@pytest.fixture
def imported(tmp_path):
    repository = tmp_path / "source"
    repository.mkdir()
    (repository / "client.py").write_text(
        "def checksum(payload):\n    return sum(payload)\n\n"
        "def request(payload):\n    return checksum(payload)\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "workbench"
    manifest = import_repository(str(repository), workspace)
    return workspace, manifest["repository_id"], repository


def test_prepare_and_reuse_without_reencoding_or_rebuilding(imported, monkeypatch):
    workspace, repository_id, _ = imported
    encoder = FixtureEncoder()
    first = prepare_repository(workspace, repository_id, encoder=encoder)
    assert first["status"] == "ready"
    assert first["execution_mode"] == "injected_encoder"
    assert first["source"]["kind"] == "local"
    assert first["source"]["commit"] is None
    assert first["source"]["working_tree"] is True
    assert all(stage["status"] == "ready" for stage in first["stages"].values())
    assert encoder.calls == 1
    assert load_preparation(workspace, repository_id) == first
    paths = {stage: workspace / first[stage] for stage in ("index", "vectors", "graph")}
    before = {stage: path.read_bytes() for stage, path in paths.items()}

    def do_not_rebuild(*args, **kwargs):
        raise AssertionError("Cached resources should not be rebuilt")

    for function in ("build_index", "build_vectors", "build_graph"):
        monkeypatch.setattr(
            f"structure_aware_retrieval.workbench.preparation.{function}", do_not_rebuild
        )
    second = prepare_repository(workspace, repository_id, encoder=encoder)
    assert second["status"] == "ready"
    assert second["resource_id"] == first["resource_id"]
    assert second["snapshot_id"] == first["snapshot_id"]
    assert all(stage["status"] == "reused" for stage in second["stages"].values())
    assert encoder.calls == 1
    assert {stage: path.read_bytes() for stage, path in paths.items()} == before


def test_new_model_spec_gets_new_vectors_and_reuses_index_and_graph(imported):
    workspace, repository_id, _ = imported
    first = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    original_vectors = (workspace / first["vectors"]).read_bytes()
    second = prepare_repository(
        workspace, repository_id, encoder=FixtureEncoder(revision="fixture-v2", dimensions=3)
    )
    assert second["status"] == "ready"
    assert second["vectors"] != first["vectors"]
    assert second["resource_id"] != first["resource_id"]
    assert second["snapshot_id"] == first["snapshot_id"]
    assert second["stages"]["vectors"]["status"] == "ready"
    assert second["stages"]["index"]["status"] == "reused"
    assert second["stages"]["graph"]["status"] == "reused"
    assert (workspace / first["vectors"]).read_bytes() == original_vectors


def test_fixture_vectors_are_never_reused_as_a_production_cache(imported, monkeypatch):
    workspace, repository_id, _ = imported
    fixture = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    encoder = FixtureEncoder()
    monkeypatch.setattr(
        "structure_aware_retrieval.workbench.preparation.SentenceEncoder", lambda cache: encoder
    )
    # This constructor double tests mode separation, not a live embedding result.
    production_path = prepare_repository(workspace, repository_id)
    assert production_path["execution_mode"] == "real_encoder"
    assert production_path["model_spec"] == fixture["model_spec"]
    assert production_path["vectors"] != fixture["vectors"]
    assert encoder.calls == 1
    assert production_path["stages"]["index"]["status"] == "reused"
    assert production_path["stages"]["graph"]["status"] == "reused"


def test_mismatched_sidecar_binding_does_not_reuse_or_replace_vectors(imported):
    workspace, repository_id, _ = imported
    first = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    relative = first["vectors"] + ".manifest.json"
    sidecar = read_json(workspace, relative)
    sidecar["binding"]["snapshot_id"] = "0" * 64
    write_json(workspace, relative, sidecar)
    before = (workspace / first["vectors"]).read_bytes()
    result = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    assert result["status"] == "partial"
    assert "binding mismatch" in result["stages"]["vectors"]["error"]
    assert result["stages"]["graph"]["status"] == "reused"
    assert (workspace / first["vectors"]).read_bytes() == before


def test_missing_pinned_model_is_partial_and_never_downloads(imported, monkeypatch):
    workspace, repository_id, _ = imported
    seen = []

    def unavailable(cache, *, download=False):
        seen.append((cache, download))
        raise ValueError("Pinned model unavailable; run sacr prepare-model --cache PATH first")

    monkeypatch.setattr(
        "structure_aware_retrieval.workbench.preparation.SentenceEncoder", unavailable
    )
    result = prepare_repository(workspace, repository_id, model_cache=Path("offline-cache"))
    assert seen == [(Path("offline-cache"), False)]
    assert result["execution_mode"] == "real_encoder"
    assert result["status"] == "partial"
    assert result["stages"]["index"]["status"] == "ready"
    assert result["stages"]["graph"]["status"] == "ready"
    assert result["stages"]["vectors"]["status"] == "failed"
    assert "prepare-model" in result["stages"]["vectors"]["error"]
    assert result["vectors"] is None
    assert "vectors" not in result["artifact_hashes"]
    assert load_preparation(workspace, repository_id) == result


def test_failed_encoder_does_not_discard_the_graph_or_publish_vectors(imported):
    workspace, repository_id, _ = imported
    encoder = FixtureEncoder()
    encoder.encode = lambda texts: np.zeros((len(texts), 2), dtype=np.float32)
    result = prepare_repository(workspace, repository_id, encoder=encoder)
    assert result["status"] == "partial"
    assert result["vectors"] is None
    assert result["graph"] is not None
    assert "normalized" in result["stages"]["vectors"]["error"]
    assert not list((workspace / "resources").rglob("vectors-*.npz"))


@pytest.mark.parametrize("stage", ["index", "vectors", "graph"])
def test_tampered_resource_is_not_overwritten_and_only_blocks_dependents(imported, stage):
    workspace, repository_id, _ = imported
    encoder = FixtureEncoder()
    first = prepare_repository(workspace, repository_id, encoder=encoder)
    target = workspace / first[stage]
    original = target.read_bytes()
    target.write_bytes(original + b"tampered")
    second = prepare_repository(workspace, repository_id, encoder=encoder)
    assert second["stages"][stage]["status"] == "failed"
    assert "mismatch" in second["stages"][stage]["error"]
    assert second[stage] is None
    assert target.read_bytes() == original + b"tampered"
    if stage == "index":
        assert second["status"] == "failed"
        assert all(state["status"] == "failed" for state in second["stages"].values())
    else:
        assert second["status"] == "partial"
        other = "graph" if stage == "vectors" else "vectors"
        assert second["stages"][other]["status"] == "reused"


def test_missing_sidecar_is_not_silently_rebuilt(imported):
    workspace, repository_id, _ = imported
    first = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    sidecar = workspace / (first["vectors"] + ".manifest.json")
    sidecar.unlink()
    before = (workspace / first["vectors"]).read_bytes()
    second = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    assert second["stages"]["vectors"]["status"] == "failed"
    assert (workspace / first["vectors"]).read_bytes() == before


def test_preparation_cannot_inherit_parent_git_or_execute_source(imported, monkeypatch):
    workspace, repository_id, original = imported

    def forbid_git(*args, **kwargs):
        raise AssertionError("Imported snapshots must not invoke Git for index provenance")

    monkeypatch.setattr("structure_aware_retrieval.indexing._git_provenance", forbid_git)
    first = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    assert first["status"] == "ready"
    index = load_index(workspace / first["index"])
    assert index.metadata["git"] == {"commit": None, "dirty": None}
    (original / "client.py").write_text(
        "raise RuntimeError('Never execute me')\n", encoding="utf-8"
    )
    second_import = import_repository(str(original), workspace)
    second = prepare_repository(workspace, second_import["repository_id"], encoder=FixtureEncoder())
    assert second["status"] == "ready"
    assert second["snapshot_id"] != first["snapshot_id"]


def test_modified_frozen_source_is_rejected_before_preparation(imported):
    workspace, repository_id, _ = imported
    imported_manifest = read_json(workspace, f"repositories/{repository_id}/manifest.json")
    (workspace / imported_manifest["source_directory"] / "client.py").write_text(
        "changed = True\n", encoding="utf-8"
    )
    with pytest.raises(ValueError):
        prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    assert not (workspace / "resources" / repository_id / "manifest.json").exists()


def test_loader_checks_manifest_integrity_but_leaves_per_strategy_bytes_to_preview(imported):
    workspace, repository_id, _ = imported
    prepared = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    (workspace / prepared["vectors"]).write_bytes(b"bad cache")
    assert load_preparation(workspace, repository_id) == prepared
    prepared["model_spec"]["revision"] = "tampered"
    write_json(workspace, f"resources/{repository_id}/manifest.json", prepared)
    with pytest.raises(ValueError, match="fingerprint"):
        load_preparation(workspace, repository_id)


@pytest.mark.parametrize("relative", ["../other.sqlite", "/index.sqlite", "resources/x/../x/a"])
def test_loader_rejects_unsafe_resource_paths_even_with_valid_record_hash(imported, relative):
    workspace, repository_id, _ = imported
    prepared = prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    prepared["index"] = relative
    prepared["fingerprint"] = stable_id(
        {key: value for key, value in prepared.items() if key != "fingerprint"}
    )
    write_json(workspace, f"resources/{repository_id}/manifest.json", prepared)
    with pytest.raises(ValueError, match="path"):
        load_preparation(workspace, repository_id)


@pytest.mark.parametrize(
    "provenance",
    [
        {"commit": None, "dirty": None},
        {"commit": "a" * 40, "dirty": False},
        {"commit": "a" * 64, "dirty": True},
    ],
)
def test_explicit_provenance_is_preserved_without_git(tmp_path, monkeypatch, provenance):
    repository = tmp_path / "source"
    repository.mkdir()
    (repository / "module.py").write_text("value = 1\n", encoding="utf-8")

    def forbidden(*args, **kwargs):
        raise AssertionError("Git should not be invoked")

    monkeypatch.setattr("structure_aware_retrieval.indexing._git_provenance", forbidden)
    path = tmp_path / "index.sqlite"
    assert build_index(repository, path, source_provenance=provenance)["git"] == provenance
    assert load_index(path).metadata["git"] == provenance


@pytest.mark.parametrize(
    "provenance",
    [
        {},
        {"commit": "short", "dirty": False},
        {"commit": "g" * 40, "dirty": False},
        {"commit": True, "dirty": False},
        {"commit": None, "dirty": 0},
        {"commit": None, "dirty": "unknown"},
        {"commit": None, "dirty": None, "other": "unexpected"},
    ],
)
def test_invalid_provenance_fails_before_writing(tmp_path, provenance):
    output = tmp_path / "index.sqlite"
    with pytest.raises(ValueError, match="Source"):
        build_index(tmp_path, output, source_provenance=provenance)
    assert not output.exists()


def test_preparation_persists_running_and_terminal_stages(imported, monkeypatch):
    workspace, repository_id, _ = imported
    observed = []

    def capture(root, path, value):
        if path == f"resources/{repository_id}/manifest.json":
            observed.append(json.loads(json.dumps(value)))
        write_json(root, path, value)

    monkeypatch.setattr("structure_aware_retrieval.workbench.preparation.write_json", capture)
    prepare_repository(workspace, repository_id, encoder=FixtureEncoder())
    assert all(stage["status"] == "queued" for stage in observed[0]["stages"].values())
    for name in ("index", "vectors", "graph"):
        assert any(item["stages"][name]["status"] == "running" for item in observed)
        assert observed[-1]["stages"][name]["status"] == "ready"
        assert observed[-1]["stages"][name]["elapsed_ms"] >= 0


@pytest.mark.parametrize("interrupted_stage", ["vectors", "graph"])
def test_interrupted_preparation_preserves_completed_resources_and_can_be_resumed(
    imported, monkeypatch, interrupted_stage
):
    workspace, repository_id, _ = imported
    encoder = FixtureEncoder()

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    with monkeypatch.context() as patch:
        if interrupted_stage == "vectors":
            patch.setattr(encoder, "encode", interrupt)
        else:
            patch.setattr("structure_aware_retrieval.workbench.preparation.build_graph", interrupt)
        with pytest.raises(KeyboardInterrupt):
            prepare_repository(workspace, repository_id, encoder=encoder)

    interrupted = load_preparation(workspace, repository_id)
    assert interrupted["status"] == "interrupted"
    state = interrupted["stages"][interrupted_stage]
    assert state["status"] == "interrupted"
    assert "KeyboardInterrupt" in state["error"]
    assert state["elapsed_ms"] >= 0
    assert interrupted[interrupted_stage] is None
    assert interrupted_stage not in interrupted["artifact_hashes"]
    assert interrupted["stages"]["index"]["status"] == "ready"
    original_index = (workspace / interrupted["index"]).read_bytes()
    if interrupted_stage == "vectors":
        assert interrupted["stages"]["graph"] == {
            "status": "queued",
            "elapsed_ms": None,
            "error": None,
        }
    else:
        assert interrupted["stages"]["vectors"]["status"] == "ready"

    # A new explicit user preparation reuses successful resources; interruption never retries.
    resumed = prepare_repository(workspace, repository_id, encoder=encoder)
    assert resumed["status"] == "ready"
    assert resumed["stages"]["index"]["status"] == "reused"
    assert (workspace / resumed["index"]).read_bytes() == original_index
    assert resumed["stages"][interrupted_stage]["status"] == "ready"
    if interrupted_stage == "graph":
        assert resumed["stages"]["vectors"]["status"] == "reused"
