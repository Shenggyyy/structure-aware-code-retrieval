"""Build provisional, source-bound labels without running retrieval or source code."""

import ast
import gzip
import hashlib
import io
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from structure_aware_retrieval.evaluation.dataset import (
    _identifier,
    _record,
    _relative,
    _string,
    load_benchmark,
    symbol_target,
    validate_index,
)
from structure_aware_retrieval.evaluation.reporting import _dump
from structure_aware_retrieval.indexing import LoadedIndex, load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.relations import snapshot_sources


def _recipe(path: Path, extra: str) -> dict:
    recipe = _record(
        json.loads(path.read_text(encoding="utf-8")),
        {"schema_version", "id", "version", "split", "repositories", extra},
        "curation recipe",
    )
    if type(recipe["schema_version"]) is not int or recipe["schema_version"] != 1:
        raise ValueError("Unsupported curation recipe schema")
    # Validate identifiers before using repository IDs to construct filesystem paths.
    for repository in recipe["repositories"]:
        _identifier(repository["id"], "repository id")
    return recipe


def _manifest(recipe: dict) -> dict:
    return {
        **{
            key: recipe[key] for key in ("schema_version", "id", "version", "split", "repositories")
        },
        "annotation_status": "provisional",
        "queries_file": "queries.jsonl",
        "qrels_file": "qrels.jsonl",
    }


def _publish(
    output: Path,
    recipe: dict,
    indexes: dict[str, LoadedIndex],
    queries: list[dict],
    judgments: list[dict],
    provenance: list[dict],
) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Benchmark output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-curation-", dir=output.parent) as temporary:
        folder = Path(temporary)
        _dump(folder / "benchmark.json", _manifest(recipe))
        for filename, rows in (
            ("queries", queries),
            ("qrels", judgments),
            ("provenance", provenance),
        ):
            (folder / f"{filename}.jsonl").write_text(
                "".join(json.dumps(row, ensure_ascii=True, allow_nan=False) + "\n" for row in rows),
                encoding="utf-8",
            )
        benchmark = load_benchmark(folder / "benchmark.json")
        for repository in benchmark.repositories:
            validate_index(benchmark, repository, indexes[repository.id])
        result = {
            "benchmark_digest": benchmark.digest,
            "provenance_digest": stable_id(provenance),
            "query_count": len(queries),
            "judgment_count": len(judgments),
            "annotation_status": benchmark.annotation_status,
            "retrieval_executed": False,
        }
        _dump(folder / "freeze.json", result)
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Benchmark output was created concurrently: {output}")
        os.rename(temporary, output)
    return result


