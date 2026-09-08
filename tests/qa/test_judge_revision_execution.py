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
