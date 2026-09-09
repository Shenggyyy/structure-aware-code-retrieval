"""Bounded static snapshots of local trees and public HTTPS Git repositories.

Remote trees are read as Git blobs, never checked out. Local Git metadata is only
an optional HEAD anchor: the copied bytes, rather than a cleanliness claim, bind
the source identity. No repository code or dependency installation is invoked.
"""

import hashlib
import ipaddress
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import tempfile
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from pathspec import GitIgnoreSpec

from structure_aware_retrieval.ingestion import EXCLUDED_DIRECTORIES
from structure_aware_retrieval.workbench.storage import workspace_root, write_json

MAX_FILE_BYTES = 1_048_576
MAX_TOTAL_BYTES = 52_428_800
MAX_FILES = 10_000
MAX_ENTRIES = 100_000
MAX_DEPTH = 60
SCAN_SECONDS = 60
GIT_SECONDS = 180
_ID = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
_RESERVED = re.compile(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", re.I)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    write_json(path.parent, path.name, value)


def _linked(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _inside(root: Path, relative: str) -> Path:
    """Reject links along an owned path before reading or writing it."""
    parts = _safe_relative(relative).parts
    current = root
    for part in parts:
        current /= part
        if _linked(current):
            raise ValueError("Workspace paths must not contain links or junctions")
    if not current.resolve().is_relative_to(root):
        raise ValueError("Workspace path escapes its root")
    return current


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or path.as_posix() != value
        or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or any(
            part in {".", ".."}
            or any(character in part for character in ':*?"<>|')
            or part.endswith((".", " "))
            or _RESERVED.fullmatch(part)
            for part in path.parts
        )
    ):
        raise ValueError("Repository contains a non-portable or unsafe source path")
    return path


def _validate_ref(ref: str) -> None:
    if (
        not isinstance(ref, str)
        or not _REF.fullmatch(ref)
        or ".." in ref
        or "//" in ref
        or ref.endswith(("/", ".", ".lock"))
        or any(part.startswith(".") for part in ref.split("/"))
    ):
        raise ValueError("Use HEAD, a branch/tag name, or a hexadecimal commit as ref")


def _public_url(source: str) -> tuple[str, str]:
    """Conservative URL syntax avoids parser disagreement and credential leakage."""
    if any(ord(character) <= 32 or ord(character) >= 127 for character in source):
        raise ValueError("HTTPS Git URL must contain printable ASCII without whitespace")
    if any(character in source for character in "\\%?#"):
        raise ValueError("HTTPS Git URL must not contain escapes, query strings, or fragments")
    try:
        parsed = urlsplit(source)
        port = parsed.port
    except ValueError as error:
        raise ValueError("Invalid HTTPS Git URL") from error
    host = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", host)
        or "." not in host
        or host.lower().endswith((".localhost", ".local", ".internal", ".test", ".invalid"))
        or not all(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", x) for x in host.split(".")
        )
        or not re.fullmatch(r"/[A-Za-z0-9._~/-]+", parsed.path)
        or any(part in {".", ".."} for part in parsed.path.split("/"))
        or "//" in parsed.path
    ):
        raise ValueError(
            "Use a public HTTPS Git URL without credentials, redirects, or extra ports"
        )
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("Use a public DNS hostname rather than an IP address")
    return f"https://{host.lower()}{parsed.path}", host.lower()


def _public_address(host: str) -> str:
    try:
        addresses = {
            record[4][0] for record in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        }
    except OSError as error:
        raise ValueError("Cannot resolve public Git hostname") from error
    if not addresses:
        raise ValueError("Public Git hostname has no addresses")
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if not parsed.is_global or parsed.is_multicast or parsed.is_unspecified:
            raise ValueError("Git hostname resolves to a non-public address")
    # Bind the checked address to libcurl; later DNS changes cannot redirect fetch.
    address = sorted(addresses, key=lambda item: (":" in item, item))[0]
    return f"[{address}]" if ":" in address else address


def _git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("GIT_", "CURL_", "SSH_"))
        and key.upper()
        not in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "OPENAI_API_KEY"}
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_ATTR_NOSYSTEM": "1",
        }
    )
    return environment


