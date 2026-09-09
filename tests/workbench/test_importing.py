"""Offline tests for the untrusted repository boundary and frozen snapshots."""

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from structure_aware_retrieval.workbench import importing
from structure_aware_retrieval.workbench.importing import import_repository, load_repository


def write(root: Path, relative: str, content: str = "value = 1\n") -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        check=True,
        text=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
    ).stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "input"
    write(root, "package/main.py", "def greet():\n    return 'hello'\n")
    write(root, "README.md", "Do not copy me")
    return root


def jobs(workspace: Path) -> list[dict]:
    return [json.loads(path.read_text()) for path in (workspace / "jobs").glob("*.json")]


def test_local_snapshot_reuse_and_content_change(repository: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workbench"
    first = import_repository(str(repository), workspace)
    assert first["source"] == {
        "kind": "local",
        "location": str(repository),
        "requested_ref": "HEAD",
        "commit": None,
        "working_tree": True,
        "dirty": None,
    }
    assert [record["path"] for record in first["files"]] == ["package/main.py"]
    assert import_repository(str(repository), workspace) == first
    assert sorted(job["cache_hit"] for job in jobs(workspace)) == [False, True]
    write(repository, "package/main.py", "value = 2\n")
    second = import_repository(str(repository), workspace)
    assert second["repository_id"] != first["repository_id"]
    assert load_repository(workspace, first["repository_id"]) == first
    assert (workspace / first["source_directory"] / "package/main.py").read_text().startswith("def")


def test_nested_ignore_rules_and_owned_workspace_are_excluded(repository: Path) -> None:
    write(repository, ".gitignore", "ignored.py\n*.generated.py\n!keep.generated.py\n")
    write(repository, "package/.gitignore", "skip.py\n")
    write(repository, "package/skip.py")
    write(repository, "ignored.py")
    write(repository, "keep.generated.py")
    write(repository, "foo.generated.py")
    write(repository, "artifacts/old.py")
    result = import_repository(str(repository), repository / "artifacts/workbench")
    assert [item["path"] for item in result["files"]] == [
        ".gitignore",
        "keep.generated.py",
        "package/.gitignore",
        "package/main.py",
    ]
    assert result["scan"]["excluded_entries"] >= 4


def test_local_head_is_anchor_without_clean_claim_or_hooks(
    repository: Path, tmp_path: Path
) -> None:
    git(repository, "init", "--template=")
    git(repository, "-c", "user.name=Test", "-c", "user.email=test@example.com", "add", ".")
    git(
        repository,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "fixture",
    )
    expected = git(repository, "rev-parse", "HEAD")
    marker = tmp_path / "MUST_NOT_EXIST"
    command = f'!echo executed > "{marker.as_posix()}"'
    git(repository, "config", "core.fsmonitor", command)
    git(repository, "config", "filter.untrusted.smudge", command)
    git(repository, "config", "filter.untrusted.clean", command)
    write(repository, ".gitattributes", "*.py filter=untrusted\n")
    write(repository, ".git/hooks/post-checkout", f'#!/bin/sh\ntouch "{marker.as_posix()}"\n')
    config_before = (repository / ".git/config").read_bytes()
    write(repository, "package/main.py", "value = 'dirty working tree'\n")
    result = import_repository(str(repository), tmp_path / "workbench")
    assert result["source"]["commit"] == expected
    assert result["source"]["working_tree"] is True
    assert result["source"]["dirty"] is None
    assert not marker.exists()
    assert (repository / ".git/config").read_bytes() == config_before
    assert (repository / "package/main.py").read_text() == "value = 'dirty working tree'\n"


@pytest.mark.parametrize("kind", ["modified", "missing", "unexpected", "manifest"])
def test_cached_source_corruption_is_rejected(repository: Path, tmp_path: Path, kind: str) -> None:
    workspace = tmp_path / "workbench"
    result = import_repository(str(repository), workspace)
    source = workspace / result["source_directory"]
    if kind == "modified":
        write(source, "package/main.py", "corrupted bytes")
    elif kind == "missing":
        (source / "package/main.py").unlink()
    elif kind == "unexpected":
        write(source, "extra.py")
    else:
        path = source.parent / "manifest.json"
        payload = json.loads(path.read_text())
        payload["source"]["commit"] = "a" * 40
        path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_repository(workspace, result["repository_id"])
    with pytest.raises(ValueError):
        import_repository(str(repository), workspace)
    assert any(job["status"] == "failed" for job in jobs(workspace))


def test_local_links_are_skipped_and_frozen_links_rejected(
    repository: Path, tmp_path: Path
) -> None:
    link = repository / "escape.py"
    outside = write(tmp_path, "outside.py")
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlinks unavailable")
    workspace = tmp_path / "workbench"
    result = import_repository(str(repository), workspace)
    assert result["scan"]["links_skipped"] == 1
    source = workspace / result["source_directory"]
    (source / "extra.py").symlink_to(outside)
    with pytest.raises(ValueError, match="link"):
        load_repository(workspace, result["repository_id"])


@pytest.mark.parametrize(
    "ref", ["--upload-pack=evil", "refs/../evil", "a:b", "HEAD~1", "a\nb", "a//b"]
)
def test_invalid_ref_is_retained_without_git(repository: Path, tmp_path: Path, ref: str) -> None:
    workspace = tmp_path / "workbench"
    with pytest.raises(ValueError, match="ref"):
        import_repository(str(repository), workspace, ref=ref)
    assert jobs(workspace)[0]["status"] == "failed"


def test_local_ref_and_overlap_rejected(repository: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="current files"):
        import_repository(str(repository), tmp_path / "workbench", ref="main")
    with pytest.raises(ValueError, match="Nested workspace"):
        import_repository(str(repository), repository / "state")
    with pytest.raises(ValueError, match="outside"):
        import_repository(str(repository), tmp_path)


@pytest.mark.parametrize(
    "source",
    [
        "http://github.com/example/repo",
        "file:///tmp/repo",
        "git@github.com:example/repo",
        "https://user:TOP_SECRET@github.com/example/repo",
        "https://localhost/repo",
        "https://127.0.0.1/repo",
        "https://example.com:8443/repo",
        "https://example.com/repo?x=1",
        "https://example.com/repo#fragment",
        "https://example.com/%2e%2e/repo",
        "https://example.com/../repo",
        "https://example.com/repo\n",
        "https://example.com\\@evil/repo",
        "https://example.com//repo",
        "https://example.internal/repo",
    ],
)
def test_unsafe_urls_rejected_without_transport(tmp_path: Path, monkeypatch, source: str) -> None:
    monkeypatch.setattr(importing, "_remote_tree", lambda *args: pytest.fail("Transport invoked"))
    workspace = tmp_path / "workbench"
    with pytest.raises(ValueError):
        import_repository(source, workspace)
    record = jobs(workspace)[0]
    assert record["status"] == "failed"
    assert "TOP_SECRET" not in json.dumps(record)


@pytest.mark.parametrize(
    "address", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "224.0.0.1"]
)
def test_dns_must_only_resolve_public_addresses(monkeypatch, address: str) -> None:
    monkeypatch.setattr(
        importing.socket, "getaddrinfo", lambda *a, **kw: [(0, 0, 0, "", (address, 443))]
    )
    with pytest.raises(ValueError, match="non-public"):
        importing._public_address("example.com")


