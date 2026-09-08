"""Freeze development QA requests without credentials, inference or reference leakage."""

import hashlib
import json
import math
import os
import tempfile
import tomllib
from dataclasses import asdict
from datetime import date
from pathlib import Path

from structure_aware_retrieval.embeddings import SentenceEncoder
from structure_aware_retrieval.evaluation.config import load_config
from structure_aware_retrieval.evaluation.dataset import (
    Benchmark,
    _identifier,
    _record,
    _string,
    load_benchmark,
    validate_index,
)
from structure_aware_retrieval.evaluation.runner import _runtime
from structure_aware_retrieval.indexing import load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.answering import (
    _object,
    complete_question,
    prepare_question,
    render_answer,
)
from structure_aware_retrieval.qa.provider import ANSWER_SCHEMA, OpenAIModel
from structure_aware_retrieval.strategies import STRATEGIES, create_retriever

DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
FRAMING_ALLOWANCE = 4096


def load_cases(path: Path) -> tuple[dict, Benchmark]:
    data = _record(
        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object),
        {
            "schema_version",
            "id",
            "version",
            "annotation_status",
            "retrieval_benchmark",
            "retrieval_benchmark_digest",
            "cases",
        },
        "QA cases",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Unsupported QA cases schema_version")
    for field in ("id", "version"):
        _identifier(data[field], field)
    if data["annotation_status"] not in ("provisional", "human_reviewed"):
        raise ValueError("Invalid QA annotation_status")
    benchmark = load_benchmark(path.parent / _string(data["retrieval_benchmark"], "benchmark"))
    if data["retrieval_benchmark_digest"] != benchmark.digest:
        raise ValueError("QA retrieval benchmark digest mismatch")
    if benchmark.split != "dev":
        raise ValueError("M7 QA cases must use development data; test results stay frozen")
    if not isinstance(data["cases"], list) or not data["cases"]:
        raise ValueError("QA cases must be a nonempty list")
    queries = {query.id: query for query in benchmark.queries}
    repositories = {repo.id for repo in benchmark.repositories}
    seen, seen_queries, seen_questions = set(), set(), set()
    for case in data["cases"]:
        _record(
            case,
            {
                "id",
                "repository",
                "question",
                "source_query_id",
                "expected_status",
                "reference_points",
                "source_targets",
                "rationale",
            },
            "QA case",
        )
        _identifier(case["id"], "QA case id")
        if case["id"] in seen:
            raise ValueError("Duplicate QA case id")
        seen.add(case["id"])
        _identifier(case["repository"], "QA repository")
        if case["repository"] not in repositories:
            raise ValueError("Unknown QA repository")
        question = _string(case["question"], "question")
        question_key = (case["repository"], " ".join(question.casefold().split()))
        if question_key in seen_questions:
            raise ValueError("Duplicate QA question in a repository")
        seen_questions.add(question_key)
        if len(question.encode("utf-8")) > 4000:
            raise ValueError("QA question exceeds 4000 bytes")
        _string(case["rationale"], "rationale")
        if not isinstance(case["reference_points"], list) or not case["reference_points"]:
            raise ValueError("QA reference_points must be a nonempty list")
        for point in case["reference_points"]:
            _string(point, "reference point")
        if not isinstance(case["source_targets"], list):
            raise ValueError("QA source_targets must be a list")
        query_id = case["source_query_id"]
        if query_id is None:
            if case["expected_status"] != "insufficient_context" or case["source_targets"]:
                raise ValueError(
                    "Standalone scope controls need insufficient_context and no targets"
                )
        else:
            _identifier(query_id, "source_query_id")
            if query_id not in queries or query_id in seen_queries:
                raise ValueError("Unknown or duplicate QA source query")
            seen_queries.add(query_id)
            query = queries[query_id]
            if query.text != question or query.repository != case["repository"]:
                raise ValueError("QA source query text/repository mismatch")
            expected = "answered" if query.answerable else "insufficient_context"
            if case["expected_status"] != expected:
                raise ValueError("QA expected_status disagrees with source query")
            targets = [
                asdict(item.target)
                for item in benchmark.judgments
                if item.query_id == query_id and item.grade > 0
            ]
            if sorted(map(stable_id, case["source_targets"])) != sorted(map(stable_id, targets)):
                raise ValueError("QA targets must exactly match all positive source judgments")
    return data, benchmark


