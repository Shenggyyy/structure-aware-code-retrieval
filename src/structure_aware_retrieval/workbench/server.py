"""Loopback workbench with offline previews and explicitly approved generation."""

import json
import os
import re
import secrets
import socket
import threading
import time
from copy import deepcopy
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.workbench.comparison import (
    list_comparisons,
    load_comparison,
    preview_question,
)
from structure_aware_retrieval.workbench.generation import (
    GENERATION_MODEL,
    create_generation_plan,
    execute_generation_plan,
    load_generation_execution,
    load_generation_plan,
    recover_generation,
    validate_generation_approval,
)
from structure_aware_retrieval.workbench.importing import import_repository, load_repository
from structure_aware_retrieval.workbench.preparation import load_preparation, prepare_repository
from structure_aware_retrieval.workbench.storage import (
    read_json,
    safe_path,
    workspace_root,
    write_json,
)

MAX_BODY_BYTES = 16_384
_JOB_ID = re.compile(r"[0-9a-f]{32}")
_REPOSITORY_ID = re.compile(r"[0-9a-f]{64}")
_TERMINAL = {"completed", "failed", "interrupted"}
_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


class _RequestError(Exception):
    def __init__(self, status: int, message: str, **fields):
        self.status = status
        self.payload = {"error": message, **fields}


class _Stopped(BaseException):
    """Stop at the next saved service checkpoint after server shutdown."""


def _identifier(value: object, pattern: re.Pattern) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise _RequestError(400, "Invalid repository, run, or job identifier")
    return value


def _read_job(workspace: Path, job_id: str) -> dict:
    _identifier(job_id, _JOB_ID)
    record = read_json(workspace, f"web-jobs/{job_id}.json")
    if (
        record.get("schema_version") != 1
        or record.get("job_id") != job_id
        or record.get("kind") not in {"import", "prepare", "preview", "generation"}
        or record.get("status") not in _TERMINAL | {"queued", "running"}
    ):
        raise ValueError("Invalid browser job record")
    return record


