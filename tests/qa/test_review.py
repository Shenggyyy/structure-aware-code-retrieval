import json
from pathlib import Path

import pytest

from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import complete_question, prepare_question
from structure_aware_retrieval.qa.execution import _review
from structure_aware_retrieval.qa.provider import ModelProviderError, ModelResponse
from structure_aware_retrieval.qa.review import check_qa_review
from structure_aware_retrieval.retrieval import BM25Retriever


class ReviewFixtureModel:
    def __init__(self, status):
        self.status = status

    def complete(self, _messages):
        if self.status == "provider_error":
            raise ModelProviderError("Synthetic provider failure")
        answer = {"status": self.status, "claims": []}
        if self.status == "answered":
            answer["claims"] = [{"text": "Synthetic checksum claim", "citations": ["S1"]}]
        text = "invalid JSON" if self.status == "invalid_answer" else json.dumps(answer)
        return ModelResponse(text, "test-model", {"total_tokens": 100})


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


@pytest.fixture
def run_fixture(sample_repository: Path, tmp_path: Path):
    database = tmp_path / "index.sqlite"
    build_index(sample_repository, database)
    retriever = BM25Retriever(load_index(database))
    cases, records = [], []
    statuses = [
        "answered",
        "answered",
        "insufficient_context",
        "provider_error",
        "preview",
        "invalid_answer",
    ]
    for number, status in enumerate(statuses):
        case_id = f"case-{number}"
        question = "What does calculate_checksum do?"
        cases.append(
            {
                "id": case_id,
                "repository": "sample",
                "question": question,
                "source_query_id": f"source-{number}",
                "expected_status": "answered",
                "reference_points": ["Provisional reference; inspect archived source."],
                "source_targets": [],
                "rationale": "Synthetic QA review fixture",
            }
        )
        prepared = prepare_question(retriever, question, top_k=1)
        result = complete_question(
            prepared, None if status == "preview" else ReviewFixtureModel(status)
        )
        records.append(
            {
                "id": stable_id("bm25", case_id),
                "strategy": "bm25",
                "case_id": case_id,
                "repository": "sample",
                "result": result,
            }
        )
    raw_cases = {
        "schema_version": 1,
        "id": "test-qa",
        "version": "v1",
        "annotation_status": "provisional",
        "retrieval_benchmark": "unread.json",
        "retrieval_benchmark_digest": stable_id("benchmark"),
        "cases": cases,
    }
    plan = {
        "schema_version": 1,
        "cases_digest": stable_id(raw_cases),
        "request_count": 8,
        "model": "test-model",
    }
    plan["plan_fingerprint"] = stable_id(plan)
    review = _review(plan, records, {case["id"]: case for case in cases})
    attempts = [
        {"id": record["id"], "model_call_planned": record["result"]["model_called"]}
        for record in records
    ]
    attempts.append({"id": stable_id("unknown-outcome"), "model_call_planned": True})
    summary = {
        "schema_version": 1,
        "plan_fingerprint": plan["plan_fingerprint"],
        "run_fingerprint": review["run_fingerprint"],
        "requested": 8,
        "attempted": 7,
        "completed": 3,
        "failed": 3,
        "not_run": 1,
        "unknown_outcome": 1,
    }
    run = tmp_path / "run"
    run.mkdir()
    for name, value in (
        ("plan.json", plan),
        ("summary.json", summary),
        ("cases.json", raw_cases),
        ("review-template.json", review),
    ):
        dump(run / name, value)
    jsonl(run / "results.jsonl", records)
    jsonl(run / "started.jsonl", attempts)
    return run, review, records


def submit_all(review):
    for number, item in enumerate(review["reviews"]):
        item.update(
            status="submitted", reviewer="Example reviewer", notes="Synthetic test judgment."
        )
        if number == 0:
            item.update(correctness="pass", citation_support="supported")
        elif number == 1:
            item.update(correctness="partial", citation_support="unsupported")
        elif number == 2:
            item.update(correctness="pass", citation_support="not_applicable")
        else:
            item.update(correctness="not_applicable", citation_support="not_applicable")


