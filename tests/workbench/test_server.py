"""HTTP-level offline tests for the single-user browser boundary and service reuse."""

import http.client
import json
import socket
import threading
import time
from contextlib import contextmanager

import numpy as np
import pytest

from structure_aware_retrieval.strategies import STRATEGIES
from structure_aware_retrieval.workbench import comparison, jobs, preparation, server, storage
from structure_aware_retrieval.workbench.storage import read_json, write_json


class FixtureEncoder:
    spec = {"id": "synthetic", "revision": "web-test", "dimensions": 2, "max_seq_length": 256}

    def encode(self, texts):
        return np.asarray(
            [[1.0, 0.0] if "checksum" in text else [0.0, 1.0] for text in texts], dtype=np.float32
        ).reshape(-1, 2)

    def token_lengths(self, texts):
        return [len(text.split()) for text in texts]


@contextmanager
def running(workspace):
    instance = server.create_server(workspace)
    thread = threading.Thread(target=instance.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    try:
        yield instance
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def request(instance, path, *, method="GET", payload=None, headers=None, body=None):
    connection = http.client.HTTPConnection("127.0.0.1", instance.server_port, timeout=10)
    if body is None and payload is not None:
        body = json.dumps(payload).encode()
    selected = {}
    if method == "POST":
        selected.update(
            {
                "Origin": instance.origin,
                "X-Workbench-Token": instance.csrf_token,
                "Content-Type": "application/json",
            }
        )
    selected.update(headers or {})
    selected = {key: value for key, value in selected.items() if value is not None}
    try:
        connection.request(method, path, body=body, headers=selected)
        response = connection.getresponse()
        data = response.read()
        value = (
            json.loads(data)
            if "application/json" in response.getheader("Content-Type", "")
            else data
        )
        return response.status, value, response.headers
    finally:
        connection.close()


def job(instance, path, payload):
    status, submitted, _ = request(instance, path, method="POST", payload=payload)
    assert status == 202, submitted
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        status, record, _ = request(instance, f"/api/jobs/{submitted['job_id']}")
        assert status == 200
        if record["status"] in {"completed", "failed", "interrupted"}:
            return record
        time.sleep(0.01)
    pytest.fail("Background job did not complete")


@pytest.fixture
def injected(monkeypatch):
    encoder = FixtureEncoder()
    events = []

    def prepare(*args, on_progress=None, **kwargs):
        def progress(detail):
            events.append(("prepare", detail))
            on_progress(detail)

        return preparation.prepare_repository(
            *args, encoder=encoder, on_progress=progress, **kwargs
        )

    def preview(*args, on_progress=None, **kwargs):
        def progress(detail):
            events.append(("preview", detail))
            on_progress(detail)

        return comparison.preview_question(*args, encoder=encoder, on_progress=progress, **kwargs)

    monkeypatch.setattr(jobs, "prepare_repository", prepare)
    monkeypatch.setattr(jobs, "preview_question", preview)
    return events


def test_http_import_prepares_five_real_strategies_and_reopens_after_restart(
    sample_repository, tmp_path, injected
):
    workspace = tmp_path / "w"
    with running(workspace) as instance:
        assert instance.server_address[0] == "127.0.0.1"
        status, session, _ = request(instance, "/api/session")
        assert status == 200 and session["mode"] == "context_preview" and session["api_calls"] == 0
        imported = job(instance, "/api/import", {"source": str(sample_repository)})
        assert imported["status"] == "completed"
        resources = imported["result"]["preparation"]
        assert resources["status"] == "ready"
        repository_id = imported["result"]["repository_id"]
        rows = request(instance, "/api/repositories")[1]
        assert rows[0]["repository_id"] == repository_id
        assert rows[0]["file_count"] > 0 and rows[0]["status"] == "ready"
        reused = job(instance, "/api/prepare", {"repository_id": repository_id})
        assert all(
            stage["status"] == "reused"
            for stage in reused["result"]["preparation"]["stages"].values()
        )
        preview = job(
            instance,
            "/api/preview",
            {"repository_id": repository_id, "question": "checksum payload", "top_k": 2},
        )
        assert (
            preview["status"] == "completed" and preview["result"]["status"] == "preview_complete"
        )
        run_id = preview["result"]["run_id"]
        status, saved, _ = request(instance, f"/api/runs/{run_id}")
        assert status == 200 and saved["api_calls"] == 0
        assert saved["benchmark_metrics"] is None and saved["relevance_labels"] == "unlabeled"
        assert [row["strategy"] for row in saved["results"]] == list(STRATEGIES)
        for row in saved["results"]:
            assert row["status"] == "preview" and row["qa"]["answer"] is None
            assert row["qa"]["automatic_checks"]["paths_valid"] is True
            assert row["hits"][0]["path"] and row["hits"][0]["start_line"] >= 1
            assert row["timing_ms"]["retrieval"] >= 0
            assert row["timing_ms"]["generation"] is None
            assert all(value is None for value in row["tokens"].values())
            assert row["cost"]["estimated_usd"] is None
        assert request(instance, "/api/history")[1][0]["run_id"] == run_id
        assert len(request(instance, "/api/jobs")[1]) == 3
        previous_token = session["csrf_token"]
    with running(workspace) as restarted:
        assert restarted.csrf_token != previous_token
        assert request(restarted, f"/api/runs/{run_id}")[1] == saved
        assert request(restarted, "/api/jobs")[1][0]["status"] == "completed"
    assert any(
        detail["stages"]["index"]["status"] == "running"
        for phase, detail in injected
        if phase == "prepare"
    )
    assert any(
        detail["results"][0]["status"] == "running"
        for phase, detail in injected
        if phase == "preview"
    )


def test_partial_preview_keeps_other_strategies_and_the_failure(
    sample_repository, tmp_path, injected, monkeypatch
):
    original = comparison.create_retriever

    def fail(strategy, *args, **kwargs):
        if strategy == "dense":
            raise ValueError("Synthetic dense failure")
        return original(strategy, *args, **kwargs)

    monkeypatch.setattr(comparison, "create_retriever", fail)
    with running(tmp_path / "w") as instance:
        imported = job(instance, "/api/import", {"source": str(sample_repository)})
        preview = job(
            instance,
            "/api/preview",
            {"repository_id": imported["result"]["repository_id"], "question": "checksum"},
        )
        assert preview["status"] == "completed" and preview["result"]["status"] == "partial"
        saved = request(instance, f"/api/runs/{preview['result']['run_id']}")[1]
        assert [row["status"] for row in saved["results"]] == [
            "preview",
            "failed",
            "preview",
            "preview",
            "preview",
        ]
        assert saved["results"][1]["qa"] is None and saved["results"][1]["error"]


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "localhost:8765"},
        {"Host": "evil.example"},
        {"Origin": "https://evil.example"},
        {"Origin": "null"},
        {"Sec-Fetch-Site": "cross-site"},
    ],
)
def test_get_rejects_foreign_host_origin_and_cross_site(tmp_path, headers):
    with running(tmp_path / "w") as instance:
        status, value, output = request(instance, "/api/session", headers=headers)
        assert status == 403 and "csrf_token" not in value
        assert "Access-Control-Allow-Origin" not in output


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": None},
        {"Origin": "https://evil.example"},
        {"X-Workbench-Token": None},
        {"X-Workbench-Token": "bad"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Host": "example.com"},
    ],
)
def test_post_requires_same_origin_and_current_session(tmp_path, headers):
    with running(tmp_path / "w") as instance:
        status, _, _ = request(
            instance, "/api/import", method="POST", payload={"source": "."}, headers=headers
        )
        assert status == 403
        assert request(instance, "/api/jobs")[1] == []


