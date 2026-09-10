"""Durable background jobs and saved repository summaries for the workbench.

HTTP routing and server lifetime locking live in ``server.py``. Jobs retain a
single daemon worker and durable checkpoints; closing never resumes paid work.
"""

import re
import threading
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.workbench.comparison import load_comparison, preview_question
from structure_aware_retrieval.workbench.generation import (
    execute_generation_plan,
    load_generation_execution,
    recover_generation,
    validate_generation_approval,
)
from structure_aware_retrieval.workbench.importing import import_repository, load_repository
from structure_aware_retrieval.workbench.preparation import load_preparation, prepare_repository
from structure_aware_retrieval.workbench.storage import read_json, safe_path, write_json

_JOB_ID = re.compile(r"[0-9a-f]{32}")
_REPOSITORY_ID = re.compile(r"[0-9a-f]{64}")
_TERMINAL = {"completed", "failed", "interrupted"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


class JobUnavailableError(Exception):
    """A job cannot be accepted because the workbench is busy or closing."""

    def __init__(self, status: int, message: str, **fields):
        super().__init__(message)
        self.status = status
        self.payload = {"error": message, **fields}


class _Stopped(BaseException):
    """Stop at the next saved service checkpoint after server shutdown."""


def read_job(workspace: Path, job_id: str) -> dict:
    if not isinstance(job_id, str) or _JOB_ID.fullmatch(job_id) is None:
        raise ValueError("Invalid repository, run, or job identifier")
    record = read_json(workspace, f"web-jobs/{job_id}.json")
    if (
        record.get("schema_version") != 1
        or record.get("job_id") != job_id
        or record.get("kind") not in {"import", "prepare", "preview", "generation"}
        or record.get("status") not in _TERMINAL | {"queued", "running"}
    ):
        raise ValueError("Invalid browser job record")
    return record


class Jobs:
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
                    record = read_job(workspace, path.stem)
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
                    rows.append(read_job(self.workspace, path.stem))
                except (OSError, ValueError):
                    rows.append(
                        {"job_id": path.stem, "status": "unreadable", "error": "Invalid saved job"}
                    )
        return sorted(rows, key=lambda row: row.get("created_at", ""), reverse=True)

    def submit(self, kind: str, payload: dict) -> dict:
        with self.lock:
            if self.closed:
                raise JobUnavailableError(503, "Workbench is closing")
            if self.active is not None:
                raise JobUnavailableError(409, "Another task is running", job_id=self.active)
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
                record = read_job(self.workspace, self.active)
                record.update(
                    status="interrupted",
                    finished_at=_now(),
                    error="Server stopped; no automatic retry",
                )
                self._save(record)
            else:
                on_stopped()


def repositories(workspace: Path) -> list[dict]:
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