def fake_remote(monkeypatch, blobs: dict[str, bytes], *, linked: bool = False) -> list:
    calls = []
    objects = {hashlib.sha1(data).hexdigest(): data for data in blobs.values()}
    tree = b"".join(
        f"100644 blob {hashlib.sha1(data).hexdigest()}\t{name}".encode() + b"\0"
        for name, data in blobs.items()
    )
    if linked:
        tree += b"120000 blob " + b"a" * 40 + b"\tescape.py\0"
        tree += b"160000 commit " + b"b" * 40 + b"\tsubmodule\0"
    monkeypatch.setattr(importing, "_public_address", lambda host: "93.184.215.14")

    def run(*args, cwd, resolve=None):
        calls.append((args, resolve))
        if args[:2] == ("help", "--config"):
            return b"http.curloptResolve\n"
        if args[0] == "init":
            Path(args[-1]).mkdir()
        elif args[0] == "rev-parse":
            return b"c" * 40 + b"\n"
        elif args[0] == "ls-tree":
            return tree
        elif args[:2] == ("cat-file", "-s"):
            return str(len(objects[args[2]])).encode()
        elif args[:2] == ("cat-file", "blob"):
            return objects[args[2]]
        return b""

    monkeypatch.setattr(importing, "_git", run)
    return calls


