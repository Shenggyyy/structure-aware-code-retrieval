import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.evaluation.recorded import read_jsonl
from structure_aware_retrieval.evaluation.review import check_review, create_pool
from structure_aware_retrieval.evaluation.runner import run_experiment


def write_rows(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


@pytest.fixture
def bundle(experiment: Path) -> Path:
    run = experiment.parent / "run"
    run_experiment(experiment, run)
    output = experiment.parent / "review"
    create_pool(experiment, [run], output, depth=1)
    return output


def test_pool_contains_all_qrels_and_blind_source_templates(experiment: Path, bundle: Path):
    pool = read_jsonl(bundle / "pool.jsonl")
    originals = [row for row in pool if row["original_judgment"] is not None]
    assert len(originals) == 3  # Includes positive judgments absent from top-1.
    assert all(row["grade"] is None for row in read_jsonl(bundle / "judgments.jsonl"))
    for row in read_jsonl(bundle / "judgments.jsonl"):
        assert set(row) == {"item_id", "grade", "rationale", "reviewer"}
    source = (bundle / "questions/q1.md").read_text(encoding="utf-8")
    assert "def calculate_checksum" in source
    assert "original_judgment" not in source and "bm25" not in source
    assert (bundle / "questions/q3.md").is_file()  # No-answer question still needs review.
    repeat = experiment.parent / "repeat-review"
    again = create_pool(experiment, [experiment.parent / "run"], repeat, depth=1)
    first = json.loads((bundle / "manifest.json").read_text())
    assert again == first
    assert (repeat / "pool.jsonl").read_bytes() == (bundle / "pool.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        create_pool(experiment, [experiment.parent / "run"], bundle)
    with pytest.raises(ValueError, match="depth"):
        create_pool(experiment, [experiment.parent / "run"], experiment.parent / "bad", depth=6)


def test_pending_review_is_not_approved_and_cli_roundtrip(bundle: Path):
    output = bundle.parent / "checked"
    cli = CliRunner().invoke(
        app,
        [
            "check-review",
            "--bundle",
            str(bundle),
            "--judgments",
            str(bundle / "judgments.jsonl"),
            "--queries",
            str(bundle / "queries.jsonl"),
            "--output",
            str(output),
        ],
    )
    assert cli.exit_code == 0, cli.output
    result = json.loads((output / "review-status.json").read_text())
    assert result["ready_for_versioning"] is False
    assert result["queries"] == {"pending": 3}
    assert result["changes"] == []
    assert result["reviewer_identity_verified"] is False
    assert (output / "judgments.jsonl").read_bytes() != b""


def fill_review(bundle):
    pool = {row["item_id"]: row for row in read_jsonl(bundle / "pool.jsonl")}
    judgments = read_jsonl(bundle / "judgments.jsonl")
    for row in judgments:
        old = pool[row["item_id"]]["original_judgment"]
        row.update(
            grade=old["grade"] if old else 0,
            reviewer="fixture-reviewer",
            rationale="Synthetic test decision.",
        )
    queries = read_jsonl(bundle / "queries.jsonl")
    for row in queries:
        row.update(
            answerable=row["query_id"] != "q3",
            clear=True,
            reviewer="fixture-reviewer",
            rationale="Synthetic test decision.",
        )
    write_rows(bundle / "judgments.jsonl", judgments)
    write_rows(bundle / "queries.jsonl", queries)
    return judgments, queries


def test_complete_review_is_archived_without_relabeling_benchmark(experiment: Path, bundle: Path):
    before = (experiment.parent / "benchmark/benchmark.json").read_bytes()
    fill_review(bundle)
    result = check_review(
        bundle, bundle / "judgments.jsonl", bundle / "queries.jsonl", bundle.parent / "checked"
    )
    assert result["ready_for_versioning"] is True
    assert result["benchmark"]["annotation_status"] == "provisional"
    assert (experiment.parent / "benchmark/benchmark.json").read_bytes() == before
    with pytest.raises(FileExistsError):
        check_review(
            bundle, bundle / "judgments.jsonl", bundle / "queries.jsonl", bundle.parent / "checked"
        )


@pytest.mark.parametrize("change", ["unsure", "unclear", "answerability", "pending"])
def test_unresolved_reviews_cannot_pass(bundle: Path, change):
    judgments, queries = fill_review(bundle)
    if change == "unsure":
        judgments[0]["grade"] = "unsure"
    elif change == "pending":
        queries[0]["clear"] = None
    elif change == "unclear":
        queries[0]["clear"] = False
    else:
        queries[0]["answerable"] = False
    write_rows(bundle / "judgments.jsonl", judgments)
    write_rows(bundle / "queries.jsonl", queries)
    result = check_review(
        bundle, bundle / "judgments.jsonl", bundle / "queries.jsonl", bundle.parent / "checked"
    )
    assert result["ready_for_versioning"] is False
    if change in {"unclear", "answerability"}:
        assert result["conflicts"]


@pytest.mark.parametrize(
    "change",
    [
        "boolean_grade",
        "missing_identity",
        "duplicate",
        "omitted",
        "unknown",
        "extra_field",
        "pool_tampering",
        "evidence_tampering",
    ],
)
def test_invalid_or_stale_review_fails_without_output(bundle: Path, change):
    judgments, _ = fill_review(bundle)
    if change == "boolean_grade":
        judgments[0]["grade"] = True
    elif change == "missing_identity":
        judgments[0]["reviewer"] = " "
    elif change == "duplicate":
        judgments.append(judgments[0])
    elif change == "omitted":
        judgments.pop()
    elif change == "unknown":
        judgments[0]["item_id"] = "unknown"
    elif change == "extra_field":
        judgments[0]["approved"] = True
    else:
        filename = "pool.jsonl" if change == "pool_tampering" else "evidence.jsonl"
        data = read_jsonl(bundle / filename)
        data[0]["tampered"] = True
        write_rows(bundle / filename, data)
    write_rows(bundle / "judgments.jsonl", judgments)
    output = bundle.parent / "invalid-review"
    with pytest.raises(ValueError):
        check_review(bundle, bundle / "judgments.jsonl", bundle / "queries.jsonl", output)
    assert not output.exists()


def test_pool_cli(experiment: Path, bundle: Path):
    cli = CliRunner().invoke(
        app,
        [
            "pool",
            "--config",
            str(experiment),
            "--run",
            str(experiment.parent / "run"),
            "--depth",
            "1",
            "--output",
            str(bundle.parent / "cli-pool"),
        ],
    )
    assert cli.exit_code == 0, cli.output
    assert "all reviews pending" in cli.output
