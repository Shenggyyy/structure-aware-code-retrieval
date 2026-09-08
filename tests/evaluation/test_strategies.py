import json
from pathlib import Path

import numpy as np
import pytest

from structure_aware_retrieval.embeddings import build_vectors
from structure_aware_retrieval.evaluation.comparison import compare_runs
from structure_aware_retrieval.evaluation.config import load_config
from structure_aware_retrieval.evaluation.runner import run_experiment
from structure_aware_retrieval.indexing import load_index


class FixtureEncoder:
    spec = {"id": "fixture-only", "revision": "test", "dimensions": 2, "max_seq_length": 8}

    def encode(self, texts):
        rows = [[1, 0] if "checksum" in text else [0, 1] for text in texts]
        return np.array(rows, dtype=np.float32)

    def token_lengths(self, texts):
        return [len(text.split()) for text in texts]


@pytest.mark.parametrize("strategy", ["dense", "hybrid", "symbol"])
def test_all_strategies_evaluate_offline_and_reproduce(experiment: Path, monkeypatch, strategy):
    encoder = FixtureEncoder()
    config = load_config(experiment)
    baseline = experiment.parent / "baseline"
    run_experiment(experiment, baseline)
    path = experiment.parent / "vectors.npz"
    build_vectors(load_index(config.indexes["fixture"]), encoder, path)
    monkeypatch.setattr(
        "structure_aware_retrieval.evaluation.runner.SentenceEncoder", lambda cache: encoder
    )
    text = experiment.read_text().replace('strategy = "bm25"', f'strategy = "{strategy}"')
    text = text.replace("[indexes]", 'model_cache = "models"\n[indexes]')
    experiment.write_text(text + '\n[vectors]\nfixture = "vectors.npz"\n')
    first = run_experiment(experiment, experiment.parent / "first")
    second = run_experiment(experiment, experiment.parent / "second")
    assert first["quality_fingerprint"] == second["quality_fingerprint"]
    assert first["overall"]["no_answer_count"] == 1
    assert first["overall"]["no_answer_with_results"] == 1
    assert first["config"]["encoder"] == encoder.spec
    assert first["indexes"]["fixture"]["vectors"]["documents"] > 0
    rankings = [
        json.loads(line)
        for line in (experiment.parent / "first/rankings.jsonl").read_text().splitlines()
    ]
    assert "components" in rankings[0]["ranking"][0]
    comparison = compare_runs(
        [baseline, experiment.parent / "first"], experiment.parent / "comparison"
    )
    assert comparison["baseline"] == "bm25"
    counts = comparison["paired"][strategy]["1"]["recall"]
    assert counts["wins"] + counts["ties"] + counts["losses"] == 2
    with pytest.raises(FileExistsError):
        compare_runs([baseline, experiment.parent / "first"], experiment.parent / "comparison")
    with pytest.raises(ValueError, match="distinct strategy"):
        compare_runs([baseline, baseline], experiment.parent / "bad")
    summary_path = experiment.parent / "first/summary.json"
    summary = json.loads(summary_path.read_text())
    summary["config"]["unit"] = "file"
    summary_path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="share benchmark"):
        compare_runs([baseline, experiment.parent / "first"], experiment.parent / "mismatch")


def test_dense_config_requires_matching_vector_repositories(experiment: Path):
    text = experiment.read_text().replace('strategy = "bm25"', 'strategy = "dense"')
    experiment.write_text(text)
    with pytest.raises(ValueError, match="model_cache"):
        load_config(experiment)
    text = text.replace("[indexes]", 'model_cache = "models"\n[indexes]')
    experiment.write_text(text + '\n[vectors]\nwrong = "vectors.npz"\n')
    with pytest.raises(ValueError, match="exactly match"):
        load_config(experiment)