@pytest.mark.parametrize(
    "path",
    [
        "/../pyproject.toml",
        "/%2e%2e/pyproject.toml",
        "/static/index.html",
        "/app.js?x=1",
        "/api/files/secret",
        "/api/generate",
        "/api/assess",
        "/api/runs/../../secret",
        "/api/jobs/..",
    ],
)
def test_no_arbitrary_files_or_paid_routes(tmp_path, path):
    with running(tmp_path / "w") as instance:
        assert request(instance, path)[0] in {400, 404}


@pytest.mark.parametrize(
    ("payload", "path"),
    [
        ({"source": ""}, "/api/import"),
        ({"source": ".", "api_key": "not-a-real-key"}, "/api/import"),
        ({"source": ".", "ref": []}, "/api/import"),
        ({"repository_id": "../x"}, "/api/prepare"),
        ({"repository_id": "a" * 64, "question": ""}, "/api/preview"),
        ({"repository_id": "a" * 64, "question": "问" * 1400}, "/api/preview"),
        ({"repository_id": "a" * 64, "question": "x", "top_k": True}, "/api/preview"),
        ({"repository_id": "a" * 64, "question": "x", "max_context_bytes": 1}, "/api/preview"),
        ({"source": "\ud800"}, "/api/import"),
    ],
)
def test_invalid_payload_is_rejected_before_task_creation(tmp_path, payload, path):
    with running(tmp_path / "w") as instance:
        assert request(instance, path, method="POST", payload=payload)[0] == 400
        assert request(instance, "/api/jobs")[1] == []