def _git(*arguments: str, cwd: Path, resolve: str | None = None) -> bytes:
    settings = [
        "credential.helper=",
        "credential.interactive=false",
        "core.askPass=",
        "core.hooksPath=" + os.devnull,
        "core.fsmonitor=false",
        "core.attributesFile=" + os.devnull,
        "protocol.allow=never",
        "protocol.https.allow=always",
        "http.followRedirects=false",
        "http.proxy=",
        "http.sslVerify=true",
        "http.extraHeader=",
        "http.cookieFile=",
        "http.saveCookies=false",
        "http.emptyAuth=false",
        "http.delegation=none",
        "http.lowSpeedLimit=1024",
        "http.lowSpeedTime=30",
        "submodule.recurse=false",
        "fetch.recurseSubmodules=false",
        "maintenance.auto=false",
        "gc.auto=0",
        "transfer.fsckObjects=true",
    ]
    if resolve is not None:
        settings.append("http.curloptResolve=" + resolve)
    executable = shutil.which("git")
    if executable is None:
        raise ValueError("Git is required and must be available on PATH")
    command = [
        str(Path(executable).resolve()),
        *(argument for setting in settings for argument in ("-c", setting)),
        *arguments,
    ]
    try:
        # Git/libcurl may consult .netrc independently of Git configuration.
        # An empty home also prevents ambient authentication files being used.
        with (
            tempfile.TemporaryDirectory(prefix="sacr-git-") as home,
            tempfile.TemporaryFile() as output,
        ):
            environment = _git_environment()
            environment.update(HOME=home, USERPROFILE=home, XDG_CONFIG_HOME=home)
            subprocess.run(
                command,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=GIT_SECONDS,
            )
            output.seek(0)
            result = output.read(MAX_TOTAL_BYTES + 1)
            if len(result) > MAX_TOTAL_BYTES:
                raise ValueError("Git metadata output exceeds its size limit")
    except subprocess.TimeoutExpired as error:
        raise ValueError("Git operation exceeded its time limit") from error
    except subprocess.CalledProcessError as error:
        # Stderr can contain a supplied URL or remote-controlled terminal content.
        raise ValueError(
            "Git operation failed; confirm a public repository and valid ref"
        ) from error
    except OSError as error:
        raise ValueError("Git is required and must be available on PATH") from error
    return result


def _local_commit(root: Path) -> str | None:
    try:
        value = _git("rev-parse", "--verify", "HEAD", cwd=root).decode("ascii").strip()
        return value if _COMMIT.fullmatch(value) else None
    except (ValueError, UnicodeError):
        return None


def _collect(root: Path) -> tuple[dict[str, bytes], dict]:
    """Reuse scanner ignore semantics with strict workbench resource bounds."""
    files: dict[str, bytes] = {}
    portable_names: set[str] = set()
    total_bytes = 0
    entries_seen = 0
    links_skipped = 0
    excluded_entries = 0
    started = time.monotonic()

    def add(path: Path) -> bytes:
        nonlocal total_bytes
        relative = path.relative_to(root).as_posix()
        _safe_relative(relative)
        if relative.casefold() in portable_names:
            raise ValueError("Repository source paths collide on case-insensitive filesystems")
        if len(files) >= MAX_FILES:
            raise ValueError("Repository exceeds the source file count limit")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("Repository source or ignore file exceeds the per-file size limit")
        with path.open("rb") as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("Repository source or ignore file exceeds the per-file size limit")
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("Repository exceeds the total source size limit")
        files[relative] = data
        portable_names.add(relative.casefold())
        return data

    def walk(directory: Path, inherited: list[tuple[Path, GitIgnoreSpec]], depth: int) -> None:
        nonlocal entries_seen, links_skipped, excluded_entries
        if depth > MAX_DEPTH or time.monotonic() - started > SCAN_SECONDS:
            raise ValueError("Repository scan exceeded its depth or time limit")
        rules = list(inherited)
        ignore = directory / ".gitignore"
        if ignore.is_file() and not _linked(ignore):
            try:
                rules.append(
                    (
                        directory,
                        GitIgnoreSpec.from_lines(add(ignore).decode("utf-8-sig").splitlines()),
                    )
                )
            except UnicodeError as error:
                raise ValueError("Repository .gitignore must be UTF-8") from error
        with os.scandir(directory) as entries:
            children = []
            for entry in entries:
                entries_seen += 1
                if entries_seen > MAX_ENTRIES or time.monotonic() - started > SCAN_SECONDS:
                    raise ValueError("Repository scan exceeded its entry count or time limit")
                children.append(entry)
        for entry in sorted(children, key=lambda item: item.name):
            path = Path(entry.path)
            if _linked(path):
                links_skipped += 1
                continue
            is_directory = entry.is_dir(follow_symlinks=False)
            if is_directory and entry.name in EXCLUDED_DIRECTORIES:
                excluded_entries += 1
                continue
            suffix = "/" if is_directory else ""
            ignored = False
            for base, spec in rules:
                match = spec.check_file(path.relative_to(base).as_posix() + suffix)
                if match.include is not None:
                    ignored = match.include
            if ignored:
                excluded_entries += 1
                continue
            if is_directory:
                _safe_relative(path.relative_to(root).as_posix())
                walk(path, rules, depth + 1)
            elif entry.is_file(follow_symlinks=False) and path.suffix == ".py":
                add(path)

    walk(root, [], 0)
    if not any(path.endswith(".py") for path in files):
        raise ValueError("Repository contains no included Python source files")
    return files, {"links_skipped": links_skipped, "excluded_entries": excluded_entries}


