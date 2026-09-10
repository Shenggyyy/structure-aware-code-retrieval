"""Browser startup stays local, lazy and free of paid execution flags."""

import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import time
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
               'fastapi', 'uvicorn', 'torch', 'sentence_transformers'):
    assert module not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX SIGTERM lifecycle is covered on Linux CI"
)
def test_cli_process_starts_from_another_directory_and_handles_sigterm(tmp_path):
    from structure_aware_retrieval.workbench.server import create_server

    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    workspace = tmp_path / "workspace"
    environment = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "structure_aware_retrieval",
            "workbench",
            "serve",
            "--workspace",
            str(workspace),
            "--model-cache",
            str(tmp_path / "unused-model-cache"),
            "--port",
            str(port),
        ],
        cwd=tmp_path,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    ready = False
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and process.poll() is None:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.5)
            try:
                connection.request("GET", "/api/session")
                response = connection.getresponse()
                session = json.loads(response.read())
                ready = response.status == 200 and session["api_calls"] == 0
                if ready:
                    assert session["generation"]["key_ready"] is False
                    break
            except (OSError, http.client.HTTPException):
                time.sleep(0.05)
            finally:
                connection.close()
        assert ready, "Workbench CLI did not start its loopback HTTP listener"
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode in {0, -signal.SIGTERM}
        assert f"Workbench: http://127.0.0.1:{port}/" in stdout
        assert "Traceback" not in stdout + stderr
        with create_server(workspace) as restarted:
            assert restarted.jobs.list() == []
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