class _Jobs:
    """One background task, durable progress, and no automatic resumption."""

    def __init__(self, workspace: Path, model_cache: Path):
        self.workspace = workspace
        self.model_cache = model_cache
        self.lock = threading.RLock()
        self.active: str | None = None
        self.closed = False
        self.on_stopped = None
        # Paid attempts have their own durable journal. Its recovery preserves
        # unknown billing outcomes and never resubmits a model request.
        recover_generation(workspace)
        directory = safe_path(workspace, "web-jobs")
        if directory.exists():
            for path in sorted(directory.glob("*.json")):
                if not _JOB_ID.fullmatch(path.stem):
                    continue
                try:
                    record = _read_job(workspace, path.stem)
                    if record["status"] not in _TERMINAL:
                        record.update(
                            status="interrupted",
                            finished_at=_now(),
                            error="Previous server stopped before completion; no automatic retry",
                        )
                    if record["status"] == "interrupted":
                        self._recover_interrupted(record)
                        self._save(record)
                except (OSError, ValueError):
                    # Keep damaged records visible through list(), never replace them.
                    continue

    def _recover_interrupted(self, record: dict) -> None:
        """Reconcile only validated archives explicitly linked by this web job."""
        progress = record.get("progress", {})
        if not isinstance(progress, dict) or not isinstance(progress.get("detail", {}), dict):
            record["recovery_warning"] = "Invalid saved progress; related archives were preserved"
            return
        detail = progress.get("detail", {})
        phase = progress.get("phase")
        try:
            if phase == "generation":
                plan_id = detail.get("plan_id")
                if not isinstance(plan_id, str) or not _JOB_ID.fullmatch(plan_id):
                    raise ValueError("Invalid linked generation plan")
                run = load_generation_execution(self.workspace, plan_id)
                if run is None:
                    return
                if detail.get("run_id", run["run_id"]) != run["run_id"]:
                    raise ValueError("Invalid linked generation run")
                # Only the generation journal may classify paid attempts.
                # In particular, a running attempt can have an unknown cost.
                detail.update(self._run_progress(run, phase))
                record["api_calls"] = run.get("api_calls", 0)
            elif phase == "preview" and _JOB_ID.fullmatch(str(detail.get("run_id", ""))):
                run = load_comparison(self.workspace, detail["run_id"])
                if run.get("mode") != "context_preview":
                    raise ValueError("Invalid linked preview run")
                if run["status"] == "running":
                    run.update(status="interrupted", finished_at=_now())
                    for row in run["results"]:
                        if row["status"] == "running":
                            row["status"] = "interrupted"
                    run["fingerprint"] = stable_id(
                        {key: value for key, value in run.items() if key != "fingerprint"}
                    )
                    write_json(self.workspace, f"runs/{run['run_id']}/run.json", run)
                detail.update(
                    status=run["status"],
                    results=[
                        {"strategy": row["strategy"], "status": row["status"]}
                        for row in run["results"]
                    ],
                )
            elif phase == "prepare" and _REPOSITORY_ID.fullmatch(
                str(detail.get("repository_id", ""))
            ):
                preparation = load_preparation(self.workspace, detail["repository_id"])
                if preparation["status"] == "preparing":
                    preparation["status"] = "interrupted"
                    for stage in preparation["stages"].values():
                        if stage["status"] == "running":
                            stage.update(
                                status="interrupted",
                                error="Previous server stopped before completion",
                            )
                    preparation["fingerprint"] = stable_id(
                        {key: value for key, value in preparation.items() if key != "fingerprint"}
                    )
                    write_json(
                        self.workspace,
                        f"resources/{preparation['repository_id']}/manifest.json",
                        preparation,
                    )
                progress["detail"] = preparation
            elif phase == "import" and _JOB_ID.fullmatch(str(detail.get("job_id", ""))):
                relative = f"jobs/{detail['job_id']}.json"
                imported = read_json(self.workspace, relative)
                if imported.get("job_id") != detail["job_id"] or not isinstance(
                    imported.get("events"), list
                ):
                    raise ValueError("Invalid import progress")
                if imported.get("status") in {
                    "created",
                    "validating",
                    "downloading",
                    "snapshotting",
                }:
                    imported.update(
                        status="interrupted", error="Previous server stopped before completion"
                    )
                    imported["events"].append({"status": "interrupted", "at": _now()})
                    write_json(self.workspace, relative, imported)
                progress["detail"] = imported
        except (OSError, ValueError, KeyError, TypeError):
            record["recovery_warning"] = (
                "Related archive is unavailable or invalid; existing bytes were preserved"
            )

    def _save(self, record: dict) -> None:
        write_json(self.workspace, f"web-jobs/{record['job_id']}.json", record)

    def list(self) -> list[dict]:
        directory = safe_path(self.workspace, "web-jobs")
        rows = []
        if directory.exists():
            for path in sorted(directory.glob("*.json"), reverse=True):
                if not _JOB_ID.fullmatch(path.stem):
                    continue
                try:
                    rows.append(_read_job(self.workspace, path.stem))
                except (OSError, ValueError):
                    rows.append(
                        {"job_id": path.stem, "status": "unreadable", "error": "Invalid saved job"}
                    )
        return sorted(rows, key=lambda row: row.get("created_at", ""), reverse=True)

    def submit(self, kind: str, payload: dict) -> dict:
        with self.lock:
            if self.closed:
                raise _RequestError(503, "Workbench is closing")
            if self.active is not None:
                raise _RequestError(409, "Another task is running", job_id=self.active)
            if kind == "generation":
                validate_generation_approval(
                    self.workspace,
                    payload["plan_id"],
                    budget_usd=payload["budget_usd"],
                    confirmed_model=payload["confirmed_model"],
                )
            record = {
                "schema_version": 1,
                "job_id": uuid4().hex,
                "kind": kind,
                "status": "queued",
                "created_at": _now(),
                "finished_at": None,
                "progress": {
                    "phase": kind,
                    "detail": {"plan_id": payload["plan_id"]} if kind == "generation" else {},
                },
                "result": None,
                "error": None,
                "api_calls": 0,
            }
            self._save(record)
            self.active = record["job_id"]
            worker = threading.Thread(target=self._run, args=(record, payload), daemon=True)
            worker.start()
            return deepcopy(record)

    @staticmethod
    def _run_progress(detail: dict, phase: str) -> dict:
        result = {
            "run_id": detail["run_id"],
            "status": detail["status"],
            "results": [
                {"strategy": row["strategy"], "status": row["status"]} for row in detail["results"]
            ],
        }
        if phase == "generation":
            result["plan_id"] = detail["generation"]["plan_id"]
            result["api_calls"] = detail.get("api_calls", 0)
        return result

    def _progress(self, record: dict, phase: str, detail: dict) -> None:
        with self.lock:
            if self.closed:
                raise _Stopped
            if phase in {"preview", "generation"}:
                detail = self._run_progress(detail, phase)
                if phase == "generation":
                    record["api_calls"] = detail["api_calls"]
            record["progress"] = {"phase": phase, "detail": detail}
            self._save(record)

    def _run(self, record: dict, payload: dict) -> None:
        try:
            with self.lock:
                if self.closed:
                    return
                record["status"] = "running"
                self._save(record)
            kind = record["kind"]
            if kind == "import":
                repository = import_repository(
                    payload["source"],
                    self.workspace,
                    ref=payload.get("ref", "HEAD"),
                    on_progress=lambda detail: self._progress(record, "import", detail),
                )
                repository_id = repository["repository_id"]
                record["result"] = {"repository_id": repository_id}
            elif kind != "generation":
                repository_id = payload["repository_id"]
            if kind in {"import", "prepare"}:
                preparation = prepare_repository(
                    self.workspace,
                    repository_id,
                    model_cache=self.model_cache,
                    on_progress=lambda detail: self._progress(record, "prepare", detail),
                )
                record["result"] = {"repository_id": repository_id, "preparation": preparation}
            elif kind == "preview":
                run = preview_question(
                    self.workspace,
                    repository_id,
                    payload["question"],
                    model_cache=self.model_cache,
                    top_k=payload.get("top_k", 10),
                    max_context_bytes=payload.get("max_context_bytes", 16000),
                    on_progress=lambda detail: self._progress(record, "preview", detail),
                )
                record["result"] = {
                    "run_id": run["run_id"],
                    "repository_id": repository_id,
                    "status": run["status"],
                }
            elif kind == "generation":
                run = execute_generation_plan(
                    self.workspace,
                    payload["plan_id"],
                    budget_usd=payload["budget_usd"],
                    confirmed_model=payload["confirmed_model"],
                    on_progress=lambda detail: self._progress(record, "generation", detail),
                )
                record["result"] = {
                    "run_id": run["run_id"],
                    "repository_id": run["repository_id"],
                    "status": run["status"],
                }
                record["api_calls"] = run.get("api_calls", 0)
            record["status"] = "completed"
        except Exception as error:
            record["status"] = "failed"
            record["error"] = (
                str(error)[:2000]
                if isinstance(error, ValueError)
                else "Task failed; check local resources and paths"
            )
        except BaseException:
            record.update(status="interrupted", error="Task interrupted; no automatic retry")
        finally:
            with self.lock:
                if not self.closed:
                    record["finished_at"] = _now()
                    try:
                        self._save(record)
                    except OSError:
                        # The last durable checkpoint stays available; no raw
                        # thread traceback or request contents reach the log.
                        pass
                    finally:
                        self.active = None
                else:
                    self.active = None
                    if self.on_stopped is not None:
                        self.on_stopped()

    def close(self, on_stopped) -> None:
        with self.lock:
            self.closed = True
            self.on_stopped = on_stopped
            if self.active is not None:
                record = _read_job(self.workspace, self.active)
                record.update(
                    status="interrupted",
                    finished_at=_now(),
                    error="Server stopped; no automatic retry",
                )
                self._save(record)
            else:
                on_stopped()


