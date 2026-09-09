"""Local state files with confined paths and atomic JSON publication."""

import json
import os
import tempfile
from pathlib import Path, PurePosixPath


def _reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError("Workspace paths cannot contain symbolic links or junctions")


def workspace_root(workspace: Path, *, create: bool = False) -> Path:
    root = Path(os.path.abspath(workspace))
    _reject_links(root)
    if create:
        root.mkdir(parents=True, exist_ok=True)
    if root.exists() and not root.is_dir():
        raise ValueError("Workspace must be a directory")
    return root


def safe_path(workspace: Path, relative: str) -> Path:
    root = workspace_root(workspace)
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("State path must be a relative POSIX path")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise ValueError("State path must stay inside the workspace")
    if any(ord(char) < 32 or ord(char) == 127 for char in relative):
        raise ValueError("Control characters are not allowed in state paths")
    target = root.joinpath(*path.parts)
    _reject_links(target)
    return target


def write_json(workspace: Path, relative: str, value: object) -> None:
    target = safe_path(workspace, relative)
    data = json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_path(workspace, relative)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent, suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_json(workspace: Path, relative: str) -> dict:
    target = safe_path(workspace, relative)
    with target.open("rb") as handle:
        data = handle.read(128 * 1024 * 1024 + 1)
    if len(data) > 128 * 1024 * 1024:
        raise ValueError("State record exceeds the size limit")
    result = json.loads(data)
    if not isinstance(result, dict):
        raise ValueError("State record must be an object")
    return result
