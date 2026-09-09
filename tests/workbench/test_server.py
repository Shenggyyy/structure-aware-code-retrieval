"""HTTP-level offline tests for the single-user browser boundary and service reuse."""

import http.client
import json
import threading
import time
from contextlib import contextmanager

import numpy as np
import pytest

from structure_aware_retrieval.strategies import STRATEGIES
from structure_aware_retrieval.workbench import comparison, preparation, server, storage
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
        return response.status, value, dict(response.getheaders())
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

    monkeypatch.setattr(server, "prepare_repository", prepare)
    monkeypatch.setattr(server, "preview_question", preview)
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

    monkeypatch.setattr(server, "import_repository", blocked)
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

    monkeypatch.setattr(server, "import_repository", blocked)
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
