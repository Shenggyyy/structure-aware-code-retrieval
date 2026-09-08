"""Audit frozen benchmark membership and split isolation without retrieving test answers."""

import json
import os
import tempfile
from collections import Counter
from pathlib import Path

from structure_aware_retrieval.evaluation.config import load_config
from structure_aware_retrieval.evaluation.dataset import _record, load_benchmark, validate_index
from structure_aware_retrieval.evaluation.recorded import analysis_provenance, read_jsonl
from structure_aware_retrieval.evaluation.reporting import _dump
from structure_aware_retrieval.indexing import load_index
from structure_aware_retrieval.models import stable_id


def audit_suite(suite_path: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Audit output already exists: {output}")
    suite = _record(
        json.loads(suite_path.read_text(encoding="utf-8")),
        {"schema_version", "id", "primary_k", "primary_metrics", "members"},
        "benchmark suite",
    )
    if type(suite["schema_version"]) is not int or suite["schema_version"] != 1:
        raise ValueError("Unsupported suite schema")
    if type(suite["primary_k"]) is not int or suite["primary_k"] < 1:
        raise ValueError("Invalid primary K")
    if (
        not isinstance(suite["primary_metrics"], list)
        or not suite["primary_metrics"]
        or len(set(suite["primary_metrics"])) != len(suite["primary_metrics"])
        or not set(suite["primary_metrics"]) <= {"recall", "precision", "mrr", "ndcg"}
    ):
        raise ValueError("Invalid primary quality metrics")
    if sorted(member["role"] for member in suite["members"]) != ["dev", "public", "test"]:
        raise ValueError("Suite requires exactly one dev, test and public member")
    owners, query_ids, texts = {}, set(), set()
    members = []
    for entry in suite["members"]:
        _record(entry, {"role", "config", "benchmark_digest", "provenance_digest"}, "suite member")
        config = load_config(suite_path.parent / entry["config"])
        benchmark = load_benchmark(config.benchmark)
        if benchmark.digest != entry["benchmark_digest"]:
            raise ValueError("Frozen benchmark digest mismatch")
        if benchmark.split != ("dev" if entry["role"] == "dev" else "test"):
            raise ValueError("Benchmark split disagrees with its suite role")
        if config.unit != "symbol" or suite["primary_k"] not in config.ks:
            raise ValueError("Suite requires symbol-level configs containing the primary K")
        if set(config.indexes) != {repo.id for repo in benchmark.repositories}:
            raise ValueError("Suite indexes must exactly match benchmark repositories")
        provenance = []
        if entry["provenance_digest"] is not None:
            provenance = read_jsonl(config.benchmark.parent / "provenance.jsonl")
            if stable_id(provenance) != entry["provenance_digest"]:
                raise ValueError("Frozen annotation provenance mismatch")
            if len(provenance) != len(benchmark.queries) or {
                row["query_id"] for row in provenance
            } != {q.id for q in benchmark.queries}:
                raise ValueError("Annotation provenance must cover every query exactly once")
        records = []
        for repository in benchmark.repositories:
            canonical = repository.url.rstrip("/").removesuffix(".git").casefold()
            if canonical in owners:
                raise ValueError("Repository overlap across suite members or aliases")
            owners[canonical] = entry["role"]
            index = load_index(config.indexes[repository.id])
            validate_index(benchmark, repository, index)
            records.append(
                {
                    "id": repository.id,
                    "url": repository.url,
                    "commit": repository.commit,
                    "license": repository.license,
                    "corpus_hash": repository.corpus_hash,
                    "snapshot_id": index.metadata["snapshot_id"],
                    "files": index.metadata["files_indexed"],
                    "symbols": len(index.symbols),
                    "chunks": len(index.chunks),
                    "index_file_bytes": config.indexes[repository.id].stat().st_size,
                }
            )
        for query in benchmark.queries:
            text = " ".join(query.text.casefold().split())
            if query.id in query_ids or text in texts:
                raise ValueError("Duplicate query ID or normalized question text across suite")
            query_ids.add(query.id)
            texts.add(text)
        members.append(
            {
                "role": entry["role"],
                "benchmark_id": benchmark.id,
                "benchmark_digest": benchmark.digest,
                "annotation_status": benchmark.annotation_status,
                "query_count": len(benchmark.queries),
                "judgment_count": len(benchmark.judgments),
                "no_answer_count": sum(not q.answerable for q in benchmark.queries),
                "by_category": dict(sorted(Counter(q.category for q in benchmark.queries).items())),
                "families": len({row["family"] for row in provenance if "family" in row}) or None,
                "repositories": records,
            }
        )
    result = {
        "suite_id": suite["id"],
        "audit_runtime": analysis_provenance(),
        "suite_digest": stable_id(suite),
        "primary_k": suite["primary_k"],
        "primary_metrics": suite["primary_metrics"],
        "repository_count": len(owners),
        "query_count": len(query_ids),
        "members": members,
        "retrieval_executed": False,
        "review_complete": all(m["annotation_status"] == "human_reviewed" for m in members),
        "limitations": [
            "Annotation status is declared, not independently authenticated.",
            "Repository disjointness and exact-text checks do not prove semantic independence "
            "or absence of model-training contamination.",
            "Public adapted scores must be reported separately "
            "from the repository question benchmark.",
        ],
    }
    lines = [
        "# Benchmark Suite Audit",
        "",
        f"Suite: `{suite['id']}`; digest: `{result['suite_digest']}`.",
        "",
        "No retrieval was executed. Annotation completeness is separate from source validation.",
        "",
        "| Role | Queries | Judgments | Repositories | Annotation status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for member in members:
        lines.append(
            f"| {member['role']} | {member['query_count']} | {member['judgment_count']} | "
            f"{len(member['repositories'])} | {member['annotation_status']} |"
        )
    lines.extend(
        [
            "",
            "## Indexed corpus sizes",
            "",
            "| Repository | Files | Symbols | Chunks | SQLite bytes |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for member in members:
        for repo in member["repositories"]:
            lines.append(
                f"| {repo['id']} | {repo['files']} | {repo['symbols']} | {repo['chunks']} | "
                f"{repo['index_file_bytes']} |"
            )
    lines.extend(["", *result["limitations"], ""])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-suite-", dir=output.parent) as temporary:
        _dump(Path(temporary) / "audit.json", result)
        (Path(temporary) / "report.md").write_text("\n".join(lines), encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Audit output was created concurrently: {output}")
        os.rename(temporary, output)
    return result
