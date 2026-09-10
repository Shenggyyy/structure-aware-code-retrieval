"""The workbench's HTTP boundary, independent of its routes and task worker.

The ASGI boundary also protects direct app transports. A small Uvicorn header
preflight preserves duplicate-header checks that h11 would otherwise normalize
or reject before an ASGI application can inspect them; h11 still parses HTTP.
"""

import asyncio
import json
import re
import secrets
from http import HTTPStatus

from starlette.requests import ClientDisconnect, Request
from starlette.responses import Response
from uvicorn.protocols.http.h11_impl import H11Protocol

from structure_aware_retrieval.workbench.jobs import JobUnavailableError

MAX_BODY_BYTES = 16_384
_MAX_HEADER_BYTES = 65_536
_READ_TIMEOUT = 10
SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
        "img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    ),
    "Connection": "close",
}


class RequestError(Exception):
    """An intentional, non-sensitive error response at the HTTP boundary."""

    def __init__(self, status: int, message: str, **fields):
        super().__init__(message)
        self.status = status
        self.payload = {"error": message, **fields}


class WorkbenchJSONResponse(Response):
    """Keep the existing JSON representation and reject non-finite values."""

    media_type = "application/json; charset=utf-8"

    def render(self, content: object) -> bytes:
        return json.dumps(content, ensure_ascii=True, allow_nan=False).encode("utf-8")


def _values(headers: list[tuple[bytes, bytes]], key: bytes) -> list[str]:
    return [value.decode("latin-1") for name, value in headers if name.lower() == key]


def _guard(headers, *, origin: str, csrf_token: str, mutation: bool) -> None:
    if _values(headers, b"host") != [origin.removeprefix("http://")]:
        raise RequestError(403, "Only this loopback origin is allowed")
    origins = _values(headers, b"origin")
    if origins and origins != [origin]:
        raise RequestError(403, "Foreign origins are not allowed")
    if "cross-site" in _values(headers, b"sec-fetch-site"):
        raise RequestError(403, "Cross-site requests are not allowed")
    if mutation:
        if origins != [origin]:
            raise RequestError(403, "Same-origin requests are required")
        tokens = _values(headers, b"x-workbench-token")
        if (
            len(tokens) != 1
            or not tokens[0].isascii()
            or not secrets.compare_digest(tokens[0], csrf_token)
        ):
            raise RequestError(403, "Invalid workbench session token")


def _body_length(headers) -> int:
    if _values(headers, b"transfer-encoding"):
        raise RequestError(400, "Transfer encoding is not supported")
    types = _values(headers, b"content-type")
    if len(types) != 1 or types[0].lower() not in {
        "application/json",
        "application/json; charset=utf-8",
    }:
        raise RequestError(415, "Use application/json with UTF-8")
    lengths = _values(headers, b"content-length")
    if len(lengths) != 1 or re.fullmatch(r"[0-9]+", lengths[0]) is None:
        raise RequestError(400, "One valid Content-Length is required")
    if len(lengths[0]) > 10:
        raise RequestError(413, "Request exceeds the 16384-byte limit")
    length = int(lengths[0])
    if not 1 <= length <= MAX_BODY_BYTES:
        raise RequestError(413, "Request exceeds the 16384-byte limit")
    return length


def _canonical_target(scope: dict) -> None:
    raw_path = scope.get("raw_path", scope["path"].encode("utf-8"))
    target = raw_path + (b"?" + scope["query_string"] if scope.get("query_string") else b"")
    target = scope.get("state", {}).get("workbench.raw_target", target)
    if target == scope["path"].encode("utf-8"):
        return
    if scope["method"] == "GET" and target.startswith(
        (b"/api/jobs/", b"/api/runs/", b"/api/generation-plans/")
    ):
        raise RequestError(400, "Invalid repository, run, or job identifier")
    raise RequestError(404, "Route not found")


def _error_response(error: Exception, method: str) -> WorkbenchJSONResponse:
    if isinstance(error, RequestError | JobUnavailableError):
        return WorkbenchJSONResponse(error.payload, error.status)
    if method == "GET":
        if isinstance(error, FileNotFoundError):
            status, message = 404, "Saved record or asset not found"
        elif isinstance(error, ValueError | OSError):
            status, message = 422, "Cannot read saved data; record may be missing or invalid"
        else:
            status, message = 500, "Cannot read workbench data"
    elif isinstance(error, FileExistsError):
        status, message = 409, "This generation plan was already started; no retry"
    elif isinstance(error, FileNotFoundError):
        status, message = 404, "Saved generation plan or preview not found"
    elif isinstance(error, TimeoutError):
        status, message = 408, "Request body timed out"
    elif isinstance(error, UnicodeError):
        status, message = 400, "Request text must be valid UTF-8"
    elif isinstance(error, ValueError):
        status, message = 400, str(error)[:2000]
    else:
        status, message = 500, "Cannot submit workbench task"
    return WorkbenchJSONResponse({"error": message}, status)