def build_curated_benchmark(recipe_path: Path, index_directory: Path, output: Path) -> dict:
    """Resolve explicit source targets, rejecting ambiguous names instead of guessing."""
    recipe = _recipe(recipe_path, "annotation_files")
    indexes = {
        repo["id"]: load_index(index_directory / f"{repo['id']}.sqlite")
        for repo in recipe["repositories"]
    }
    sources = {repo: snapshot_sources(index) for repo, index in indexes.items()}
    queries, judgments, provenance = [], [], []
    seen_repositories = set()
    for relative in recipe["annotation_files"]:
        path = (recipe_path.parent / _relative(relative, "annotation file")).resolve()
        if not path.is_relative_to(recipe_path.parent.resolve()):
            raise ValueError("Annotation file escapes the recipe directory")
        spec = _record(
            json.loads(path.read_text(encoding="utf-8")),
            {"schema_version", "repository_id", "questions"},
            "annotations",
        )
        if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
            raise ValueError("Unsupported annotation schema")
        repo = spec["repository_id"]
        if repo not in indexes or repo in seen_repositories:
            raise ValueError("Each recipe repository needs exactly one annotation file")
        seen_repositories.add(repo)
        index = indexes[repo]
        for query in spec["questions"]:
            _record(query, {"id", "category", "family", "text", "targets"}, "draft query")
            _identifier(query["family"], "question family")
            evidence = []
            for target in query["targets"]:
                _record(
                    target,
                    {"path", "name", "grade", "rationale"}
                    | ({"start_line"} if "start_line" in target else set()),
                    "draft target",
                )
                _relative(target["path"], "target path")
                _string(target["name"], "target name")
                if "start_line" in target and (
                    type(target["start_line"]) is not int or target["start_line"] < 1
                ):
                    raise ValueError("Target start_line must be a positive integer")
                module = target["path"][:-3].replace("/", ".").removesuffix(".__init__")
                qualified = module + "." + target["name"]
                matches = [
                    symbol
                    for symbol in index.symbols.values()
                    if symbol.path == target["path"]
                    and symbol.qualified_name == qualified
                    and ("start_line" not in target or symbol.start_line == target["start_line"])
                ]
                if len(matches) != 1:
                    raise ValueError(f"{query['id']}: target must resolve uniquely: {qualified}")
                symbol = matches[0]
                locator = asdict(symbol_target(symbol))
                judgments.append(
                    {
                        "query_id": query["id"],
                        "target": locator,
                        "grade": target["grade"],
                        "rationale": target["rationale"],
                    }
                )
                text = "".join(
                    io.StringIO(sources[repo][symbol.path]).readlines()[
                        symbol.start_line - 1 : symbol.end_line
                    ]
                )
                evidence.append(
                    {
                        "target": locator,
                        "file_sha256": dict(index.metadata["manifest"])[symbol.path],
                        "symbol_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    }
                )
            queries.append(
                {
                    "id": query["id"],
                    "repository": repo,
                    "category": query["category"],
                    "text": query["text"],
                    "answerable": any(target["grade"] > 0 for target in query["targets"]),
                }
            )
            if (
                query["category"] == "cross_file"
                and len({target["path"] for target in query["targets"] if target["grade"] > 0}) < 2
            ):
                raise ValueError("Cross-file questions need positive targets in at least two files")
            provenance.append(
                {
                    "query_id": query["id"],
                    "origin": "agent_authored_source_checked_draft",
                    "family": f"{repo}:{query['family']}",
                    "recipe_digest": stable_id(recipe),
                    "annotation_digest": stable_id(spec),
                    "snapshot_id": index.metadata["snapshot_id"],
                    "independent_review": "pending",
                    "evidence": evidence,
                }
            )
    if seen_repositories != set(indexes):
        raise ValueError("Each recipe repository needs exactly one annotation file")
    return _publish(output, recipe, indexes, queries, judgments, provenance)


def build_repoqa_subset(
    recipe_path: Path, archive: Path, index_directory: Path, output: Path
) -> dict:
    """Adapt all needles for one pinned repository; do not sample based on retrieval scores."""
    recipe = _recipe(recipe_path, "source")
    source = _record(
        recipe["source"],
        {"url", "sha256", "release", "license", "language", "repository", "expected_needles"},
        "RepoQA source",
    )
    raw = archive.read_bytes()
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise ValueError("RepoQA archive checksum mismatch")
    if len(recipe["repositories"]) != 1 or source["language"] != "python":
        raise ValueError("This adapter requires one Python repository")
    data = json.loads(gzip.decompress(raw))
    matches = [repo for repo in data["python"] if repo["repo"] == source["repository"]]
    if len(matches) != 1:
        raise ValueError("RepoQA repository must occur exactly once")
    upstream = matches[0]
    repository = recipe["repositories"][0]
    if (
        upstream["commit_sha"] != repository["commit"]
        or repository["url"] != f"https://github.com/{upstream['repo']}.git"
    ):
        raise ValueError("RepoQA repository/commit mismatch")
    index = load_index(index_directory / f"{repository['id']}.sqlite")
    if (
        type(source["expected_needles"]) is not int
        or source["expected_needles"] < 1
        or len(upstream["needles"]) != source["expected_needles"]
    ):
        raise ValueError("Unexpected RepoQA needle count")
    queries, judgments, provenance = [], [], []
    for ordinal, needle in enumerate(upstream["needles"], 1):
        path = _relative(needle["path"], "RepoQA source path")
        content = upstream["content"][path]
        file_bytes = content.encode("utf-8")
        if hashlib.sha256(file_bytes).hexdigest() != dict(index.metadata["manifest"]).get(path):
            raise ValueError("RepoQA source file differs from indexed snapshot bytes")
        for key in ("start_line", "end_line", "start_byte", "end_byte"):
            if type(needle[key]) is not int:
                raise ValueError("RepoQA offsets must be integers")
        nodes = [
            node
            for node in ast.walk(ast.parse(content))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == needle["name"]
            and node.lineno == needle["start_line"] + 1
            and node.end_lineno == needle["end_line"]
        ]
        if len(nodes) != 1:
            raise ValueError("RepoQA function/line mapping is ambiguous or invalid")
        node = nodes[0]
        lines = io.BytesIO(file_bytes).readlines()
        start = sum(map(len, lines[: node.lineno - 1])) + node.col_offset
        end = sum(map(len, lines[: node.end_lineno - 1])) + node.end_col_offset
        if (start, end) != (needle["start_byte"], needle["end_byte"]):
            raise ValueError("RepoQA byte offsets do not match the AST function")
        start_line = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
        symbols = [
            s
            for s in index.symbols.values()
            if s.path == path
            and s.name == node.name
            and s.start_line == start_line
            and s.end_line == node.end_lineno
        ]
        if len(symbols) != 1:
            raise ValueError("RepoQA target must match exactly one indexed symbol")
        target = asdict(symbol_target(symbols[0]))
        query_id = f"repoqa-{repository['id']}-{ordinal:02}"
        queries.append(
            {
                "id": query_id,
                "repository": repository["id"],
                "category": "behavior",
                "text": _string(needle["description"], "RepoQA description"),
                "answerable": True,
            }
        )
        judgments.append(
            {
                "query_id": query_id,
                "target": target,
                "grade": 2,
                "rationale": "Designated RepoQA needle; source bytes and AST location verified. "
                "Other relevant symbols remain unjudged.",
            }
        )
        provenance.append(
            {
                "query_id": query_id,
                "origin": "repoqa_generated_description",
                "source": source,
                "upstream_ordinal": ordinal,
                "upstream_needle": {
                    k: needle[k]
                    for k in ("name", "path", "start_line", "end_line", "start_byte", "end_byte")
                },
                "target": target,
                "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
                "needle_sha256": hashlib.sha256(file_bytes[start:end]).hexdigest(),
                "description_sha256": hashlib.sha256(
                    needle["description"].encode("utf-8")
                ).hexdigest(),
                "independent_review": "pending",
            }
        )
    return _publish(output, recipe, {repository["id"]: index}, queries, judgments, provenance)
