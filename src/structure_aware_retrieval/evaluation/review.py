"""Frozen, source-bound relevance pools and auditable manual review templates."""

import io
import json
import os
import re
import tempfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

from structure_aware_retrieval.evaluation.config import load_config
from structure_aware_retrieval.evaluation.dataset import (
    load_benchmark,
    symbol_target,
    validate_index,
)
from structure_aware_retrieval.evaluation.recorded import keyed, load_runs, read_jsonl
from structure_aware_retrieval.evaluation.reporting import _dump
from structure_aware_retrieval.indexing import load_index
from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.relations import snapshot_sources


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _new_output(output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output already exists: {output}")


def create_pool(config_path: Path, runs: list[Path], output: Path, *, depth: int = 10) -> dict:
    """Union top-depth unique symbols and every existing qrel, with no automatic labels."""
    _new_output(output)
    if type(depth) is not int or depth < 1:
        raise ValueError("Pool depth must be a positive integer")
    config = load_config(config_path)
    benchmark = load_benchmark(config.benchmark)
    recorded = load_runs(runs)
    if any(run.summary["config"]["unit"] != "symbol" for run in recorded):
        raise ValueError("Review pools require symbol-level runs")
    if any(depth > max(run.summary["config"]["ks"]) for run in recorded):
        raise ValueError("Pool depth exceeds stored ranking depth")
    if any(run.summary["benchmark"]["digest"] != benchmark.digest for run in recorded):
        raise ValueError("Run benchmark digest does not match the pool benchmark")
    queries = {query.id: query for query in benchmark.queries}
    if set(recorded[0].queries) != set(queries):
        raise ValueError("Pool benchmark and recorded query IDs differ")
    repo_ids = {repo.id for repo in benchmark.repositories}
    if set(config.indexes) != repo_ids:
        raise ValueError("Pool indexes must exactly match benchmark repositories")
    indexes = {repo: load_index(path) for repo, path in config.indexes.items()}
    targets = {}
    source_lines = {}
    for repository in benchmark.repositories:
        index = indexes[repository.id]
        validate_index(benchmark, repository, index)
        if any(
            run.summary["indexes"][repository.id]["snapshot_id"] != index.metadata["snapshot_id"]
            for run in recorded
        ):
            raise ValueError("Run snapshot does not match the pool index")
        targets[repository.id] = {
            symbol_target(symbol).key: symbol for symbol in index.symbols.values()
        }
        source_lines[repository.id] = {
            path: io.StringIO(text).readlines() for path, text in snapshot_sources(index).items()
        }
    candidates = {}

    def candidate(query_id: str, target: dict) -> dict:
        from structure_aware_retrieval.evaluation.dataset import Target

        locator = Target(**target)
        repo = queries[query_id].repository
        symbol = targets[repo].get(locator.key)
        if symbol is None or asdict(symbol_target(symbol)) != target:
            raise ValueError("Pooled target does not match a snapshot symbol")
        item_id = stable_id(benchmark.digest, query_id, locator.key)
        return candidates.setdefault(
            item_id,
            {
                "item_id": item_id,
                "query_id": query_id,
                "repository": repo,
                "target": target,
                "original_judgment": None,
                "origins": [],
            },
        )

    for judgment in benchmark.judgments:
        row = candidate(judgment.query_id, asdict(judgment.target))
        row["original_judgment"] = {"grade": judgment.grade, "rationale": judgment.rationale}
    for run in recorded:
        for query_id, record in run.rankings.items():
            query = queries[query_id]
            row = run.queries[query_id]
            if (
                record["query"] != query.text
                or row["repository"] != query.repository
                or row["category"] != query.category
                or row["answerable"] != query.answerable
            ):
                raise ValueError("Recorded query does not match the benchmark")
            seen = set()
            for rank, hit in enumerate(record["ranking"][:depth], 1):
                pooled = candidate(query_id, hit["target"])
                if hit["rank"] != rank or hit["key"] in seen:
                    raise ValueError("Pool rankings must have consecutive ranks and unique symbols")
                symbol = targets[query.repository].get(hit["key"])
                if symbol is None or asdict(symbol_target(symbol)) != hit["target"]:
                    raise ValueError("Ranking key and target disagree")
                seen.add(hit["key"])
                pooled["origins"].append({"run": run.name, "rank": rank})
    pool = sorted(candidates.values(), key=lambda row: (row["query_id"], row["item_id"]))
    evidence = []
    repositories = {repo.id: repo for repo in benchmark.repositories}
    for row in pool:
        row["origins"].sort(key=lambda origin: (origin["run"], origin["rank"]))
        target = row["target"]
        repository = repositories[row["repository"]]
        url = repository.url.removesuffix(".git").rstrip("/")
        source_url = (
            f"{url}/blob/{repository.commit}/{quote(target['path'], safe='/')}"
            f"#L{target['start_line']}-L{target['end_line']}"
            if url.startswith("https://github.com/")
            else None
        )
        lines = source_lines[row["repository"]][target["path"]]
        text = "".join(lines[target["start_line"] - 1 : target["end_line"]])
        evidence.append({"item_id": row["item_id"], "source_url": source_url, "text": text})
    manifest = {
        "schema_version": 1,
        "benchmark": recorded[0].summary["benchmark"],
        "repositories": [asdict(repo) for repo in benchmark.repositories],
        "queries": [asdict(query) for query in sorted(queries.values(), key=lambda q: q.id)],
        "snapshots": {
            repo: index.metadata["snapshot_id"] for repo, index in sorted(indexes.items())
        },
        "runs": sorted(
            [
                {"name": run.name, "quality_fingerprint": run.summary["quality_fingerprint"]}
                for run in recorded
            ],
            key=lambda run: run["name"],
        ),
        "depth": depth,
        "policy": "union_top_depth_symbols_plus_all_existing_judgments",
        "item_count": len(pool),
        "unjudged_count": sum(row["original_judgment"] is None for row in pool),
        "by_repository": dict(sorted(Counter(row["repository"] for row in pool).items())),
        "review_status": "pending",
    }
    manifest["pool_digest"] = stable_id(manifest, pool, evidence)
    judgments = [
        {"item_id": row["item_id"], "grade": None, "rationale": "", "reviewer": ""} for row in pool
    ]
    query_reviews = [
        {"query_id": query.id, "answerable": None, "clear": None, "rationale": "", "reviewer": ""}
        for query in sorted(queries.values(), key=lambda q: q.id)
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-review-", dir=output.parent) as temporary:
        folder = Path(temporary)
        _dump(folder / "manifest.json", manifest)
        for name, rows in (
            ("pool", pool),
            ("evidence", evidence),
            ("judgments", judgments),
            ("queries", query_reviews),
        ):
            _jsonl(folder / f"{name}.jsonl", rows)
        _review_pages(folder, manifest, pool, evidence)
        _new_output(output)
        os.rename(temporary, output)
    return manifest


def _review_pages(folder: Path, manifest: dict, pool: list[dict], evidence: list[dict]) -> None:
    snippets = keyed(evidence, "item_id")
    pages = folder / "questions"
    pages.mkdir()
    intro = [
        "# Relevance Review",
        "",
        "Read the question and source evidence; edit `judgments.jsonl` and `queries.jsonl`. "
        "Grade 2: directly answers the question; 1: useful supporting evidence; "
        '0: irrelevant; `"unsure"`: needs adjudication; null: pending. '
        "Every submitted decision needs a reviewer identifier and a source-based rationale.",
        "",
        "For every query, review clarity and repository-level answerability, including queries "
        "without candidates. A pool is not exhaustive: search outside it before declaring "
        "no answer. Record missing targets for a new pool version.",
        "",
        "Strategy names, ranks and previous labels are withheld from these pages and the "
        "decision templates; `pool.jsonl` is an administrative audit file. Candidate order "
        "uses hashed IDs, not retrieval rank. Do not inspect that audit file while grading.",
        "",
        "Source is reconstructed from the frozen index, including nested definitions; "
        "omitted whitespace-only spans become blank lines. Follow pinned links for the "
        "original formatting and wider context. Code is displayed as text, never executed. "
        "Repository license identifiers and revisions are in `manifest.json`.",
        "",
    ]
    for query in manifest["queries"]:
        rows = [row for row in pool if row["query_id"] == query["id"]]
        intro.append(f"- [{query['id']}](questions/{query['id']}.md): {len(rows)} candidates")
        lines = [
            f"# {query['id']}",
            "",
            query["text"],
            "",
            f"Repository: `{query['repository']}`.",
            "",
        ]
        for row in rows:
            target = row["target"]
            snippet = snippets[row["item_id"]]
            # A source string containing Markdown fences must remain in the code block.
            fence = "`" * max(
                3, max((len(s) for s in re.findall(r"`+", snippet["text"])), default=0) + 1
            )
            lines.extend(
                [
                    f"## {row['item_id']}",
                    "",
                    f"`{target['path']}:{target['start_line']}-{target['end_line']}` — "
                    f"`{target['qualified_name']}`",
                    "",
                    f"[Pinned source]({snippet['source_url']})"
                    if snippet["source_url"]
                    else "Local snapshot evidence:",
                    "",
                    f"{fence}python",
                    snippet["text"].rstrip("\n"),
                    fence,
                    "",
                ]
            )
        (pages / f"{query['id']}.md").write_text("\n".join(lines), encoding="utf-8")
    (folder / "review.md").write_text("\n".join(intro) + "\n", encoding="utf-8")


def check_review(bundle: Path, judgments_path: Path, queries_path: Path, output: Path) -> dict:
    """Validate a submitted review and record changes, without altering benchmark labels."""
    _new_output(output)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    pool = read_jsonl(bundle / "pool.jsonl")
    evidence = read_jsonl(bundle / "evidence.jsonl")
    original_digest = manifest.pop("pool_digest")
    if stable_id(manifest, pool, evidence) != original_digest:
        raise ValueError("Review pool digest mismatch")
    candidates = keyed(pool, "item_id")
    judgments = keyed(read_jsonl(judgments_path), "item_id")
    queries = keyed(read_jsonl(queries_path), "query_id")
    expected_queries = {query["id"] for query in manifest["queries"]}
    if set(judgments) != set(candidates) or set(queries) != expected_queries:
        raise ValueError("Review must include exactly the pool item IDs and query IDs")

    def validate(row: dict, fields: dict[str, tuple], id_key: str) -> str:
        if set(row) != {id_key, "rationale", "reviewer", *fields}:
            raise ValueError("Unexpected review fields")
        for key in ("rationale", "reviewer"):
            if not isinstance(row[key], str):
                raise ValueError("Review rationale and reviewer must be strings")
        for key, options in fields.items():
            if not any(type(row[key]) is type(v) and row[key] == v for v in options):
                raise ValueError(f"Invalid review {key}")
        submitted = any(row[key] is not None for key in fields)
        if submitted and any(not row[key].strip() for key in ("rationale", "reviewer")):
            raise ValueError("Submitted decisions require a reviewer and rationale")
        if any(row[key] is None for key in fields):
            return "pending"
        if any(row[key] == "unsure" for key in fields):
            return "unsure"
        return "complete"

    item_states = {
        key: validate(row, {"grade": (None, 0, 1, 2, "unsure")}, "item_id")
        for key, row in judgments.items()
    }
    query_states = {
        key: validate(
            row,
            {"answerable": (None, False, True, "unsure"), "clear": (None, False, True)},
            "query_id",
        )
        for key, row in queries.items()
    }
    conflicts = []
    changes = []
    for query_id, query in queries.items():
        related = [key for key, row in candidates.items() if row["query_id"] == query_id]
        if query_states[query_id] == "complete":
            if not query["clear"]:
                conflicts.append({"query_id": query_id, "reason": "query_needs_rewriting"})
            if all(item_states[key] == "complete" for key in related):
                positive = any(judgments[key]["grade"] > 0 for key in related)
                if positive != query["answerable"]:
                    conflicts.append(
                        {"query_id": query_id, "reason": "answerability_qrels_disagree"}
                    )
    for key, row in judgments.items():
        if item_states[key] != "complete":
            continue
        old = candidates[key]["original_judgment"]
        previous = old["grade"] if old is not None else None
        if previous != row["grade"]:
            changes.append(
                {
                    "item_id": key,
                    "query_id": candidates[key]["query_id"],
                    "before": previous,
                    "after": row["grade"],
                }
            )
    ready = (
        all(state == "complete" for state in (*item_states.values(), *query_states.values()))
        and not conflicts
    )
    result = {
        "pool_digest": original_digest,
        "benchmark": manifest["benchmark"],
        "decision_digest": stable_id(
            sorted(judgments.values(), key=lambda r: r["item_id"]),
            sorted(queries.values(), key=lambda r: r["query_id"]),
        ),
        "judgments": dict(sorted(Counter(item_states.values()).items())),
        "queries": dict(sorted(Counter(query_states.values()).items())),
        "conflicts": sorted(conflicts, key=lambda r: (r["query_id"], r["reason"])),
        "changes": sorted(changes, key=lambda r: r["item_id"]),
        "ready_for_versioning": ready,
        "reviewer_identity_verified": False,
        "note": "Structural validation only. Reviewer identity and independence are self-declared. "
        "Publish an explicitly versioned benchmark after adjudication; "
        "no labels or human-review status were changed.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sacr-review-check-", dir=output.parent) as temporary:
        _dump(Path(temporary) / "review-status.json", result)
        _jsonl(
            Path(temporary) / "judgments.jsonl",
            sorted(judgments.values(), key=lambda r: r["item_id"]),
        )
        _jsonl(
            Path(temporary) / "queries.jsonl", sorted(queries.values(), key=lambda r: r["query_id"])
        )
        _new_output(output)
        os.rename(temporary, output)
    return result
