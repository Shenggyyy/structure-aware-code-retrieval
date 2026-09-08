"""Judge-only execution tests use injected responses and forbid live credentials/transports."""

import json
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from runpy import run_path
from types import SimpleNamespace

import pytest

from structure_aware_retrieval.qa.provider import ModelProviderError, OpenAIModel
from tests.qa.test_assessment import OfflineModel, _read, _rows
from tests.qa.test_assessment import forbid_live_calls as forbid_live_calls  # noqa: F401
from tests.qa.test_assessment import study as study  # noqa: F401
from tests.qa.test_assessment_archive import _run
from tests.qa.test_judge_revision import prepare_revision
from tests.qa.test_judge_revision import revision_config as revision_config  # noqa: F401
from tests.qa.test_preparation import qa_experiment as qa_experiment  # noqa: F401

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/run_qa_judge_revision.py"
RUNTIME = run_path(str(SCRIPT))
execute_revision = RUNTIME["execute_revision"]


class RevisionModel:
    def __init__(self, settings, prepared, calls, *, behavior=None, output=None):
        self.model = settings["model"]
        self.output_schema = deepcopy(prepared["output_schema"])
        self.calls, self.behavior, self.output = calls, behavior, output

    def complete(self, messages):
        self.calls.append(deepcopy(messages))
        if self.output:
            attempts = _rows(self.output / "attempts.jsonl")
            assert attempts[-1]["request_payload"]["input"] == messages
            assert attempts[-1]["request_payload"]["text"]["format"]["schema"] == self.output_schema
            saved = _read(self.output / "summary.json")
            assert saved["overall"]["judging"]["unknown_outcome_count"] == 1
        if self.behavior:
            result = self.behavior(messages)
            if result is not None:
                return result
        response = OfflineModel("judging", []).complete(messages)
        value = json.loads(response.text)
        value["rubric_id"] = "repository-qa-judge-rubric-v2"
        return replace(response, text=json.dumps(value), model=self.model, raw_response=None)


@pytest.fixture
def revision(study, tmp_path, revision_config):
    source = _run(study, tmp_path)
    bundle = tmp_path / "revision"
    plan = prepare_revision(source, revision_config, bundle)
    return SimpleNamespace(source=source, bundle=bundle, plan=plan)


def run_revision(revision, output, calls, *, behavior=None, **overrides):
    arguments = {
        "budget_usd": revision.plan["estimated_cost"]["combined_usd"],
        "judge_model_id": revision.plan["judge"]["model"],
        "approved_plan": revision.plan["plan_fingerprint"],
        "execute": True,
        "model_factory": lambda settings, prepared: RevisionModel(
            settings,
            prepared,
            calls,
            behavior=behavior,
            output=output,
        ),
        **overrides,
    }
    return execute_revision(revision.bundle, output, **arguments)


def test_success_reuses_answers_and_journals_each_exact_request(revision, tmp_path):
    before = {p: p.read_bytes() for p in revision.bundle.rglob("*") if p.is_file()}
    output, calls = tmp_path / "judged", []
    summary = run_revision(revision, output, calls)
    assert summary["status"] == "complete"
    assert summary["execution_mode"] == "injected_models"
    assert summary["new_generation_calls"] == 0
    assert not (output / "interruption.json").exists()
    assert len(calls) == len(_rows(output / "attempts.jsonl")) == 6
    source = _read(revision.source / "records.json")
    records = _read(output / "records.json")
    for old, new in zip(source, records, strict=True):
        assert {k: v for k, v in new.items() if k != "judging"} == {
            k: v for k, v in old.items() if k != "judging"
        }
        assert new["judging"]["judgment"]["rubric_id"] == "repository-qa-judge-rubric-v2"
    assert before == {p: p.read_bytes() for p in before}
    assert _read(output / "prepared/plan.json")["execution_authorized"] is False
    assert _read(output / "approval.json")["plan_fingerprint"] == revision.plan["plan_fingerprint"]
    assert summary["overall"]["judging"]["tokens"]["input_tokens"] == 1200
    assert "Offline injected-model fixture" in (output / "report.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "overrides",
    [
        {"execute": False},
        {"execute": "yes"},
        {"approved_plan": "wrong"},
        {"judge_model_id": "wrong"},
        {"budget_usd": 0.000001},
        {"budget_usd": float("nan")},
        {"budget_usd": float("inf")},
        {"budget_usd": True},
        {"budget_usd": -1},
    ],
)
def test_approval_gates_precede_calls_and_output(revision, tmp_path, overrides):
    output, calls = tmp_path / "judged", []
    with pytest.raises(ValueError):
        run_revision(revision, output, calls, **overrides)
    assert calls == []
    assert not output.exists()