def _load_settings(path: Path) -> dict:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    _record(
        data,
        {
            "schema_version",
            "cases",
            "model",
            "max_output_tokens",
            "max_context_bytes",
            "top_k",
            "api_key_env",
            "pricing",
            "retrieval_configs",
        },
        "QA config",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Unsupported QA config schema_version")
    OpenAIModel(data["model"], data["api_key_env"], data["max_output_tokens"])
    for field, minimum, maximum in (
        ("max_context_bytes", 2, 1_000_000),
        ("top_k", 1, 1000),
        ("max_output_tokens", 1, 16384),
    ):
        if type(data[field]) is not int or not minimum <= data[field] <= maximum:
            raise ValueError(f"{field} must be an integer in [{minimum}, {maximum}]")
    _record(data["pricing"], {"input_per_million", "output_per_million", "as_of"}, "pricing")
    for field in ("input_per_million", "output_per_million"):
        rate = data["pricing"][field]
        if type(rate) not in (int, float) or not math.isfinite(rate) or rate < 0:
            raise ValueError("Pricing must contain finite nonnegative rates")
    date.fromisoformat(_string(data["pricing"]["as_of"], "pricing as_of"))
    paths = data["retrieval_configs"]
    if not isinstance(paths, dict) or not paths or set(paths) - set(STRATEGIES):
        raise ValueError("retrieval_configs must map canonical strategy names to configs")
    for key, value in paths.items():
        _string(value, f"retrieval config {key}")
    _string(data["cases"], "cases path")
    return data


def prepare_experiment(config_path: Path, output: Path) -> dict:
    """Prepare exact requests; wall-clock measurements never affect prompt identity."""
    if output.exists() or output.is_symlink():
        raise FileExistsError("QA preparation output already exists; choose a new directory")
    config_path = config_path.resolve()
    settings = _load_settings(config_path)
    cases, benchmark = load_cases(config_path.parent / settings["cases"])
    rows, records, encoders, snapshots = [], {}, {}, {}
    configs = {
        name: load_config(config_path.parent / relative)
        for name, relative in settings["retrieval_configs"].items()
    }
    for name, config in configs.items():
        if name != config.strategy:
            raise ValueError("QA strategy name must match the retrieval config strategy")
        if load_benchmark(config.benchmark).digest != benchmark.digest:
            raise ValueError("All QA strategies must use the same retrieval benchmark")
        if set(config.indexes) != {repo.id for repo in benchmark.repositories}:
            raise ValueError("QA indexes must exactly match benchmark repositories")
    for name, config in configs.items():
        records[name] = {
            "config_sha256": hashlib.sha256(config.source.read_bytes()).hexdigest(),
            "strategy": config.strategy,
            "structure": config.structure,
            "indexes": {},
        }
        encoder = None
        if config.model_cache is not None:
            if config.model_cache not in encoders:
                encoders[config.model_cache] = SentenceEncoder(config.model_cache)
            encoder = encoders[config.model_cache]
        for repository in benchmark.repositories:
            index = load_index(config.indexes[repository.id])
            validate_index(benchmark, repository, index)
            snapshot = index.metadata["snapshot_id"]
            if repository.id in snapshots and snapshots[repository.id] != snapshot:
                raise ValueError("QA strategies must use identical source snapshots")
            snapshots[repository.id] = snapshot
            retriever = create_retriever(
                name,
                index,
                encoder=encoder,
                vectors=config.vectors.get(repository.id),
                graph=config.graphs.get(repository.id),
                structure=config.structure,
            )
            inputs = {"index": config.indexes[repository.id]}
            if repository.id in config.vectors:
                inputs["vectors"] = config.vectors[repository.id]
            if repository.id in config.graphs:
                inputs["graph"] = config.graphs[repository.id]
            records[name]["indexes"][repository.id] = {
                "snapshot_id": snapshot,
                "corpus_hash": repository.corpus_hash,
                "git": index.metadata["git"],
                "config": index.metadata["config"],
                "input_hashes": {
                    key: hashlib.sha256(path.read_bytes()).hexdigest()
                    for key, path in inputs.items()
                },
                "embedding_model": encoder.spec if encoder else None,
            }
            for case in cases["cases"]:
                if case["repository"] != repository.id:
                    continue
                rows.append(
                    {
                        "id": stable_id(name, case["id"]),
                        "strategy": name,
                        "case_id": case["id"],
                        "repository": repository.id,
                        "prepared": prepare_question(
                            retriever,
                            case["question"],
                            max_context_bytes=settings["max_context_bytes"],
                            top_k=settings["top_k"],
                        ),
                    }
                )
    candidates = [row for row in rows if row["prepared"]["context"]["evidence"]]
    schema_bytes = len(
        json.dumps(ANSWER_SCHEMA, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    estimated_input = sum(
        sum(len(m["content"].encode("utf-8")) for m in row["prepared"]["messages"])
        + FRAMING_ALLOWANCE
        + schema_bytes
        for row in candidates
    )
    estimated_output = len(candidates) * settings["max_output_tokens"]
    pricing = settings["pricing"]
    plan = {
        "schema_version": 1,
        "status": "prepared",
        "model": settings["model"],
        "max_output_tokens": settings["max_output_tokens"],
        "api_key_env": settings["api_key_env"],
        "max_context_bytes": settings["max_context_bytes"],
        "top_k": settings["top_k"],
        "request_count": len(rows),
        "maximum_api_calls": len(candidates),
        "request_digest": stable_id(rows),
        "cases_digest": stable_id(cases),
        "content_fingerprint": stable_id(
            [(r["id"], r["prepared"]["prompt_fingerprint"]) for r in rows]
        ),
        "retrieval_benchmark_digest": benchmark.digest,
        "annotation_status": cases["annotation_status"],
        "strategies": records,
        "runtime": _runtime(next(iter(configs.values()))),
        "pricing": pricing,
        "cost_estimation": {
            "scope": "answer_generation_only",
            "includes_llm_judging": False,
            "method": "one token per UTF-8 content/schema byte plus framing allowance",
            "framing_allowance_tokens_per_request": FRAMING_ALLOWANCE,
            "estimated_input_tokens": estimated_input,
            "maximum_output_tokens": estimated_output,
            "billing_guarantee": False,
        },
        "estimated_cost_usd": (
            estimated_input * pricing["input_per_million"]
            + estimated_output * pricing["output_per_million"]
        )
        / 1_000_000,
    }
    plan["plan_fingerprint"] = stable_id(plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-qa-plan-", dir=output.parent) as temporary:
        folder = Path(temporary)

        def write_json(filename: str, value: object) -> None:
            (folder / filename).write_text(
                json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
                encoding="utf-8",
            )

        write_json("plan.json", plan)
        write_json("cases.json", cases)
        (folder / "requests.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=True, allow_nan=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        previews = folder / "previews"
        previews.mkdir()
        for row in rows:
            (previews / f"{row['strategy']}-{row['case_id']}.md").write_text(
                render_answer(complete_question(row["prepared"])), encoding="utf-8"
            )
        (folder / "README.md").write_text(
            "# Prepared QA Experiment\n\n"
            "No model was called. No answers or QA quality scores exist.\n\n"
            f"{len(rows)} cases/strategies; at most {len(candidates)} API calls. "
            f"Proposed model: `{plan['model']}`. "
            f"Generation-only cost projection: ${plan['estimated_cost_usd']:.4f} USD; "
            "this is not a billing guarantee.\n\n"
            "Inspect requests.jsonl for exact messages and previews/ for source evidence. "
            "cases.json contains separate provisional references, never answering-model input. "
            "LLM judging is not included; M7b needs a combined generation/judging estimate "
            "and explicit model/budget approval. Context budgets count UTF-8 bytes, "
            "not model tokens. "
            "Timing is one preparation pass, "
            "not a latency benchmark. Execution requires explicit budget "
            "and environment credentials.\n",
            encoding="utf-8",
        )
        if output.exists() or output.is_symlink():
            raise FileExistsError("QA preparation output created concurrently")
        os.rename(folder, output)
    return plan