@pytest.mark.parametrize(
    ("body", "headers", "status"),
    [
        (b"not json", {}, 400),
        (b"[]", {}, 400),
        (b'{"source":".","source":"elsewhere"}', {}, 400),
        (b"{}", {"Content-Type": "text/plain"}, 415),
        (b"x" * 16385, {}, 413),
        (b"{}", {"Transfer-Encoding": "chunked"}, 400),
        (b"{}", {"Content-Length": "x"}, 400),
        (b"{}", {"Content-Length": "9" * 100}, 413),
        (b"\xff", {}, 400),
    ],
)
def test_bad_json_and_bounded_body(tmp_path, body, headers, status):
    with running(tmp_path / "w") as instance:
        assert (
            request(instance, "/api/import", method="POST", body=body, headers=headers)[0] == status
        )


def test_only_one_task_can_run_and_refresh_observes_progress(tmp_path, monkeypatch):
    entered, release = threading.Event(), threading.Event()

    def blocked(source, workspace, *, ref, on_progress):
        on_progress({"status": "downloading"})
        entered.set()
        assert release.wait(timeout=10)
        raise ValueError("Synthetic download failed")

    monkeypatch.setattr(jobs, "import_repository", blocked)
    with running(tmp_path / "w") as instance:
        first = request(instance, "/api/import", method="POST", payload={"source": "."})[1]
        assert entered.wait(timeout=5)
        status, busy, _ = request(instance, "/api/import", method="POST", payload={"source": "."})
        assert status == 409 and busy["job_id"] == first["job_id"]
        record = request(instance, f"/api/jobs/{first['job_id']}")[1]
        assert record["progress"] == {"phase": "import", "detail": {"status": "downloading"}}
        release.set()
        deadline = time.monotonic() + 5
        while instance.jobs.active is not None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert request(instance, f"/api/jobs/{first['job_id']}")[1]["status"] == "failed"


def test_stale_jobs_are_interrupted_and_corrupt_jobs_are_preserved(tmp_path):
    workspace = tmp_path / "w"
    unfinished = {"schema_version": 1, "job_id": "a" * 32, "kind": "preview", "status": "running"}
    write_json(workspace, f"web-jobs/{'a' * 32}.json", unfinished)
    write_json(workspace, f"web-jobs/{'b' * 32}.json", {"bad": "record"})
    with running(workspace) as instance:
        rows = request(instance, "/api/jobs")[1]
        assert {row["status"] for row in rows} == {"interrupted", "unreadable"}
        assert "no automatic retry" in request(instance, f"/api/jobs/{'a' * 32}")[1]["error"]
        assert request(instance, f"/api/jobs/{'b' * 32}")[0] == 422
        assert request(instance, f"/api/jobs/{'c' * 32}")[0] == 404
    assert read_json(workspace, f"web-jobs/{'b' * 32}.json") == {"bad": "record"}