def _remote_tree(url: str, host: str, ref: str, staging: Path) -> tuple[Path, str]:
    started = time.monotonic()
    address = _public_address(host)
    configuration = _git("help", "--config", cwd=staging)
    if b"http.curloptResolve" not in configuration.splitlines():
        raise ValueError("Git with http.curloptResolve support is required for public imports")
    bare = staging / "git"
    _git("init", "--bare", "--template=", str(bare), cwd=staging)
    _git(
        "fetch",
        "--depth=1",
        "--no-tags",
        "--no-recurse-submodules",
        "--",
        url,
        ref,
        cwd=bare,
        resolve=f"{host}:443:{address}",
    )
    commit = _git("rev-parse", "--verify", "FETCH_HEAD^{commit}", cwd=bare).decode("ascii").strip()
    if not _COMMIT.fullmatch(commit):
        raise ValueError("Git fetch did not resolve to a valid commit")
    if _COMMIT.fullmatch(ref.lower()) and commit != ref.lower():
        raise ValueError("Fetched commit differs from the requested commit")
    tree = _git("ls-tree", "-rz", "--full-tree", commit, cwd=bare)
    entries = tree.split(b"\0")
    if len(entries) > MAX_ENTRIES + 1:
        raise ValueError("Remote repository exceeds the tree entry limit")
    source = staging / "tree"
    source.mkdir()
    total_bytes = 0
    selected = 0
    portable_names: set[str] = set()
    for entry in entries:
        if time.monotonic() - started > GIT_SECONDS * 2:
            raise ValueError("Remote repository preparation exceeded its total time limit")
        if not entry:
            continue
        try:
            description, raw_path = entry.split(b"\t", 1)
            mode, kind, object_id = description.decode("ascii").split()
            name = raw_path.decode("utf-8")
        except (ValueError, UnicodeError) as error:
            raise ValueError("Remote tree contains invalid metadata or non-UTF-8 paths") from error
        if mode not in {"100644", "100755"} or kind != "blob":
            continue  # No symlinks, gitlinks, submodules, or special file types.
        path = _safe_relative(name)
        if len(path.parts) > MAX_DEPTH:
            raise ValueError("Remote repository exceeds the source path depth limit")
        if any(part in EXCLUDED_DIRECTORIES for part in path.parts[:-1]):
            continue
        if path.suffix != ".py" and path.name != ".gitignore":
            continue
        if name.casefold() in portable_names:
            raise ValueError("Repository source paths collide on case-insensitive filesystems")
        portable_names.add(name.casefold())
        if not _COMMIT.fullmatch(object_id):
            raise ValueError("Remote tree contains an invalid blob ID")
        size = int(_git("cat-file", "-s", object_id, cwd=bare).strip())
        selected += 1
        total_bytes += size
        if selected > MAX_FILES or size > MAX_FILE_BYTES or total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("Remote repository exceeds the source size or count limit")
        data = _git("cat-file", "blob", object_id, cwd=bare)
        if len(data) != size:
            raise ValueError("Remote source blob size changed unexpectedly")
        target = _inside(source.resolve(), name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return source, commit


def _identity(source: dict, files: list[dict]) -> str:
    return _digest({"schema_version": 1, "source": source, "files": files})


def _cached_pinned(workspace: Path, url: str, ref: str) -> dict | None:
    """An exact commit needs no new resolution; mutable refs still require fetch."""
    if not _COMMIT.fullmatch(ref.lower()):
        return None
    repositories = _inside(workspace, "repositories")
    if not repositories.exists():
        return None
    inspected = 0
    for child in repositories.iterdir():
        if not _ID.fullmatch(child.name):
            continue
        inspected += 1
        if inspected > MAX_FILES:
            raise ValueError("Repository cache inventory exceeds its entry limit")
        path = _inside(workspace, f"repositories/{child.name}/manifest.json")
        try:
            with path.open("rb") as handle:
                data = handle.read(5_000_001)
            if len(data) > 5_000_000:
                raise ValueError("Repository manifest is too large")
            candidate = json.loads(data)
            provenance = candidate["source"]
            if not isinstance(provenance, dict):
                raise ValueError("Invalid repository cache manifest")
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise ValueError("Cannot inspect a valid frozen repository cache") from error
        if (
            provenance.get("kind") == "https"
            and provenance.get("location") == url
            and provenance.get("requested_ref") == ref
            and provenance.get("commit") == ref.lower()
        ):
            # A corrupt matching snapshot is an error, never a reason to silently
            # re-download or replace history under its old identity.
            return load_repository(workspace, child.name)
    return None


def _remove_staging(workspace: Path, staging: Path) -> None:
    """Remove one owned temporary tree, including Git's Windows read-only packs."""
    workspace = workspace_root(workspace)
    staging_root = _inside(workspace, ".staging")
    target = _inside(workspace, staging.relative_to(workspace).as_posix())
    if target == staging_root or not target.is_relative_to(staging_root):
        raise ValueError("Cleanup target must be one owned staging directory")
    if not target.exists():
        return
    # Never traverse a junction or link even if an unexpected one was introduced
    # into the owned directory. A failed cleanup does not invalidate a snapshot.
    for parent, directories, files in os.walk(target, followlinks=False):
        for name in [*directories, *files]:
            if _linked(Path(parent) / name):
                raise ValueError("Cleanup cannot traverse a link or junction")

    def clear_readonly(function, path: str, error: BaseException) -> None:
        if not isinstance(error, PermissionError):
            raise error
        candidate = Path(os.path.abspath(path))
        if candidate != target and not candidate.is_relative_to(target):
            raise ValueError("Cleanup retry escaped its owned staging directory")
        candidate = _inside(workspace, candidate.relative_to(workspace).as_posix())
        mode = candidate.stat(follow_symlinks=False).st_mode
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise error
        candidate.chmod(mode | stat.S_IWRITE)
        function(path)

    shutil.rmtree(target, onexc=clear_readonly)


def load_repository(workspace: Path, repository_id: str) -> dict:
    """Load an immutable manifest only after checking every snapshotted byte."""
    if not isinstance(repository_id, str) or not _ID.fullmatch(repository_id):
        raise ValueError("Invalid repository ID")
    workspace = workspace_root(workspace)
    manifest_path = _inside(workspace, f"repositories/{repository_id}/manifest.json")
    try:
        if manifest_path.stat().st_size > 5_000_000:
            raise ValueError("Repository manifest is too large")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source = manifest["source"]
        files = manifest["files"]
        expected_directory = f"repositories/{repository_id}/source"
        if (
            manifest["schema_version"] != 1
            or manifest["repository_id"] != repository_id
            or manifest["source_directory"] != expected_directory
            or not isinstance(source, dict)
            or source["kind"] not in {"local", "https"}
            or not isinstance(source["location"], str)
            or not isinstance(source["working_tree"], bool)
            or source["working_tree"] != (source["kind"] == "local")
            or source["dirty"] is not (None if source["working_tree"] else False)
            or (source["commit"] is not None and not _COMMIT.fullmatch(source["commit"]))
            or (source["kind"] == "https" and source["commit"] is None)
            or not isinstance(files, list)
            or not 1 <= len(files) <= MAX_FILES
            or not isinstance(manifest["created_at"], str)
        ):
            raise ValueError("Invalid repository manifest")
        _validate_ref(source["requested_ref"])
        if _identity(source, files) != repository_id:
            raise ValueError("Repository manifest identity mismatch")
        directory = _inside(workspace, expected_directory)
        expected: dict[str, dict] = {}
        for record in files:
            name = record["path"]
            path = _safe_relative(name)
            if (
                name in expected
                or (path.suffix != ".py" and path.name != ".gitignore")
                or type(record["bytes"]) is not int
                or not 0 <= record["bytes"] <= MAX_FILE_BYTES
                or not _ID.fullmatch(record["sha256"])
            ):
                raise ValueError("Invalid repository source record")
            expected[name] = record
        actual: set[str] = set()
        total = 0
        entries_seen = 0
        for parent, directories, names in os.walk(directory, followlinks=False):
            for name in [*directories, *names]:
                entries_seen += 1
                if entries_seen > MAX_ENTRIES:
                    raise ValueError("Frozen repository exceeds its entry count limit")
                item = Path(parent) / name
                if _linked(item):
                    raise ValueError("Frozen repository contains a link or junction")
            for name in names:
                path = Path(parent) / name
                relative = path.relative_to(directory).as_posix()
                if relative not in expected:
                    raise ValueError("Frozen repository contains an unexpected file")
                record = expected[relative]
                if path.stat().st_size != record["bytes"]:
                    raise ValueError("Frozen repository source integrity mismatch")
                with path.open("rb") as handle:
                    data = handle.read(MAX_FILE_BYTES + 1)
                total += len(data)
                if total > MAX_TOTAL_BYTES or hashlib.sha256(data).hexdigest() != record["sha256"]:
                    raise ValueError("Frozen repository source integrity mismatch")
                actual.add(relative)
        if actual != set(expected):
            raise ValueError("Frozen repository is missing source files")
    except (KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Cannot load a valid frozen repository manifest and source") from error
    return manifest


def import_repository(source: str, workspace: Path, *, ref: str = "HEAD") -> dict:
    """Import once, retaining progress/errors and never replacing a cached snapshot."""
    workspace = workspace_root(workspace, create=True)
    job_id = uuid.uuid4().hex
    job_path = _inside(workspace, f"jobs/{job_id}.json")
    staging = _inside(workspace, f".staging/{job_id}")
    job = {"schema_version": 1, "job_id": job_id, "status": "created", "events": []}

    def progress(status: str, **fields: object) -> None:
        job.update(status=status, **fields)
        job["events"].append({"status": status, "at": datetime.now(UTC).isoformat()})
        _write_json(job_path, job)

    progress("validating")
    try:
        _validate_ref(ref)
        if not isinstance(source, str) or not source or any(ord(char) < 32 for char in source):
            raise ValueError("Repository source must be a local directory or public HTTPS Git URL")
        staging.mkdir(parents=True)
        if "://" in source or source.startswith(("git@", "https:")):
            url, host = _public_url(source)
            cached = _cached_pinned(workspace, url, ref)
            if cached is not None:
                progress("completed", repository_id=cached["repository_id"], cache_hit=True)
                return cached
            progress("downloading")
            root, commit = _remote_tree(url, host, ref, staging)
            provenance = {
                "kind": "https",
                "location": url,
                "requested_ref": ref,
                "commit": commit,
                "working_tree": False,
                "dirty": False,
            }
        else:
            if ref != "HEAD":
                raise ValueError("Local imports copy current files; use HEAD as the ref")
            raw_root = Path(source).expanduser()
            if _linked(raw_root) or source.startswith(("\\\\", "//")):
                raise ValueError("Local source must not be a link, junction, or network share")
            root = workspace_root(raw_root).resolve(strict=True)
            if not root.is_dir() or root.is_relative_to(workspace):
                raise ValueError("Local source must be a directory outside the workbench workspace")
            if workspace.is_relative_to(root):
                relative = workspace.relative_to(root)
                if not any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
                    raise ValueError(
                        "Nested workspace must be inside an excluded directory such as artifacts"
                    )
            provenance = {
                "kind": "local",
                "location": str(root),
                "requested_ref": ref,
                "commit": _local_commit(root),
                "working_tree": True,
                "dirty": None,
            }
        progress("snapshotting")
        contents, scan = _collect(root)
        records = [
            {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for name, data in sorted(contents.items())
        ]
        repository_id = _identity(provenance, records)
        destination = _inside(workspace, f"repositories/{repository_id}")
        if destination.exists():
            manifest = load_repository(workspace, repository_id)
            progress("completed", repository_id=repository_id, cache_hit=True)
            return manifest
        snapshot = staging / "snapshot"
        snapshot.mkdir()
        for name, data in contents.items():
            target = _inside(snapshot.resolve(), f"source/{name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest = {
            "schema_version": 1,
            "repository_id": repository_id,
            "source": provenance,
            "source_directory": f"repositories/{repository_id}/source",
            "files": records,
            "created_at": datetime.now(UTC).isoformat(),
            "scan": scan,
        }
        _write_json(snapshot / "manifest.json", manifest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        snapshot.rename(destination)
        result = load_repository(workspace, repository_id)
        progress("completed", repository_id=repository_id, cache_hit=False)
        return result
    except (OSError, ValueError) as error:
        message = (
            str(error) if isinstance(error, ValueError) else "Cannot read or save repository files"
        )
        progress("failed", error=message)
        raise ValueError(message) from error
    except BaseException:
        progress("interrupted", error="Repository import was interrupted before completion")
        raise
    finally:
        # This owned staging tree is the only recursive removal target. Validate
        # its absolute boundary again before removal, including on Windows.
        try:
            _remove_staging(workspace, staging)
        except (OSError, ValueError):
            # Cleanup must not replace a primary error or interruption.
            # Keep an auditable warning when the state directory remains writable.
            job["cleanup_error"] = "Temporary import files could not be removed"
            try:
                _write_json(job_path, job)
            except (OSError, ValueError):
                pass
