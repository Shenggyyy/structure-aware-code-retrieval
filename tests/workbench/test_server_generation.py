"""Paid HTTP boundary tests use an injected model and never contact an API."""

import http.client
import json
import threading
import time
from contextlib import contextmanager

import numpy as np
import pytest

from structure_aware_retrieval.qa.provider import ModelProviderError, ModelResponse
from structure_aware_retrieval.workbench import generation, server
from structure_aware_retrieval.workbench.comparison import preview_question
from structure_aware_retrieval.workbench.importing import import_repository
from structure_aware_retrieval.workbench.preparation import prepare_repository
from structure_aware_retrieval.workbench.storage import read_json, write_json


class FixtureEncoder:
    spec = {
        "id": "synthetic",
        "revision": "web-generation-test",
        "dimensions": 2,
        "max_seq_length": 256,
    }

    def encode(self, texts):
        return np.asarray([[1.0, 0.0] for _ in texts], dtype=np.float32).reshape(-1, 2)

    def token_lengths(self, texts):
        return [len(text.split()) for text in texts]


class RecordingModel:
    def __init__(self):
        self.messages = []

    def complete(self, messages):
        self.messages.append(messages)
        return ModelResponse(
            text=json.dumps(
                {"status": "answered", "claims": [{"text": "Fixture answer", "citations": ["S1"]}]}
            ),
            model=generation.GENERATION_MODEL,
            usage={
                "input_tokens": 32,
                "output_tokens": 24,
                "total_tokens": 56,
                "cached_tokens": 0,
                "reasoning_tokens": 0,
            },
            request_id="offline-fixture-request",
            raw_response={"fixture": True},
        )