def test_restart_reconciles_linked_running_resources_and_preview(
    tmp_path, sample_repository, injected
):
    workspace = tmp_path / "w"
    with running(workspace) as instance:
        imported = job(instance, "/api/import", {"source": str(sample_repository)})
        repository_id = imported["result"]["repository_id"]
        preview = job(
            instance, "/api/preview", {"repository_id": repository_id, "question": "checksum"}
        )
    unfinished_preparation = next(
        detail
        for phase, detail in injected
        if phase == "prepare" and detail["stages"]["graph"]["status"] == "running"
    )
    unfinished_preview = next(
        detail
        for phase, detail in injected
        if phase == "preview" and detail["results"][0]["status"] == "running"
    )
    write_json(workspace, f"resources/{repository_id}/manifest.json", unfinished_preparation)
    write_json(workspace, f"runs/{unfinished_preview['run_id']}/run.json", unfinished_preview)
    imported.update(
        status="running", progress={"phase": "prepare", "detail": unfinished_preparation}
    )
    preview.update(
        status="interrupted",
        progress={"phase": "preview", "detail": {"run_id": unfinished_preview["run_id"]}},
    )
    write_json(workspace, f"web-jobs/{imported['job_id']}.json", imported)
    write_json(workspace, f"web-jobs/{preview['job_id']}.json", preview)
    with running(workspace) as instance:
        saved = request(instance, f"/api/runs/{unfinished_preview['run_id']}")[1]
        assert saved["status"] == "interrupted" and saved["finished_at"]
        assert saved["results"][0]["status"] == "interrupted"
        assert all(row["status"] != "running" for row in saved["results"])
        resources = preparation.load_preparation(workspace, repository_id)
        assert resources["status"] == "interrupted"
        assert resources["stages"]["graph"]["status"] == "interrupted"
        assert resources["stages"]["index"]["status"] == "ready"
        assert all(row["status"] == "interrupted" for row in request(instance, "/api/jobs")[1])
        assert request(instance, "/api/repositories")[1][0]["status"] == "interrupted"

    # Graceful service shutdown may already have saved interrupted archives,
    # while the web job still contains the previous running checkpoint.
    imported["status"] = "interrupted"
    preview["progress"]["detail"]["status"] = "running"
    write_json(workspace, f"web-jobs/{imported['job_id']}.json", imported)
    write_json(workspace, f"web-jobs/{preview['job_id']}.json", preview)
    with running(workspace) as instance:
        rows = request(instance, "/api/jobs")[1]
        assert all(row["progress"]["detail"]["status"] == "interrupted" for row in rows)
        assert comparison.load_comparison(workspace, saved["run_id"]) == saved
        assert preparation.load_preparation(workspace, repository_id) == resources


def test_restart_syncs_finished_linked_archives_without_rewriting_them(
    tmp_path, sample_repository, injected
):
    workspace = tmp_path / "w"
    with running(workspace) as instance:
        imported = job(instance, "/api/import", {"source": str(sample_repository)})
        repository_id = imported["result"]["repository_id"]
        preview = job(
            instance, "/api/preview", {"repository_id": repository_id, "question": "checksum"}
        )
    imported.update(
        status="interrupted",
        progress={
            "phase": "prepare",
            "detail": {"repository_id": repository_id, "status": "preparing"},
        },
    )
    preview.update(
        status="interrupted",
        progress={
            "phase": "preview",
            "detail": {"run_id": preview["result"]["run_id"], "status": "running"},
        },
    )
    write_json(workspace, f"web-jobs/{imported['job_id']}.json", imported)
    write_json(workspace, f"web-jobs/{preview['job_id']}.json", preview)
    import_archive = next((workspace / "jobs").glob("*.json"))
    write_json(
        workspace,
        f"web-jobs/{'a' * 32}.json",
        {
            "schema_version": 1,
            "job_id": "a" * 32,
            "kind": "import",
            "status": "interrupted",
            "progress": {
                "phase": "import",
                "detail": {"job_id": import_archive.stem, "status": "downloading"},
            },
        },
    )
    archives = [
        import_archive,
        workspace / f"resources/{repository_id}/manifest.json",
        workspace / f"runs/{preview['result']['run_id']}/run.json",
    ]
    before = [path.read_bytes() for path in archives]
    with running(workspace) as instance:
        rows = request(instance, "/api/jobs")[1]
        assert {row["progress"]["phase"]: row["progress"]["detail"]["status"] for row in rows} == {
            "import": "completed",
            "prepare": "ready",
            "preview": "preview_complete",
        }
    assert [path.read_bytes() for path in archives] == before


