"""Check the installed CLI's offline delivery workflow in a separate process."""

import json
import os
import subprocess
import sys
from pathlib import Path

from structure_aware_retrieval.indexing import load_index

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/smoke.py"


def _run(output: Path, *, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--output", str(output)],
        cwd=output.parent,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_delivery_smoke_preserves_offline_source_and_review_contracts(tmp_path: Path) -> None:
    output = tmp_path / "delivery"
    environment = {
        **os.environ,
        "GIT_DIR": str(tmp_path / "unrelated-git-directory"),
        "OPENAI_API_KEY": "offline-smoke-test-placeholder",
    }
    result = _run(output, environment=environment)

    assert result.returncode == 0, result.stderr
    summary = _read(output / "summary.json")
    assert json.loads(result.stdout) == summary
    assert summary["status"] == "passed"
    assert summary["synthetic_fixture_only"] is True
    assert summary["source_files"] == 3
    assert summary["api_calls"] == summary["model_downloads"] == 0
    index = load_index(output / "index.sqlite")
    assert index.metadata["git"] == {"commit": summary["fixture_commit"], "dirty": False}
    assert index.metadata["snapshot_id"] == summary["snapshot_id"]
    assert not index.metadata["diagnostics"]
    assert "raise RuntimeError" in (output / "repository/client.py").read_text(encoding="utf-8")

    lexical = _read(output / "search.json")
    assert lexical["results"][0]["qualified_name"] == "client.calculate_checksum"
    graph = _read(output / "graph.json")
    assert {"containment", "import", "test"} <= {edge["kind"] for edge in graph["edges"]}
    structural = _read(output / "structure-search.json")
    assert structural["strategy"] == "structure"
    assert all(hit["symbol_id"] in index.symbols for hit in structural["results"])

    preview = _read(output / "qa-preview/qa.json")
    empty = _read(output / "qa-empty/qa.json")
    assert preview["status"] == "preview"
    assert preview["context"]["evidence"]
    assert empty["status"] == "insufficient_context"
    assert empty["context"]["evidence"] == []
    for answer in (preview, empty):
        assert answer["model_called"] is False
        assert answer["provider"] is answer["raw_output"] is None
        assert answer["evaluation"]["answer_correctness"] is None
        assert answer["evaluation"]["citation_support"] is None

    first = _read(output / "bm25-first/summary.json")
    repeat = _read(output / "bm25-repeat/summary.json")
    assert first["quality_fingerprint"] == repeat["quality_fingerprint"]
    assert summary["quality_fingerprint"] == first["quality_fingerprint"]
    assert summary["repeat_quality_matches"] is True
    assert first["overall"]["answerable_count"] == 2
    assert first["overall"]["no_answer_count"] == 1
    assert first["overall"]["no_answer_with_results"] == 0
    assert first["benchmark"]["annotation_status"] == "provisional"
    review = _read(output / "review/manifest.json")
    assert review["review_status"] == "pending"
    assert review["item_count"] > 0
    assert all(
        json.loads(line)["grade"] is None
        for line in (output / "review/judgments.jsonl").read_text(encoding="utf-8").splitlines()
    )
    for relative in (
        "qa-preview/answer.md",
        "qa-empty/answer.md",
        "bm25-first/report.md",
        "bm25-repeat/report.md",
        "structure-run/report.md",
        "comparison/report.md",
        "review/review.md",
    ):
        assert (output / relative).is_file()
    commands = json.loads((output / "commands.json").read_text(encoding="utf-8"))
    assert len(commands) == summary["command_count"]
    assert all(command["returncode"] == 0 for command in commands)
    assert all("--execute" not in command["arguments"] for command in commands)
    assert "offline-smoke-test-placeholder" not in json.dumps(commands)


def test_delivery_smoke_refuses_existing_output_without_changes(tmp_path: Path) -> None:
    output = tmp_path / "delivery"
    output.mkdir()
    marker = output / "owner-data.bin"
    marker.write_bytes(b"preserve\x00existing\xffbytes")

    result = _run(output)

    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert marker.read_bytes() == b"preserve\x00existing\xffbytes"
    assert list(output.iterdir()) == [marker]


def test_delivery_smoke_records_missing_git_failure(tmp_path: Path) -> None:
    output = tmp_path / "delivery"
    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()

    result = _run(output, environment={**os.environ, "PATH": str(empty_path)})

    assert result.returncode == 1
    assert "Smoke failed" in result.stderr
    summary = _read(output / "summary.json")
    assert summary["status"] == "failed"
    assert "error" in summary
    assert not (output / "index.sqlite").exists()
