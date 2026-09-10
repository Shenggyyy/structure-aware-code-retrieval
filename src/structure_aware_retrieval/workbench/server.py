"""Explicit FastAPI routes and the loopback Uvicorn service lifecycle.

Business operations live in the existing workbench modules; jobs.py owns the
single durable worker and security.py owns the shared HTTP boundary.
"""

import os
import re
import secrets
import socket
import threading
from contextlib import asynccontextmanager
from importlib.resources import files
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.responses import Response

from structure_aware_retrieval.workbench.comparison import list_comparisons, load_comparison
from structure_aware_retrieval.workbench.generation import (
    GENERATION_MODEL,
    create_generation_plan,
    load_generation_plan,
)
from structure_aware_retrieval.workbench.jobs import Jobs, read_job, repositories
from structure_aware_retrieval.workbench.security import (
    RequestError,
    WorkbenchBoundary,
    WorkbenchH11Protocol,
    WorkbenchJSONResponse,
    read_payload,
)
from structure_aware_retrieval.workbench.storage import safe_path, workspace_root

_RECORD_ID = re.compile(r"[0-9a-f]{32}")
_REPOSITORY_ID = re.compile(r"[0-9a-f]{64}")


def _identifier(value: object, pattern: re.Pattern) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise RequestError(400, "Invalid repository, run, or job identifier")
    return value


def _asset(name: str, content_type: str) -> Response:
    asset = files("structure_aware_retrieval.workbench").joinpath("static", name)
    return Response(asset.read_bytes(), media_type=content_type)