def test_pending_template_has_no_quality_metrics_and_preserves_verbatim_input(
    run_fixture, tmp_path
):
    run, _, _ = run_fixture
    judgments = run / "review-template.json"
    original = judgments.read_bytes()
    output = tmp_path / "checked"
    result = check_qa_review(run, judgments, output)
    assert result["review_complete"] is False
    assert result["reviewed"] == 0
    assert result["pending"] == 6
    assert result["answer_correctness"] is result["citation_support"] is None
    assert result["pass_fraction_requested"] is None
    assert result["reviewer_identity_verified"] is result["independence_verified"] is False
    assert result["denominators"] == {
        "requested": 8,
        "attempted": 7,
        "completed": 3,
        "failed": 3,
        "not_run": 1,
        "unknown_outcome": 1,
    }
    assert (output / "judgments.json").read_bytes() == original
    assert json.loads((output / "summary.json").read_text()) == result


def test_partial_reviews_do_not_publish_partial_quality_scores(run_fixture, tmp_path):
    run, review, _ = run_fixture
    review["reviews"][0].update(
        status="submitted",
        reviewer="Reviewer",
        notes="Checked source.",
        correctness="pass",
        citation_support="supported",
    )
    judgments = tmp_path / "partial.json"
    dump(judgments, review)
    result = check_qa_review(run, judgments, tmp_path / "partial-check")
    assert result["reviewed"] == 1
    assert result["pending"] == 5
    assert result["answer_correctness"] is result["citation_support"] is None


def test_completed_reviews_keep_denominators_and_do_not_grade_from_draft_expected_status(
    run_fixture, tmp_path
):
    run, review, _ = run_fixture
    submit_all(review)
    judgments = tmp_path / "submitted.json"
    dump(judgments, review)
    result = check_qa_review(run, judgments, tmp_path / "reviewed")
    assert result["review_complete"] is True
    assert result["answer_correctness"] == {
        "pass": 2,
        "partial": 1,
        "fail": 0,
        "denominator": 3,
        "pass_rate": pytest.approx(2 / 3),
    }
    assert result["citation_support"] == {
        "supported": 1,
        "unsupported": 1,
        "denominator": 2,
        "rate": 0.5,
    }
    assert result["pass_fraction_requested"] == 2 / 8
    assert result["status_counts"] == {
        "answered": 2,
        "insufficient_context": 1,
        "provider_error": 1,
        "preview": 1,
        "invalid_answer": 1,
    }
    # The abstention passed manual review despite the provisional expected status "answered".
    assert review["reviews"][2]["correctness"] == "pass"
    assert result["independence_verified"] is False


@pytest.mark.parametrize(
    ("index", "updates"),
    [
        (0, {"reviewer": " "}),
        (0, {"notes": ""}),
        (0, {"status": "approved"}),
        (0, {"correctness": "not_applicable"}),
        (0, {"correctness": 2}),
        (0, {"citation_support": True}),
        (0, {"citation_support": "not_applicable"}),
        (2, {"correctness": "partial"}),
        (2, {"citation_support": "supported"}),
        (3, {"correctness": "fail"}),
        (4, {"citation_support": "supported"}),
        (0, {"status": "pending"}),
        (0, {"reviewer": None}),
    ],
)
def test_incomplete_or_inapplicable_judgments_are_rejected(run_fixture, tmp_path, index, updates):
    run, review, _ = run_fixture
    submit_all(review)
    review["reviews"][index].update(updates)
    judgments = tmp_path / "invalid.json"
    dump(judgments, review)
    output = tmp_path / "must-not-exist"
    with pytest.raises(ValueError):
        check_qa_review(run, judgments, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "change", ["id", "answer", "context", "run", "plan", "missing", "duplicate", "extra"]
)
def test_review_binding_and_exact_coverage_are_required(run_fixture, tmp_path, change):
    run, review, _ = run_fixture
    if change in {"id", "answer", "context"}:
        key = {"id": "id", "answer": "answer_fingerprint", "context": "context_fingerprint"}[change]
        review["reviews"][0][key] = stable_id("different")
    elif change in {"run", "plan"}:
        review[f"{change}_fingerprint"] = stable_id("different")
    elif change == "missing":
        review["reviews"].pop()
    elif change == "duplicate":
        review["reviews"].append(review["reviews"][0])
    else:
        review["reviews"][0]["extra"] = "unsupported"
    judgments = tmp_path / "bad-binding.json"
    dump(judgments, review)
    with pytest.raises(ValueError):
        check_qa_review(run, judgments, tmp_path / "invalid")