def test_remote_raw_blob_import_pins_address_and_commit(tmp_path: Path, monkeypatch) -> None:
    calls = fake_remote(
        monkeypatch,
        {"package/main.py": b"value = 1\n", ".gitignore": b"ignored.py\n", "ignored.py": b"pass\n"},
        linked=True,
    )
    workspace = tmp_path / "workbench"
    result = import_repository("https://example.com/example/repo.git", workspace)
    assert result["source"]["commit"] == "c" * 40
    assert result["source"]["working_tree"] is False
    assert result["source"]["dirty"] is False
    assert [record["path"] for record in result["files"]] == [".gitignore", "package/main.py"]
    fetches = [item for item in calls if item[0][0] == "fetch"]
    assert len(fetches) == 1
    assert fetches[0][1] == "example.com:443:93.184.215.14"
    assert all(item[0][0] not in {"checkout", "clone", "submodule"} for item in calls)
    assert not list((workspace / ".staging").iterdir())
    assert [event["status"] for event in jobs(workspace)[0]["events"]] == [
        "validating",
        "downloading",
        "snapshotting",
        "completed",
    ]


@pytest.mark.parametrize("name", ["../evil.py", "/evil.py", "C:/evil.py", "a\\evil.py", "nul.py"])
def test_remote_unsafe_tree_paths_rejected(tmp_path: Path, monkeypatch, name: str) -> None:
    fake_remote(monkeypatch, {name: b"pass\n"})
    with pytest.raises(ValueError, match="unsafe source path"):
        import_repository("https://example.com/repo", tmp_path / "workbench")


@pytest.mark.parametrize("limit", ["MAX_FILE_BYTES", "MAX_TOTAL_BYTES", "MAX_FILES", "MAX_ENTRIES"])
def test_limits_fail_explicitly_without_partial_snapshot(
    repository: Path, tmp_path: Path, monkeypatch, limit: str
) -> None:
    monkeypatch.setattr(importing, limit, 0)
    workspace = tmp_path / "workbench"
    with pytest.raises(ValueError, match="limit"):
        import_repository(str(repository), workspace)
    assert jobs(workspace)[0]["status"] == "failed"
    assert not (workspace / "repositories").exists()


