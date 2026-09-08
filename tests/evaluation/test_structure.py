import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.evaluation.comparison import compare_runs
from structure_aware_retrieval.evaluation.config import load_config
from structure_aware_retrieval.evaluation.runner import run_experiment
from structure_aware_retrieval.indexing import load_index
from structure_aware_retrieval.relations import build_graph


def graph_config(experiment: Path) -> None:
    config = load_config(experiment)
    build_graph(load_index(config.indexes["fixture"]), experiment.parent / "graph.json")
    text = experiment.read_text().replace(
        'strategy = "bm25"', 'strategy = "structure"\nname = "no-edges"'
    )
    experiment.write_text(
        text + '\n[graphs]\nfixture = "graph.json"\n[structure]\n'
        'seed_strategy = "bm25"\nrelations = []\n'
    )


def test_no_edge_fingerprint_context_cost_and_named_ablation_comparison(experiment: Path):
    baseline = experiment.parent / "baseline"
    before = run_experiment(experiment, baseline)
    graph_config(experiment)
    disabled = experiment.parent / "disabled"
    off = run_experiment(experiment, disabled)
    assert off["quality_fingerprint"] == before["quality_fingerprint"]
    assert off["overall"]["retrieval_work"]["edges_examined"] == 0
    assert (
        off["overall"]["context_cost"][5]["utf8_bytes"]
        >= off["overall"]["context_cost"][1]["utf8_bytes"]
    )
    experiment.write_text(
        experiment.read_text()
        .replace('name = "no-edges"', 'name = "with-edges"')
        .replace("relations = []", 'relations = ["call", "containment", "test", "import"]')
    )
    enabled = experiment.parent / "enabled"
    on = run_experiment(experiment, enabled)
    repeat = run_experiment(experiment, experiment.parent / "repeat")
    assert repeat["quality_fingerprint"] == on["quality_fingerprint"]
    assert on["indexes"]["fixture"]["graph"]["edge_counts"]["containment"] > 0
    result = compare_runs([baseline, disabled, enabled], experiment.parent / "comparison")
    assert [row["strategy"] for row in result["runs"]] == ["bm25", "no-edges", "with-edges"]
    cli = CliRunner().invoke(
        app,
        [
            "compare",
            "--run",
            str(disabled),
            "--run",
            str(enabled),
            "--output",
            str(experiment.parent / "cli-comparison"),
        ],
    )
    assert cli.exit_code == 0, cli.output


def test_graph_config_errors_and_wrong_snapshot_fail_before_output(experiment: Path):
    graph_config(experiment)
    valid = experiment.read_text()
    experiment.write_text(valid.replace('fixture = "graph.json"', 'wrong = "graph.json"'))
    with pytest.raises(ValueError, match="graphs must exactly match"):
        load_config(experiment)
    experiment.write_text(valid.replace('seed_strategy = "bm25"', 'seed_strategy = "hybrid"'))
    with pytest.raises(ValueError, match="model_cache"):
        load_config(experiment)
    experiment.write_text(valid)
    graph = experiment.parent / "graph.json"
    data = json.loads(graph.read_text())
    data["metadata"]["binding"]["snapshot_id"] = "mismatch"
    graph.write_text(json.dumps(data))
    output = experiment.parent / "invalid"
    with pytest.raises(ValueError, match="cache mismatch"):
        run_experiment(experiment, output)
    assert not output.exists()
