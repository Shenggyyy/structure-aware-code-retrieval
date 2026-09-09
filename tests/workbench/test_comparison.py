"""Offline integration of real retrievers with explicitly synthetic embeddings."""

import numpy as np
import pytest

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.strategies import STRATEGIES
from structure_aware_retrieval.workbench import comparison, preparation
from structure_aware_retrieval.workbench.importing import import_repository
from structure_aware_retrieval.workbench.storage import read_json, safe_path, write_json


class FixtureEncoder:
    spec = {"id": "synthetic", "revision": "fixture", "dimensions": 2, "max_seq_length": 256}

    def encode(self, texts):
        return np.asarray(
            [[1.0, 0.0] if "checksum" in text else [0.0, 1.0] for text in texts],
            dtype=np.float32,
        ).reshape(-1, 2)

    def token_lengths(self, texts):
        return [len(text.split()) for text in texts]


@pytest.fixture
def prepared(sample_repository, tmp_path):
    workspace = tmp_path / "workbench"
    repository = import_repository(str(sample_repository), workspace)
    encoder = FixtureEncoder()
    resources = preparation.prepare_repository(
        workspace, repository["repository_id"], encoder=encoder
    )
    assert resources["status"] == "ready"
    return workspace, repository["repository_id"], encoder, resources


def test_five_real_retrievers_save_canonical_context_and_no_quality_or_generation(prepared):
    workspace, repository_id, encoder, resources = prepared
    record = comparison.preview_question(
        workspace, repository_id, "calculate_checksum payload bytes", encoder=encoder, top_k=2
    )
    assert record["status"] == "preview_complete"
    assert record["mode"] == "context_preview"
    assert record["encoder_mode"] == "injected_encoder"
    assert record["api_calls"] == 0
    assert record["benchmark_metrics"] is None
    assert record["relevance_labels"] == "unlabeled"
    assert [row["strategy"] for row in record["results"]] == list(STRATEGIES)
    for row in record["results"]:
        assert row["status"] == "preview"
        assert row["qa"]["model_called"] is False
        assert row["qa"]["answer"] is None
        assert row["qa"]["evaluation"]["answer_correctness"] is None
        assert row["qa"]["automatic_checks"]["paths_valid"] is True
        assert row["timing_ms"]["generation"] is None
        assert row["timing_ms"]["retrieval"] >= 0
        assert all(value is None for value in row["tokens"].values())
        context = row["qa"]["context"]
        assert context["snapshot_id"] == resources["snapshot_id"]
        assert context["budget"]["used_context_bytes"] <= 16000
        assert len(context["evidence"]) <= 2
        hits = {hit["chunk_id"]: hit for hit in row["hits"]}
        assert hits
        for evidence in context["evidence"]:
            hit = hits[evidence["chunk_id"]]
            assert hit["start_line"] <= evidence["start_line"] <= evidence["end_line"]
            assert evidence["end_line"] <= hit["end_line"]
            assert hit["path"] == evidence["path"]
            assert "components" in hit and "provenance" in hit
    assert (
        comparison.load_comparison(workspace, record["run_id"])["fingerprint"]
        == record["fingerprint"]
    )


def test_one_retriever_failure_keeps_other_results_and_saved_error(prepared, monkeypatch):
    workspace, repository_id, encoder, _ = prepared
    original = comparison.create_retriever

    def failing(strategy, *args, **kwargs):
        if strategy == "dense":
            raise RuntimeError("synthetic isolated failure")
        return original(strategy, *args, **kwargs)

    monkeypatch.setattr(comparison, "create_retriever", failing)
    record = comparison.preview_question(workspace, repository_id, "checksum", encoder=encoder)
    assert record["status"] == "partial"
    assert [row["status"] for row in record["results"]] == [
        "preview",
        "failed",
        "preview",
        "preview",
        "preview",
    ]
    failure = comparison.load_comparison(workspace, record["run_id"])["results"][1]
    assert failure["qa"] is None and failure["hits"] == []
    assert failure["error"]["type"] == "RuntimeError"


@pytest.mark.parametrize(("artifact", "failures"), [("graph", 1), ("vectors", 4), ("index", 5)])
def test_resource_tampering_fails_only_dependent_strategies(prepared, artifact, failures):
    workspace, repository_id, encoder, resources = prepared
    path = safe_path(workspace, resources[artifact])
    path.write_bytes(b"damaged cache")
    record = comparison.preview_question(workspace, repository_id, "checksum", encoder=encoder)
    assert sum(row["status"] == "failed" for row in record["results"]) == failures
    assert path.read_bytes() == b"damaged cache"
    assert comparison.load_comparison(workspace, record["run_id"])["status"] == record["status"]