def test_git_environment_and_transport_flags_exclude_ambient_configuration(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.sshCommand")
    monkeypatch.setenv("HTTPS_PROXY", "http://localhost:1234")
    monkeypatch.setenv("GIT_SSL_NO_VERIFY", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-must-not-reach-git")
    captured = {}

    def run(command, **kwargs):
        captured.update(command=command, **kwargs)
        kwargs["stdout"].write(b"ok")

    monkeypatch.setattr(importing.subprocess, "run", run)
    assert importing._git("fetch", cwd=tmp_path, resolve="example.com:443:93.184.215.14") == b"ok"
    assert "GIT_CONFIG_COUNT" not in captured["env"]
    assert "HTTPS_PROXY" not in captured["env"]
    assert "GIT_SSL_NO_VERIFY" not in captured["env"]
    assert "OPENAI_API_KEY" not in captured["env"]
    assert captured["env"]["GIT_CONFIG_GLOBAL"] == os.devnull
    assert captured["env"]["HOME"] == captured["env"]["USERPROFILE"]
    assert captured["env"]["HOME"] != str(Path.home())
    for setting in [
        "http.followRedirects=false",
        "credential.helper=",
        "core.fsmonitor=false",
        "http.proxy=",
        "http.sslVerify=true",
        "protocol.allow=never",
        "http.curloptResolve=example.com:443:93.184.215.14",
    ]:
        assert setting in captured["command"]
    assert Path(captured["command"][0]).is_absolute()
    assert captured["stderr"] == subprocess.DEVNULL


def test_git_errors_are_sanitized_and_not_retried(tmp_path: Path, monkeypatch) -> None:
    calls = []

    def fail(command, **kwargs):
        calls.append(command)
        raise subprocess.CalledProcessError(128, command, stderr=b"TOP_SECRET\x1b[31m")

    monkeypatch.setattr(importing.subprocess, "run", fail)
    with pytest.raises(ValueError, match="Git operation failed") as error:
        importing._git("fetch", cwd=tmp_path)
    assert "TOP_SECRET" not in str(error.value)
    assert len(calls) == 1


def test_remote_pinned_commit_mismatch_is_rejected(tmp_path: Path, monkeypatch) -> None:
    fake_remote(monkeypatch, {"main.py": b"pass\n"})
    with pytest.raises(ValueError, match="differs"):
        import_repository("https://example.com/repo", tmp_path / "workbench", ref="d" * 40)


def test_remote_source_limits_are_enforced_before_reading_blobs(
    tmp_path: Path, monkeypatch
) -> None:
    calls = fake_remote(monkeypatch, {"main.py": b"longer than limit\n"})
    monkeypatch.setattr(importing, "MAX_FILE_BYTES", 1)
    with pytest.raises(ValueError, match="source size"):
        import_repository("https://example.com/repo", tmp_path / "workbench")
    assert not any(call[0][:2] == ("cat-file", "blob") for call in calls)


def test_dns_mixed_public_private_answers_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        importing.socket,
        "getaddrinfo",
        lambda *a, **kw: [
            (0, 0, 0, "", ("93.184.215.14", 443)),
            (0, 0, 0, "", ("10.0.0.1", 443)),
        ],
    )
    with pytest.raises(ValueError, match="non-public"):
        importing._public_address("example.com")


def test_import_requires_curl_resolve_support(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(importing, "_public_address", lambda host: "93.184.215.14")
    monkeypatch.setattr(importing, "_git", lambda *a, **kw: b"http.proxy\n")
    with pytest.raises(ValueError, match="curloptResolve"):
        import_repository("https://example.com/repo", tmp_path / "workbench")


def test_case_colliding_remote_paths_are_rejected(tmp_path: Path, monkeypatch) -> None:
    fake_remote(monkeypatch, {"Main.py": b"pass\n", "main.py": b"pass\n"})
    with pytest.raises(ValueError, match="case-insensitive"):
        import_repository("https://example.com/repo", tmp_path / "workbench")


def test_git_timeout_is_sanitized(tmp_path: Path, monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("git", 180, stderr=b"TOP_SECRET")

    monkeypatch.setattr(importing.subprocess, "run", timeout)
    with pytest.raises(ValueError, match="time limit") as error:
        importing._git("fetch", cwd=tmp_path)
    assert "TOP_SECRET" not in str(error.value)


def test_exact_remote_commit_reuses_verified_cache_without_network(
    tmp_path: Path, monkeypatch
) -> None:
    calls = fake_remote(monkeypatch, {"main.py": b"pass\n"})
    workspace = tmp_path / "workbench"
    first = import_repository("https://example.com/repo", workspace, ref="c" * 40)
    calls.clear()
    monkeypatch.setattr(importing, "_public_address", lambda *a: pytest.fail("DNS was invoked"))
    assert import_repository("https://example.com/repo", workspace, ref="c" * 40) == first
    assert not calls
    assert sorted(record["cache_hit"] for record in jobs(workspace)) == [False, True]
    assert any(
        [event["status"] for event in record["events"]] == ["validating", "completed"]
        for record in jobs(workspace)
    )


def test_corrupt_pinned_cache_fails_without_network_or_replacement(
    tmp_path: Path, monkeypatch
) -> None:
    calls = fake_remote(monkeypatch, {"main.py": b"pass\n"})
    workspace = tmp_path / "workbench"
    first = import_repository("https://example.com/repo", workspace, ref="c" * 40)
    write(workspace / first["source_directory"], "main.py", "corrupt\n")
    calls.clear()
    with pytest.raises(ValueError, match="integrity"):
        import_repository("https://example.com/repo", workspace, ref="c" * 40)
    assert not calls
    assert any(record["status"] == "failed" for record in jobs(workspace))


def test_mutable_remote_ref_is_resolved_again(tmp_path: Path, monkeypatch) -> None:
    calls = fake_remote(monkeypatch, {"main.py": b"pass\n"})
    workspace = tmp_path / "workbench"
    first = import_repository("https://example.com/repo", workspace)
    calls.clear()
    assert import_repository("https://example.com/repo", workspace) == first
    assert any(call[0][0] == "fetch" for call in calls)


def test_remote_depth_limit_is_an_error_not_a_partial_snapshot(tmp_path: Path, monkeypatch) -> None:
    fake_remote(monkeypatch, {"main.py": b"pass\n", "pkg/deep.py": b"pass\n"})
    monkeypatch.setattr(importing, "MAX_DEPTH", 1)
    workspace = tmp_path / "workbench"
    with pytest.raises(ValueError, match="depth limit"):
        import_repository("https://example.com/repo", workspace)
    assert not (workspace / "repositories").exists()


@pytest.mark.parametrize("remote", [False, True])
def test_interruption_is_recorded_and_does_not_change_source(
    repository: Path, tmp_path: Path, monkeypatch, remote: bool
) -> None:
    original = (repository / "package/main.py").read_bytes()
    workspace = tmp_path / "workbench"

    def interrupt(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(importing, "_remote_tree" if remote else "_collect", interrupt)
    source = "https://example.com/repo" if remote else str(repository)
    with pytest.raises(KeyboardInterrupt):
        import_repository(source, workspace)
    record = jobs(workspace)[0]
    assert record["status"] == "interrupted"
    assert record["events"][-1]["status"] == "interrupted"
    assert "interrupted" in record["error"]
    assert not list((workspace / ".staging").iterdir())
    assert not (workspace / "repositories").exists()
    assert (repository / "package/main.py").read_bytes() == original


def test_cleanup_failure_preserves_primary_interruption(
    repository: Path, tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "workbench"
    monkeypatch.setattr(importing, "_local_commit", lambda *args: None)

    def interrupt(*args):
        raise KeyboardInterrupt()

    def cleanup_failure(*args, **kwargs):
        raise OSError("untrusted detail must not be logged")

    monkeypatch.setattr(importing, "_collect", interrupt)
    with monkeypatch.context() as cleanup_patch:
        cleanup_patch.setattr(importing.shutil, "rmtree", cleanup_failure)
        with pytest.raises(KeyboardInterrupt):
            import_repository(str(repository), workspace)
    record = jobs(workspace)[0]
    assert record["status"] == "interrupted"
    assert record["cleanup_error"] == "Temporary import files could not be removed"
    assert "untrusted detail" not in json.dumps(record)


def test_owned_staging_cleanup_removes_real_readonly_git_pack_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workbench"
    staging = workspace / ".staging/import-id"
    for suffix in [".pack", ".idx", ".rev"]:
        path = write(staging, f"git/objects/pack/pack-example{suffix}", "pack fixture")
        path.chmod(stat.S_IREAD)
    retained = write(workspace, "repositories/retained.py", "outside staging")
    importing._remove_staging(workspace, staging)
    assert not staging.exists()
    assert retained.read_text() == "outside staging"


def test_completed_import_cleans_readonly_git_files_without_warning(
    tmp_path: Path, monkeypatch
) -> None:
    def remote_tree(url, host, ref, staging):
        pack = write(staging, "git/objects/pack/fixture.idx", "read-only pack fixture")
        pack.chmod(stat.S_IREAD)
        source = staging / "tree"
        write(source, "main.py")
        return source, "c" * 40

    monkeypatch.setattr(importing, "_remote_tree", remote_tree)
    workspace = tmp_path / "workbench"
    manifest = import_repository("https://example.com/repo", workspace)
    assert load_repository(workspace, manifest["repository_id"]) == manifest
    assert jobs(workspace)[0]["status"] == "completed"
    assert "cleanup_error" not in jobs(workspace)[0]
    assert not list((workspace / ".staging").iterdir())


def test_cleanup_readonly_retry_reexecutes_only_the_failed_operation(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "workbench"
    staging = workspace / ".staging/import-id"
    readonly = write(staging, "git/objects/fixture.idx")
    readonly.chmod(stat.S_IREAD)
    original = importing.shutil.rmtree
    retried = []

    def remove(path):
        retried.append(path)
        os.unlink(path)

    def fail_once(path, *, onexc):
        onexc(remove, str(readonly), PermissionError("read only"))
        original(path)

    with monkeypatch.context() as cleanup_patch:
        cleanup_patch.setattr(importing.shutil, "rmtree", fail_once)
        importing._remove_staging(workspace, staging)
    assert retried == [str(readonly)]
    assert not staging.exists()


def test_cleanup_retry_cannot_change_or_delete_an_external_file(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "workbench"
    staging = workspace / ".staging/import-id"
    write(staging, "fixture.idx")
    external = write(workspace, "repositories/retained.py", "keep me")
    before = external.stat().st_mode

    def attack(path, *, onexc):
        onexc(os.unlink, str(external), PermissionError("read only"))

    with monkeypatch.context() as cleanup_patch:
        cleanup_patch.setattr(importing.shutil, "rmtree", attack)
        with pytest.raises(ValueError, match="escaped"):
            importing._remove_staging(workspace, staging)
    assert external.read_text() == "keep me"
    assert external.stat().st_mode == before


def test_cleanup_rejects_links_without_removing_other_source(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workbench"
    staging = workspace / ".staging/import-id"
    suspicious = write(staging, "unexpected-link.py")
    original = importing._linked
    monkeypatch.setattr(importing, "_linked", lambda path: path == suspicious or original(path))
    with pytest.raises(ValueError, match="link or junction"):
        importing._remove_staging(workspace, staging)
    assert suspicious.exists()