def create_app(service: "WorkbenchServer") -> FastAPI:
    """Map each existing address to its handler, without changing API schemas."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            service.close_jobs()

    app = FastAPI(
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        redirect_slashes=False,
        default_response_class=WorkbenchJSONResponse,
    )
    app.state.workbench = service
    app.add_middleware(WorkbenchBoundary, origin=service.origin, csrf_token=service.csrf_token)

    @app.exception_handler(HTTPException)
    async def route_not_found(request: Request, error: HTTPException):
        # GET/POST on an unknown address, including the wrong method for a
        # known address, used to return this same 404 JSON response.
        return WorkbenchJSONResponse({"error": "Route not found"}, 404)

    @app.get("/")
    def index():
        return _asset("index.html", "text/html; charset=utf-8")

    @app.get("/app.js")
    def javascript():
        return _asset("app.js", "text/javascript; charset=utf-8")

    @app.get("/i18n.js")
    def translations():
        return _asset("i18n.js", "text/javascript; charset=utf-8")

    @app.get("/app.css")
    def stylesheet():
        return _asset("app.css", "text/css; charset=utf-8")

    @app.get("/api/session")
    def session():
        return {
            "csrf_token": service.csrf_token,
            "mode": "context_preview",
            "api_calls": 0,
            "generation": {
                "model": GENERATION_MODEL,
                "key_ready": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
                "request_limit": 5,
                "judge_calls": 0,
            },
        }

    @app.get("/api/repositories")
    def repository_list():
        return repositories(service.workspace)

    @app.get("/api/history")
    def history():
        return list_comparisons(service.workspace)

    @app.get("/api/jobs")
    def job_list():
        return service.jobs.list()

    @app.get("/api/jobs/{job_id:path}")
    def job_status(job_id: str):
        return read_job(service.workspace, _identifier(job_id, _RECORD_ID))

    @app.get("/api/runs/{run_id:path}")
    def comparison(run_id: str):
        return load_comparison(service.workspace, _identifier(run_id, _RECORD_ID))

    @app.get("/api/generation-plans/{plan_id:path}")
    def generation_plan(plan_id: str):
        return load_generation_plan(service.workspace, _identifier(plan_id, _RECORD_ID))

    @app.post("/api/import", status_code=202)
    async def import_source(request: Request):
        payload = await read_payload(request, {"source", "ref"})
        for key, limit in (("source", 4096), ("ref", 200)):
            value = payload.get(key, "HEAD" if key == "ref" else None)
            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value.encode("utf-8")) > limit
                or any(ord(c) < 32 for c in value)
            ):
                raise RequestError(400, "Invalid repository source or ref")
        return await run_in_threadpool(service.jobs.submit, "import", payload)

    @app.post("/api/prepare", status_code=202)
    async def prepare(request: Request):
        payload = await read_payload(request, {"repository_id"})
        _identifier(payload.get("repository_id"), _REPOSITORY_ID)
        return await run_in_threadpool(service.jobs.submit, "prepare", payload)

    @app.post("/api/preview", status_code=202)
    async def preview(request: Request):
        payload = await read_payload(
            request, {"repository_id", "question", "top_k", "max_context_bytes"}
        )
        _identifier(payload.get("repository_id"), _REPOSITORY_ID)
        question = payload.get("question")
        if (
            not isinstance(question, str)
            or not question.strip()
            or len(question.encode("utf-8")) > 4000
        ):
            raise RequestError(400, "Question must contain 1 to 4000 UTF-8 bytes")
        for key, minimum, maximum, default in (
            ("top_k", 1, 100, 10),
            ("max_context_bytes", 2, 1_000_000, 16000),
        ):
            value = payload.get(key, default)
            if type(value) is not int or not minimum <= value <= maximum:
                raise RequestError(400, f"Invalid {key}")
        return await run_in_threadpool(service.jobs.submit, "preview", payload)

    @app.post("/api/generation-plan", status_code=201)
    async def plan_generation(request: Request):
        payload = await read_payload(request, {"run_id"})
        run_id = _identifier(payload.get("run_id"), _RECORD_ID)
        return await run_in_threadpool(create_generation_plan, service.workspace, run_id)

    @app.post("/api/generate", status_code=202)
    async def generate(request: Request):
        payload = await read_payload(
            request, {"plan_id", "confirmed_model", "budget_usd", "confirm"}
        )
        _identifier(payload.get("plan_id"), _RECORD_ID)
        if payload.get("confirm") is not True:
            raise RequestError(400, "Explicit generation confirmation is required")
        if not isinstance(payload.get("confirmed_model"), str):
            raise RequestError(400, "Confirm the model from the generation plan")
        if type(payload.get("budget_usd")) not in {int, float}:
            raise RequestError(400, "A numeric generation budget is required")
        return await run_in_threadpool(service.jobs.submit, "generation", payload)

    return app


class _WorkbenchUvicorn(uvicorn.Server):
    """Stop the durable worker before waiting for HTTP connections to finish."""

    def __init__(self, config: uvicorn.Config, owner: "WorkbenchServer"):
        super().__init__(config)
        self.owner = owner

    def handle_exit(self, sig, frame):
        self.owner.close_jobs()
        super().handle_exit(sig, frame)

    async def shutdown(self, sockets=None):
        self.owner.close_jobs()
        await super().shutdown(sockets)


class WorkbenchServer:
    """One loopback Uvicorn instance with an exclusive workspace lifetime.

    The small runtime facade keeps CLI and embedded/test startup identical.
    The public HTTP routes are all defined by create_app above.
    """

    def __init__(self, workspace: Path, model_cache: Path, port: int):
        self.workspace = workspace_root(workspace, create=True)
        self.csrf_token = secrets.token_urlsafe(32)
        self._state_lock = threading.RLock()
        self._jobs_closed = False
        self._closed = False
        self._serving_thread = None
        self._stopped = threading.Event()
        self._workspace_lock = safe_path(self.workspace, ".web-server.lock").open("a+b")
        try:
            self._workspace_lock.seek(0)
            if os.name == "nt":
                import msvcrt

                if self._workspace_lock.read(1) == b"":
                    self._workspace_lock.write(b"0")
                    self._workspace_lock.flush()
                self._workspace_lock.seek(0)
                msvcrt.locking(self._workspace_lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._workspace_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self._workspace_lock.close()
            raise ValueError("Another browser server is using this workspace") from error

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.bind(("127.0.0.1", port))
            self._socket.listen(128)
            self._socket.setblocking(False)
            self.server_address = self._socket.getsockname()
            self.server_port = self.server_address[1]
            self.origin = f"http://127.0.0.1:{self.server_port}"
            self.jobs = Jobs(self.workspace, model_cache)
            self.app = create_app(self)
            config = uvicorn.Config(
                self.app,
                host="127.0.0.1",
                port=self.server_port,
                http=WorkbenchH11Protocol,
                loop="asyncio",
                ws="none",
                interface="asgi3",
                workers=1,
                lifespan="on",
                access_log=False,
                log_config=None,
                log_level="critical",
                proxy_headers=False,
                server_header=False,
                date_header=False,
                timeout_graceful_shutdown=2,
                h11_max_incomplete_event_size=65_536,
            )
            self._uvicorn = _WorkbenchUvicorn(config, self)
        except BaseException:
            self._socket.close()
            self._workspace_lock.close()
            raise

    def close_jobs(self) -> None:
        with self._state_lock:
            if not self._jobs_closed:
                self._jobs_closed = True
                # A worker inside Git/model work may still be finishing. Its
                # final checkpoint releases the lock; it never resumes itself.
                self.jobs.close(self._workspace_lock.close)

    def serve_forever(self, poll_interval: float = 0.2) -> None:
        """Run Uvicorn; poll_interval is retained for existing embedded callers."""
        with self._state_lock:
            if self._closed:
                raise ValueError("Workbench is closed")
            if self._serving_thread is not None:
                raise ValueError("Workbench is already serving")
            self._serving_thread = threading.current_thread()
        try:
            self._uvicorn.run(sockets=[self._socket])
        finally:
            try:
                self.server_close()
            finally:
                self._stopped.set()

    def shutdown(self) -> None:
        self.close_jobs()
        self._uvicorn.should_exit = True
        if (
            self._serving_thread is not None
            and self._serving_thread is not threading.current_thread()
        ):
            self._stopped.wait(timeout=10)

    def server_close(self) -> None:
        with self._state_lock:
            if self._closed:
                return
            self._closed = True
            self._uvicorn.should_exit = True
            try:
                self.close_jobs()
            finally:
                self._socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()
        self.server_close()


def create_server(
    workspace: Path,
    *,
    model_cache: Path = Path("artifacts/models"),
    port: int = 0,
) -> WorkbenchServer:
    """Create a server for local use; tests may request an OS-assigned port."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("Port must be an integer from 0 to 65535")
    return WorkbenchServer(workspace, Path(model_cache), port)


def serve(
    workspace: Path,
    *,
    model_cache: Path = Path("artifacts/models"),
    port: int = 8765,
) -> None:
    """Serve the local workbench without opening a browser or calling a model."""
    with create_server(workspace, model_cache=model_cache, port=port) as server:
        print(f"Workbench: {server.origin}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
