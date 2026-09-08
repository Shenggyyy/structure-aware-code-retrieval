"""One-repository-per-query experiments with validated labels and atomic outputs."""

import hashlib
import os
import platform
import random
import statistics
import tempfile
import time
from dataclasses import asdict
from datetime import UTC, datetime
from functools import partial
from importlib.metadata import version
from pathlib import Path

from structure_aware_retrieval.embeddings import SentenceEncoder
from structure_aware_retrieval.evaluation.config import ExperimentConfig, load_config
from structure_aware_retrieval.evaluation.dataset import (
    Benchmark,
    load_benchmark,
    symbol_target,
    validate_index,
)
from structure_aware_retrieval.evaluation.metrics import (
    QUALITY_METRICS,
    evaluate_ranking,
    percentile,
)
from structure_aware_retrieval.evaluation.reporting import write_report
from structure_aware_retrieval.indexing import _git_provenance, load_index
from structure_aware_retrieval.models import SearchResult, stable_id
from structure_aware_retrieval.strategies import RRF_K, SYMBOL_WEIGHTS, Retriever, create_retriever
from structure_aware_retrieval.tokenization import tokenize_code


def rank_units(retriever: Retriever, hits: list[SearchResult], unit: str) -> list[dict]:
    """Deduplicate before truncating so long functions do not consume several ranks."""
    seen = set()
    results = []
    for hit in hits:
        symbol = retriever.index.symbols[hit.symbol_id]
        key = symbol.path if unit == "file" else symbol_target(symbol).key
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "rank": len(results) + 1,
                "key": key,
                "score": hit.score,
                **({"components": hit.components} if hit.components else {}),
                **({"provenance": hit.provenance} if hit.provenance else {}),
                "target": asdict(symbol_target(symbol)),
                "evidence_chunk": {
                    "id": hit.chunk_id,
                    "start_line": hit.start_line,
                    "end_line": hit.end_line,
                },
            }
        )
    return results