class WorkbenchBoundary:
    """Apply request guards and response headers without changing app routes."""

    def __init__(self, app, *, origin: str, csrf_token: str):
        self.app = app
        self.origin = origin
        self.csrf_token = csrf_token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def secured_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                headers = list(message.get("headers", []))
                for name, value in SECURITY_HEADERS.items():
                    key = name.lower().encode("ascii")
                    headers = [(k, v) for k, v in headers if k.lower() != key]
                    headers.append((key, value.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            if scope["method"] not in {"GET", "POST"}:
                raise RequestError(501, "Invalid HTTP request")
            _guard(
                scope["headers"],
                origin=self.origin,
                csrf_token=self.csrf_token,
                mutation=scope["method"] == "POST",
            )
            _canonical_target(scope)
            await self.app(scope, receive, secured_send)
        except Exception as error:
            # Routes return complete in-memory responses. A response already
            # sent cannot be replaced and must not leak exception details.
            if not started:
                await _error_response(error, scope["method"])(scope, receive, secured_send)


async def read_payload(request: Request, allowed: set[str]) -> dict:
    """Read a bounded JSON object without framework field coercion."""
    length = _body_length(request.scope["headers"])
    data = bytearray()
    try:
        async with asyncio.timeout(_READ_TIMEOUT):
            async for chunk in request.stream():
                if len(data) + len(chunk) > length:
                    raise RequestError(400, "Incomplete JSON request")
                data.extend(chunk)
    except ClientDisconnect as error:
        raise RequestError(400, "Incomplete JSON request") from error
    if len(data) != length:
        raise RequestError(400, "Incomplete JSON request")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result

    try:
        payload = json.loads(data.decode("utf-8"), object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as error:
        raise RequestError(400, "Invalid JSON request") from error
    if not isinstance(payload, dict):
        raise RequestError(400, "Request must be a JSON object")
    if payload.keys() - allowed:
        raise RequestError(400, "Unexpected request fields")
    return payload


class WorkbenchH11Protocol(H11Protocol):
    """Inspect a bounded first header block before h11 normalizes framing.

    Each response closes the connection, as the previous HTTP/1.0 service did.
    This is not a second router or parser: h11 handles valid HTTP requests and
    bodies. Only security-sensitive header multiplicity and limits are checked.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._header_buffer = bytearray()
        self._headers_checked = False
        self._rejected = False
        self._header_timeout = None
        self._close_after_error = None

    def connection_made(self, transport):
        super().connection_made(transport)
        self._header_timeout = self.loop.call_later(_READ_TIMEOUT, self.transport.close)

    def connection_lost(self, exc):
        for timer in (self._header_timeout, self._close_after_error):
            if timer is not None:
                timer.cancel()
        super().connection_lost(exc)

    def data_received(self, data: bytes) -> None:
        if self._rejected:
            return
        if self._headers_checked:
            super().data_received(data)
            return
        self._header_buffer.extend(data)
        separator = re.search(rb"\r?\n\r?\n", self._header_buffer)
        if separator is None:
            if len(self._header_buffer) > _MAX_HEADER_BYTES:
                self._reject(431, {"error": "Invalid HTTP request"})
            return
        if separator.end() > _MAX_HEADER_BYTES:
            self._reject(431, {"error": "Invalid HTTP request"})
            return
        block = bytes(self._header_buffer[: separator.start()])
        try:
            lines = block.splitlines()
            if len(lines) > 100:
                raise RequestError(431, "Invalid HTTP request")
            if not lines:
                raise RequestError(400, "Invalid HTTP request")
            request_line = lines[0].split()
            if len(request_line) != 3 or not request_line[1].isascii():
                raise RequestError(400, "Invalid HTTP request")
            method = request_line[0]
            if method not in {b"GET", b"POST"}:
                raise RequestError(501, "Invalid HTTP request")
            headers = []
            for line in lines[1:]:
                name, colon, value = line.partition(b":")
                if not colon or not name or line[:1] in {b" ", b"\t"}:
                    raise RequestError(400, "Invalid HTTP request")
                # The previous header parser removed leading whitespace but
                # preserved trailing whitespace. Do not let h11 silently
                # turn a rejected origin, token or framing value into a match.
                headers.append((name.lower(), value.lstrip(b" \t")))
            state = self.config.app.state.workbench
            _guard(
                headers,
                origin=state.origin,
                csrf_token=state.csrf_token,
                mutation=method == b"POST",
            )
            if method == b"POST":
                # Preserve the existing guard -> route -> body rejection
                # order, including malformed framing on unknown endpoints.
                # Read the route declarations; do not maintain a second URL
                # table or select a handler here. POST routes are fixed paths.
                paths = {
                    route.path.encode("ascii")
                    for route in self.config.app.routes
                    if "POST" in (getattr(route, "methods", None) or ())
                }
                if request_line[1] not in paths:
                    raise RequestError(404, "Route not found")
                _body_length(headers)
        except RequestError as error:
            self._reject(error.status, error.payload)
            return
        self._headers_checked = True
        # Preserve a bare trailing '?' too; ASGI's empty query_string alone
        # cannot distinguish it from the original fixed endpoint URL.
        self.app_state = {**self.app_state, "workbench.raw_target": request_line[1]}
        if self._header_timeout is not None:
            self._header_timeout.cancel()
        buffered = bytes(self._header_buffer)
        self._header_buffer.clear()
        super().data_received(buffered)

    def send_400_response(self, msg: str) -> None:
        # h11's diagnostic stays internal; never print request bytes or URLs.
        self._reject(400, {"error": "Invalid HTTP request"})

    def _reject(self, status: int, payload: dict) -> None:
        if self._rejected:
            return
        self._rejected = True
        self._header_buffer.clear()
        if self._header_timeout is not None:
            self._header_timeout.cancel()
        response = WorkbenchJSONResponse(payload, status)
        headers = {**dict(response.headers), **SECURITY_HEADERS}
        head = f"HTTP/1.1 {status} {HTTPStatus(status).phrase}\r\n"
        head += "".join(f"{name}: {value}\r\n" for name, value in headers.items()) + "\r\n"
        self.transport.write(head.encode("ascii") + response.body)
        # Flush the response before closing an unread request on Windows.
        # Discard arriving bytes for a bounded interval without buffering them.
        if self.transport.can_write_eof():
            self.transport.write_eof()
        self._close_after_error = self.loop.call_later(0.1, self.transport.close)