def test_missing_model_keeps_bm25_and_does_not_fake_dense(sample_repository, tmp_path, monkeypatch):
    workspace = tmp_path / "workbench"
    repository_id = import_repository(str(sample_repository), workspace)["repository_id"]

    def missing(*args, **kwargs):
        raise ValueError("Pinned model missing; run prepare-model")

    monkeypatch.setattr(preparation, "SentenceEncoder", missing)
    resources = preparation.prepare_repository(workspace, repository_id)
    assert resources["status"] == "partial"
    monkeypatch.setattr(comparison, "SentenceEncoder", missing)
    record = comparison.preview_question(workspace, repository_id, "checksum")
    assert record["status"] == "partial"
    assert record["results"][0]["status"] == "preview"
    assert all(row["status"] == "failed" and row["qa"] is None for row in record["results"][1:])


def test_history_reopens_with_only_saved_run_and_rejects_corruption(prepared, tmp_path):
    workspace, repository_id, encoder, _ = prepared
    record = comparison.preview_question(workspace, repository_id, "checksum", encoder=encoder)
    portable = tmp_path / "history-only"
    relative = f"runs/{record['run_id']}/run.json"
    saved = read_json(workspace, relative)
    write_json(portable, relative, saved)
    assert comparison.load_comparison(portable, record["run_id"]) == saved
    assert comparison.list_comparisons(portable)[0]["question"] == "checksum"
    saved["question"] = "tampered"
    write_json(portable, relative, saved)
    with pytest.raises(ValueError, match="checksum"):
        comparison.load_comparison(portable, record["run_id"])
    assert comparison.list_comparisons(portable)[0]["status"] == "unreadable"


def test_invalid_history_shape_is_rejected_even_with_recomputed_checksum(prepared):
    workspace, repository_id, encoder, _ = prepared
    record = comparison.preview_question(workspace, repository_id, "checksum", encoder=encoder)
    record["results"] = [None] * 5
    record["fingerprint"] = stable_id({k: v for k, v in record.items() if k != "fingerprint"})
    write_json(workspace, f"runs/{record['run_id']}/run.json", record)
    with pytest.raises(ValueError):
        comparison.load_comparison(workspace, record["run_id"])
    assert comparison.list_comparisons(workspace)[0]["status"] == "unreadable"


@pytest.mark.parametrize("run_id", ["../escape", "a/b", "A" * 32, "", "c:" + "a" * 30])
def test_history_id_confined(tmp_path, run_id):
    with pytest.raises(ValueError):
        comparison.load_comparison(tmp_path, run_id)


@pytest.mark.parametrize(
    "options",
    [
        {"question": " "},
        {"question": "a" * 4001},
        {"top_k": 0},
        {"top_k": True},
        {"max_context_bytes": 1},
    ],
)
def test_invalid_preview_settings_create_no_run(prepared, options):
    workspace, repository_id, encoder, _ = prepared
    settings = {"question": "checksum", **options}
    with pytest.raises(ValueError):
        comparison.preview_question(workspace, repository_id, encoder=encoder, **settings)
    assert comparison.list_comparisons(workspace) == []


def test_interrupt_retains_finished_pending_and_interrupted_rows(prepared, monkeypatch):
    workspace, repository_id, encoder, _ = prepared
    original = comparison.create_retriever

    def interrupt(strategy, *args, **kwargs):
        if strategy == "hybrid":
            raise KeyboardInterrupt
        return original(strategy, *args, **kwargs)

    monkeypatch.setattr(comparison, "create_retriever", interrupt)
    with pytest.raises(KeyboardInterrupt):
        comparison.preview_question(workspace, repository_id, "checksum", encoder=encoder)
    item = comparison.list_comparisons(workspace)[0]
    saved = comparison.load_comparison(workspace, item["run_id"])
    assert saved["status"] == "interrupted"
    assert [row["status"] for row in saved["results"]] == [
        "preview",
        "preview",
        "interrupted",
        "pending",
        "pending",
    ]
    assert saved["api_calls"] == 0


def test_history_bad_json_stays_visible(tmp_path):
    run_id = "b" * 32
    path = safe_path(tmp_path, f"runs/{run_id}/run.json")
    path.parent.mkdir(parents=True)
    path.write_text("{", encoding="utf-8")
    assert comparison.list_comparisons(tmp_path)[0]["status"] == "unreadable"


def test_interrupt_during_shared_encoder_load_marks_saved_run(prepared, monkeypatch):
    workspace, repository_id, _, _ = prepared

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(comparison, "SentenceEncoder", interrupt)
    with pytest.raises(KeyboardInterrupt):
        comparison.preview_question(workspace, repository_id, "checksum")
    item = comparison.list_comparisons(workspace)[0]
    saved = comparison.load_comparison(workspace, item["run_id"])
    assert saved["status"] == "interrupted"
    assert saved["finished_at"] is not None
    assert all(row["status"] == "pending" for row in saved["results"])
    assert saved["shared_setup"]["encoder_load_ms"] is not None
