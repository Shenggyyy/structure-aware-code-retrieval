"""Direct ASGI tests: guards also apply when Uvicorn is not the transport."""

import asyncio
import json
from urllib.parse import unquote

import pytest
from starlette.requests import Request

from structure_aware_retrieval.workbench import security, server


@pytest.fixture
def application(tmp_path):
    with server.create_server(tmp_path / "workbench") as service:
        yield service


def _scope(service, path, *, method="GET", headers=()):
    raw_path, _, query = path.partition("?")
    return {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": unquote(raw_path),
        "raw_path": raw_path.encode("ascii"),
        "query_string": query.encode("ascii"),
        "headers": [(b"host", service.origin.removeprefix("http://").encode()), *headers],
        "scheme": "http",
        "server": ("127.0.0.1", service.server_port),
        "client": ("127.0.0.1", 1234),
    }


def _post_headers(service, length):
    return [
        (b"origin", service.origin.encode()),
        (b"x-workbench-token", service.csrf_token.encode()),
        (b"content-type", b"application/json"),
        (b"content-length", str(length).encode()),
    ]


async def _exchange(service, path, *, method="GET", headers=(), messages=(), receive=None):
    pending = iter(messages)

    async def next_message():
        return next(pending, {"type": "http.disconnect"})

    sent = []

    async def send(message):
        sent.append(message)

    await service.app(
        _scope(service, path, method=method, headers=headers), receive or next_message, send
    )
    start = sent[0]
    response_headers = dict(start["headers"])
    for name, value in security.SECURITY_HEADERS.items():
        assert response_headers[name.lower().encode()] == value.encode()
    body = b"".join(message.get("body", b"") for message in sent[1:])
    return start["status"], body


@pytest.mark.parametrize(
    ("header", "value", "method"),
    [
        (b"host", b"127.0.0.1:1", "GET"),
        (b"origin", b"https://example.test", "GET"),
        (b"sec-fetch-site", b"cross-site", "GET"),
        (b"x-workbench-token", b"wrong-token", "POST"),
        (b"x-workbench-token", b"\xff", "POST"),
    ],
)
def test_direct_transport_cannot_bypass_origin_or_session_checks(
    application, header, value, method
):
    headers = _post_headers(application, 2) if method == "POST" else []
    headers.append((header, value))
    status, _ = asyncio.run(_exchange(application, "/api/import", method=method, headers=headers))
    assert status == 403
    assert application.jobs.list() == []


@pytest.mark.parametrize("method", ["HEAD", "OPTIONS", "PUT", "DELETE"])
def test_direct_transport_does_not_enable_framework_methods(application, method):
    status, body = asyncio.run(_exchange(application, "/api/session", method=method))
    assert status == 501
    assert json.loads(body) == {"error": "Invalid HTTP request"}


@pytest.mark.parametrize(
    ("path", "status"),
    [
        ("/api/session?cache=false", 404),
        ("/api/%73ession", 404),
        ("/api/jobs/" + "a" * 32 + "?cache=false", 400),
        ("/api/runs/%61" + "a" * 31, 400),
    ],
)
def test_direct_transport_does_not_add_url_aliases(application, path, status):
    assert asyncio.run(_exchange(application, path))[0] == status


@pytest.mark.parametrize(
    ("body", "length", "message"),
    [
        (b"{}extra", 2, "Incomplete JSON request"),
        (b"{", 2, "Incomplete JSON request"),
        (b'{"source":"a","source":"b"}', 27, "Invalid JSON request"),
        (b"\xff", 1, "Invalid JSON request"),
        (b"[]", 2, "Request must be a JSON object"),
    ],
)
def test_direct_body_errors_cannot_create_tasks(application, body, length, message):
    # Duplicate JSON has its actual content length, independent of formatting.
    if message == "Invalid JSON request":
        length = len(body)
    status, response = asyncio.run(
        _exchange(
            application,
            "/api/import",
            method="POST",
            headers=_post_headers(application, length),
            messages=[{"type": "http.request", "body": body, "more_body": False}],
        )
    )
    assert status == 400
    assert json.loads(response) == {"error": message}
    assert application.jobs.list() == []


def test_body_deadline_returns_408_without_work(application, monkeypatch):
    monkeypatch.setattr(security, "_READ_TIMEOUT", 0.01)

    async def stalled_receive():
        await asyncio.Event().wait()

    status, body = asyncio.run(
        _exchange(
            application,
            "/api/import",
            method="POST",
            headers=_post_headers(application, 2),
            receive=stalled_receive,
        )
    )
    assert status == 408
    assert json.loads(body) == {"error": "Request body timed out"}
    assert application.jobs.list() == []


def test_stream_limit_stops_before_reading_another_chunk(application):
    received = 0

    async def receive():
        nonlocal received
        received += 1
        if received > 1:
            pytest.fail("Oversized chunk must be rejected without another receive")
        return {"type": "http.request", "body": b"x" * 10, "more_body": True}

    request = Request(
        _scope(application, "/api/import", method="POST", headers=_post_headers(application, 2)),
        receive,
    )
    with pytest.raises(security.RequestError, match="Incomplete JSON request"):
        asyncio.run(security.read_payload(request, {"source"}))
    assert received == 1


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_message"),
    [
        (OSError("private path"), 422, "Cannot read saved data; record may be missing or invalid"),
        (RuntimeError("private path"), 500, "Cannot read workbench data"),
    ],
)
def test_route_errors_are_redacted_before_framework_500(
    application, monkeypatch, error, expected_status, expected_message
):
    def fail(workspace):
        raise error

    monkeypatch.setattr(server, "repositories", fail)
    status, body = asyncio.run(_exchange(application, "/api/repositories"))
    assert status == expected_status
    assert json.loads(body) == {"error": expected_message}
    assert b"private path" not in body


def test_json_keeps_original_ascii_representation(application, monkeypatch):
    monkeypatch.setattr(server, "repositories", lambda workspace: {"label": "中文"})
    status, body = asyncio.run(_exchange(application, "/api/repositories"))
    assert status == 200
    assert body == b'{"label": "\\u4e2d\\u6587"}'