def test_restart_syncs_already_interrupted_import_progress(tmp_path):
    workspace = tmp_path / "w"
    imported = {"schema_version": 1, "job_id": "a" * 32, "status": "interrupted", "events": []}
    write_json(workspace, f"jobs/{'a' * 32}.json", imported)
    write_json(
        workspace,
        f"web-jobs/{'b' * 32}.json",
        {
            "schema_version": 1,
            "job_id": "b" * 32,
            "kind": "import",
            "status": "interrupted",
            "progress": {
                "phase": "import",
                "detail": {"job_id": "a" * 32, "status": "downloading"},
            },
        },
    )
    with running(workspace) as instance:
        assert request(instance, "/api/jobs")[1][0]["progress"]["detail"] == imported
    assert read_json(workspace, f"jobs/{'a' * 32}.json") == imported


def test_restart_preserves_corrupt_linked_archive_and_reports_warning(tmp_path):
    workspace = tmp_path / "w"
    write_json(workspace, f"runs/{'a' * 32}/run.json", {"corrupt": True})
    write_json(
        workspace,
        f"web-jobs/{'b' * 32}.json",
        {
            "schema_version": 1,
            "job_id": "b" * 32,
            "kind": "preview",
            "status": "running",
            "progress": {"phase": "preview", "detail": {"run_id": "a" * 32}},
        },
    )
    with running(workspace) as instance:
        row = request(instance, "/api/jobs")[1][0]
        assert row["status"] == "interrupted" and row["recovery_warning"]
    assert read_json(workspace, f"runs/{'a' * 32}/run.json") == {"corrupt": True}


@pytest.mark.parametrize(
    ("path", "content_type"),
    [
        ("/", "text/html"),
        ("/app.js", "text/javascript"),
        ("/i18n.js", "text/javascript"),
        ("/app.css", "text/css"),
    ],
)
def test_only_packaged_browser_assets_are_served(tmp_path, path, content_type):
    with running(tmp_path / "w") as instance:
        status, data, headers = request(instance, path)
        assert status == 200 and data
        assert headers["Content-Type"].startswith(content_type)


def test_workspace_lock_prevents_two_servers_and_releases_on_close(tmp_path):
    workspace = tmp_path / "w"
    with server.create_server(workspace) as first:
        with pytest.raises(ValueError, match="Another browser server"):
            server.create_server(workspace)
        assert first.server_address[0] == "127.0.0.1"
    with server.create_server(workspace) as second:
        assert second.server_port > 0


def test_close_retains_workspace_lock_until_background_worker_stops(tmp_path, monkeypatch):
    workspace = tmp_path / "w"
    entered, release = threading.Event(), threading.Event()

    def blocked(source, workspace, *, ref, on_progress):
        entered.set()
        assert release.wait(timeout=10)
        on_progress({"status": "snapshotting"})
        pytest.fail("A stopped server must interrupt the next saved checkpoint")

    monkeypatch.setattr(jobs, "import_repository", blocked)
    instance = server.create_server(workspace)
    submitted = instance.jobs.submit("import", {"source": "."})
    try:
        assert entered.wait(timeout=5)
        instance.server_close()
        assert (
            read_json(workspace, f"web-jobs/{submitted['job_id']}.json")["status"] == "interrupted"
        )
        with pytest.raises(ValueError, match="Another browser server"):
            server.create_server(workspace)
    finally:
        release.set()
    deadline = time.monotonic() + 5
    while instance.jobs.active is not None and time.monotonic() < deadline:
        time.sleep(0.01)
    with server.create_server(workspace) as restarted:
        assert restarted.jobs.list()[0]["status"] == "interrupted"


def test_json_reader_does_not_collide_with_atomic_writer(tmp_path, monkeypatch):
    workspace = tmp_path / "w"
    write_json(workspace, "state.json", {"value": "before"})
    original = storage._read_json
    reading, release, writing, written = (threading.Event() for _ in range(4))

    def held_reader(*args):
        reading.set()
        assert release.wait(timeout=5)
        return original(*args)

    def writer():
        writing.set()
        write_json(workspace, "state.json", {"value": "after"})
        written.set()

    monkeypatch.setattr(storage, "_read_json", held_reader)
    reader_thread = threading.Thread(target=read_json, args=(workspace, "state.json"))
    writer_thread = threading.Thread(target=writer)
    reader_thread.start()
    assert reading.wait(timeout=5)
    writer_thread.start()
    try:
        assert writing.wait(timeout=5)
        assert not written.wait(timeout=0.05)
    finally:
        release.set()
        reader_thread.join(timeout=5)
        writer_thread.join(timeout=5)
    assert written.is_set() and read_json(workspace, "state.json") == {"value": "after"}


