import json
from dataclasses import asdict
from pathlib import Path

import pytest

from structure_aware_retrieval.evaluation.dataset import corpus_hash, symbol_target
from structure_aware_retrieval.indexing import build_index, load_index


@pytest.fixture
def experiment(sample_repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Synthetic provenance allows offline integration testing without committing a test repo.
    monkeypatch.setattr(
        "structure_aware_retrieval.indexing._git_provenance",
        lambda root: {"commit": "a" * 40, "dirty": False},
    )
    database = tmp_path / "index.sqlite"
    build_index(sample_repository, database, max_chunk_lines=2)
    index = load_index(database)
    symbols = {symbol.qualified_name: symbol for symbol in index.symbols.values()}
    folder = tmp_path / "benchmark"
    folder.mkdir()
    manifest = {
        "schema_version": 1,
        "id": "fixture",
        "version": "1",
        "split": "dev",
        "annotation_status": "provisional",
        "repositories": [
            {
                "id": "fixture",
                "url": "https://example.invalid/fixture.git",
                "ref": "v1",
                "commit": "a" * 40,
                "license": "test-fixture",
                "corpus_hash": corpus_hash(index),
            }
        ],
        "queries_file": "queries.jsonl",
        "qrels_file": "qrels.jsonl",
    }
    queries = [
        {
            "id": "q1",
            "repository": "fixture",
            "category": "symbol",
            "text": "calculate_checksum trace",
            "answerable": True,
        },
        {
            "id": "q2",
            "repository": "fixture",
            "category": "behavior",
            "text": "deadline",
            "answerable": True,
        },
        {
            "id": "q3",
            "repository": "fixture",
            "category": "behavior",
            "text": "zzzzunseenmarker",
            "answerable": False,
        },
    ]
    qrels = [
        {
            "query_id": query,
            "target": asdict(symbol_target(symbols[name])),
            "grade": grade,
            "rationale": "Synthetic source fixture judgment.",
        }
        for query, name, grade in [
            ("q1", "client.calculate_checksum", 2),
            ("q1", "client.trace", 1),
            ("q2", "errors.TimeoutError", 2),
        ]
    ]
    (folder / "benchmark.json").write_text(json.dumps(manifest), encoding="utf-8")
    for filename, records in (("queries", queries), ("qrels", qrels)):
        (folder / f"{filename}.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in records), encoding="utf-8"
        )
    config = tmp_path / "experiment.toml"
    config.write_text(
        'schema_version = 1\nbenchmark = "benchmark/benchmark.json"\nstrategy = "bm25"\n'
        'unit = "symbol"\nks = [1, 2, 5]\nwarmup_queries = 1\nrepeats = 2\nseed = 0\n'
        '[indexes]\nfixture = "index.sqlite"\n',
        encoding="utf-8",
    )
    return config
