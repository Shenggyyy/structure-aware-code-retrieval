"""Public QA commands remain offline unless generation is explicitly selected."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.indexing import build_index
from structure_aware_retrieval.qa.provider import ModelResponse

runner = CliRunner()


@pytest.fixture
def qa_index(sample_repository: Path, tmp_path: Path) -> Path:
    index = tmp_path / "index.sqlite"
    build_index(sample_repository, index)
    return index


def test_ask_previews_then_executes_once(qa_index, tmp_path, monkeypatch):
    calls = []

    def complete(self, messages):
        calls.append(messages)
        return ModelResponse(
            '{"status":"answered","claims":[{"text":"A checksum function.","citations":["S1"]}]}',
            self.model,
            {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30},
        )

    monkeypatch.setattr("structure_aware_retrieval.qa.provider.OpenAIModel.complete", complete)
    args = ["ask", "calculate_checksum", "--index", str(qa_index)]
    preview = tmp_path / "preview"
    result = runner.invoke(app, [*args, "--output", str(preview)])
    assert result.exit_code == 0, result.output
    assert "preview" in result.output
    assert not calls
    archive = json.loads((preview / "qa.json").read_text())
    assert archive["evaluation"]["answer_correctness"] is None
    assert (preview / "answer.md").is_file()
    answer = tmp_path / "answer"
    result = runner.invoke(app, [*args, "--output", str(answer), "--execute"])
    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert "[S1](#s1)" in (answer / "answer.md").read_text(encoding="utf-8")
    result = runner.invoke(app, [*args, "--output", str(answer), "--execute"])
    assert result.exit_code == 1
    assert len(calls) == 1


@pytest.mark.parametrize("response", ["bad JSON", "provider_error"])
def test_ask_archives_failed_generation(qa_index, tmp_path, monkeypatch, response):
    def complete(self, messages):
        if response == "provider_error":
            raise ValueError("Offline simulated failure")
        return ModelResponse(response, self.model, {})

    monkeypatch.setattr("structure_aware_retrieval.qa.provider.OpenAIModel.complete", complete)
    output = tmp_path / "failed"
    result = runner.invoke(
        app, ["ask", "checksum", "--index", str(qa_index), "--output", str(output), "--execute"]
    )
    assert result.exit_code == 1
    archive = json.loads((output / "qa.json").read_text())
    assert archive["status"] in ("provider_error", "invalid_answer")
    assert archive["error"]


@pytest.mark.parametrize(
    "extra",
    [
        ["--strategy", "unknown"],
        ["--strategy", "dense"],
        ["--strategy", "structure"],
        ["--vectors", "unused.npz"],
        ["--graph", "unused.json"],
        ["--max-context-bytes", "1"],
    ],
)
def test_ask_rejects_invalid_options_before_outputs(qa_index, tmp_path, extra):
    output = tmp_path / "bad"
    result = runner.invoke(
        app, ["ask", "checksum", "--index", str(qa_index), "--output", str(output), *extra]
    )
    assert result.exit_code != 0
    assert not output.exists()


def test_run_requires_explicit_execute(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("Execution must not be reached without --execute")

    monkeypatch.setattr("structure_aware_retrieval.qa.execution.execute_bundle", fail)
    result = runner.invoke(
        app,
        [
            "run-qa",
            "--bundle",
            str(tmp_path),
            "--output",
            str(tmp_path / "run"),
            "--budget-usd",
            "2",
        ],
    )
    assert result.exit_code == 1
    assert "No calls made" in result.output


@pytest.mark.parametrize(
    "command",
    [
        "ask",
        "prepare-qa",
        "run-qa",
        "check-qa-review",
        "prepare-qa-assessment",
        "check-qa-assessment",
        "run-qa-assessment",
    ],
)
def test_qa_help(command):
    assert runner.invoke(app, [command, "--help"]).exit_code == 0
