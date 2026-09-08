"""Private copies keep tests independent of each other and the committed fixture."""

import shutil
from pathlib import Path

import pytest


@pytest.fixture
def sample_repository(tmp_path: Path) -> Path:
    source = Path(__file__).parent / "fixtures" / "sample_repo"
    return Path(shutil.copytree(source, tmp_path / "repository"))