def test_missing_encoder_keeps_index_graph_and_bm25_preview(
    tmp_path, sample_repository, monkeypatch
):
    def missing(*args, **kwargs):
        raise ValueError("Pinned model missing; run prepare-model")

    monkeypatch.setattr(preparation, "SentenceEncoder", missing)
    with running(tmp_path / "w") as instance:
        imported = job(instance, "/api/import", {"source": str(sample_repository)})
        assert imported["status"] == "completed"
        resources = imported["result"]["preparation"]
        assert resources["status"] == "partial"
        assert resources["stages"]["index"]["status"] == "ready"
        assert resources["stages"]["vectors"]["status"] == "failed"
        assert resources["stages"]["graph"]["status"] == "ready"
        preview = job(
            instance,
            "/api/preview",
            {"repository_id": imported["result"]["repository_id"], "question": "checksum"},
        )
        saved = request(instance, f"/api/runs/{preview['result']['run_id']}")[1]
        assert saved["status"] == "partial" and saved["results"][0]["status"] == "preview"
        assert all(row["status"] == "failed" for row in saved["results"][1:])


def test_rejected_source_credentials_do_not_enter_job_error(tmp_path):
    with running(tmp_path / "w") as instance:
        record = job(
            instance,
            "/api/import",
            {"source": "https://user:secret-test-marker@example.com/repo.git"},
        )
        assert record["status"] == "failed"
        assert "secret-test-marker" not in json.dumps(record)


def test_invalid_repository_and_preparation_remain_visible(tmp_path, sample_repository, injected):
    workspace = tmp_path / "w"
    with running(workspace) as instance:
        imported = job(instance, "/api/import", {"source": str(sample_repository)})
        repository_id = imported["result"]["repository_id"]
        write_json(workspace, f"resources/{repository_id}/manifest.json", {"bad": True})
        write_json(workspace, f"repositories/{'a' * 64}/manifest.json", {"bad": True})
        rows = request(instance, "/api/repositories")[1]
        assert len(rows) == 2 and all(row["status"] == "unreadable" for row in rows)


def test_security_headers_and_no_request_content_logging(tmp_path, capsys):
    with running(tmp_path / "w") as instance:
        _, _, headers = request(instance, "/api/session")
        assert headers["Cache-Control"] == "no-store"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "'unsafe-inline'" not in headers["Content-Security-Policy"]
        assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
        request(instance, "/secret-request-marker")
    output = capsys.readouterr()
    assert "secret-request-marker" not in output.out + output.err


@pytest.mark.parametrize("port", [-1, 65536, True, "8765"])
def test_invalid_port_is_rejected(tmp_path, port):
    with pytest.raises(ValueError, match="Port"):
        server.create_server(tmp_path / "w", port=port)


def raw_request(instance, path, *, method="POST", headers=None, body=b"{}", omit=()):
    """Send exact header fields without a client's duplicate/framing normalization."""
    selected = [
        ("Host", instance.origin.removeprefix("http://")),
        ("Origin", instance.origin),
        ("X-Workbench-Token", instance.csrf_token),
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(body))),
    ]
    selected = [(name, value) for name, value in selected if name not in omit]
    selected.extend(headers or [])
    head = f"{method} {path} HTTP/1.1\r\n" + "".join(
        f"{name}: {value}\r\n" for name, value in selected
    )
    with socket.create_connection(("127.0.0.1", instance.server_port), timeout=10) as connection:
        connection.sendall(head.encode("ascii") + b"\r\n" + body)
        response = http.client.HTTPResponse(connection, method=method)
        response.begin()
        data = response.read()
        return response.status, data, response.headers


def assert_response_protection(headers):
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Access-Control-Allow-Origin" not in headers


