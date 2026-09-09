"""Confinement checks for local UI state, independent of OS link privileges."""

from pathlib import Path

import pytest

from structure_aware_retrieval.workbench.storage import read_json, safe_path, write_json


@pytest.mark.parametrize(
    "relative", ["../x", "/etc/x", "a/../x", "a\\x", "C:/x", "a//x", "a/./x", "a\nx"]
)
def test_rejects_unconfined_state_paths(tmp_path, relative):
    with pytest.raises(ValueError):
        safe_path(tmp_path, relative)


def test_atomic_record_replacement_and_no_leftover_files(tmp_path):
    write_json(tmp_path, "jobs/a.json", {"status": "running"})
    write_json(tmp_path, "jobs/a.json", {"status": "ready"})
    assert read_json(tmp_path, "jobs/a.json") == {"status": "ready"}
    assert [path.name for path in (tmp_path / "jobs").iterdir()] == ["a.json"]


def test_junction_or_symlink_ancestor_rejected(tmp_path, monkeypatch):
    blocked = tmp_path / "linked"
    monkeypatch.setattr(Path, "is_junction", lambda self: self == blocked)
    with pytest.raises(ValueError, match="links or junctions"):
        safe_path(tmp_path, "linked/nested/result.json")


def test_nonfinite_values_cannot_replace_valid_record(tmp_path):
    write_json(tmp_path, "record.json", {"value": 1})
    with pytest.raises(ValueError):
        write_json(tmp_path, "record.json", {"value": float("nan")})
    assert read_json(tmp_path, "record.json") == {"value": 1}
