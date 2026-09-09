"""Workbench CLI contracts remain explicit, durable and free of generation flags."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app

runner = CliRunner()
REPOSITORY_ID = "a" * 64
RUN_ID = "b" * 32
MODULE = "structure_aware_retrieval.workbench."


def _manifest():
    return {
        "repository_id": REPOSITORY_ID,
        "source": {
            "location": "local/source",
            "commit": "c" * 40,
            "working_tree": True,
        },
        "files": [{"path": "example.py", "sha256": "unchanged"}],
    }


def _preparation(status="ready"):
    return {
        "repository_id": REPOSITORY_ID,
        "status": status,
        "stages": {
            "index": {"status": "ready", "error": None},
            "vectors": {
                "status": "ready" if status == "ready" else "failed",
                "error": None if status == "ready" else "Local model cache unavailable",
            },
            "graph": {"status": "ready", "error": None},
        },
    }


def _comparison(status="preview_complete"):
    return {
        "run_id": RUN_ID,
        "repository_id": REPOSITORY_ID,
        "status": status,
        "question": "Where is the checksum calculated?",
        "mode": "context_preview",
        "api_calls": 0,
        "results": [
            {
                "strategy": strategy,
                "status": "failed" if strategy == "dense" and status == "partial" else "preview",
                "hits": [{"chunk_id": "source-one", "code": "def checksum(): pass"}],
                "error": {"type": "ValueError", "message": "No vectors"}
                if strategy == "dense" and status == "partial"
                else None,
            }
            for strategy in ("bm25", "dense", "hybrid", "symbol", "structure")
        ],
    }


def test_import_forwards_source_defaults_and_reports_provenance(monkeypatch):
    calls = []

    def import_repository(source, workspace, *, ref):
        calls.append((source, workspace, ref))
        return _manifest()

    monkeypatch.setattr(MODULE + "importing.import_repository", import_repository)
    result = runner.invoke(app, ["workbench", "import", "local/source"])
    assert result.exit_code == 0, result.output
    assert calls == [("local/source", Path("artifacts/workbench"), "HEAD")]
    assert REPOSITORY_ID in result.output
    assert "c" * 40 in result.output
    assert "current local files" in result.output
    assert "API calls: 0" in result.output
    assert "manifest.json" in result.output


def test_import_remote_ref_and_json_preserve_manifest(monkeypatch, tmp_path):
    calls = []
    manifest = _manifest()
    manifest["source"]["working_tree"] = False

    def import_repository(source, workspace, *, ref):
        calls.append((source, workspace, ref))
        return manifest

    monkeypatch.setattr(MODULE + "importing.import_repository", import_repository)
    source = "https://example.com/owner/project.git"
    result = runner.invoke(
        app,
        ["workbench", "import", source, "--ref", "v1.0", "--workspace", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0, result.output
    assert calls == [(source, tmp_path, "v1.0")]
    assert json.loads(result.output) == manifest


def test_import_without_git_commit_has_clear_output(monkeypatch):
    manifest = _manifest()
    manifest["source"]["commit"] = None
    monkeypatch.setattr(MODULE + "importing.import_repository", lambda *a, **k: manifest)
    result = runner.invoke(app, ["workbench", "import", "local/source"])
    assert result.exit_code == 0
    assert "Commit: unavailable" in result.output


def test_prepare_forwards_defaults_and_reports_each_stage(monkeypatch):
    calls = []

    def prepare_repository(workspace, repository_id, *, model_cache):
        calls.append((workspace, repository_id, model_cache))
        return _preparation()

    monkeypatch.setattr(MODULE + "preparation.prepare_repository", prepare_repository)
    result = runner.invoke(app, ["workbench", "prepare", REPOSITORY_ID])
    assert result.exit_code == 0, result.output
    assert calls == [(Path("artifacts/workbench"), REPOSITORY_ID, Path("artifacts/models"))]
    for stage in ("index", "vectors", "graph"):
        assert f"{stage}: ready" in result.output
    assert "manifest.json" in result.output
    assert "API calls: 0" in result.output


@pytest.mark.parametrize("status", ["ready", "partial", "failed"])
def test_prepare_json_preserves_outcome_before_exit(monkeypatch, tmp_path, status):
    record = _preparation(status)
    calls = []

    def prepare_repository(workspace, repository_id, *, model_cache):
        calls.append((workspace, repository_id, model_cache))
        return record

    monkeypatch.setattr(MODULE + "preparation.prepare_repository", prepare_repository)
    cache = tmp_path / "model"
    result = runner.invoke(
        app,
        [
            "workbench",
            "prepare",
            REPOSITORY_ID,
            "--workspace",
            str(tmp_path),
            "--model-cache",
            str(cache),
            "--json",
        ],
    )
    assert result.exit_code == (0 if status == "ready" else 1)
    assert calls == [(tmp_path, REPOSITORY_ID, cache)]
    assert json.loads(result.output) == record


def test_prepare_failure_keeps_stage_reason_and_saved_location(monkeypatch):
    monkeypatch.setattr(
        MODULE + "preparation.prepare_repository", lambda *a, **k: _preparation("partial")
    )
    result = runner.invoke(app, ["workbench", "prepare", REPOSITORY_ID])
    assert result.exit_code == 1
    assert "index: ready" in result.output
    assert "vectors: failed; Local model cache unavailable" in result.output
    assert "manifest.json" in result.output


def test_preview_forwards_defaults_and_describes_all_strategies(monkeypatch):
    calls = []

    def preview_question(workspace, repository_id, question, **options):
        calls.append((workspace, repository_id, question, options))
        return _comparison()

    monkeypatch.setattr(MODULE + "comparison.preview_question", preview_question)
    result = runner.invoke(app, ["workbench", "preview", REPOSITORY_ID, "checksum"])
    assert result.exit_code == 0, result.output
    assert calls == [
        (
            Path("artifacts/workbench"),
            REPOSITORY_ID,
            "checksum",
            {"model_cache": Path("artifacts/models"), "top_k": 10, "max_context_bytes": 16000},
        )
    ]
    assert "context_preview; API calls: 0" in result.output
    for strategy in ("bm25", "dense", "hybrid", "symbol", "structure"):
        assert f"{strategy}: preview" in result.output
    assert RUN_ID in result.output
    assert "run.json" in result.output


@pytest.mark.parametrize("status", ["preview_complete", "partial", "failed"])
def test_preview_json_preserves_all_results_before_exit(monkeypatch, tmp_path, status):
    record = _comparison(status)
    calls = []

    def preview_question(workspace, repository_id, question, **options):
        calls.append((workspace, repository_id, question, options))
        return record

    monkeypatch.setattr(MODULE + "comparison.preview_question", preview_question)
    cache = tmp_path / "model"
    result = runner.invoke(
        app,
        [
            "workbench",
            "preview",
            REPOSITORY_ID,
            "checksum",
            "--workspace",
            str(tmp_path),
            "--model-cache",
            str(cache),
            "--top-k",
            "4",
            "--max-context-bytes",
            "9000",
            "--json",
        ],
    )
    assert result.exit_code == (0 if status == "preview_complete" else 1)
    assert calls == [
        (
            tmp_path,
            REPOSITORY_ID,
            "checksum",
            {"model_cache": cache, "top_k": 4, "max_context_bytes": 9000},
        )
    ]
    assert json.loads(result.output) == record


def test_preview_partial_exposes_failure_without_hiding_other_results(monkeypatch):
    monkeypatch.setattr(
        MODULE + "comparison.preview_question", lambda *a, **k: _comparison("partial")
    )
    result = runner.invoke(app, ["workbench", "preview", REPOSITORY_ID, "checksum"])
    assert result.exit_code == 1
    assert "dense: failed" in result.output
    assert "ValueError: No vectors" in result.output
    assert "bm25: preview" in result.output
    assert "run.json" in result.output


def test_history_lists_saved_and_damaged_records_without_retrieval(monkeypatch, tmp_path):
    records = [
        {
            "run_id": RUN_ID,
            "repository_id": REPOSITORY_ID,
            "question": "checksum",
            "status": "partial",
        },
        {
            "run_id": "d" * 32,
            "status": "unreadable",
            "error": {"type": "ValueError", "message": "Bad fingerprint"},
        },
    ]
    calls = []

    def list_comparisons(workspace):
        calls.append(workspace)
        return records

    monkeypatch.setattr(MODULE + "comparison.list_comparisons", list_comparisons)
    monkeypatch.setattr(
        MODULE + "comparison.preview_question", lambda *a, **k: pytest.fail("rerun")
    )
    result = runner.invoke(app, ["workbench", "history", "--workspace", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert calls == [tmp_path]
    assert "partial" in result.output
    assert "unreadable | ValueError: Bad fingerprint" in result.output
    result = runner.invoke(app, ["workbench", "history", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output) == records


def test_history_handles_empty_workspace(monkeypatch):
    monkeypatch.setattr(MODULE + "comparison.list_comparisons", lambda *a: [])
    result = runner.invoke(app, ["workbench", "history"])
    assert result.exit_code == 0
    assert "No saved comparisons." in result.output


@pytest.mark.parametrize("as_json", [False, True])
def test_show_reads_saved_partial_run_without_rerunning(monkeypatch, tmp_path, as_json):
    record = _comparison("partial")
    calls = []

    def load_comparison(workspace, run_id):
        calls.append((workspace, run_id))
        return record

    monkeypatch.setattr(MODULE + "comparison.load_comparison", load_comparison)
    monkeypatch.setattr(
        MODULE + "comparison.preview_question", lambda *a, **k: pytest.fail("rerun")
    )
    args = ["workbench", "show", RUN_ID, "--workspace", str(tmp_path)]
    result = runner.invoke(app, [*args, "--json"] if as_json else args)
    assert result.exit_code == 0, result.output
    assert calls == [(tmp_path, RUN_ID)]
    if as_json:
        assert json.loads(result.output) == record
    else:
        assert "partial" in result.output
        assert "ValueError: No vectors" in result.output


@pytest.mark.parametrize(
    ("arguments", "function", "error"),
    [
        (["import", "source"], "importing.import_repository", OSError("Unreadable source")),
        (["prepare", REPOSITORY_ID], "preparation.prepare_repository", ValueError("Unknown repo")),
        (
            ["preview", REPOSITORY_ID, "q"],
            "comparison.preview_question",
            sqlite3.Error("Bad index"),
        ),
        (["history"], "comparison.list_comparisons", OSError("Unreadable workspace")),
        (["show", RUN_ID], "comparison.load_comparison", ValueError("Unknown run")),
    ],
)
def test_command_errors_are_clear_without_tracebacks(monkeypatch, arguments, function, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(MODULE + function, fail)
    result = runner.invoke(app, ["workbench", *arguments])
    assert result.exit_code == 1
    assert f"Error: {error}" in result.output
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    "options",
    [["--top-k", "0"], ["--top-k", "101"], ["--max-context-bytes", "1"], ["--execute"]],
)
def test_preview_rejects_invalid_or_generation_options_before_backend(monkeypatch, options):
    monkeypatch.setattr(
        MODULE + "comparison.preview_question", lambda *a, **k: pytest.fail("backend called")
    )
    result = runner.invoke(app, ["workbench", "preview", REPOSITORY_ID, "question", *options])
    assert result.exit_code == 2


@pytest.mark.parametrize("command", ["import", "prepare", "preview", "history", "show"])
def test_workbench_help_has_no_paid_execution_options(command):
    result = runner.invoke(app, ["workbench", command, "--help"])
    assert result.exit_code == 0
    assert "--json" in result.output
    for flag in ("--execute", "--api-key", "--budget-usd", "--answer-model"):
        assert flag not in result.output


def test_command_discovery_does_not_import_retrieval_or_model_backends():
    script = """
import sys
from typer.testing import CliRunner
from structure_aware_retrieval.cli import app
result = CliRunner().invoke(app, ['workbench', '--help'])
assert result.exit_code == 0, result.output
assert 'structure_aware_retrieval.workbench.comparison' not in sys.modules
assert 'structure_aware_retrieval.workbench.preparation' not in sys.modules
assert 'structure_aware_retrieval.workbench.importing' not in sys.modules
assert 'torch' not in sys.modules
assert 'sentence_transformers' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
