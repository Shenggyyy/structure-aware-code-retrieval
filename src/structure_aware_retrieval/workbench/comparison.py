"""Five retrieval contexts in one durable run, without answer generation."""

import hashlib
import re
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from structure_aware_retrieval.embeddings import Encoder, SentenceEncoder
from structure_aware_retrieval.indexing import load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import complete_question, prepare_question
from structure_aware_retrieval.strategies import (
    RRF_K,
    STRATEGIES,
    SYMBOL_WEIGHTS,
    create_retriever,
)
from structure_aware_retrieval.structure import StructureConfig
from structure_aware_retrieval.workbench.preparation import load_preparation
from structure_aware_retrieval.workbench.storage import (
    read_json,
    safe_path,
    workspace_root,
    write_json,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _error(error: Exception) -> dict:
    return {"type": type(error).__name__, "message": str(error)[:2000]}


def _run_path(run_id: str) -> str:
    if not isinstance(run_id, str) or not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise ValueError("Comparison ID must be 32 lowercase hexadecimal characters")
    return f"runs/{run_id}/run.json"


def _save(workspace: Path, record: dict) -> None:
    record["fingerprint"] = stable_id({k: v for k, v in record.items() if k != "fingerprint"})
    write_json(workspace, _run_path(record["run_id"]), record)


def _artifact(workspace: Path, resources: dict, name: str) -> Path:
    relative = resources.get(name)
    expected = resources.get("artifact_hashes", {}).get(name)
    if relative is None or expected is None:
        detail = resources.get("stages", {}).get(name, {}).get("error")
        raise ValueError(f"{name} resource is unavailable; prepare the repository first. {detail}")
    path = safe_path(workspace, relative)
    with path.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"{name} resource checksum mismatch; existing artifact was not changed")
    return path


class _Capture:
    def __init__(self, retriever):
        self.retriever = retriever
        self.index = retriever.index
        self.hits = []

    def search(self, query: str, *, top_k: int = 5):
        self.hits = self.retriever.search(query, top_k=top_k)
        return self.hits


