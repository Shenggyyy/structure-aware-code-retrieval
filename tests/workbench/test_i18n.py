"""Run the dependency-free browser localization contract tests offline."""

import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest


def test_browser_localization_contracts(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for browser contract tests; CI checks its availability")
    script = Path(__file__).with_name("i18n_contracts.mjs")
    root = script.parents[2]
    with zipfile.ZipFile(root / "reports/m9c-live/run.zip") as archive:
        members = [
            item
            for item in archive.infolist()
            if item.filename.endswith(("/plan.json", "/run.json"))
        ]
        assert len(members) == 3 and all(item.file_size <= 2_000_000 for item in members)
        records = [json.loads(archive.read(item.filename)) for item in members]
    fixtures = tmp_path / "archives.json"
    fixtures.write_text(json.dumps(records), encoding="utf-8")
    result = subprocess.run(
        [node, "--test", str(script)],
        cwd=root,
        env={**os.environ, "SACR_I18N_FIXTURES": str(fixtures)},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
