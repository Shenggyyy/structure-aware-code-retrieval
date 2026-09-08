import subprocess
from pathlib import Path

import pytest

from structure_aware_retrieval.evaluation.preparation import _git, prepare_benchmark


def test_existing_pinned_checkout_is_reused_without_network(
    experiment: Path, sample_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = experiment.parent / "benchmark/benchmark.json"
    destination = experiment.parent / "prepared"
    checkout = destination / "repos/fixture"
    checkout.parent.mkdir(parents=True)
    sample_repository.rename(checkout)
    calls = []

    def git(*args):
        calls.append(args)
        if args[-1] == "--show-toplevel":
            return str(checkout)
        if args[-1] == "HEAD":
            return "a" * 40
        return ""

    monkeypatch.setattr("structure_aware_retrieval.evaluation.preparation._git", git)
    records = prepare_benchmark(manifest, destination)
    assert records[0]["repository"] == "fixture"
    assert all("clone" not in args for args in calls)
    assert prepare_benchmark(manifest, destination) == records


def test_wrong_commit_is_not_checked_out_or_reset(
    experiment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = experiment.parent / "prepared"
    checkout = destination / "repos/fixture"
    checkout.mkdir(parents=True)
    monkeypatch.setattr(
        "structure_aware_retrieval.evaluation.preparation._git",
        lambda *args: str(checkout) if args[-1] == "--show-toplevel" else "b" * 40,
    )
    with pytest.raises(ValueError, match="pinned commit mismatch"):
        prepare_benchmark(experiment.parent / "benchmark/benchmark.json", destination)
    assert not (destination / "indexes").exists()


def test_git_failures_are_readable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "git", stderr="repository unavailable")

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(ValueError, match="repository unavailable"):
        _git("clone", "https://example.invalid/repo")
