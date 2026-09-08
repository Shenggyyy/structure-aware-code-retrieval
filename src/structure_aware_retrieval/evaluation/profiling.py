"""One operation per fresh process, including native allocations in peak memory."""

import argparse
import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


def peak_memory() -> dict:
    """OS high-water mark for this process, not a delta or process-tree total."""
    if sys.platform == "win32":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
                (name, ctypes.c_size_t)
                for name in (
                    "peak",
                    "working",
                    "peak_paged",
                    "paged",
                    "peak_nonpaged",
                    "nonpaged",
                    "pagefile",
                    "peak_pagefile",
                )
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(Counters),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(
            kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return {"bytes": counters.peak, "method": "GetProcessMemoryInfo.PeakWorkingSetSize"}
    if sys.platform in {"linux", "darwin"}:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {
            "bytes": int(value * (1024 if sys.platform == "linux" else 1)),
            "method": "getrusage(RUSAGE_SELF).ru_maxrss",
        }
    raise ValueError("Peak-memory profiling supports Windows, Linux and macOS")


def execute_job(job: dict) -> dict:
    """Called in a child interpreter; imports and input loads are timed too."""
    start = time.perf_counter()
    output = Path(job["output"])
    kind = job["kind"]
    if kind == "experiment":
        from structure_aware_retrieval.evaluation.config import load_config
        from structure_aware_retrieval.evaluation.dataset import load_benchmark
        from structure_aware_retrieval.evaluation.runner import run_experiment

        config_path = Path(job["config"])
        if (
            "config_sha256" in job
            and hashlib.sha256(config_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            != job["config_sha256"]
        ):
            raise ValueError("Experiment configuration changed after freeze")
        if (
            "benchmark_digest" in job
            and load_benchmark(load_config(config_path).benchmark).digest != job["benchmark_digest"]
        ):
            raise ValueError("Benchmark changed after freeze")
        summary = run_experiment(config_path, output)
        details = {"quality_fingerprint": summary["quality_fingerprint"]}
    elif kind in {"index", "graph", "vectors"}:
        from structure_aware_retrieval.indexing import build_index, load_index

        if kind == "index":
            metadata = build_index(Path(job["source"]), output, **job["index_options"])
            if metadata["snapshot_id"] != job["snapshot_id"]:
                raise ValueError("Rebuilt index differs from the frozen snapshot")
            if metadata["git"] != {"commit": job["commit"], "dirty": False}:
                raise ValueError("Source checkout must be clean and at the pinned commit")
            details = {
                key: metadata[key] for key in ("snapshot_id", "files_indexed", "diagnostics")
            }
        else:
            index = load_index(Path(job["index"]))
            if index.metadata["snapshot_id"] != job["snapshot_id"]:
                raise ValueError("Profile input snapshot mismatch")
            if kind == "graph":
                from structure_aware_retrieval.relations import build_graph

                metadata = build_graph(index, output)
                details = {
                    key: metadata[key]
                    for key in ("graph_hash", "edge_counts", "unresolved_counts", "build_seconds")
                }
            else:
                from structure_aware_retrieval.embeddings import SentenceEncoder, build_vectors

                metadata = build_vectors(index, SentenceEncoder(Path(job["model_cache"])), output)
                details = {key: value for key, value in metadata.items() if key != "binding"}
                details["encoder"] = metadata["binding"]["encoder"]
            details.update(symbols=len(index.symbols), chunks=len(index.chunks))
        details["artifact_bytes"] = output.stat().st_size
    else:
        raise ValueError(f"Unknown profile job: {kind}")
    seconds = time.perf_counter() - start
    memory = peak_memory()
    return {
        "schema_version": 1,
        "kind": kind,
        "operation_seconds": seconds,
        "peak_memory": memory,
        "memory_scope": "fresh_worker_process_lifetime_including_imports_not_children",
        "runtime": {
            "python": platform.python_version(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cpus": os.cpu_count(),
            "thread_environment": {
                name: os.environ.get(name)
                for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
            },
        },
        "details": details,
    }


def profile_job(job: dict, directory: Path) -> dict:
    """Preserve job, logs and completion evidence; never reuse partial measurements."""
    directory.mkdir(parents=True, exist_ok=False)
    job_path = directory / "job.json"
    job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")
    result_path = directory / "profile.json"
    env = {
        **os.environ,
        "OMP_NUM_THREADS": "4",
        "MKL_NUM_THREADS": "4",
        "OPENBLAS_NUM_THREADS": "4",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "TOKENIZERS_PARALLELISM": "false",
    }
    start = time.perf_counter()
    with (directory / "worker.log").open("w", encoding="utf-8") as log:
        completed = subprocess.run(
            [sys.executable, "-m", __name__, str(job_path.resolve()), str(result_path.resolve())],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            check=False,
        )
    wall = time.perf_counter() - start
    if completed.returncode != 0:
        (directory / "failure.json").write_text(
            json.dumps({"returncode": completed.returncode, "wall_seconds": wall}), encoding="utf-8"
        )
        raise RuntimeError(f"Profile worker failed; inspect {directory / 'worker.log'}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["worker_wall_seconds"] = wall
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    if args.result.exists():
        parser.error("Profile result already exists")
    result = execute_job(json.loads(args.job.read_text(encoding="utf-8")))
    with args.result.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