def _judgments(benchmark: Benchmark, query_id: str, unit: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in benchmark.judgments:
        if item.query_id == query_id:
            key = item.target.path if unit == "file" else item.target.key
            result[key] = max(result.get(key, 0), item.grade)
    return result


def retrieve_units(retriever: Retriever, text: str, *, unit: str) -> list[dict]:
    depth = max(1, len(retriever.index.chunks))
    return rank_units(retriever, retriever.search(text, top_k=depth), unit)


def _aggregate(queries: list[dict], ks: tuple[int, ...]) -> dict:
    answerable = [query for query in queries if query["answerable"]]
    metrics = {}
    for k in ks:
        metrics[k] = {
            name: statistics.mean(query["metrics"][k][name] for query in answerable)
            if answerable
            else None
            for name in QUALITY_METRICS
        }
        metrics[k]["judged_fraction"] = statistics.mean(
            query["metrics"][k]["judged_fraction"] for query in queries
        )
    samples = [sample for query in queries for sample in query["latency_ms"]["samples"]]
    return {
        "query_count": len(queries),
        "answerable_count": len(answerable),
        "no_answer_count": len(queries) - len(answerable),
        "no_answer_with_results": sum(
            not query["answerable"] and query["returned_units"] > 0 for query in queries
        ),
        "metrics": metrics,
        "latency_ms": {"p50": percentile(samples, 0.5), "p95": percentile(samples, 0.95)},
        "context_cost": {
            k: {
                name: statistics.mean(row["context_cost"][k][name] for row in queries)
                for name in ("utf8_bytes", "lines", "lexical_tokens")
            }
            for k in ks
        },
        "retrieval_work": {
            name: statistics.mean(row.get("retrieval_work", {}).get(name, 0) for row in queries)
            for name in ("seed_symbols", "edges_examined", "expanded_symbols", "edge_cap_seeds")
        },
    }


def _runtime(config: ExperimentConfig) -> dict:
    package = Path(__file__).resolve().parents[1]
    code = [
        (path.relative_to(package).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
        for path in sorted(package.rglob("*.py"))
    ]
    lock = config.source.parent.parent / "uv.lock"
    return {
        "python": platform.python_version(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
        },
        "packages": {
            name: version(name)
            for name in ("structure-aware-code-retrieval", "rank-bm25", "numpy", "pathspec")
        },
        "implementation_git": _git_provenance(package),
        "implementation_hash": stable_id(code),
        "lockfile_hash": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.is_file() else None,
    }


def run_experiment(config_path: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Run output already exists: {output}; choose a new directory")
    config = load_config(config_path)
    benchmark = load_benchmark(config.benchmark)
    if set(config.indexes) != {item.id for item in benchmark.repositories}:
        raise ValueError("Config indexes must exactly match the benchmark repositories")
    # Validate all inputs before running any query or creating output directories.
    retrievers = {}
    index_records = {}
    encoder = None
    model_load_ms = None
    if config.model_cache is not None:
        start = time.perf_counter_ns()
        encoder = SentenceEncoder(config.model_cache)
        model_load_ms = (time.perf_counter_ns() - start) / 1_000_000
    for repository in benchmark.repositories:
        start = time.perf_counter_ns()
        index = load_index(config.indexes[repository.id])
        retriever = create_retriever(
            config.strategy,
            index,
            encoder=encoder,
            vectors=config.vectors.get(repository.id),
            graph=config.graphs.get(repository.id),
            structure=config.structure,
        )
        load_ms = (time.perf_counter_ns() - start) / 1_000_000
        validate_index(benchmark, repository, index)
        retrievers[repository.id] = retriever
        index_records[repository.id] = {
            "snapshot_id": index.metadata["snapshot_id"],
            "corpus_hash": repository.corpus_hash,
            "git": index.metadata["git"],
            "config": index.metadata["config"],
            "symbol_count": len(index.symbols),
            "chunk_count": len(index.chunks),
            "load_ms": load_ms,
            "index_file_hash": hashlib.sha256(
                config.indexes[repository.id].read_bytes()
            ).hexdigest(),
        }
        if encoder is not None:
            from structure_aware_retrieval.embeddings import load_vectors

            _, metadata = load_vectors(config.vectors[repository.id], index, encoder.spec)
            index_records[repository.id]["vectors"] = metadata
            index_records[repository.id]["vector_file_bytes"] = (
                config.vectors[repository.id].stat().st_size
            )
        if config.strategy == "structure":
            index_records[repository.id]["graph"] = retriever.graph_metadata
            index_records[repository.id]["graph_file_bytes"] = (
                config.graphs[repository.id].stat().st_size
            )

    rows = []
    ranking_records = []
    schedule = []
    for repository in benchmark.repositories:
        retriever = retrievers[repository.id]
        chunk_costs = {
            chunk.id: {
                "utf8_bytes": len(chunk.text.encode("utf-8")),
                "lines": chunk.end_line - chunk.start_line + 1,
                "lexical_tokens": len(tokenize_code(chunk.text)),
            }
            for chunk in retriever.index.chunks
        }
        queries = [query for query in benchmark.queries if query.repository == repository.id]
        random.Random(config.seed).shuffle(queries)
        retrieve = partial(retrieve_units, retriever, unit=config.unit)

        for query in queries[: config.warmup_queries]:
            retrieve(query.text)
        for query in queries:
            schedule.append(query.id)
            samples = []
            ranking = None
            for _ in range(config.repeats):
                start = time.perf_counter_ns()
                current = retrieve(query.text)[: max(config.ks)]
                samples.append((time.perf_counter_ns() - start) / 1_000_000)
                if ranking is not None and current != ranking:
                    raise ValueError(f"Nondeterministic ranking during repeated query {query.id}")
                ranking = current
            assert ranking is not None
            grades = _judgments(benchmark, query.id, config.unit)
            for hit in ranking:
                hit["judgment"] = grades.get(hit["key"])
            metrics = evaluate_ranking([hit["key"] for hit in ranking], grades, config.ks)
            rows.append(
                {
                    "query_id": query.id,
                    "repository": repository.id,
                    "category": query.category,
                    "answerable": query.answerable,
                    "known_relevant": sum(grade > 0 for grade in grades.values()),
                    "returned_units": len(ranking),
                    "metrics": metrics,
                    "context_cost": {
                        k: {
                            name: sum(
                                chunk_costs[hit["evidence_chunk"]["id"]][name]
                                for hit in ranking[:k]
                            )
                            for name in ("utf8_bytes", "lines", "lexical_tokens")
                        }
                        for k in config.ks
                    },
                    "retrieval_work": dict(getattr(retriever, "last_stats", {})),
                    "latency_ms": {
                        "samples": samples,
                        "p50": percentile(samples, 0.5),
                        "p95": percentile(samples, 0.95),
                    },
                }
            )
            ranking_records.append(
                {
                    "query_id": query.id,
                    "repository": repository.id,
                    "query": query.text,
                    "ranking": ranking,
                }
            )
    rows.sort(key=lambda row: row["query_id"])
    ranking_records.sort(key=lambda row: row["query_id"])
    effective = {
        "strategy": config.strategy,
        "unit": config.unit,
        "ks": config.ks,
        "warmup_queries": config.warmup_queries,
        "repeats": config.repeats,
        "seed": config.seed,
        "candidate_policy": "all_matching_chunks_then_unique_units",
        "query_order": schedule,
    }
    if encoder is not None:
        effective["encoder"] = encoder.spec
        effective["rrf_k"] = RRF_K if config.strategy in ("hybrid", "symbol") else None
        effective["symbol_weights"] = SYMBOL_WEIGHTS if config.strategy == "symbol" else None
    if config.name is not None:
        effective["name"] = config.name
    if config.strategy == "structure":
        from structure_aware_retrieval.structure import parse_structure

        effective["structure"] = parse_structure(config.structure).describe()
        effective["rrf_k"] = RRF_K if effective["structure"]["seed_strategy"] != "bm25" else None
        effective["symbol_weights"] = (
            SYMBOL_WEIGHTS if effective["structure"]["seed_strategy"] == "symbol" else None
        )
    quality = [
        {
            key: value
            for key, value in row.items()
            if key not in {"latency_ms", "context_cost", "retrieval_work"}
        }
        for row in rows
    ]
    summary = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "benchmark": {
            "id": benchmark.id,
            "version": benchmark.version,
            "split": benchmark.split,
            "annotation_status": benchmark.annotation_status,
            "digest": benchmark.digest,
        },
        "config": effective,
        "runtime": _runtime(config),
        "indexes": index_records,
        "quality_fingerprint": stable_id(
            benchmark.digest, config.unit, config.ks, quality, ranking_records
        ),
        "overall": _aggregate(rows, config.ks),
        "by_repository": {
            repo: _aggregate([row for row in rows if row["repository"] == repo], config.ks)
            for repo in sorted({row["repository"] for row in rows})
        },
        "by_category": {
            category: _aggregate([row for row in rows if row["category"] == category], config.ks)
            for category in sorted({row["category"] for row in rows})
        },
    }
    if encoder is not None:
        summary["runtime"]["model_load_ms"] = model_load_ms
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-run-", dir=output.parent) as temporary:
        write_report(Path(temporary), summary, rows, ranking_records)
        if output.exists():
            raise FileExistsError(f"Run output was created concurrently: {output}")
        os.rename(temporary, output)
    return summary
