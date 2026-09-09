"""Generation CLI requires a reviewed plan and explicit bounded paid consent."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app

runner = CliRunner()
MODULE = "structure_aware_retrieval.workbench.generation."
PREVIEW_ID = "a" * 32
PLAN_ID = "b" * 32
RUN_ID = "c" * 32
MODEL = "gpt-5.4-mini-2026-03-17"


def _plan():
    return {
        "plan_id": PLAN_ID,
        "preview_run_id": PREVIEW_ID,
        "model": MODEL,
        "request_limit": 4,
        "judge_calls": 0,
        "estimated_cost_usd": 0.0624,
        "strategies": [
            {"strategy": "bm25", "status": "ready"},
            {"strategy": "dense", "status": "unavailable"},
        ],
    }


def _generation(status="generation_complete", cost=0.00625):
    return {
        "run_id": RUN_ID,
        "repository_id": "d" * 64,
        "question": "Where are source paths checked?",
        "status": status,
        "mode": "model_generation",
        "api_calls": 2,
        "generation": {"summary": {"usage": {"cost_usd_at_frozen_uncached_rates": cost}}},
        "results": [
            {"strategy": "bm25", "status": "answered", "hits": [], "error": None},
            {
                "strategy": "dense",
                "status": "outcome_unknown" if status == "partial" else "answered",
                "hits": [],
                "error": "No saved response" if status == "partial" else None,
            },
        ],
    }


def test_plan_forwards_preview_and_reports_scope_without_execution(monkeypatch):
    calls = []

    def create_plan(workspace, preview_run_id):
        calls.append((workspace, preview_run_id))
        return _plan()

    monkeypatch.setattr(MODULE + "create_generation_plan", create_plan)
    monkeypatch.setattr(
        MODULE + "execute_generation_plan", lambda *a, **k: pytest.fail("paid execution")
    )
    result = runner.invoke(app, ["workbench", "plan", PREVIEW_ID])
    assert result.exit_code == 0, result.output
    assert calls == [(Path("artifacts/workbench"), PREVIEW_ID)]
    assert MODEL in result.output
    assert PLAN_ID in result.output
    assert "Maximum generation requests: 4; judge requests: 0" in result.output
    assert "US$0.062400" in result.output
    assert "dense: unavailable" in result.output
    assert "API calls: 0" in result.output
    assert "not an invoice" in result.output


def test_plan_json_preserves_exact_plan(monkeypatch, tmp_path):
    calls = []
    plan = _plan()

    def create_plan(workspace, preview_run_id):
        calls.append((workspace, preview_run_id))
        return plan

    monkeypatch.setattr(MODULE + "create_generation_plan", create_plan)
    result = runner.invoke(
        app, ["workbench", "plan", PREVIEW_ID, "--workspace", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == plan
    assert calls == [(tmp_path, PREVIEW_ID)]


def _arguments(*extra):
    return [
        "workbench",
        "generate",
        PLAN_ID,
        "--budget-usd",
        "0.10",
        "--confirm-model",
        MODEL,
        *extra,
    ]


def test_generation_requires_paid_flag_before_backend(monkeypatch):
    monkeypatch.setattr(
        MODULE + "execute_generation_plan", lambda *a, **k: pytest.fail("paid execution")
    )
    result = runner.invoke(app, _arguments())
    assert result.exit_code == 1
    assert "requires explicit --confirm-paid" in result.output


@pytest.mark.parametrize("budget", ["0", "-1", "nan", "inf"])
def test_generation_rejects_nonpositive_or_nonfinite_budget_before_backend(monkeypatch, budget):
    monkeypatch.setattr(
        MODULE + "execute_generation_plan", lambda *a, **k: pytest.fail("paid execution")
    )
    arguments = _arguments("--confirm-paid")
    arguments[4] = budget
    result = runner.invoke(app, arguments)
    assert result.exit_code != 0


@pytest.mark.parametrize("omit", ["--budget-usd", "--confirm-model"])
def test_generation_requires_model_and_budget_options(monkeypatch, omit):
    monkeypatch.setattr(
        MODULE + "execute_generation_plan", lambda *a, **k: pytest.fail("paid execution")
    )
    arguments = _arguments("--confirm-paid")
    offset = arguments.index(omit)
    del arguments[offset : offset + 2]
    result = runner.invoke(app, arguments)
    assert result.exit_code == 2


def test_generation_forwards_confirmed_plan_model_budget_and_reports_result(monkeypatch, tmp_path):
    calls = []

    def execute(workspace, plan_id, *, budget_usd, confirmed_model):
        calls.append((workspace, plan_id, budget_usd, confirmed_model))
        return _generation()

    monkeypatch.setattr(MODULE + "execute_generation_plan", execute)
    result = runner.invoke(app, _arguments("--confirm-paid", "--workspace", str(tmp_path)))
    assert result.exit_code == 0, result.output
    assert calls == [(tmp_path, PLAN_ID, 0.1, MODEL)]
    assert "generation_complete; mode: model_generation; API calls: 2" in result.output
    assert "bm25: answered" in result.output
    assert "US$0.006250" in result.output
    assert "attempted requests cannot be retried" in result.output


@pytest.mark.parametrize("status", ["generation_complete", "partial", "interrupted"])
def test_generation_json_preserves_outcomes_before_nonzero_exit(monkeypatch, status):
    record = _generation(status, cost=None)
    monkeypatch.setattr(MODULE + "execute_generation_plan", lambda *a, **k: record)
    result = runner.invoke(app, _arguments("--confirm-paid", "--json"))
    assert result.exit_code == (0 if status == "generation_complete" else 1)
    assert json.loads(result.output) == record


def test_partial_generation_keeps_unknown_usage_and_prior_answers(monkeypatch):
    monkeypatch.setattr(
        MODULE + "execute_generation_plan", lambda *a, **k: _generation("partial", cost=None)
    )
    result = runner.invoke(app, _arguments("--confirm-paid"))
    assert result.exit_code == 1
    assert "bm25: answered" in result.output
    assert "dense: outcome_unknown" in result.output
    assert "Usage-based cost estimate: unknown" in result.output


@pytest.mark.parametrize(
    ("command", "function", "message"),
    [
        (["workbench", "plan", PREVIEW_ID], "create_generation_plan", "Invalid saved preview"),
        (_arguments("--confirm-paid"), "execute_generation_plan", "Plan already executed"),
        (_arguments("--confirm-paid"), "execute_generation_plan", "Confirmed model mismatch"),
        (_arguments("--confirm-paid"), "execute_generation_plan", "Budget below frozen estimate"),
    ],
)
def test_plan_or_approval_failure_is_clear_without_retry(monkeypatch, command, function, message):
    calls = []

    def fail(*args, **kwargs):
        calls.append(args)
        raise ValueError(message)

    monkeypatch.setattr(MODULE + function, fail)
    result = runner.invoke(app, command)
    assert result.exit_code == 1
    assert f"Error: {message}" in result.output
    assert "Traceback" not in result.output
    assert len(calls) == 1


def test_generation_discovery_remains_lazy_without_secret_input_flags():
    script = """
import sys
from typer.testing import CliRunner
from structure_aware_retrieval.cli import app
for command in ('plan', 'generate'):
    result = CliRunner().invoke(app, ['workbench', command, '--help'])
    assert result.exit_code == 0, result.output
    assert '--api-key' not in result.output
assert '--confirm-paid' in result.output
assert '--confirm-model' in result.output
assert '--budget-usd' in result.output
assert 'structure_aware_retrieval.workbench.generation' not in sys.modules
assert 'structure_aware_retrieval.qa.provider' not in sys.modules
assert 'torch' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
