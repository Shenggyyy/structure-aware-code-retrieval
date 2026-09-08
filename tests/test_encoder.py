"""Exercise the adapter without installing torch, downloading or running a real model."""

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.embeddings import MODEL_REVISION, SentenceEncoder


@pytest.fixture
def fake_runtime(monkeypatch):
    calls = {}

    class Model:
        def __init__(self, name, **kwargs):
            calls["load"] = kwargs

        def eval(self):
            calls["eval"] = True

        def get_embedding_dimension(self):
            return 384

        def encode(self, texts, **kwargs):
            calls["encode"] = kwargs
            return np.ones((len(texts), 384)) / np.sqrt(384)

        def tokenizer(self, texts, **kwargs):
            calls["tokenizer"] = kwargs
            return {"input_ids": [[0, 1, 2] for text in texts]}

    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            set_num_threads=lambda n: calls.update(threads=n),
            manual_seed=lambda n: None,
            use_deterministic_algorithms=lambda enabled: None,
        ),
    )
    monkeypatch.setitem(
        sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=Model)
    )
    monkeypatch.setattr("structure_aware_retrieval.embeddings.version", lambda name: "fixture")
    return calls


def test_adapter_pins_model_offline_safetensors_and_encoding(fake_runtime, tmp_path: Path):
    encoder = SentenceEncoder(tmp_path)
    assert fake_runtime["load"]["revision"] == MODEL_REVISION
    assert fake_runtime["load"]["local_files_only"] is True
    assert fake_runtime["load"]["trust_remote_code"] is False
    assert fake_runtime["load"]["model_kwargs"]["use_safetensors"] is True
    assert fake_runtime["threads"] == 4
    assert encoder.encode(["code"]).dtype == np.float32
    assert encoder.encode([]).shape == (0, 384)
    assert fake_runtime["encode"]["normalize_embeddings"] is True
    assert fake_runtime["encode"]["prompt"] == ""
    assert encoder.token_lengths(["code"]) == [3]
    assert encoder.token_lengths([]) == []
    assert fake_runtime["tokenizer"]["truncation"] is False


def test_prepare_model_is_the_explicit_download_path(fake_runtime, tmp_path: Path):
    result = CliRunner().invoke(app, ["prepare-model", "--cache", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert fake_runtime["load"]["local_files_only"] is False
    assert MODEL_REVISION in result.output


def test_missing_optional_dependencies_has_install_command(monkeypatch, tmp_path: Path):
    monkeypatch.setitem(sys.modules, "torch", None)
    with pytest.raises(ValueError, match="uv sync --locked --extra dense"):
        SentenceEncoder(tmp_path)


def test_embed_and_dense_search_cli_offline(fake_runtime, sample_repository: Path, tmp_path: Path):
    runner = CliRunner()
    database, vectors = tmp_path / "index.sqlite", tmp_path / "vectors.npz"
    result = runner.invoke(app, ["index", str(sample_repository), "--output", str(database)])
    assert result.exit_code == 0
    args = [
        "embed",
        "--index",
        str(database),
        "--output",
        str(vectors),
        "--model-cache",
        str(tmp_path),
    ]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert runner.invoke(app, args).exit_code == 1
    result = runner.invoke(
        app,
        [
            "search",
            "checksum",
            "--index",
            str(database),
            "--vectors",
            str(vectors),
            "--model-cache",
            str(tmp_path),
            "--strategy",
            "dense",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert '"cosine"' in result.output