@pytest.mark.parametrize(
    ("name", "value", "status"),
    [
        ("Host", "foreign.example", 403),
        ("Host", "same", 403),
        ("Origin", "https://foreign.example", 403),
        ("Origin", "same", 403),
        ("X-Workbench-Token", "other", 403),
        ("X-Workbench-Token", "same", 403),
        ("Content-Type", "application/json", 415),
        ("Content-Length", "2", 400),
        ("Content-Length", "3", 400),
        ("Transfer-Encoding", "chunked", 400),
    ],
)
def test_duplicate_headers_and_body_framing_are_not_normalized_away(tmp_path, name, value, status):
    with running(tmp_path / "w") as instance:
        if value == "same":
            value = {
                "Host": instance.origin.removeprefix("http://"),
                "Origin": instance.origin,
                "X-Workbench-Token": instance.csrf_token,
            }[name]
        received, data, headers = raw_request(instance, "/api/import", headers=[(name, value)])
        assert received == status, data
        assert_response_protection(headers)
        assert headers["Content-Type"].startswith("application/json")
        assert set(json.loads(data)) == {"error"}
        assert instance.csrf_token.encode() not in data
        assert request(instance, "/api/jobs")[1] == []


@pytest.mark.parametrize(
    "path",
    [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/session/",
        "/api/session?anything=1",
        "/api/session?",
        "/app.js?",
        "/?anything=1",
        "/%61pi/session",
        "/api/%73ession",
        "/api//session",
        "/api/import",
    ],
)
def test_framework_defaults_do_not_add_routes_or_redirects(tmp_path, path):
    with running(tmp_path / "w") as instance:
        status, value, headers = request(instance, path)
        assert status == 404 and value == {"error": "Route not found"}
        assert "Location" not in headers
        assert_response_protection(headers)


@pytest.mark.parametrize("suffix", ["/", "?x=1", "?", "/more", "%61", "%2f", ".."])
def test_saved_ids_are_validated_before_decoding_or_path_normalization(tmp_path, suffix):
    with running(tmp_path / "w") as instance:
        status, value, _ = request(instance, "/api/runs/" + "a" * 32 + suffix)
        assert status == 400
        assert value == {"error": "Invalid repository, run, or job identifier"}


@pytest.mark.parametrize("method", ["HEAD", "OPTIONS", "PUT", "DELETE", "PATCH", "TRACE"])
def test_unsupported_methods_do_not_gain_fastapi_or_cors_behavior(tmp_path, method):
    with running(tmp_path / "w") as instance:
        status, data, headers = raw_request(instance, "/api/session", method=method, body=b"")
        assert status == 501
        assert_response_protection(headers)
        if method == "HEAD":
            assert data == b""
        else:
            assert json.loads(data) == {"error": "Invalid HTTP request"}
        assert request(instance, "/api/jobs")[1] == []


def test_proxy_headers_cannot_override_local_origin(tmp_path):
    with running(tmp_path / "w") as instance:
        status, value, _ = request(
            instance,
            "/api/session",
            headers={
                "Host": "foreign.example",
                "X-Forwarded-Host": instance.origin.removeprefix("http://"),
                "X-Forwarded-For": "127.0.0.1",
                "X-Forwarded-Proto": "http",
                "Forwarded": "for=127.0.0.1;host=" + instance.origin.removeprefix("http://"),
            },
        )
        assert status == 403 and "csrf_token" not in value


def test_internal_read_failure_is_sanitized_and_does_not_break_the_server(
    tmp_path, monkeypatch, capsys, caplog
):
    def failed(*args):
        raise RuntimeError("private-repository-or-request-marker")

    monkeypatch.setattr(server, "load_comparison", failed)
    with running(tmp_path / "w") as instance:
        status, value, headers = request(instance, "/api/runs/" + "a" * 32)
        assert status == 500 and value == {"error": "Cannot read workbench data"}
        assert_response_protection(headers)
        assert request(instance, "/api/session")[0] == 200
    captured = capsys.readouterr()
    assert "private-repository-or-request-marker" not in captured.out + captured.err + caplog.text


def test_failed_socket_bind_releases_the_new_workspaces_lock(tmp_path):
    with server.create_server(tmp_path / "first") as first:
        with pytest.raises(OSError):
            server.create_server(tmp_path / "second", port=first.server_port)
        with server.create_server(tmp_path / "second") as recovered:
            assert recovered.server_port > 0