def test_invalid_judgment_is_preserved_without_retry(revision, tmp_path):
    output, calls = tmp_path / "judged", []

    def malformed(_messages):
        return replace(OfflineModel("judging", []).response({"broken": True}), raw_response=None)

    summary = run_revision(revision, output, calls, behavior=malformed)
    assert summary["status"] == "complete_with_failures"
    assert len(calls) == 6
    assert summary["overall"]["dimensions"]["correctness"]["mean"] is None
    assert all(r["judging"]["judgment"] is None for r in _read(output / "records.json"))
    assert all(r["judging"]["raw_output"] for r in _read(output / "records.json"))


def test_provider_failure_stops_and_unknown_usage_is_not_zero(revision, tmp_path):
    output, calls = tmp_path / "judged", []

    def broken(_messages):
        raise ModelProviderError("Offline transport failure")

    summary = run_revision(revision, output, calls, behavior=broken)
    assert summary["status"] == "failed"
    assert len(calls) == 1
    stage = summary["overall"]["judging"]
    assert stage["not_run_count"] == 5
    assert stage["cost_usd_at_frozen_uncached_rates"] is None
    assert stage["observed_cost_subtotal_usd_at_frozen_uncached_rates"] == 0
    assert not (output / "interruption.json").exists()


def test_interruption_preserves_unknown_attempt_without_resume(revision, tmp_path):
    output, calls = tmp_path / "judged", []

    def interrupted(_messages):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_revision(revision, output, calls, behavior=interrupted)
    summary = _read(output / "summary.json")
    assert summary["status"] == "interrupted"
    assert summary["overall"]["judging"]["unknown_outcome_count"] == 1
    assert summary["overall"]["judging"]["cost_usd_at_frozen_uncached_rates"] is None
    assert len(calls) == 1
    interruption = _read(output / "interruption.json")
    assert interruption["exception_type"] == "KeyboardInterrupt"
    assert interruption["phase"] == "model_call"
    assert interruption["attempted_count"] == 1
    assert interruption["completed_count"] == 0
    with pytest.raises(FileExistsError):
        run_revision(revision, output, calls)
    assert len(calls) == 1


def test_existing_output_cannot_be_replaced(revision, tmp_path):
    output = tmp_path / "judged"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run_revision(revision, output, [])
    assert marker.read_text() == "keep"


def test_tampered_bundle_cannot_trigger_calls(revision, tmp_path):
    request = revision.bundle / "requests.jsonl"
    request.write_text("{}\n", encoding="utf-8")
    calls = []
    with pytest.raises(ValueError):
        run_revision(revision, tmp_path / "judged", calls)
    assert calls == []


def test_live_adapters_cannot_hide_in_injected_mode(revision, tmp_path):
    def factory(settings, prepared):
        return RUNTIME["_model"](settings, prepared)

    with pytest.raises(ValueError, match="offline models"):
        run_revision(revision, tmp_path / "judged", [], model_factory=factory)


def test_wrong_schema_is_rejected_before_any_call(revision, tmp_path):
    calls = []

    def factory(settings, prepared):
        model = RevisionModel(settings, prepared, calls)
        model.output_schema = {}
        return model

    with pytest.raises(ValueError, match="per-answer output schema"):
        run_revision(revision, tmp_path / "judged", calls, model_factory=factory)
    assert calls == []


def test_runner_reads_only_copied_inputs_after_preflight(revision, tmp_path):
    calls = []

    def factory(settings, prepared):
        (revision.bundle / "requests.jsonl").write_text("changed after copy", encoding="utf-8")
        return RevisionModel(settings, prepared, calls)

    result = run_revision(revision, tmp_path / "judged", calls, model_factory=factory)
    assert result["status"] == "complete"
    assert len(calls) == 6