@contextmanager
def running(workspace):
    instance = server.create_server(workspace)
    thread = threading.Thread(target=instance.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    try:
        yield instance
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def request(instance, path, *, payload=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", instance.server_port, timeout=10)
    selected = {}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        selected.update(
            {
                "Origin": instance.origin,
                "X-Workbench-Token": instance.csrf_token,
                "Content-Type": "application/json",
            }
        )
    selected.update(headers or {})
    selected = {key: value for key, value in selected.items() if value is not None}
    try:
        connection.request("POST" if payload is not None else "GET", path, body, selected)
        response = connection.getresponse()
        data = response.read()
        value = (
            json.loads(data)
            if "application/json" in response.getheader("Content-Type", "")
            else data
        )
        return response.status, value
    finally:
        connection.close()


def wait_job(instance, job_id):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        status, row = request(instance, f"/api/jobs/{job_id}")
        assert status == 200
        if row["status"] in {"completed", "failed", "interrupted"}:
            return row
        time.sleep(0.01)
    pytest.fail("Generation job did not finish")


@pytest.fixture
def preview(tmp_path, sample_repository):
    workspace = tmp_path / "workspace"
    repository = import_repository(str(sample_repository), workspace)
    encoder = FixtureEncoder()
    prepare_repository(workspace, repository["repository_id"], encoder=encoder)
    run = preview_question(
        workspace, repository["repository_id"], "checksum payload", encoder=encoder, top_k=2
    )
    assert run["status"] == "preview_complete"
    return workspace, read_json(workspace, f"runs/{run['run_id']}/run.json")


@pytest.fixture
def fake_model(monkeypatch):
    model = RecordingModel()
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key-secret-marker")

    def execute(*args, **kwargs):
        return generation.execute_generation_plan(*args, model=model, **kwargs)

    monkeypatch.setattr(server, "execute_generation_plan", execute)
    return model


def plan_request(instance, preview):
    status, plan = request(instance, "/api/generation-plan", payload={"run_id": preview["run_id"]})
    assert status == 201, plan
    return plan


def approval(plan):
    return {
        "plan_id": plan["plan_id"],
        "confirmed_model": plan["model"],
        "budget_usd": max(1, plan["estimated_cost_usd"] * 2),
        "confirm": True,
    }


def test_plan_and_read_routes_are_offline_without_a_key(preview, monkeypatch):
    workspace, saved = preview
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def forbidden(*args, **kwargs):
        pytest.fail("Planning and reading cannot invoke a model")

    monkeypatch.setattr(server, "execute_generation_plan", forbidden)
    with running(workspace) as instance:
        status, session = request(instance, "/api/session")
        assert status == 200 and session["api_calls"] == 0
        assert session["generation"] == {
            "model": generation.GENERATION_MODEL,
            "key_ready": False,
            "request_limit": 5,
            "judge_calls": 0,
        }
        plan = plan_request(instance, saved)
        assert plan["request_limit"] == 5 and plan["judge_calls"] == 0
        assert plan["estimated_cost_usd"] > 0
        assert plan["model"] == generation.GENERATION_MODEL
        assert request(instance, f"/api/generation-plans/{plan['plan_id']}") == (200, plan)
        assert request(instance, f"/api/runs/{saved['run_id']}") == (200, saved)
        assert len(request(instance, "/api/history")[1]) == 1
        assert request(instance, "/api/jobs")[1] == []
        assert request(instance, "/")[0] == 200
        assert request(instance, "/api/generate")[0] == 404
        assert request(instance, "/api/generate", payload=approval(plan))[0] == 400
        assert request(instance, "/api/jobs")[1] == []
        assert generation.load_generation_execution(workspace, plan["plan_id"]) is None


@pytest.mark.parametrize(
    "change",
    [
        {"confirm": False},
        {"confirm": 1},
        {"confirm": None},
        {"confirmed_model": "other-model"},
        {"confirmed_model": None},
        {"budget_usd": None},
        {"budget_usd": True},
        {"budget_usd": "1.00"},
        {"budget_usd": -1},
        {"budget_usd": 0},
        {"budget_usd": float("nan")},
        {"budget_usd": float("inf")},
        {"plan_id": "../outside"},
        {"api_key": "forbidden"},
        {"model": "other-model"},
        {"endpoint": "https://example.com"},
    ],
)
def test_invalid_approval_is_rejected_before_a_job_or_request(preview, fake_model, change):
    workspace, saved = preview
    with running(workspace) as instance:
        plan = plan_request(instance, saved)
        payload = approval(plan) | change
        assert request(instance, "/api/generate", payload=payload)[0] == 400
        assert request(instance, "/api/jobs")[1] == []
    assert fake_model.messages == []


@pytest.mark.parametrize("field", ["plan_id", "confirmed_model", "budget_usd", "confirm"])
def test_all_approval_fields_are_required(preview, fake_model, field):
    workspace, saved = preview
    with running(workspace) as instance:
        plan = plan_request(instance, saved)
        payload = approval(plan)
        del payload[field]
        assert request(instance, "/api/generate", payload=payload)[0] == 400
        assert request(instance, "/api/jobs")[1] == []
    assert fake_model.messages == []


@pytest.mark.parametrize("endpoint", ["/api/generation-plan", "/api/generate"])
@pytest.mark.parametrize(
    "headers",
    [{"Origin": None}, {"Origin": "https://evil.example"}, {"X-Workbench-Token": None}],
)
def test_generation_mutations_keep_same_origin_session_protection(tmp_path, endpoint, headers):
    with running(tmp_path / "workspace") as instance:
        assert request(instance, endpoint, payload={}, headers=headers)[0] == 403
        assert request(instance, "/api/jobs")[1] == []


def test_generation_is_saved_separately_and_cannot_replay_after_restart(preview, fake_model):
    workspace, saved = preview
    original = (workspace / f"runs/{saved['run_id']}/run.json").read_bytes()
    with running(workspace) as instance:
        plan = plan_request(instance, saved)
        assert request(instance, "/api/session")[1]["generation"]["key_ready"] is True
        status, submitted = request(instance, "/api/generate", payload=approval(plan))
        assert status == 202, submitted
        record = wait_job(instance, submitted["job_id"])
        assert record["status"] == "completed", record
        assert record["kind"] == "generation" and record["api_calls"] == 0
        generated = request(instance, f"/api/runs/{record['result']['run_id']}")[1]
        assert generated["run_id"] != saved["run_id"]
        assert generated["parent_preview_run_id"] == saved["run_id"]
        assert generated["mode"] == "offline_test"
        assert generated["status"] == "generation_complete"
        assert generated["api_calls"] == 0
        assert generated["generation"]["summary"]["calls_started"] == 5
        assert generated["benchmark_metrics"] is None
        for row in generated["results"]:
            assert row["qa"]["answer"]["claims"][0]["text"] == "Fixture answer"
            assert row["qa"]["automatic_checks"]["paths_valid"] is True
            assert row["qa"]["llm_assessment"]["status"] == "not_run"
        assert len(request(instance, "/api/history")[1]) == 2
        assert request(instance, "/api/generate", payload=approval(plan))[0] == 409
        assert "not-a-real-key-secret-marker" not in json.dumps(
            [generated, request(instance, "/api/session")[1], record]
        )
    assert len(fake_model.messages) == 5
    assert (workspace / f"runs/{saved['run_id']}/run.json").read_bytes() == original
    with running(workspace) as instance:
        assert request(instance, f"/api/runs/{generated['run_id']}")[1] == generated
        assert request(instance, "/api/generate", payload=approval(plan))[0] == 409
    assert len(fake_model.messages) == 5


def test_recovery_resolves_claim_before_first_web_progress_without_rewriting_results(
    preview, fake_model
):
    workspace, saved = preview
    with running(workspace) as instance:
        plan = plan_request(instance, saved)
        status, submitted = request(instance, "/api/generate", payload=approval(plan))
        assert status == 202
        record = wait_job(instance, submitted["job_id"])
        assert record["status"] == "completed"
    generated_id = record["result"]["run_id"]
    archive = workspace / f"runs/{generated_id}/run.json"
    original = archive.read_bytes()
    record.update(
        status="running",
        result=None,
        api_calls=0,
        progress={"phase": "generation", "detail": {"plan_id": plan["plan_id"]}},
    )
    write_json(workspace, f"web-jobs/{record['job_id']}.json", record)
    with running(workspace) as instance:
        recovered = request(instance, f"/api/jobs/{record['job_id']}")[1]
        assert recovered["status"] == "interrupted"
        assert recovered["api_calls"] == 0
        assert recovered["progress"]["detail"]["run_id"] == generated_id
        assert recovered["progress"]["detail"]["status"] == "generation_complete"
        assert request(instance, "/api/generate", payload=approval(plan))[0] == 409
    assert len(fake_model.messages) == 5
    assert archive.read_bytes() == original


def test_busy_generation_and_unknown_outcome_never_resubmit(preview, fake_model, monkeypatch):
    workspace, saved = preview
    entered, release = threading.Event(), threading.Event()

    def unknown(messages):
        fake_model.messages.append(messages)
        entered.set()
        assert release.wait(timeout=10)
        raise ModelProviderError("Transport failed; response outcome is unknown")

    monkeypatch.setattr(fake_model, "complete", unknown)
    with running(workspace) as instance:
        plan = plan_request(instance, saved)
        status, submitted = request(instance, "/api/generate", payload=approval(plan))
        assert status == 202
        try:
            assert entered.wait(timeout=5)
            status, conflict = request(instance, "/api/generate", payload=approval(plan))
            assert status == 409 and conflict["job_id"] == submitted["job_id"]
        finally:
            release.set()
        record = wait_job(instance, submitted["job_id"])
        assert record["status"] == "completed"
        generated = request(instance, f"/api/runs/{record['result']['run_id']}")[1]
        assert generated["status"] == "interrupted"
        summary = generated["generation"]["summary"]
        assert summary["calls_started"] == 1 and summary["outcome_unknown"] == 1
        assert summary["not_run"] == 4
        assert generated["results"][0]["status"] == "outcome_unknown"
        assert generated["results"][0]["tokens"]["input"] is None
        assert generated["results"][0]["cost"]["estimated_usd"] is None
        assert all(row["qa"]["answer"] is None for row in generated["results"])
        assert request(instance, "/api/generate", payload=approval(plan))[0] == 409
    with running(workspace) as instance:
        assert request(instance, f"/api/runs/{generated['run_id']}")[1] == generated
        assert request(instance, "/api/generate", payload=approval(plan))[0] == 409
    assert len(fake_model.messages) == 1


def test_shutdown_keeps_received_answer_and_stops_remaining_calls(preview, fake_model, monkeypatch):
    workspace, saved = preview
    entered, release = threading.Event(), threading.Event()
    complete = fake_model.complete

    def held(messages):
        entered.set()
        assert release.wait(timeout=10)
        return complete(messages)

    monkeypatch.setattr(fake_model, "complete", held)
    plan = generation.create_generation_plan(workspace, saved["run_id"])
    instance = server.create_server(workspace)
    submitted = instance.jobs.submit("generation", approval(plan))
    try:
        assert entered.wait(timeout=5)
        instance.server_close()
        with pytest.raises(ValueError, match="Another browser server"):
            server.create_server(workspace)
    finally:
        release.set()
    deadline = time.monotonic() + 5
    while instance.jobs.active is not None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert instance.jobs.active is None
    generated = generation.load_generation_execution(workspace, plan["plan_id"])
    assert generated["status"] == "interrupted"
    summary = generated["generation"]["summary"]
    assert summary["calls_started"] == 1 and summary["responses_received"] == 1
    assert summary["outcome_unknown"] == 0 and summary["not_run"] == 4
    assert generated["results"][0]["qa"]["answer"]["claims"][0]["text"] == "Fixture answer"
    with running(workspace) as restarted:
        recovered = request(restarted, f"/api/jobs/{submitted['job_id']}")[1]
        assert recovered["status"] == "interrupted"
        assert recovered["progress"]["detail"]["status"] == "interrupted"
        assert recovered["progress"]["detail"]["results"][0]["status"] == "answered"
    assert len(fake_model.messages) == 1


def test_invalid_generation_archive_remains_visible_without_overwriting_it(tmp_path):
    workspace = tmp_path / "workspace"
    write_json(workspace, f"generation-plans/{'a' * 32}/plan.json", {"broken": True})
    record = {
        "schema_version": 1,
        "job_id": "b" * 32,
        "kind": "generation",
        "status": "running",
        "progress": {"phase": "generation", "detail": {"plan_id": "../invalid"}},
    }
    write_json(workspace, f"web-jobs/{record['job_id']}.json", record)
    with running(workspace) as instance:
        recovered = request(instance, f"/api/jobs/{record['job_id']}")[1]
        assert recovered["status"] == "interrupted" and recovered["recovery_warning"]
    assert read_json(workspace, f"generation-plans/{'a' * 32}/plan.json") == {"broken": True}
