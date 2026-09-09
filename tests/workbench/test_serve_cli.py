"""Browser startup stays local, lazy and free of paid execution flags."""

import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app

runner = CliRunner()
SERVE = "structure_aware_retrieval.workbench.server.serve"


def test_serve_forwards_local_defaults(monkeypatch):
    calls = []

    def serve(workspace, *, model_cache, port):
        calls.append((workspace, model_cache, port))

    monkeypatch.setattr(SERVE, serve)
    result = runner.invoke(app, ["workbench", "serve"])
    assert result.exit_code == 0, result.output
    assert calls == [(Path("artifacts/workbench"), Path("artifacts/models"), 8765)]


def test_serve_forwards_explicit_paths_and_port(monkeypatch, tmp_path):
    calls = []

    def serve(workspace, *, model_cache, port):
        calls.append((workspace, model_cache, port))

    monkeypatch.setattr(SERVE, serve)
    workspace = tmp_path / "history"
    cache = tmp_path / "weights"
    result = runner.invoke(
        app,
        [
            "workbench",
            "serve",
            "--workspace",
            str(workspace),
            "--model-cache",
            str(cache),
            "--port",
            "9876",
        ],
    )
    assert result.exit_code == 0, result.output
    assert calls == [(workspace, cache, 9876)]


@pytest.mark.parametrize(
    "options",
    [["--port", "0"], ["--port", "65536"], ["--host", "0.0.0.0"], ["--execute"]],
)
def test_serve_rejects_unsupported_options_before_startup(monkeypatch, options):
    monkeypatch.setattr(SERVE, lambda *a, **k: pytest.fail("server started"))
    result = runner.invoke(app, ["workbench", "serve", *options])
    assert result.exit_code == 2


def test_serve_bind_failure_is_actionable_without_traceback(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("Port already in use")

    monkeypatch.setattr(SERVE, fail)
    result = runner.invoke(app, ["workbench", "serve"])
    assert result.exit_code == 1
    assert "Error: Port already in use" in result.output
    assert "Traceback" not in result.output


def test_serve_help_does_not_load_backends_or_accept_model_credentials():
    script = """
import sys
from typer.testing import CliRunner
from structure_aware_retrieval.cli import app
result = CliRunner().invoke(app, ['workbench', 'serve', '--help'])
assert result.exit_code == 0, result.output
for flag in ('--workspace', '--model-cache', '--port'):
    assert flag in result.output
for flag in ('--host', '--execute', '--api-key', '--answer-model', '--budget-usd'):
    assert flag not in result.output
for module in ('structure_aware_retrieval.workbench.server',
               'structure_aware_retrieval.workbench.comparison',
               'structure_aware_retrieval.workbench.preparation',
               'torch', 'sentence_transformers'):
    assert module not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