def _repositories(workspace: Path) -> list[dict]:
    rows = []
    directory = safe_path(workspace, "repositories")
    if not directory.exists():
        return rows
    for path in sorted(directory.iterdir()):
        if not _REPOSITORY_ID.fullmatch(path.name):
            continue
        try:
            repository = load_repository(workspace, path.name)
            row = {
                "repository_id": path.name,
                "source": repository["source"],
                "created_at": repository["created_at"],
                "file_count": len(repository["files"]),
                "status": "imported",
                "stages": None,
                "error": None,
            }
            if safe_path(workspace, f"resources/{path.name}/manifest.json").exists():
                try:
                    preparation = load_preparation(workspace, path.name)
                    row.update(status=preparation["status"], stages=preparation["stages"])
                except (OSError, ValueError):
                    row.update(status="unreadable", error="Invalid saved preparation")
            rows.append(row)
        except (OSError, ValueError):
            rows.append(
                {
                    "repository_id": path.name,
                    "status": "unreadable",
                    "error": "Invalid saved repository",
                }
            )
    return sorted(rows, key=lambda row: row.get("created_at", ""), reverse=True)


class WorkbenchServer(ThreadingHTTPServer):
    """Do not expose this server on a network interface or through a proxy."""

    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, workspace: Path, model_cache: Path, port: int):
        self.workspace = workspace_root(workspace, create=True)
        self.csrf_token = secrets.token_urlsafe(32)
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
        try:
            super().__init__(("127.0.0.1", port), _Handler)
            self.jobs = _Jobs(self.workspace, model_cache)
        except BaseException:
            self._workspace_lock.close()
            raise
        self.origin = f"http://127.0.0.1:{self.server_port}"

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address

    def server_close(self) -> None:
        try:
            if hasattr(self, "jobs"):
                # A Git fetch or model load can still be finishing in the
                # daemon worker. Keep the workspace locked until it stops.
                self.jobs.close(self._workspace_lock.close)
            else:
                self._workspace_lock.close()
        finally:
            super().server_close()

    def handle_error(self, request, client_address) -> None:
        # Never print request details, question contents, or repository bytes.
        pass


