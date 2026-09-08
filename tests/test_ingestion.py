from pathlib import Path

import pytest

from structure_aware_retrieval.ingestion import scan_repository


def write(root: Path, path: str, text: str = "value = 1\n") -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def test_nested_ignore_rules_builtins_and_additional_patterns(tmp_path: Path) -> None:
    write(tmp_path, ".gitignore", "ignored.py\n*.generated.py\n!keep.generated.py\n")
    write(tmp_path, "pkg/.gitignore", "skip.py\n!keep.generated.py\n")
    for path in [
        "z.py",
        "a.py",
        "ignored.py",
        "keep.generated.py",
        "pkg/keep.generated.py",
        "pkg/skip.py",
        "other.generated.py",
        "excluded.py",
        ".venv/hidden.py",
        "note.txt",
    ]:
        write(tmp_path, path)
    result = scan_repository(tmp_path, exclude=("excluded.py",))
    assert [file.path for file in result.files] == [
        "a.py",
        "keep.generated.py",
        "pkg/keep.generated.py",
        "z.py",
    ]
    assert result.excluded_entries == 5
    assert result.diagnostics == []


def test_ignored_directories_cannot_reinclude_children(tmp_path: Path) -> None:
    write(tmp_path, ".gitignore", "ignored/\n!ignored/keep.py\n")
    write(tmp_path, "ignored/keep.py")
    assert scan_repository(tmp_path).files == []


def test_oversized_files_have_diagnostics(tmp_path: Path) -> None:
    write(tmp_path, "large.py", "#" * 100)
    result = scan_repository(tmp_path, max_file_bytes=10)
    assert result.files == []
    assert result.diagnostics[0].reason == "too_large"


def test_symbolic_links_are_not_followed(tmp_path: Path) -> None:
    write(tmp_path, "real.py")
    link = tmp_path / "link.py"
    try:
        link.symlink_to(tmp_path / "real.py")
    except OSError:
        pytest.skip("Creating symlinks is unavailable on this host")
    result = scan_repository(tmp_path)
    assert [file.path for file in result.files] == ["real.py"]
    assert result.diagnostics[0].reason == "link_skipped"


def test_invalid_root_and_size_are_rejected(tmp_path: Path) -> None:
    write(tmp_path, "file.py")
    with pytest.raises(ValueError, match="directory"):
        scan_repository(tmp_path / "file.py")
    with pytest.raises(ValueError, match="positive"):
        scan_repository(tmp_path, max_file_bytes=0)
