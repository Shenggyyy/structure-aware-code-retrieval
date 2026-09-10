"""Check packaged workbench assets over real HTTP in an isolated, offline process."""

import argparse
import http.client
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


def _worker(require_installed: bool) -> dict:
    from fastapi import FastAPI

    import structure_aware_retrieval
    from structure_aware_retrieval.workbench.server import create_server

    installed = (
        Path(structure_aware_retrieval.__file__)
        .resolve()
        .is_relative_to(Path(sys.prefix).resolve())
    )
    if require_installed and not installed:
        raise AssertionError("Expected a noneditable package under the Python environment")

    workspace = Path.cwd() / "workspace"
    instance = create_server(workspace, model_cache=Path.cwd() / "models")
    thread = threading.Thread(target=instance.serve_forever)
    thread.start()

    def get(path: str, **headers):
        connection = http.client.HTTPConnection("127.0.0.1", instance.server_port, timeout=2)
        try:
            connection.request("GET", path, headers=headers)
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                status, body, _ = get("/api/session")
                assert status == 200
                session = json.loads(body)
                break
            except (OSError, http.client.HTTPException):
                if time.monotonic() >= deadline or not thread.is_alive():
                    raise
                time.sleep(0.05)

        assert isinstance(instance.app, FastAPI)
        routes = {route.path for route in instance.app.routes}
        assert {"/", "/api/session", "/api/import", "/api/preview", "/api/history"} <= routes
        assert instance.server_address[0] == "127.0.0.1"
        assert session["mode"] == "context_preview" and session["api_calls"] == 0
        assert not session["generation"]["key_ready"]

        assets = {
            "/": (b"<!doctype html>", "text/html"),
            "/app.css": (b":root", "text/css"),
            "/app.js": (b"use strict", "text/javascript"),
            "/i18n.js": (b"WorkbenchI18n", "text/javascript"),
        }
        for path, (marker, content_type) in assets.items():
            status, body, headers = get(path)
            headers = {key.lower(): value for key, value in headers.items()}
            assert status == 200 and marker.lower() in body.lower(), path
            assert headers["content-type"].startswith(content_type), path
            assert headers["cache-control"] == "no-store"
            assert headers["x-content-type-options"] == "nosniff"
            assert "default-src 'none'" in headers["content-security-policy"]
        assert json.loads(get("/api/history")[1]) == []
        assert get("/api/session", Host="untrusted.invalid")[0] == 403
        assert get("/api/session", Origin="https://untrusted.invalid")[0] == 403
        assert get("/missing")[0] == 404
        assert get("/docs")[0] == 404
        assert get("/openapi.json")[0] == 404
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=10)
        assert not thread.is_alive(), "Workbench failed to stop"

    # Closing releases the workspace lock; reopening starts no generation or jobs.
    reopened = create_server(workspace, model_cache=Path.cwd() / "models")
    reopened.server_close()
    return {
        "status": "passed",
        "backend": "FastAPI / Uvicorn",
        "noneditable_installation": installed,
        "packaged_assets": list(assets),
        "checks": ["routes", "session", "empty_history", "access_boundaries", "shutdown", "reopen"],
        "model_api_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-installed", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(_worker(args.require_installed), indent=2))
        return

    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"OPENAI_API_KEY", "PYTHONPATH", "PYTHONHOME"}
    }
    environment.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryDirectory(prefix="sacr-http-smoke-") as scratch:
        help_result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "structure_aware_retrieval",
                "workbench",
                "serve",
                "--help",
            ],
            cwd=scratch,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
            check=True,
        )
        assert all(name in help_result.stdout for name in ("workspace", "model-cache", "port"))
        command = [sys.executable, "-I", str(Path(__file__).resolve()), "--worker"]
        if args.require_installed:
            command.append("--require-installed")
        subprocess.run(command, cwd=scratch, env=environment, timeout=40, check=True)


if __name__ == "__main__":
    main()