def preview_question(
    workspace: Path,
    repository_id: str,
    question: str,
    *,
    model_cache: Path = Path("artifacts/models"),
    top_k: int = 10,
    max_context_bytes: int = 16000,
    encoder: Encoder | None = None,
) -> dict:
    """Persist all five outcomes; an injected encoder is explicitly labeled as a fixture."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be nonblank")
    if len(question.encode("utf-8")) > 4000:
        raise ValueError("Question exceeds the 4000-byte limit")
    if type(top_k) is not int or not 1 <= top_k <= 100:
        raise ValueError("top_k must be an integer in [1, 100]")
    if type(max_context_bytes) is not int or not 2 <= max_context_bytes <= 1_000_000:
        raise ValueError("max_context_bytes must be an integer in [2, 1000000]")
    root = workspace_root(workspace, create=True)
    resources = load_preparation(root, repository_id)
    run_id = uuid4().hex
    safe_path(root, f"runs/{run_id}").mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    record = {
        "schema_version": 1,
        "kind": "five_strategy_comparison",
        "run_id": run_id,
        "repository_id": repository_id,
        "created_at": _now(),
        "finished_at": None,
        "mode": "context_preview",
        "status": "running",
        "question": question,
        "resources": resources,
        "settings": {
            "strategies": list(STRATEGIES),
            "context_top_k": top_k,
            "display_top_k": top_k,
            "max_context_bytes": max_context_bytes,
            "ranking_policy": "display_top_k_plus_selected_context_chunks",
            "rrf_k": RRF_K,
            "symbol_weights": SYMBOL_WEIGHTS,
            "structure": StructureConfig().describe(),
            "generation_enabled": False,
            "answer_model": None,
            "max_output_tokens": None,
        },
        "encoder_mode": "injected_encoder" if encoder is not None else resources["execution_mode"],
        "shared_setup": {"encoder_load_ms": None, "encoder_error": None},
        "elapsed_ms": None,
        "api_calls": 0,
        "benchmark_metrics": None,
        "relevance_labels": "unlabeled",
        "results": [
            {
                "strategy": strategy,
                "status": "pending",
                "error": None,
                "hits": [],
                "ranked_candidates": None,
                "structure_stats": None,
                "qa": None,
                "timing_ms": {
                    "resource_load": None,
                    "retrieval": None,
                    "context_and_prompt": None,
                    "automatic_validation": None,
                    "generation": None,
                    "strategy_total": None,
                },
                "tokens": {"input": None, "output": None, "total": None, "cached": None},
                "cost": {"estimated_usd": None, "billed_usd": None, "model_calls": 0},
            }
            for strategy in STRATEGIES
        ],
    }
    _save(root, record)
    try:
        if encoder is None and resources.get("vectors") is not None:
            load_started = time.perf_counter()
            try:
                encoder = SentenceEncoder(model_cache)
            except Exception as error:
                record["shared_setup"]["encoder_error"] = _error(error)
            finally:
                record["shared_setup"]["encoder_load_ms"] = (
                    time.perf_counter() - load_started
                ) * 1000
            _save(root, record)
        for row in record["results"]:
            row["status"] = "running"
            _save(root, record)
            row_started = time.perf_counter()
            try:
                index = load_index(_artifact(root, resources, "index"))
                if index.metadata["snapshot_id"] != resources["snapshot_id"]:
                    raise ValueError("Prepared index snapshot differs from resource manifest")
                vectors = (
                    None if row["strategy"] == "bm25" else _artifact(root, resources, "vectors")
                )
                graph = (
                    _artifact(root, resources, "graph") if row["strategy"] == "structure" else None
                )
                if row["strategy"] != "bm25" and encoder is None:
                    raise ValueError(
                        "Pinned encoder unavailable; install the dense extra and prepare-model. "
                        f"{record['shared_setup']['encoder_error']}"
                    )
                retriever = create_retriever(
                    row["strategy"], index, encoder=encoder, vectors=vectors, graph=graph
                )
                row["timing_ms"]["resource_load"] = (time.perf_counter() - row_started) * 1000
                capture = _Capture(retriever)
                prepared = prepare_question(
                    capture, question, top_k=top_k, max_context_bytes=max_context_bytes
                )
                qa = complete_question(prepared)
                selected = {source["chunk_id"] for source in qa["context"]["evidence"]}
                row["hits"] = [
                    asdict(hit)
                    for position, hit in enumerate(capture.hits)
                    if position < top_k or hit.chunk_id in selected
                ]
                row["ranked_candidates"] = len(capture.hits)
                row["structure_stats"] = getattr(retriever, "last_stats", None)
                row["qa"] = qa
                row["status"] = qa["status"]
                row["timing_ms"].update(
                    retrieval=qa["timing_ms"]["retrieval"],
                    context_and_prompt=qa["timing_ms"]["context_and_prompt"],
                    automatic_validation=qa["timing_ms"]["generation_and_validation"],
                )
            except Exception as error:
                row["status"] = "failed"
                row["error"] = _error(error)
            row["timing_ms"]["strategy_total"] = (time.perf_counter() - row_started) * 1000
            _save(root, record)
    except BaseException:
        for row in record["results"]:
            if row["status"] == "running":
                row["status"] = "interrupted"
        record["status"] = "interrupted"
        record["finished_at"] = _now()
        record["elapsed_ms"] = (time.perf_counter() - started) * 1000
        _save(root, record)
        raise
    failures = sum(row["status"] == "failed" for row in record["results"])
    record["status"] = "failed" if failures == 5 else "partial" if failures else "preview_complete"
    record["elapsed_ms"] = (time.perf_counter() - started) * 1000
    record["finished_at"] = _now()
    _save(root, record)
    return record


def load_comparison(workspace: Path, run_id: str) -> dict:
    """Reopen self-contained results even if prepared resources or source are gone."""
    record = read_json(workspace, _run_path(run_id))
    fingerprint = stable_id({k: v for k, v in record.items() if k != "fingerprint"})
    if (
        record.get("schema_version") != 1
        or record.get("kind") != "five_strategy_comparison"
        or record.get("run_id") != run_id
        or record.get("fingerprint") != fingerprint
        or not isinstance(record.get("results"), list)
        or any(not isinstance(row, dict) for row in record["results"])
        or [row.get("strategy") for row in record["results"]] != list(STRATEGIES)
    ):
        raise ValueError("Comparison record identity or checksum mismatch")
    return record


def list_comparisons(workspace: Path) -> list[dict]:
    """List valid runs and damaged records separately; never silently discard failures."""
    directory = safe_path(workspace, "runs")
    if not directory.exists():
        return []
    rows = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name, reverse=True):
        if not re.fullmatch(r"[0-9a-f]{32}", path.name):
            continue
        try:
            record = load_comparison(workspace, path.name)
            rows.append(
                {
                    key: record[key]
                    for key in (
                        "run_id",
                        "repository_id",
                        "question",
                        "created_at",
                        "mode",
                        "status",
                    )
                }
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            rows.append({"run_id": path.name, "status": "unreadable", "error": _error(error)})
    return sorted(rows, key=lambda row: (row.get("created_at", ""), row["run_id"]), reverse=True)
