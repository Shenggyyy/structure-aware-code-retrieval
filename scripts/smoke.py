"""Exercise the installed CLI offline using a tiny, isolated Git source fixture."""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from structure_aware_retrieval.evaluation.dataset import corpus_hash, symbol_target
from structure_aware_retrieval.indexing import load_index

ROOT = Path(__file__).resolve().parents[1]
QUESTION = "calculate_checksum payload bytes"
UNKNOWN = "zzzzsacrsmokeunmatchedtoken"


def _write(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_smoke(output: Path) -> dict:
    """Leave inspectable outputs; never reuse a directory or modify the project Git repo."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Smoke output already exists; choose a new directory")
    output.mkdir(parents=True, exist_ok=False)
    # Isolate scratch Git from parent repo/config/hooks and credentials. No network
    # preparation, API execution, source importing, or model download is requested.
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and key != "OPENAI_API_KEY"
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "SACR smoke fixture",
            "GIT_AUTHOR_EMAIL": "smoke@example.invalid",
            "GIT_COMMITTER_NAME": "SACR smoke fixture",
            "GIT_COMMITTER_EMAIL": "smoke@example.invalid",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    commands = []

    def command(arguments: list[str], cwd: Path = output) -> str:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        commands.append(
            {
                "arguments": arguments,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        _write(output / "commands.json", commands)
        if result.returncode:
            raise ValueError(f"Smoke command failed ({arguments[0]}): {result.stderr}")
        return result.stdout

    def cli(*arguments: str) -> str:
        return command([sys.executable, "-I", "-m", "structure_aware_retrieval", *arguments])

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(f"Smoke check failed: {message}")

    try:
        repository = output / "repository"
        repository.mkdir()
        for relative in ("client.py", "errors.py", "tests/test_client.py"):
            source = ROOT / "tests/fixtures/sample_repo" / relative
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
            )
        git = [
            "git",
            "-c",
            "core.autocrlf=false",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=.git/no-hooks",
        ]
        command(
            [*git, "init", "--quiet", "--initial-branch=main", "--object-format=sha1"], repository
        )
        command([*git, "add", "client.py", "errors.py", "tests/test_client.py"], repository)
        command([*git, "commit", "--quiet", "-m", "Create isolated smoke fixture"], repository)
        commit = command([*git, "rev-parse", "HEAD"], repository).strip()
        require(not command([*git, "status", "--porcelain"], repository).strip(), "clean fixture")

        cli("index", str(repository), "--output", str(output / "index.sqlite"))
        index = load_index(output / "index.sqlite")
        require(index.metadata["files_indexed"] == 3, "three source files indexed")
        require(not index.metadata["diagnostics"], "all fixture source parsed")
        require(index.metadata["git"] == {"commit": commit, "dirty": False}, "real Git provenance")
        lexical = json.loads(cli("search", QUESTION, "--index", "index.sqlite", "--json"))
        require(
            lexical["results"][0]["qualified_name"] == "client.calculate_checksum", "BM25 checksum"
        )
        require(
            not json.loads(cli("search", UNKNOWN, "--index", "index.sqlite", "--json"))["results"],
            "unmatched search is empty",
        )
        _write(output / "search.json", lexical)

        cli("graph", "--index", "index.sqlite", "--output", "graph.json")
        graph = _read(output / "graph.json")
        require(
            {"containment", "import", "test"} <= {edge["kind"] for edge in graph["edges"]},
            "fixture containment, import and test relationships",
        )
        structural = json.loads(
            cli(
                "search",
                QUESTION,
                "--index",
                "index.sqlite",
                "--strategy",
                "structure",
                "--seed-strategy",
                "bm25",
                "--graph",
                "graph.json",
                "--json",
            )
        )
        require(
            any(
                hit["qualified_name"] == "client.calculate_checksum"
                for hit in structural["results"]
            ),
            "structure retrieval keeps checksum evidence",
        )
        _write(output / "structure-search.json", structural)
        cli("ask", QUESTION, "--index", "index.sqlite", "--output", "qa-preview")
        preview = _read(output / "qa-preview/qa.json")
        require(
            preview["status"] == "preview" and preview["model_called"] is False,
            "offline QA preview",
        )
        require(bool(preview["context"]["evidence"]), "QA has canonical source evidence")
        require(preview["evaluation"]["answer_correctness"] is None, "no invented QA quality")
        cli("ask", UNKNOWN, "--index", "index.sqlite", "--output", "qa-empty")
        empty = _read(output / "qa-empty/qa.json")
        require(
            empty["status"] == "insufficient_context" and empty["model_called"] is False,
            "empty evidence abstains without a model",
        )

        dataset = output / "benchmark"
        dataset.mkdir()
        _write(
            dataset / "benchmark.json",
            {
                "schema_version": 1,
                "id": "delivery-smoke",
                "version": "1",
                "split": "dev",
                "annotation_status": "provisional",
                "repositories": [
                    {
                        "id": "fixture",
                        "url": "https://example.invalid/smoke.git",
                        "ref": "local-smoke",
                        "commit": commit,
                        "license": "project-fixture",
                        "corpus_hash": corpus_hash(index),
                    }
                ],
                "queries_file": "queries.jsonl",
                "qrels_file": "qrels.jsonl",
            },
        )
        queries = [
            {
                "id": name,
                "repository": "fixture",
                "category": "symbol",
                "text": text,
                "answerable": answerable,
            }
            for name, text, answerable in (
                ("checksum", QUESTION, True),
                ("timeout", "configured deadline TimeoutError", True),
                ("unmatched", UNKNOWN, False),
            )
        ]
        symbols = {symbol.qualified_name: symbol for symbol in index.symbols.values()}
        judgments = [
            {
                "query_id": query,
                "target": asdict(symbol_target(symbols[name])),
                "grade": 2,
                "rationale": "Synthetic smoke check, not a research relevance judgment.",
            }
            for query, name in (
                ("checksum", "client.calculate_checksum"),
                ("timeout", "errors.TimeoutError"),
            )
        ]
        for filename, values in (("queries.jsonl", queries), ("qrels.jsonl", judgments)):
            (dataset / filename).write_text(
                "".join(json.dumps(value) + "\n" for value in values),
                encoding="utf-8",
                newline="\n",
            )
        for strategy in ("bm25", "structure"):
            config = (
                'schema_version = 1\nbenchmark = "benchmark/benchmark.json"\n'
                f'strategy = "{strategy}"\nunit = "symbol"\nks = [1, 5]\n'
                'warmup_queries = 1\nrepeats = 2\nseed = 0\n[indexes]\nfixture = "index.sqlite"\n'
            )
            if strategy == "structure":
                config += '[graphs]\nfixture = "graph.json"\n[structure]\nseed_strategy = "bm25"\n'
            (output / f"{strategy}.toml").write_text(config, encoding="utf-8", newline="\n")
        for name, config in (
            ("bm25-first", "bm25.toml"),
            ("bm25-repeat", "bm25.toml"),
            ("structure-run", "structure.toml"),
        ):
            cli("evaluate", "--config", config, "--output", name)
        first = _read(output / "bm25-first/summary.json")
        second = _read(output / "bm25-repeat/summary.json")
        require(
            first["quality_fingerprint"] == second["quality_fingerprint"],
            "repeated retrieval quality",
        )
        require(
            first["overall"]["answerable_count"] == 2 and first["overall"]["no_answer_count"] == 1,
            "evaluation separates unanswerable queries",
        )
        cli("compare", "--run", "bm25-first", "--run", "structure-run", "--output", "comparison")
        cli(
            "pool",
            "--config",
            "bm25.toml",
            "--run",
            "bm25-first",
            "--run",
            "structure-run",
            "--output",
            "review",
            "--depth",
            "5",
        )
        review = _read(output / "review/manifest.json")
        require(review["review_status"] == "pending", "source pool remains unreviewed")
        summary = {
            "schema_version": 1,
            "status": "passed",
            "synthetic_fixture_only": True,
            "fixture_commit": commit,
            "snapshot_id": index.metadata["snapshot_id"],
            "source_files": index.metadata["files_indexed"],
            "quality_fingerprint": first["quality_fingerprint"],
            "repeat_quality_matches": True,
            "qa_status": preview["status"],
            "empty_context_status": empty["status"],
            "api_calls": 0,
            "model_downloads": 0,
            "review_status": "pending",
            "command_count": len(commands),
        }
        _write(output / "summary.json", summary)
        return summary
    except Exception as error:
        _write(
            output / "summary.json", {"schema_version": 1, "status": "failed", "error": str(error)}
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="New directory for smoke artifacts"
    )
    arguments = parser.parse_args()
    try:
        result = run_smoke(arguments.output)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Smoke failed: {error}\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
