"""Exercise the public CLI contract without network access or model downloads."""

import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app

runner = CliRunner()


@pytest.mark.parametrize("arguments", [[], ["--help"]])
def test_help_is_available(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 0
    assert "Code retrieval and evaluation" in result.output
    assert "--version" in result.output


def test_version_matches_installed_distribution() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == f"sacr {version('structure-aware-code-retrieval')}"


def test_unknown_command_fails() -> None:
    result = runner.invoke(app, ["not-a-command"])

    assert result.exit_code == 2
    assert "No such command" in result.output


@pytest.mark.parametrize("entrypoint", ["module", "console"])
def test_installed_entrypoints_work_outside_repository(tmp_path: Path, entrypoint: str) -> None:
    if entrypoint == "module":
        command = [sys.executable, "-I", "-m", "structure_aware_retrieval"]
    else:
        executable = "sacr.exe" if os.name == "nt" else "sacr"
        command = [str(Path(sys.executable).parent / executable)]

    result = subprocess.run(
        [*command, "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"sacr {version('structure-aware-code-retrieval')}"