class _Handler(BaseHTTPRequestHandler):
    server: WorkbenchServer
    protocol_version = "HTTP/1.0"
    server_version = "LocalWorkbench"
    sys_version = ""

    def log_message(self, format, *args) -> None:
        pass

    def _respond(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        )
        self.end_headers()
        self.wfile.write(data)
        if status >= 400 and self.command == "POST":
            # Closing with unread POST bytes can reset the connection on
            # Windows before the client receives the rejection. Half-close
            # the response, then discard only a bounded amount of input.
            self.wfile.flush()
            try:
                self.connection.shutdown(socket.SHUT_WR)
                deadline = time.monotonic() + 0.1
                remaining = MAX_BODY_BYTES * 4
                while remaining and (remaining_seconds := deadline - time.monotonic()) > 0:
                    self.connection.settimeout(remaining_seconds)
                    chunk = self.rfile.read1(min(remaining, 8192))
                    if not chunk:
                        break
                    remaining -= len(chunk)
            except OSError:
                pass

    def _json(self, status: int, value: object) -> None:
        data = json.dumps(value, ensure_ascii=True, allow_nan=False).encode("utf-8")
        self._respond(status, data, "application/json; charset=utf-8")

    def send_error(self, code, message=None, explain=None) -> None:
        self._json(code, {"error": "Invalid HTTP request"})

    def _guard(self, *, mutation: bool = False) -> None:
        if self.headers.get_all("Host") != [self.server.origin.removeprefix("http://")]:
            raise _RequestError(403, "Only this loopback origin is allowed")
        origins = self.headers.get_all("Origin")
        if origins is not None and origins != [self.server.origin]:
            raise _RequestError(403, "Foreign origins are not allowed")
        if "cross-site" in self.headers.get_all("Sec-Fetch-Site", []):
            raise _RequestError(403, "Cross-site requests are not allowed")
        if mutation:
            if origins != [self.server.origin]:
                raise _RequestError(403, "Same-origin requests are required")
            tokens = self.headers.get_all("X-Workbench-Token")
            if (
                tokens is None
                or len(tokens) != 1
                or not tokens[0].isascii()
                or not secrets.compare_digest(tokens[0], self.server.csrf_token)
            ):
                raise _RequestError(403, "Invalid workbench session token")

    def do_GET(self) -> None:
        try:
            self._guard()
            if self.path in _ASSETS:
                name, content_type = _ASSETS[self.path]
                asset = files("structure_aware_retrieval.workbench").joinpath("static", name)
                self._respond(200, asset.read_bytes(), content_type)
                return
            if self.path == "/api/session":
                result = {
                    "csrf_token": self.server.csrf_token,
                    "mode": "context_preview",
                    "api_calls": 0,
                    "generation": {
                        "model": GENERATION_MODEL,
                        "key_ready": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
                        "request_limit": 5,
                        "judge_calls": 0,
                    },
                }
            elif self.path == "/api/repositories":
                result = _repositories(self.server.workspace)
            elif self.path == "/api/history":
                result = list_comparisons(self.server.workspace)
            elif self.path == "/api/jobs":
                result = self.server.jobs.list()
            elif self.path.startswith("/api/jobs/"):
                result = _read_job(self.server.workspace, _identifier(self.path[10:], _JOB_ID))
            elif self.path.startswith("/api/runs/"):
                result = load_comparison(
                    self.server.workspace, _identifier(self.path[10:], _JOB_ID)
                )
            elif self.path.startswith("/api/generation-plans/"):
                result = load_generation_plan(
                    self.server.workspace, _identifier(self.path[22:], _JOB_ID)
                )
            else:
                raise _RequestError(404, "Route not found")
            self._json(200, result)
        except _RequestError as error:
            self._json(error.status, error.payload)
        except FileNotFoundError:
            self._json(404, {"error": "Saved record or asset not found"})
        except (ValueError, OSError):
            self._json(422, {"error": "Cannot read saved data; record may be missing or invalid"})
        except Exception:
            self._json(500, {"error": "Cannot read workbench data"})

    def _body(self) -> dict:
        if self.headers.get_all("Transfer-Encoding") is not None:
            raise _RequestError(400, "Transfer encoding is not supported")
        types = self.headers.get_all("Content-Type")
        if (
            types is None
            or len(types) != 1
            or types[0].lower() not in {"application/json", "application/json; charset=utf-8"}
        ):
            raise _RequestError(415, "Use application/json with UTF-8")
        lengths = self.headers.get_all("Content-Length")
        if lengths is None or len(lengths) != 1 or re.fullmatch(r"[0-9]+", lengths[0]) is None:
            raise _RequestError(400, "One valid Content-Length is required")
        if len(lengths[0]) > 10:
            raise _RequestError(413, "Request exceeds the 16384-byte limit")
        length = int(lengths[0])
        if not 1 <= length <= MAX_BODY_BYTES:
            raise _RequestError(413, "Request exceeds the 16384-byte limit")
        data = self.rfile.read(length)
        if len(data) != length:
            raise _RequestError(400, "Incomplete JSON request")
        try:

            def pairs(items):
                result = {}
                for key, value in items:
                    if key in result:
                        raise ValueError("Duplicate JSON field")
                    result[key] = value
                return result

            payload = json.loads(data.decode("utf-8"), object_pairs_hook=pairs)
        except (ValueError, UnicodeError) as error:
            raise _RequestError(400, "Invalid JSON request") from error
        if not isinstance(payload, dict):
            raise _RequestError(400, "Request must be a JSON object")
        return payload

    def do_POST(self) -> None:
        try:
            self._guard(mutation=True)
            if self.path not in {
                "/api/import",
                "/api/prepare",
                "/api/preview",
                "/api/generation-plan",
                "/api/generate",
            }:
                raise _RequestError(404, "Route not found")
            kind = self.path.removeprefix("/api/")
            payload = self._body()
            allowed = {
                "import": {"source", "ref"},
                "prepare": {"repository_id"},
                "preview": {"repository_id", "question", "top_k", "max_context_bytes"},
                "generation-plan": {"run_id"},
                "generate": {"plan_id", "confirmed_model", "budget_usd", "confirm"},
            }[kind]
            if payload.keys() - allowed:
                raise _RequestError(400, "Unexpected request fields")
            if kind == "generation-plan":
                run_id = _identifier(payload.get("run_id"), _JOB_ID)
                plan = create_generation_plan(self.server.workspace, run_id)
                self._json(201, plan)
                return
            if kind == "generate":
                _identifier(payload.get("plan_id"), _JOB_ID)
                if payload.get("confirm") is not True:
                    raise _RequestError(400, "Explicit generation confirmation is required")
                if not isinstance(payload.get("confirmed_model"), str):
                    raise _RequestError(400, "Confirm the model from the generation plan")
                if type(payload.get("budget_usd")) not in {int, float}:
                    raise _RequestError(400, "A numeric generation budget is required")
                self._json(202, self.server.jobs.submit("generation", payload))
                return
            if kind == "import":
                for key, limit in (("source", 4096), ("ref", 200)):
                    value = payload.get(key, "HEAD" if key == "ref" else None)
                    if (
                        not isinstance(value, str)
                        or not value.strip()
                        or len(value.encode("utf-8")) > limit
                        or any(ord(c) < 32 for c in value)
                    ):
                        raise _RequestError(400, "Invalid repository source or ref")
            else:
                _identifier(payload.get("repository_id"), _REPOSITORY_ID)
            if kind == "preview":
                question = payload.get("question")
                if (
                    not isinstance(question, str)
                    or not question.strip()
                    or len(question.encode("utf-8")) > 4000
                ):
                    raise _RequestError(400, "Question must contain 1 to 4000 UTF-8 bytes")
                for key, minimum, maximum, default in (
                    ("top_k", 1, 100, 10),
                    ("max_context_bytes", 2, 1_000_000, 16000),
                ):
                    value = payload.get(key, default)
                    if type(value) is not int or not minimum <= value <= maximum:
                        raise _RequestError(400, f"Invalid {key}")
            self._json(202, self.server.jobs.submit(kind, payload))
        except _RequestError as error:
            self._json(error.status, error.payload)
        except FileExistsError:
            self._json(409, {"error": "This generation plan was already started; no retry"})
        except FileNotFoundError:
            self._json(404, {"error": "Saved generation plan or preview not found"})
        except TimeoutError:
            self._json(408, {"error": "Request body timed out"})
        except UnicodeError:
            self._json(400, {"error": "Request text must be valid UTF-8"})
        except ValueError as error:
            self._json(400, {"error": str(error)[:2000]})
        except Exception:
            self._json(500, {"error": "Cannot submit workbench task"})


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
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
