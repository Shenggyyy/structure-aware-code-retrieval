import json
from dataclasses import replace
from pathlib import Path

import pytest

from structure_aware_retrieval.evaluation.config import load_config
from structure_aware_retrieval.evaluation.dataset import load_benchmark, validate_index
from structure_aware_retrieval.indexing import load_index


def test_fixture_and_committed_seed_validate(experiment: Path) -> None:
    config = load_config(experiment)
    benchmark = load_benchmark(config.benchmark)
    assert len(benchmark.queries) == 3
    validate_index(benchmark, benchmark.repositories[0], load_index(config.indexes["fixture"]))
    seed = Path(__file__).resolve().parents[2] / "benchmarks/seed-v1/benchmark.json"
    seed = load_benchmark(seed)
    assert len(seed.queries) == 40
    assert len(seed.repositories) == 2
    assert seed.annotation_status == "provisional"


@pytest.mark.parametrize(
    "case",
    [
        "duplicate_query",
        "unknown_query",
        "duplicate_judgment",
        "grade_bool",
        "path_escape",
        "bad_lines",
        "answerability",
        "blank_query",
    ],
)
def test_invalid_records_fail_with_value_error(experiment: Path, case: str) -> None:
    folder = experiment.parent / "benchmark"
    qpath, jpath = folder / "queries.jsonl", folder / "qrels.jsonl"
    queries = [json.loads(line) for line in qpath.read_text().splitlines()]
    judgments = [json.loads(line) for line in jpath.read_text().splitlines()]
    if case == "duplicate_query":
        queries.append(queries[0])
    elif case == "unknown_query":
        judgments[0]["query_id"] = "missing"
    elif case == "duplicate_judgment":
        judgments.append(judgments[0])
    elif case == "grade_bool":
        judgments[0]["grade"] = True
    elif case == "path_escape":
        judgments[0]["target"]["path"] = "../outside.py"
    elif case == "bad_lines":
        judgments[0]["target"]["start_line"] = 0
    elif case == "answerability":
        queries[0]["answerable"] = False
    else:
        queries[0]["text"] = " "
    for path, records in ((qpath, queries), (jpath, judgments)):
        path.write_text("".join(json.dumps(row) + "\n" for row in records))
    with pytest.raises(ValueError):
        load_benchmark(folder / "benchmark.json")


def test_source_or_locator_mismatch_fails(experiment: Path) -> None:
    config = load_config(experiment)
    benchmark = load_benchmark(config.benchmark)
    index = load_index(config.indexes["fixture"])
    with pytest.raises(ValueError, match="corpus hash"):
        validate_index(benchmark, replace(benchmark.repositories[0], corpus_hash="b" * 64), index)
    with pytest.raises(ValueError, match="pinned"):
        validate_index(benchmark, replace(benchmark.repositories[0], commit="b" * 40), index)
    judgment = benchmark.judgments[0]
    altered = replace(
        benchmark, judgments=(replace(judgment, target=replace(judgment.target, start_line=1)),)
    )
    with pytest.raises(ValueError, match="target is absent"):
        validate_index(altered, benchmark.repositories[0], index)


def test_config_paths_are_relative_and_unknown_fields_rejected(
    experiment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(experiment.parent / "benchmark")
    assert load_config(experiment).indexes["fixture"] == experiment.parent / "index.sqlite"
    experiment.write_text(
        experiment.read_text().replace('strategy = "bm25"', 'strategy = "unknown"')
    )
    with pytest.raises(ValueError, match="Supported strategies"):
        load_config(experiment)


def test_json_errors_include_location(experiment: Path) -> None:
    manifest = experiment.parent / "benchmark/benchmark.json"
    (manifest.parent / "queries.jsonl").write_text("not json\n")
    with pytest.raises(ValueError, match="queries.jsonl:1"):
        load_benchmark(manifest)
