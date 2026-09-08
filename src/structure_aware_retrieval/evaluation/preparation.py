"""Explicit, opt-in fetching of pinned benchmark sources; never run by evaluation."""

import os
import re
import subprocess
from pathlib import Path

from structure_aware_retrieval.evaluation.dataset import load_benchmark, validate_index
from structure_aware_retrieval.indexing import build_index, load_index


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as error:
        raise ValueError(f"Git failed: {error.stderr.strip()}") from error
    except subprocess.TimeoutExpired as error:
        raise ValueError("Git operation timed out") from error


def prepare_benchmark(manifest: Path, destination: Path, *, rebuild: bool = False) -> list[dict]:
    benchmark = load_benchmark(manifest)
    records = []
    for repository in benchmark.repositories:
        checkout = (destination / "repos" / repository.id).resolve()
        if not checkout.exists():
            checkout.parent.mkdir(parents=True, exist_ok=True)
            if re.fullmatch(r"[0-9a-f]{40}", repository.ref):
                if repository.ref != repository.commit:
                    raise ValueError("A commit ref must equal the pinned repository commit")
                _git("init", str(checkout))
                _git("-C", str(checkout), "remote", "add", "origin", repository.url)
                _git("-C", str(checkout), "fetch", "--depth", "1", "origin", repository.commit)
                _git(
                    "-C",
                    str(checkout),
                    "-c",
                    "core.autocrlf=false",
                    "checkout",
                    "--detach",
                    "FETCH_HEAD",
                )
            else:
                _git(
                    "-c",
                    "core.autocrlf=false",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    repository.ref,
                    repository.url,
                    str(checkout),
                )
        # Never checkout/reset an existing directory or silently use a containing repo.
        if Path(_git("-C", str(checkout), "rev-parse", "--show-toplevel")).resolve() != checkout:
            raise ValueError(f"Expected a standalone checkout at {checkout}")
        if _git("-C", str(checkout), "rev-parse", "HEAD") != repository.commit:
            raise ValueError(
                f"{repository.id}: pinned commit mismatch; existing checkout was not changed"
            )
        if _git("-C", str(checkout), "status", "--porcelain", "--untracked-files=normal"):
            raise ValueError(f"{repository.id}: checkout is dirty; existing files were not changed")
        database = destination / "indexes" / f"{repository.id}.sqlite"
        if rebuild or not database.exists():
            build_index(checkout, database, overwrite=rebuild)
        index = load_index(database)
        validate_index(benchmark, repository, index)
        records.append(
            {
                "repository": repository.id,
                "index": str(database.resolve()),
                "snapshot_id": index.metadata["snapshot_id"],
            }
        )
    return records
