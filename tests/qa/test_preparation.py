import json
from dataclasses import asdict
from pathlib import Path

import pytest

from structure_aware_retrieval.evaluation.dataset import (
    corpus_hash,
    load_benchmark,
    symbol_target,
)
from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.preparation import load_cases, prepare_experiment
from structure_aware_retrieval.retrieval import BM25Retriever


@pytest.fixture
def qa_experiment(sample_repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
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
        "id": "qa-fixture",
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
            "id": query_id,
            "repository": "fixture",
            "category": category,
            "text": text,
            "answerable": True,
        }
        for query_id, category, text in (
            ("q1", "symbol", "calculate_checksum trace"),
            ("q2", "behavior", "deadline"),
        )
    ]
    qrels = [
        {
            "query_id": query,
            "target": asdict(symbol_target(symbols[name])),
            "grade": grade,
            "rationale": "Retrieval-only judgment marker.",
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
    benchmark = load_benchmark(folder / "benchmark.json")
    cases = [
        {
            "id": f"qa-{query['id']}",
            "repository": "fixture",
            "question": query["text"],
            "source_query_id": query["id"],
            "expected_status": "answered",
            "reference_points": ["REFERENCE-ONLY-MARKER never belongs in a prompt."],
            "source_targets": [row["target"] for row in qrels if row["query_id"] == query["id"]],
            "rationale": "RATIONALE-ONLY-MARKER for independent review.",
        }
        for query in queries
    ]
    cases.append(
        {
            "id": "qa-scope",
            "repository": "fixture",
            "question": "Which private production deadline was configured today?",
            "source_query_id": None,
            "expected_status": "insufficient_context",
            "reference_points": ["REFERENCE-ONLY-MARKER: deployment configuration is needed."],
            "source_targets": [],
            "rationale": "RATIONALE-ONLY-MARKER: missing application-specific evidence.",
        }
    )
    data = {
        "schema_version": 1,
        "id": "qa-seed",
        "version": "0.1.0",
        "annotation_status": "provisional",
        "retrieval_benchmark": "benchmark/benchmark.json",
        "retrieval_benchmark_digest": benchmark.digest,
        "cases": cases,
    }
    (tmp_path / "cases.json").write_text(json.dumps(data), encoding="utf-8")
    (tmp_path / "retrieval.toml").write_text(
        'schema_version = 1\nbenchmark = "benchmark/benchmark.json"\nstrategy = "bm25"\n'
        'unit = "symbol"\nks = [1, 2, 5]\nwarmup_queries = 0\nrepeats = 1\nseed = 0\n'
        '[indexes]\nfixture = "index.sqlite"\n',
        encoding="utf-8",
    )
    config = tmp_path / "qa.toml"
    config.write_text(
        'schema_version = 1\ncases = "cases.json"\nmodel = "gpt-5.4-mini-2026-03-17"\n'
        "max_output_tokens = 1024\nmax_context_bytes = 16000\ntop_k = 10\n"
        'api_key_env = "OPENAI_API_KEY"\n'
        "[pricing]\ninput_per_million = 0.75\noutput_per_million = 4.5\n"
        'as_of = "2026-09-08"\n'
        '[retrieval_configs]\nbm25 = "retrieval.toml"\n',
        encoding="utf-8",
    )
    return config


def _edit_cases(config: Path, edit) -> None:
    path = config.parent / "cases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    edit(data)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_load_cases_preserves_question_and_all_positive_targets(qa_experiment: Path):
    raw, benchmark = load_cases(qa_experiment.parent / "cases.json")
    assert raw["retrieval_benchmark_digest"] == benchmark.digest
    assert raw["cases"][0]["question"] == benchmark.queries[0].text
    assert raw["cases"][0]["source_targets"] == [
        asdict(row.target) for row in benchmark.judgments if row.query_id == "q1" and row.grade > 0
    ]
    assert len(raw["cases"][0]["source_targets"]) == 2
    assert raw["cases"][2]["source_query_id"] is None


@pytest.mark.parametrize(
    "edit",
    [
        lambda d: d.update(schema_version=True),
        lambda d: d.update(unexpected="field"),
        lambda d: d.update(retrieval_benchmark_digest="0" * 64),
        lambda d: d.update(cases=[]),
        lambda d: d["cases"].append(d["cases"][0].copy()),
        lambda d: d["cases"][0].update(repository="unknown"),
        lambda d: d["cases"][0].update(repository=[]),
        lambda d: d["cases"][0].update(question="A rewritten query with the same source ID"),
        lambda d: d["cases"][0].update(source_query_id="unknown"),
        lambda d: d["cases"][0].update(source_targets=d["cases"][0]["source_targets"][:1]),
        lambda d: d["cases"][0]["source_targets"][0].update(start_line=1),
        lambda d: d["cases"][0].update(reference_points=[]),
        lambda d: d["cases"][0].update(reference_points=[False]),
        lambda d: d["cases"][0].update(expected_status="preview"),
        lambda d: d["cases"][0].update(expected_status="insufficient_context"),
        lambda d: d["cases"][2].update(expected_status="answered"),
        lambda d: d["cases"][2].update(source_targets=d["cases"][0]["source_targets"]),
    ],
    ids=[
        "boolean-schema",
        "extra-field",
        "stale-benchmark",
        "empty-cases",
        "duplicate-id",
        "unknown-repository",
        "nonstring-repository",
        "changed-question",
        "unknown-source-query",
        "missing-support-target",
        "changed-source-range",
        "empty-reference",
        "invalid-reference",
        "invalid-status",
        "answerable-as-abstention",
        "scope-as-answered",
        "scope-with-targets",
    ],
)
def test_load_cases_rejects_invalid_or_unbound_labels(qa_experiment: Path, edit):
    _edit_cases(qa_experiment, edit)
    with pytest.raises(ValueError):
        load_cases(qa_experiment.parent / "cases.json")


def test_prepare_refuses_existing_output(qa_experiment: Path, tmp_path: Path):
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "preserve.txt"
    marker.write_text("preserve this result", encoding="utf-8")
    with pytest.raises(FileExistsError):
        prepare_experiment(qa_experiment, output)
    assert marker.read_text(encoding="utf-8") == "preserve this result"


def test_prepare_is_offline_and_keeps_gold_out_of_messages(
    qa_experiment: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def unexpected_call(*args, **kwargs):
        pytest.fail("Offline preparation must not call a model or access the network")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("socket.create_connection", unexpected_call)
    monkeypatch.setattr("urllib.request.OpenerDirector.open", unexpected_call)
    monkeypatch.setattr(
        "structure_aware_retrieval.qa.provider.OpenAIModel.complete", unexpected_call
    )
    monkeypatch.setattr("structure_aware_retrieval.qa.preparation.SentenceEncoder", unexpected_call)
    output = tmp_path / "prepared"
    plan = prepare_experiment(qa_experiment, output)
    rows = [json.loads(line) for line in (output / "requests.jsonl").read_text().splitlines()]
    cases = json.loads((output / "cases.json").read_text())
    assert plan == json.loads((output / "plan.json").read_text())
    assert plan["status"] == "prepared"
    assert plan["request_count"] == len(rows) == 3
    assert 0 < plan["maximum_api_calls"] <= len(rows)
    assert plan["maximum_api_calls"] == sum(
        bool(row["prepared"]["context"]["evidence"]) for row in rows
    )
    assert plan["request_digest"] == stable_id(rows)
    assert plan["cases_digest"] == stable_id(cases)
    assert plan["estimated_cost_usd"] > 0
    assert plan["cost_estimation"]["billing_guarantee"] is False
    assert plan["cost_estimation"]["maximum_output_tokens"] == (
        plan["maximum_api_calls"] * plan["max_output_tokens"]
    )
    cases_by_id = {case["id"]: case for case in cases["cases"]}
    for row in rows:
        prepared = row["prepared"]
        encoded = json.dumps(prepared)
        for secret in ("REFERENCE-ONLY-MARKER", "RATIONALE-ONLY-MARKER"):
            assert secret not in encoded
        for field in ("reference_points", "source_targets", "expected_status"):
            assert field not in encoded
        user_message = json.loads(prepared["messages"][1]["content"])
        assert set(user_message) == {"question", "evidence"}
        assert user_message["question"] == cases_by_id[row["case_id"]]["question"]
        assert user_message["evidence"] == json.loads(prepared["context"]["context_text"])
        assert prepared["context"]["budget"]["used_context_bytes"] <= 16000
        assert (
            prepared["context"]["snapshot_id"]
            == (plan["strategies"]["bm25"]["indexes"]["fixture"]["snapshot_id"])
        )
    assert len(list((output / "previews").glob("*.md"))) == 3
    assert "No model was called" in (output / "README.md").read_text()


def test_preparation_content_is_repeatable_and_independent_of_references(
    qa_experiment: Path, tmp_path: Path
):
    first = prepare_experiment(qa_experiment, tmp_path / "first")
    second = prepare_experiment(qa_experiment, tmp_path / "second")
    assert first["content_fingerprint"] == second["content_fingerprint"]
    assert first["cases_digest"] == second["cases_digest"]
    # Changing evaluation-only text must not affect retrieval or model prompts.
    _edit_cases(
        qa_experiment,
        lambda data: data["cases"][0].update(
            reference_points=["A completely changed reference for a human reviewer."],
            rationale="An amended reviewer rationale.",
        ),
    )
    third = prepare_experiment(qa_experiment, tmp_path / "changed-labels")
    assert first["content_fingerprint"] == third["content_fingerprint"]
    assert first["cases_digest"] != third["cases_digest"]
    assert first["plan_fingerprint"] != third["plan_fingerprint"]


@pytest.mark.parametrize(
    ("original", "replacement"),
    [
        ("schema_version = 1", "schema_version = true"),
        ("max_output_tokens = 1024", "max_output_tokens = 0"),
        ("max_context_bytes = 16000", "max_context_bytes = 1"),
        ("top_k = 10", "top_k = true"),
        ('api_key_env = "OPENAI_API_KEY"', 'api_key_env = "invalid-variable-name"'),
        ("input_per_million = 0.75", "input_per_million = nan"),
        ("output_per_million = 4.5", "output_per_million = -1"),
        ('as_of = "2026-09-08"', 'as_of = "not-a-date"'),
        ('bm25 = "retrieval.toml"', 'alias = "retrieval.toml"'),
        ('bm25 = "retrieval.toml"', 'dense = "retrieval.toml"'),
    ],
)
def test_prepare_rejects_invalid_settings_before_publishing(
    qa_experiment: Path, tmp_path: Path, original: str, replacement: str
):
    source = qa_experiment.read_text(encoding="utf-8")
    assert original in source
    qa_experiment.write_text(source.replace(original, replacement), encoding="utf-8")
    output = tmp_path / "invalid-output"
    with pytest.raises(ValueError):
        prepare_experiment(qa_experiment, output)
    assert not output.exists()


def test_prepare_rejects_retrieval_benchmark_mismatch(qa_experiment: Path, tmp_path: Path):
    source = qa_experiment.parent / "benchmark" / "benchmark.json"
    manifest = json.loads(source.read_text(encoding="utf-8"))
    manifest["id"] = "different-benchmark"
    (source.parent / "other.json").write_text(json.dumps(manifest), encoding="utf-8")
    retrieval = qa_experiment.parent / "retrieval.toml"
    retrieval.write_text(
        retrieval.read_text(encoding="utf-8").replace("benchmark.json", "other.json"),
        encoding="utf-8",
    )
    output = tmp_path / "mismatch"
    with pytest.raises(ValueError, match="same retrieval benchmark"):
        prepare_experiment(qa_experiment, output)
    assert not output.exists()


def test_cases_reject_conflicting_scope_label_for_existing_question(qa_experiment: Path):
    _edit_cases(
        qa_experiment,
        lambda data: data["cases"][2].update(question=data["cases"][0]["question"]),
    )
    with pytest.raises(ValueError):
        load_cases(qa_experiment.parent / "cases.json")


def test_cases_reject_test_split_even_with_matching_digest(qa_experiment: Path):
    source = qa_experiment.parent / "benchmark" / "benchmark.json"
    manifest = json.loads(source.read_text(encoding="utf-8"))
    manifest["split"] = "test"
    source.write_text(json.dumps(manifest), encoding="utf-8")
    benchmark = load_benchmark(source)
    _edit_cases(
        qa_experiment,
        lambda data: data.update(retrieval_benchmark_digest=benchmark.digest),
    )
    with pytest.raises(ValueError, match="development data"):
        load_cases(qa_experiment.parent / "cases.json")


def test_cases_reject_duplicate_json_fields(qa_experiment: Path):
    path = qa_experiment.parent / "cases.json"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            '"schema_version": 1', '"schema_version": 1, "schema_version": 1'
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate JSON"):
        load_cases(path)


def test_preparation_requires_identical_snapshot_across_strategies(
    qa_experiment: Path,
    sample_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    # Same source content and labels, different chunking: corpus hashes still match.
    alternate = tmp_path / "other-index.sqlite"
    build_index(sample_repository, alternate, max_chunk_lines=1)
    original = load_index(tmp_path / "index.sqlite")
    other = load_index(alternate)
    assert corpus_hash(original) == corpus_hash(other)
    assert original.metadata["snapshot_id"] != other.metadata["snapshot_id"]
    dense_config = tmp_path / "dense.toml"
    dense_config.write_text(
        'schema_version = 1\nbenchmark = "benchmark/benchmark.json"\nstrategy = "dense"\n'
        'unit = "symbol"\nks = [1]\nwarmup_queries = 0\nrepeats = 1\nseed = 0\n'
        'model_cache = "model"\n[indexes]\nfixture = "other-index.sqlite"\n'
        '[vectors]\nfixture = "vectors.npz"\n',
        encoding="utf-8",
    )
    qa_experiment.write_text(
        qa_experiment.read_text(encoding="utf-8") + 'dense = "dense.toml"\n',
        encoding="utf-8",
    )

    class FakeEncoder:
        spec = {"model": "offline-fixture"}

        def __init__(self, path):
            self.path = path

    monkeypatch.setattr("structure_aware_retrieval.qa.preparation.SentenceEncoder", FakeEncoder)
    monkeypatch.setattr(
        "structure_aware_retrieval.qa.preparation.create_retriever",
        lambda strategy, index, **kwargs: BM25Retriever(index),
    )
    output = tmp_path / "different-snapshots"
    with pytest.raises(ValueError, match="identical source snapshots"):
        prepare_experiment(qa_experiment, output)
    assert not output.exists()