@pytest.mark.parametrize(
    "change", ["source", "answer", "raw", "identity", "counts", "plan", "cases", "attempts"]
)
def test_tampered_run_or_evidence_is_rejected(run_fixture, tmp_path, change):
    run, _, records = run_fixture
    if change == "source":
        records[0]["result"]["context"]["evidence"][0]["text"] = "forged source\n"
    elif change == "answer":
        records[0]["result"]["answer"]["claims"][0]["text"] = "Changed accepted answer"
    elif change == "raw":
        records[0]["result"]["raw_output"] += "\n"
    elif change == "identity":
        records[0]["case_id"] = "unknown-case"
    elif change in {"counts", "plan", "cases"}:
        filename = {"counts": "summary.json", "plan": "plan.json", "cases": "cases.json"}[change]
        value = json.loads((run / filename).read_text())
        if change == "counts":
            value["not_run"] = 0
        elif change == "plan":
            value["model"] = "unbound-model"
        else:
            value["cases"][0]["reference_points"] = ["Changed reference"]
        dump(run / filename, value)
    else:
        attempts = [json.loads(line) for line in (run / "started.jsonl").read_text().splitlines()]
        attempts[0]["id"] = stable_id("different")
        jsonl(run / "started.jsonl", attempts)
    jsonl(run / "results.jsonl", records)
    with pytest.raises(ValueError):
        check_qa_review(run, run / "review-template.json", tmp_path / "tampered")


def test_duplicate_json_fields_and_nonfinite_values_are_rejected(run_fixture, tmp_path):
    run, _, _ = run_fixture
    for number, text in enumerate(['{"schema_version":1,"schema_version":1}', '{"number":NaN}']):
        path = tmp_path / f"bad-{number}.json"
        path.write_text(text)
        with pytest.raises(ValueError):
            check_qa_review(run, path, tmp_path / f"out-{number}")


def test_no_recorded_outcomes_cannot_complete_review(run_fixture, tmp_path):
    run, _, _ = run_fixture
    plan = json.loads((run / "plan.json").read_text())
    review = _review(plan, [], {})
    summary = json.loads((run / "summary.json").read_text())
    summary.update(
        run_fingerprint=review["run_fingerprint"],
        attempted=0,
        completed=0,
        failed=0,
        not_run=8,
        unknown_outcome=0,
    )
    jsonl(run / "results.jsonl", [])
    jsonl(run / "started.jsonl", [])
    dump(run / "summary.json", summary)
    dump(run / "review-template.json", review)
    result = check_qa_review(run, run / "review-template.json", tmp_path / "no-records")
    assert result["review_complete"] is False
    assert result["answer_correctness"] is None
    assert result["denominators"]["not_run"] == 8


def test_empty_evidence_abstention_remains_reviewable(run_fixture, tmp_path):
    run, _, records = run_fixture
    retriever = BM25Retriever(load_index(tmp_path / "index.sqlite"))
    prepared = prepare_question(retriever, records[0]["result"]["question"], max_context_bytes=2)
    records[0]["result"] = complete_question(prepared)
    plan = json.loads((run / "plan.json").read_text())
    review = _review(plan, records, {})
    summary = json.loads((run / "summary.json").read_text())
    summary["run_fingerprint"] = review["run_fingerprint"]
    attempts = [json.loads(line) for line in (run / "started.jsonl").read_text().splitlines()]
    attempts[0]["model_call_planned"] = False
    jsonl(run / "results.jsonl", records)
    jsonl(run / "started.jsonl", attempts)
    dump(run / "summary.json", summary)
    dump(run / "review-template.json", review)
    result = check_qa_review(run, run / "review-template.json", tmp_path / "empty-evidence")
    assert result["status_counts"]["insufficient_context"] == 2
    assert result["reviewed"] == 0
    assert result["answer_correctness"] is None


