import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from structure_aware_retrieval.evaluation.config import load_config
from structure_aware_retrieval.evaluation.profiling import execute_job, peak_memory, profile_job
from structure_aware_retrieval.indexing import load_index


def test_fresh_process_profiles_real_bm25_and_preserves_failure(experiment):
    root = experiment.parent
    job = {"kind": "experiment", "config": str(experiment), "output": str(root / "run")}
    result = profile_job(job, root / "profile")
    assert result["peak_memory"]["bytes"] > 0
    assert result["worker_wall_seconds"] >= result["operation_seconds"] > 0
    assert result["runtime"]["thread_environment"]["OMP_NUM_THREADS"] == "4"
    assert (
        result["details"]["quality_fingerprint"]
        == json.loads((root / "run/summary.json").read_text())["quality_fingerprint"]
    )
    with pytest.raises(FileExistsError):
        profile_job(job, root / "profile")
    with pytest.raises(RuntimeError, match="worker failed"):
        profile_job(job, root / "failure")
    assert json.loads((root / "failure/failure.json").read_text())["returncode"] != 0
    assert "already exists" in (root / "failure/worker.log").read_text()
    assert not (root / "failure/profile.json").exists()


def test_build_profiles_validate_snapshots_and_measure_artifacts(experiment, monkeypatch):
    root = experiment.parent
    database = load_config(experiment).indexes["fixture"]
    index = load_index(database)
    job = {
        "kind": "index",
        "source": index.metadata["repository"],
        "output": str(root / "rebuilt.sqlite"),
        "snapshot_id": index.metadata["snapshot_id"],
        "commit": "a" * 40,
        "index_options": {"max_chunk_lines": 2},
    }
    built = execute_job(job)
    assert built["details"]["artifact_bytes"] == Path(job["output"]).stat().st_size
    assert built["details"]["snapshot_id"] == job["snapshot_id"]
    graph = {
        "kind": "graph",
        "index": str(database),
        "snapshot_id": job["snapshot_id"],
        "output": str(root / "graph.json"),
    }
    assert execute_job(graph)["details"]["edge_counts"]["containment"] > 0
    for key, value in (("snapshot_id", "wrong"), ("commit", "b" * 40)):
        with pytest.raises(ValueError):
            execute_job({**job, key: value, "output": str(root / f"bad-{key}.sqlite")})
    with pytest.raises(ValueError, match="snapshot mismatch"):
        execute_job({**graph, "snapshot_id": "wrong", "output": str(root / "bad.json")})

    class Encoder:
        spec = {"dimensions": 2, "max_seq_length": 2}

        def __init__(self, cache):
            pass

        def token_lengths(self, texts):
            return [3] * len(texts)

        def encode(self, texts):
            return np.tile(np.array([1, 0], dtype=np.float32), (len(texts), 1))

    monkeypatch.setattr("structure_aware_retrieval.embeddings.SentenceEncoder", Encoder)
    vectors = execute_job(
        {**graph, "kind": "vectors", "model_cache": str(root), "output": str(root / "vectors.npz")}
    )
    assert vectors["details"]["truncated_documents"] == len(index.chunks)
    assert vectors["details"]["vector_bytes"] == len(index.chunks) * 2 * 4
    assert "binding" not in vectors["details"]


def test_unsupported_platform_and_unknown_job_fail(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="Unknown profile job"):
        execute_job({"kind": "invalid", "output": str(tmp_path / "no")})
    monkeypatch.setattr(sys, "platform", "unknown")
    with pytest.raises(ValueError, match="supports"):
        peak_memory()


def test_experiment_rejects_changed_config_or_benchmark_before_retrieval(experiment):
    job = {
        "kind": "experiment",
        "config": str(experiment),
        "output": str(experiment.parent / "result"),
    }
    with pytest.raises(ValueError, match="configuration changed"):
        execute_job({**job, "config_sha256": "0" * 64})
    with pytest.raises(ValueError, match="Benchmark changed"):
        execute_job({**job, "benchmark_digest": "0" * 64})
    assert not Path(job["output"]).exists()
    result = execute_job(
        {
            **job,
            "config_sha256": hashlib.sha256(
                experiment.read_text(encoding="utf-8").encode("utf-8")
            ).hexdigest(),
        }
    )
    assert result["details"]["quality_fingerprint"]