def test_changed_input_during_copy_is_rejected_before_model_factory(
    revision, tmp_path, monkeypatch
):
    copyfile = RUNTIME["shutil"].copyfile
    factories = []

    def changed(source, target):
        result = copyfile(source, target)
        if target.name == "config.toml":
            with target.open("a", encoding="utf-8") as stream:
                stream.write("\n# Changed during input copy\n")
        return result

    def factory(settings, prepared):
        factories.append(True)
        return RevisionModel(settings, prepared, [])

    monkeypatch.setattr(RUNTIME["shutil"], "copyfile", changed)
    with pytest.raises(ValueError, match="differs"):
        run_revision(revision, tmp_path / "judged", [], model_factory=factory)
    assert factories == []


def test_cli_without_execution_flag_runs_in_isolated_python_and_makes_no_output(revision, tmp_path):
    output = tmp_path / "judged"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(SCRIPT),
            "--bundle",
            str(revision.bundle),
            "--output",
            str(output),
            "--judge-model",
            revision.plan["judge"]["model"],
            "--approved-plan",
            revision.plan["plan_fingerprint"],
            "--budget-usd",
            "5",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert not output.exists()


def test_no_generation_or_live_provider_is_used_by_execution(revision, tmp_path, monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail(
            "Judge-only execution must not generate answers or use a live provider in tests"
        )

    monkeypatch.setattr(OpenAIModel, "complete", forbidden)
    monkeypatch.setattr("structure_aware_retrieval.qa.answering.complete_question", forbidden)
    result = run_revision(revision, tmp_path / "judged", [])
    assert result["status"] == "complete"


def test_precall_checkpoint_failure_records_safe_metadata_without_calling_model(
    revision, tmp_path, monkeypatch
):
    output, calls = tmp_path / "judged", []
    original = PermissionError(13, "sk-secret-exception-message", "secret-file-path")
    original.winerror = 5
    write = execute_revision.__globals__["_write"]
    summary_writes = 0

    def failed_checkpoint(path, value):
        nonlocal summary_writes
        if path == output / "summary.json":
            summary_writes += 1
            if summary_writes == 2:
                raise original
        return write(path, value)

    monkeypatch.setitem(execute_revision.__globals__, "_write", failed_checkpoint)
    with pytest.raises(PermissionError) as caught:
        run_revision(revision, output, calls)
    assert caught.value is original
    assert calls == []
    diagnostic_text = (output / "interruption.json").read_text(encoding="utf-8")
    assert "sk-secret" not in diagnostic_text
    assert "secret-file-path" not in diagnostic_text
    diagnostic = json.loads(diagnostic_text)
    assert diagnostic["exception_type"] == "PermissionError"
    assert diagnostic["phase"] == "precall_checkpoint"
    assert diagnostic["errno"] == 13
    assert diagnostic["winerror"] == 5
    assert diagnostic["active_request_id"] == _rows(output / "attempts.jsonl")[0]["id"]
    assert diagnostic["attempted_count"] == 1
    assert diagnostic["completed_count"] == 0
    assert 1 <= len(diagnostic["traceback_locations"]) <= 8
    for location in diagnostic["traceback_locations"]:
        assert set(location) == {"file", "function", "line"}
        assert Path(location["file"]).name == location["file"]
        assert type(location["line"]) is int
    assert _read(output / "summary.json")["status"] == "interrupted"


def test_unexpected_model_exception_records_identity_but_never_exception_text(revision, tmp_path):
    output, calls = tmp_path / "judged", []
    original = RuntimeError("sk-secret", {"Authorization": "Bearer private"})

    def broken(_messages):
        raise original

    with pytest.raises(RuntimeError) as caught:
        run_revision(revision, output, calls, behavior=broken)
    assert caught.value is original
    diagnostic_text = (output / "interruption.json").read_text(encoding="utf-8")
    assert "sk-secret" not in diagnostic_text
    assert "Authorization" not in diagnostic_text
    assert "Bearer private" not in diagnostic_text
    diagnostic = json.loads(diagnostic_text)
    assert diagnostic["exception_type"] == "RuntimeError"
    assert diagnostic["phase"] == "model_call"
    assert diagnostic["attempted_count"] == 1
    assert diagnostic["completed_count"] == 0
    assert len(calls) == 1


def test_initialize_failure_is_recorded_before_any_attempt(revision, tmp_path, monkeypatch):
    output, calls = tmp_path / "judged", []
    original = OSError("private-copy-path")

    def broken_copy(_source, _target):
        raise original

    monkeypatch.setattr(RUNTIME["shutil"], "copyfile", broken_copy)
    with pytest.raises(OSError) as caught:
        run_revision(revision, output, calls)
    assert caught.value is original
    diagnostic = _read(output / "interruption.json")
    assert diagnostic["phase"] == "initialize"
    assert diagnostic["active_request_id"] is None
    assert diagnostic["attempted_count"] == diagnostic["completed_count"] == 0
    assert calls == []
    assert "private-copy-path" not in (output / "interruption.json").read_text(encoding="utf-8")


@pytest.mark.parametrize("diagnostic_fails", [False, True])
def test_secondary_checkpoint_or_diagnostic_failure_never_masks_original(
    revision, tmp_path, monkeypatch, diagnostic_fails
):
    output, calls = tmp_path / "judged", []
    original = RuntimeError("original-private-message")
    write = execute_revision.__globals__["_write"]
    write_text = Path.write_text

    def broken(_messages):
        raise original

    def checkpoint_failure(path, value):
        if path == output / "summary.json" and value["status"] == "interrupted":
            raise PermissionError("secondary-private-message")
        return write(path, value)

    def diagnostic_failure(path, *args, **kwargs):
        if diagnostic_fails and path == output / "interruption.json":
            raise OSError("diagnostic-private-message")
        return write_text(path, *args, **kwargs)

    monkeypatch.setitem(execute_revision.__globals__, "_write", checkpoint_failure)
    monkeypatch.setattr(Path, "write_text", diagnostic_failure)
    with pytest.raises(RuntimeError) as caught:
        run_revision(revision, output, calls, behavior=broken)
    assert caught.value is original
    assert len(calls) == 1
    assert len(_rows(output / "attempts.jsonl")) == 1
    assert _rows(output / "results.jsonl") == []
    if diagnostic_fails:
        assert not (output / "interruption.json").exists()
    else:
        diagnostic = _read(output / "interruption.json")
        assert diagnostic["exception_type"] == "RuntimeError"
        assert diagnostic["phase"] == "model_call"


def test_final_checkpoint_failure_is_diagnosed_after_results_are_journaled(
    revision, tmp_path, monkeypatch
):
    output, calls = tmp_path / "judged", []
    original = PermissionError("private-final-checkpoint")
    write = execute_revision.__globals__["_write"]

    def checkpoint_failure(path, value):
        if path == output / "summary.json" and value["status"] == "complete":
            raise original
        return write(path, value)

    monkeypatch.setitem(execute_revision.__globals__, "_write", checkpoint_failure)
    with pytest.raises(PermissionError) as caught:
        run_revision(revision, output, calls)
    assert caught.value is original
    diagnostic = _read(output / "interruption.json")
    assert diagnostic["status"] == "interrupted"
    assert diagnostic["phase"] == "final_checkpoint"
    assert diagnostic["active_request_id"] is None
    assert diagnostic["attempted_count"] == diagnostic["completed_count"] == 6
    assert len(_rows(output / "results.jsonl")) == len(calls) == 6


@pytest.mark.parametrize("exception_type", [PermissionError, RuntimeError, KeyboardInterrupt])
def test_cli_reports_safe_exception_class_without_printing_secret_arguments(
    tmp_path, monkeypatch, capsys, exception_type
):
    def broken(*_args, **_kwargs):
        raise exception_type("sk-secret-exception", {"Authorization": "Bearer private"})

    main = RUNTIME["main"]
    monkeypatch.setitem(main.__globals__, "execute_revision", broken)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--bundle",
            str(tmp_path / "bundle"),
            "--output",
            str(tmp_path / "judged"),
            "--judge-model",
            "test-model",
            "--approved-plan",
            "test-plan",
            "--budget-usd",
            "1",
            "--execute",
        ],
    )
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == (130 if exception_type is KeyboardInterrupt else 1)
    captured = capsys.readouterr()
    assert exception_type.__name__ in captured.err
    assert "interruption.json" in captured.err
    assert "sk-secret" not in captured.err + captured.out
    assert "Authorization" not in captured.err + captured.out
    assert "Bearer private" not in captured.err + captured.out