def test_strategy_comparison_waits_for_global_review_and_uses_planned_denominators(
    run_fixture, tmp_path
):
    run, _, records = run_fixture
    for number, row in enumerate(records):
        row["strategy"] = "bm25" if number in (0, 2, 3) else "dense"
        row["id"] = stable_id(row["strategy"], row["case_id"])
    plan = json.loads((run / "plan.json").read_text())
    review = _review(plan, records, {})
    summary = json.loads((run / "summary.json").read_text())
    summary.update(
        run_fingerprint=review["run_fingerprint"],
        per_strategy={
            "bm25": {"requested": 4},
            "dense": {"requested": 3},
            "structure": {"requested": 1},
        },
    )
    attempts = [json.loads(line) for line in (run / "started.jsonl").read_text().splitlines()]
    for row, attempt in zip(records, attempts, strict=False):
        attempt["id"] = row["id"]
    jsonl(run / "results.jsonl", records)
    jsonl(run / "started.jsonl", attempts)
    dump(run / "summary.json", summary)
    judgments = tmp_path / "strategy-judgments.json"
    submit_all(review)
    review["reviews"][1].update(correctness="fail")
    # One pending unrelated outcome withholds every strategy's quality metrics.
    review["reviews"][-1].update(status="pending", correctness=None, citation_support=None)
    dump(judgments, review)
    pending = check_qa_review(run, judgments, tmp_path / "strategies-pending")
    assert set(pending["per_strategy"]) == {"bm25", "dense", "structure"}
    for strategy in pending["per_strategy"].values():
        assert strategy["answer_correctness"] is strategy["citation_support"] is None
        assert strategy["pass_fraction_requested"] is None
    review["reviews"][-1].update(
        status="submitted", correctness="not_applicable", citation_support="not_applicable"
    )
    dump(judgments, review)
    completed = check_qa_review(run, judgments, tmp_path / "strategies-complete")["per_strategy"]
    assert completed["bm25"]["recorded"] == 3
    assert completed["bm25"]["answer_correctness"]["pass"] == 2
    assert completed["bm25"]["answer_correctness"]["pass_rate"] == 1
    assert completed["bm25"]["citation_support"]["rate"] == 1
    assert completed["bm25"]["pass_fraction_requested"] == 2 / 4
    assert completed["dense"]["answer_correctness"]["fail"] == 1
    assert completed["dense"]["citation_support"]["rate"] == 0
    assert completed["dense"]["pass_fraction_requested"] == 0 / 3
    assert completed["structure"]["requested"] == 1
    assert completed["structure"]["recorded"] == 0
    assert completed["structure"]["answer_correctness"]["pass_rate"] is None
    assert completed["structure"]["pass_fraction_requested"] == 0


def test_existing_output_and_failed_publish_preserve_data(run_fixture, tmp_path, monkeypatch):
    run, _, _ = run_fixture
    output = tmp_path / "existing"
    output.mkdir()
    (output / "owner.txt").write_text("Keep me")
    with pytest.raises(FileExistsError):
        check_qa_review(run, run / "review-template.json", output)
    assert (output / "owner.txt").read_text() == "Keep me"

    def fail_rename(_source, _destination):
        raise OSError("Synthetic publish failure")

    monkeypatch.setattr("structure_aware_retrieval.qa.review.os.rename", fail_rename)
    output = tmp_path / "failed"
    with pytest.raises(OSError, match="publish failure"):
        check_qa_review(run, run / "review-template.json", output)
    assert not output.exists()
    assert list(tmp_path.glob(".sacr-qa-review-*")) == []
