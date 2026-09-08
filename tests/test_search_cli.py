import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app

runner = CliRunner()


def test_index_and_search_in_separate_processes(sample_repository: Path, tmp_path: Path) -> None:
    database = tmp_path / "snapshot with spaces.sqlite"
    command = [sys.executable, "-I", "-m", "structure_aware_retrieval"]
    indexed = subprocess.run(
        [*command, "index", str(sample_repository), "--output", str(database), "--json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    metadata = json.loads(indexed.stdout)
    # The second process cannot rely on the first process's memory or original file.
    (sample_repository / "client.py").unlink()
    searched = subprocess.run(
        [*command, "search", "calculate_checksum", "--index", str(database), "--json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    result = json.loads(searched.stdout)
    assert result["snapshot_id"] == metadata["snapshot_id"]
    assert result["results"][0]["qualified_name"] == "client.calculate_checksum"
    assert "def calculate_checksum" in result["results"][0]["text"]


def test_text_output_and_no_match(sample_repository: Path, tmp_path: Path) -> None:
    database = tmp_path / "index.sqlite"
    indexed = runner.invoke(app, ["index", str(sample_repository), "--output", str(database)])
    assert indexed.exit_code == 0, indexed.output
    assert "Indexed 3 files" in indexed.output
    found = runner.invoke(
        app, ["search", "calculate_checksum", "--index", str(database), "-k", "1"]
    )
    assert found.exit_code == 0
    assert "client.py:" in found.output
    assert "client.calculate_checksum" in found.output
    missing = runner.invoke(app, ["search", "nonexistent_xyz_marker", "--index", str(database)])
    assert missing.exit_code == 0
    assert "No matching code" in missing.output


def test_index_diagnostics_are_visible(sample_repository: Path, tmp_path: Path) -> None:
    (sample_repository / "broken.py").write_text("def bad(:", encoding="utf-8")
    result = runner.invoke(
        app, ["index", str(sample_repository), "--output", str(tmp_path / "i.db")]
    )
    assert result.exit_code == 0
    assert "broken.py [parse_error]" in result.stderr


def test_missing_index_has_a_readable_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["search", "query", "--index", str(tmp_path / "missing.db")])
    assert result.exit_code == 1
    assert "Index not found" in result.output
    assert "Traceback" not in result.output


def test_existing_output_fails_without_overwrite(sample_repository: Path, tmp_path: Path) -> None:
    command = ["index", str(sample_repository), "--output", str(tmp_path / "i.db")]
    assert runner.invoke(app, command).exit_code == 0
    assert runner.invoke(app, command).exit_code == 1
    assert runner.invoke(app, [*command, "--overwrite"]).exit_code == 0


@pytest.mark.parametrize(
    "arguments", [["search", "query", "--top-k", "0"], ["index", ".", "--max-chunk-lines", "0"]]
)
def test_invalid_limits_fail_at_argument_parsing(arguments: list[str]) -> None:
    assert runner.invoke(app, arguments).exit_code == 2
