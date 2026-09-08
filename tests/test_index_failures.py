import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.ingestion import scan_repository


def test_unreadable_file_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    blocked = tmp_path / "blocked.py"
    blocked.write_text("value = 1", encoding="utf-8")
    original_open = Path.open

    def patched_open(path: Path, *args, **kwargs):
        if path == blocked:
            raise PermissionError("simulated unreadable source")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", patched_open)
    scanned = scan_repository(tmp_path)
    assert scanned.files == []
    assert scanned.diagnostics[0].reason == "read_error"


def test_link_detection_without_host_symlink_privileges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "link.py"
    target.write_text("must_not_read = True", encoding="utf-8")
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == target or original(path))
    scanned = scan_repository(tmp_path)
    assert scanned.files == []
    assert scanned.diagnostics[0].reason == "link_skipped"


def test_ignore_file_changes_are_part_of_snapshot_provenance(
    sample_repository: Path, tmp_path: Path
) -> None:
    ignore = sample_repository / ".gitignore"
    ignore.write_text("# first rule set\n", encoding="utf-8")
    first = build_index(sample_repository, tmp_path / "one.db")
    ignore.write_text("# revised rule set\n", encoding="utf-8")
    second = build_index(sample_repository, tmp_path / "two.db")
    assert first["manifest"] == second["manifest"]
    assert first["snapshot_id"] != second["snapshot_id"]


def test_malformed_tokens_and_missing_metadata_are_readable_errors(
    sample_repository: Path, tmp_path: Path
) -> None:
    database = tmp_path / "index.db"
    build_index(sample_repository, database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("UPDATE chunks SET tokens=?", (json.dumps({"invalid": 1}),))
    with pytest.raises(ValueError, match="Invalid stored tokens"):
        load_index(database)
    build_index(sample_repository, database, overwrite=True)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("DELETE FROM metadata WHERE key='snapshot_id'")
    with pytest.raises(ValueError, match="Invalid or incomplete"):
        load_index(database)
