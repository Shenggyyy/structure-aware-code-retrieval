import json
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.retrieval import BM25Retriever


def test_roundtrip_preserves_source_symbols_imports_and_diagnostics(
    sample_repository: Path, tmp_path: Path
) -> None:
    (sample_repository / "broken.py").write_text("def broken(:", encoding="utf-8")
    (sample_repository / "encoding.py").write_bytes(b"value = '\xff'\n")
    database = tmp_path / "index.sqlite"
    summary = build_index(sample_repository, database)
    loaded = load_index(database)

    assert summary["files_scanned"] == 5
    assert summary["files_indexed"] == 3
    assert {item["path"] for item in summary["diagnostics"]} == {"broken.py", "encoding.py"}
    assert summary["chunk_count"] == len(loaded.chunks)
    assert len(loaded.tokens) == len(loaded.chunks)
    assert loaded.metadata["snapshot_id"] == summary["snapshot_id"]
    assert summary["import_count"] == 2
    for chunk in loaded.chunks:
        source = (
            (sample_repository / chunk.path).read_text(encoding="utf-8").splitlines(keepends=True)
        )
        assert chunk.text == "".join(source[chunk.start_line - 1 : chunk.end_line])
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        references = [
            json.loads(row[0]) for row in connection.execute("SELECT payload FROM imports")
        ]
    assert any(item["alias"] == "RequestTimeout" for item in references)


def test_snapshot_is_location_independent_and_changes_with_content_or_config(
    sample_repository: Path, tmp_path: Path
) -> None:
    first = build_index(sample_repository, tmp_path / "one.db")
    copy = Path(shutil.copytree(sample_repository, tmp_path / "copy"))
    second = build_index(copy, tmp_path / "two.db")
    assert first["snapshot_id"] == second["snapshot_id"]
    different_config = build_index(copy, tmp_path / "three.db", max_chunk_lines=3)
    assert first["snapshot_id"] != different_config["snapshot_id"]
    (copy / "new.py").write_text("unique_content = 1\n", encoding="utf-8")
    changed = build_index(copy, tmp_path / "four.db")
    assert first["snapshot_id"] != changed["snapshot_id"]


def test_search_uses_snapshot_after_source_is_changed(
    sample_repository: Path, tmp_path: Path
) -> None:
    database = tmp_path / "index.db"
    build_index(sample_repository, database)
    first = BM25Retriever.from_path(database).search("calculate_checksum", top_k=2)
    (sample_repository / "client.py").write_text("# replaced source\n", encoding="utf-8")
    assert first == BM25Retriever.from_path(database).search("calculate_checksum", top_k=2)
    assert first[0].qualified_name == "client.calculate_checksum"


def test_rebuild_requires_explicit_overwrite_and_removes_deleted_files(
    sample_repository: Path, tmp_path: Path
) -> None:
    database = tmp_path / "index.db"
    build_index(sample_repository, database)
    with pytest.raises(FileExistsError, match="overwrite"):
        build_index(sample_repository, database)
    (sample_repository / "errors.py").unlink()
    summary = build_index(sample_repository, database, overwrite=True)
    assert summary["files_indexed"] == 2
    assert all(symbol.path != "errors.py" for symbol in load_index(database).symbols.values())


def test_failed_replacement_preserves_existing_index(
    sample_repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "index.db"
    original = build_index(sample_repository, database)
    (sample_repository / "new.py").write_text("changed = True\n", encoding="utf-8")

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated replacement failure")

    monkeypatch.setattr("structure_aware_retrieval.indexing.os.replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        build_index(sample_repository, database, overwrite=True)
    assert load_index(database).metadata["snapshot_id"] == original["snapshot_id"]
    assert list(tmp_path.glob(".index.db.*.tmp")) == []


def test_unrelated_database_and_source_cannot_be_overwritten(
    sample_repository: Path, tmp_path: Path
) -> None:
    database = tmp_path / "unrelated.db"
    database.write_bytes(b"not a database")
    with pytest.raises(ValueError, match="non-SACR"):
        build_index(sample_repository, database, overwrite=True)
    assert database.read_bytes() == b"not a database"
    with pytest.raises(ValueError, match="extension"):
        build_index(sample_repository, sample_repository / "client.py", overwrite=True)


def test_missing_corrupt_and_future_indexes_are_rejected(
    sample_repository: Path, tmp_path: Path
) -> None:
    database = tmp_path / "index.db"
    with pytest.raises(FileNotFoundError, match="Index not found"):
        load_index(database)
    assert not database.exists()
    database.write_text("invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid"):
        load_index(database)
    database.unlink()
    build_index(sample_repository, database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("PRAGMA user_version=999")
    with pytest.raises(ValueError, match="Unsupported index schema"):
        load_index(database)


def test_empty_and_comment_only_repositories(tmp_path: Path) -> None:
    repository = tmp_path / "empty"
    repository.mkdir()
    database = tmp_path / "empty.db"
    summary = build_index(repository, database)
    assert summary["chunk_count"] == 0
    assert BM25Retriever.from_path(database).search("anything") == []
    (repository / "comments.py").write_text("# special_marker\n", encoding="utf-8")
    build_index(repository, database, overwrite=True)
    assert BM25Retriever.from_path(database).search("special_marker")[0].path == "comments.py"


def test_unsupported_tokenizer_is_rejected(sample_repository: Path, tmp_path: Path) -> None:
    database = tmp_path / "index.db"
    summary = build_index(sample_repository, database)
    summary["config"]["tokenizer_version"] = 999
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "UPDATE metadata SET value=? WHERE key='config'", (json.dumps(summary["config"]),)
        )
    with pytest.raises(ValueError, match="tokenizer"):
        load_index(database)