def test_shutdown_is_idempotent_and_closes_the_listener_and_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "3")
    workspace = tmp_path / "w"
    instance = server.create_server(workspace)
    assert instance._uvicorn.config.workers == 1
    thread = threading.Thread(target=instance.serve_forever)
    thread.start()
    try:
        assert request(instance, "/api/session")[0] == 200
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=5)
    assert not thread.is_alive()
    instance.shutdown()
    instance.server_close()
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", instance.server_port), timeout=0.2)
    with server.create_server(workspace) as restarted:
        assert restarted.jobs.list() == []


@pytest.mark.parametrize(
    "path",
    [
        "/api/session",
        "/api/import/",
        "/api/import?x=1",
        "/api/import?",
        "/api/%69mport",
        "/not-a-route",
    ],
)
def test_unknown_post_routes_stay_404_before_body_validation(tmp_path, path):
    with running(tmp_path / "w") as instance:
        status, data, headers = raw_request(instance, path, body=b"not JSON")
        assert status == 404 and json.loads(data) == {"error": "Route not found"}
        assert "Location" not in headers
        assert_response_protection(headers)
        assert request(instance, "/api/jobs")[1] == []


@pytest.mark.parametrize(
    ("headers", "status"),
    [
        ([], 400),
        ([("Content-Length", "+2")], 400),
        ([("Content-Length", "0")], 413),
        ([("Content-Length", "9" * 100)], 413),
    ],
)
def test_raw_invalid_lengths_are_bounded_with_json_errors(tmp_path, headers, status):
    with running(tmp_path / "w") as instance:
        received, data, response_headers = raw_request(
            instance, "/api/import", headers=headers, omit=("Content-Length",)
        )
        assert received == status and set(json.loads(data)) == {"error"}
        assert_response_protection(response_headers)
        assert request(instance, "/api/jobs")[1] == []


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [("Content-Type", "text/plain"), ("Content-Length", "2")],
        [("Content-Type", "application/json"), ("Content-Length", "999999")],
    ],
)
def test_unknown_post_route_precedes_json_header_validation(tmp_path, headers):
    with running(tmp_path / "w") as instance:
        status, data, response_headers = raw_request(
            instance,
            "/not-a-route",
            headers=headers,
            omit=("Content-Type", "Content-Length"),
        )
        assert status == 404 and json.loads(data) == {"error": "Route not found"}
        assert_response_protection(response_headers)


def test_direct_close_stops_a_running_uvicorn_listener(tmp_path):
    workspace = tmp_path / "w"
    instance = server.create_server(workspace)
    thread = threading.Thread(target=instance.serve_forever)
    thread.start()
    try:
        assert request(instance, "/api/session")[0] == 200
        instance.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()
        with pytest.raises(OSError):
            socket.create_connection(("127.0.0.1", instance.server_port), timeout=0.2)
        with server.create_server(workspace) as restarted:
            assert restarted.jobs.list() == []
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize(
    ("name", "status", "message"),
    [
        ("Host", 403, "Only this loopback origin is allowed"),
        ("Origin", 403, "Foreign origins are not allowed"),
        ("X-Workbench-Token", 403, "Invalid workbench session token"),
        ("Content-Type", 415, "Use application/json with UTF-8"),
        ("Content-Length", 400, "One valid Content-Length is required"),
    ],
)
@pytest.mark.parametrize("suffix", [" ", "\t"])
def test_trailing_header_whitespace_does_not_weaken_exact_validation(
    tmp_path, name, status, message, suffix
):
    with running(tmp_path / "w") as instance:
        original = {
            "Host": instance.origin.removeprefix("http://"),
            "Origin": instance.origin,
            "X-Workbench-Token": instance.csrf_token,
            "Content-Type": "application/json",
            "Content-Length": "2",
        }[name]
        received, data, headers = raw_request(
            instance, "/api/import", headers=[(name, original + suffix)], omit=(name,)
        )
        assert received == status and json.loads(data) == {"error": message}
        assert_response_protection(headers)
        assert request(instance, "/api/jobs")[1] == []
