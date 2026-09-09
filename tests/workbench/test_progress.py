"""Progress observers must not leave stale state or mask a service interruption."""

import numpy as np
import pytest

from structure_aware_retrieval.workbench import comparison, importing, preparation
from structure_aware_retrieval.workbench.storage import read_json


class StopWork(BaseException):
    """Represent a server shutdown checkpoint without relying on server internals."""


class FixtureEncoder:
    spec = {"id": "synthetic", "revision": "progress", "dimensions": 2, "max_seq_length": 256}

    def encode(self, texts):
        return np.asarray([[1.0, 0.0] for _ in texts], dtype=np.float32).reshape(-1, 2)

    def token_lengths(self, texts):
        return [len(text.split()) for text in texts]


@pytest.mark.parametrize("service", ["import", "prepare", "preview"])
@pytest.mark.parametrize("checkpoint", ["first_callback", "operation"])
def test_progress_interruption_is_persisted_without_masking_original(
    sample_repository, tmp_path, monkeypatch, service, checkpoint
):
    workspace = tmp_path / "w"
    encoder = FixtureEncoder()
    original = StopWork("server stopped")
    stopped = False
    callbacks = []

    def observer(record):
        nonlocal stopped
        if stopped:
            raise RuntimeError("Observer must not run again while saving an interruption")
        callbacks.append(record)
        if checkpoint == "first_callback":
            stopped = True
            raise original

    def interrupt(*args, **kwargs):
        nonlocal stopped
        stopped = True
        raise original

    repository_id = None
    if service != "import":
        repository_id = importing.import_repository(str(sample_repository), workspace)[
            "repository_id"
        ]
    if service == "preview":
        preparation.prepare_repository(workspace, repository_id, encoder=encoder)

    if checkpoint == "operation":
        if service == "import":
            monkeypatch.setattr(importing, "_collect", interrupt)
        elif service == "prepare":
            monkeypatch.setattr(preparation, "build_vectors", interrupt)
        else:
            create = comparison.create_retriever

            def stop_after_bm25(strategy, *args, **kwargs):
                if strategy == "dense":
                    interrupt()
                return create(strategy, *args, **kwargs)

            monkeypatch.setattr(comparison, "create_retriever", stop_after_bm25)

    with pytest.raises(StopWork) as caught:
        if service == "import":
            importing.import_repository(str(sample_repository), workspace, on_progress=observer)
        elif service == "prepare":
            preparation.prepare_repository(
                workspace, repository_id, encoder=encoder, on_progress=observer
            )
        else:
            comparison.preview_question(
                workspace, repository_id, "checksum", encoder=encoder, on_progress=observer
            )
    assert caught.value is original
    assert callbacks
    if checkpoint == "first_callback":
        assert len(callbacks) == 1

    if service == "import":
        paths = list((workspace / "jobs").glob("*.json"))
        assert len(paths) == 1
        saved = read_json(workspace, f"jobs/{paths[0].name}")
        assert saved["events"][-1]["status"] == "interrupted"
    elif service == "prepare":
        saved = preparation.load_preparation(workspace, repository_id)
        assert all(stage["status"] != "running" for stage in saved["stages"].values())
        if checkpoint == "operation":
            assert saved["stages"]["index"]["status"] == "ready"
            assert saved["stages"]["vectors"]["status"] == "interrupted"
    else:
        runs = comparison.list_comparisons(workspace)
        assert len(runs) == 1
        saved = comparison.load_comparison(workspace, runs[0]["run_id"])
        assert saved["finished_at"] is not None
        assert all(row["status"] != "running" for row in saved["results"])
        if checkpoint == "operation":
            assert saved["results"][0]["status"] == "preview"
            assert saved["results"][0]["qa"] is not None
            assert saved["results"][1]["status"] == "interrupted"
    assert saved["status"] == "interrupted"
