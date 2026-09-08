"""Command-line entry points for indexing and searching repository snapshots."""

import json
import sqlite3
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    help="Code retrieval and evaluation for repository-level LLM applications.",
    add_completion=False,
    rich_markup_mode=None,
    invoke_without_command=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    show_version: Annotated[
        bool, typer.Option("--version", help="Show the installed package version and exit.")
    ] = False,
) -> None:
    """Display top-level CLI information."""
    if show_version:
        typer.echo(f"sacr {version('structure-aware-code-retrieval')}")
        raise typer.Exit()
    elif ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("index")
def index_repository(
    repository: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
    output: Annotated[Path, typer.Option("--output", help="SQLite snapshot to create.")] = Path(
        "artifacts/index.sqlite"
    ),
    max_chunk_lines: Annotated[int, typer.Option(min=1)] = 80,
    max_file_bytes: Annotated[int, typer.Option(min=1)] = 1_048_576,
    exclude: Annotated[
        list[str] | None,
        typer.Option(help="Additional root-relative gitignore pattern; repeatable."),
    ] = None,
    overwrite: Annotated[
        bool, typer.Option(help="Atomically replace an existing SACR index.")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Print metadata and diagnostics as JSON.")
    ] = False,
) -> None:
    """Parse Python source and save code, symbols, imports, and lexical tokens."""
    from structure_aware_retrieval.indexing import build_index

    try:
        metadata = build_index(
            repository,
            output,
            max_chunk_lines=max_chunk_lines,
            max_file_bytes=max_file_bytes,
            exclude=tuple(exclude or ()),
            overwrite=overwrite,
        )
    except (OSError, ValueError, sqlite3.Error) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    if json_output:
        typer.echo(json.dumps(metadata, ensure_ascii=True, indent=2))
    else:
        typer.echo(
            f"Indexed {metadata['files_indexed']} files, {metadata['symbol_count']} symbols, "
            f"{metadata['chunk_count']} chunks, {metadata['import_count']} imports."
        )
        typer.echo(f"Index: {output.resolve()}\nSnapshot: {metadata['snapshot_id']}")
        for item in metadata["diagnostics"]:
            typer.echo(f"Skipped {item['path']} [{item['reason']}]: {item['message']}", err=True)


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Keyword or natural-language code question.")],
    index: Annotated[
        Path, typer.Option("--index", help="Previously created SQLite snapshot.")
    ] = Path("artifacts/index.sqlite"),
    top_k: Annotated[int, typer.Option("--top-k", "-k", min=1)] = 5,
    strategy: Annotated[
        str, typer.Option(help="bm25, dense, hybrid, symbol, or structure")
    ] = "bm25",
    graph: Annotated[Path | None, typer.Option(help="Snapshot-bound relation graph")] = None,
    seed_strategy: Annotated[
        str, typer.Option(help="Seed method for structure retrieval")
    ] = "hybrid",
    vectors: Annotated[Path | None, typer.Option(help="Snapshot-bound vector archive")] = None,
    model_cache: Annotated[Path, typer.Option(help="Local pinned model cache")] = Path(
        "artifacts/models"
    ),
    json_output: Annotated[
        bool, typer.Option("--json", help="Print full results as JSON.")
    ] = False,
) -> None:
    """Retrieve code chunks using a selected strategy and stored source locations."""
    from structure_aware_retrieval.embeddings import SentenceEncoder
    from structure_aware_retrieval.indexing import load_index
    from structure_aware_retrieval.strategies import STRATEGIES, create_retriever

    try:
        if strategy not in STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}")
        if strategy == "structure" and graph is None:
            raise ValueError("--graph is required for structure search")
        if strategy != "structure" and graph is not None:
            raise ValueError("Only structure search uses --graph")
        base_strategy = seed_strategy if strategy == "structure" else strategy
        if base_strategy != "bm25" and vectors is None:
            raise ValueError("--vectors is required for dense, hybrid and symbol search")
        if base_strategy == "bm25" and vectors is not None:
            raise ValueError("BM25 does not use --vectors")
        snapshot = load_index(index)
        encoder = SentenceEncoder(model_cache) if base_strategy != "bm25" else None
        retriever = create_retriever(
            strategy,
            snapshot,
            encoder=encoder,
            vectors=vectors,
            graph=graph,
            structure={"seed_strategy": seed_strategy},
        )
        results = retriever.search(query, top_k=top_k)
    except (OSError, ValueError, sqlite3.Error) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "query": query,
                    "snapshot_id": retriever.index.metadata["snapshot_id"],
                    "strategy": retriever.index.metadata["config"]["bm25"]
                    if strategy == "bm25"
                    else strategy,
                    "results": [asdict(result) for result in results],
                },
                ensure_ascii=True,
                indent=2,
            )
        )
    elif not results:
        typer.echo("No matching code found.")
    else:
        for result in results:
            typer.echo(
                f"{result.rank}. {result.path}:{result.start_line}-{result.end_line} "
                f"[{result.kind}] {result.qualified_name} (score={result.score:.4f})"
            )
            preview = result.text.splitlines()
            typer.echo("\n".join(preview[:12]))
            if len(preview) > 12:
                typer.echo("... (use --json for the full chunk)")
            typer.echo()


@app.command("evaluate")
def evaluate(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    output: Annotated[
        Path, typer.Option("--output", help="New directory for experiment artifacts.")
    ],
) -> None:
    """Validate a benchmark and run reproducible retrieval evaluation."""
    from structure_aware_retrieval.evaluation.runner import run_experiment

    try:
        summary = run_experiment(config, output)
    except (OSError, ValueError, sqlite3.Error) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(
        f"Evaluated {summary['overall']['query_count']} queries "
        f"({summary['config']['unit']} level)."
    )
    typer.echo(f"Annotation status: {summary['benchmark']['annotation_status']}")
    typer.echo(f"Quality fingerprint: {summary['quality_fingerprint']}")
    typer.echo(f"Report: {output.resolve() / 'report.md'}")


@app.command("prepare-benchmark")
def prepare(
    benchmark: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    destination: Annotated[Path, typer.Option("--destination")] = Path("artifacts/benchmark"),
    rebuild: Annotated[
        bool, typer.Option(help="Rebuild existing indexes after source checks.")
    ] = False,
) -> None:
    """Download pinned source checkouts and build benchmark indexes (requires Git/network)."""
    from structure_aware_retrieval.evaluation.preparation import prepare_benchmark

    try:
        records = prepare_benchmark(benchmark, destination, rebuild=rebuild)
    except (OSError, ValueError, sqlite3.Error) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    for record in records:
        typer.echo(f"Ready: {record['repository']} -> {record['index']}")


@app.command("prepare-model")
def prepare_model(
    cache: Annotated[Path, typer.Option(help="Model cache destination")] = Path("artifacts/models"),
) -> None:
    """Download and validate the pinned CPU embedding model (network required)."""
    from structure_aware_retrieval.embeddings import SentenceEncoder

    try:
        encoder = SentenceEncoder(cache, download=True)
        typer.echo(json.dumps(encoder.spec, indent=2))
    except (OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error


@app.command("embed")
def embed(
    index: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option(help="New .npz vector archive")],
    model_cache: Annotated[Path, typer.Option()] = Path("artifacts/models"),
) -> None:
    """Encode stored chunks offline; refuse existing outputs or stale model caches."""
    from structure_aware_retrieval.embeddings import SentenceEncoder, build_vectors
    from structure_aware_retrieval.indexing import load_index

    try:
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Vector output already exists: {output}; choose a new file")
        metadata = build_vectors(load_index(index), SentenceEncoder(model_cache), output)
    except (OSError, ValueError, sqlite3.Error) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(json.dumps(metadata, indent=2))


@app.command("compare")
def compare(
    runs: Annotated[list[Path], typer.Option("--run", exists=True, file_okay=False)],
    output: Annotated[Path, typer.Option(help="New comparison directory")],
    bootstrap_samples: Annotated[int, typer.Option(min=100, max=20_000)] = 2000,
    bootstrap_seed: Annotated[int, typer.Option(min=0, max=2**32 - 1)] = 0,
) -> None:
    """Compare compatible evaluation runs; the first --run is the baseline."""
    from structure_aware_retrieval.evaluation.comparison import compare_runs

    try:
        compare_runs(
            runs, output, bootstrap_samples=bootstrap_samples, bootstrap_seed=bootstrap_seed
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Comparison: {output.resolve() / 'report.md'}")


@app.command("graph")
def graph_index(
    index: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option(help="New relation graph JSON file")],
) -> None:
    """Extract typed relations and unresolved references from saved source chunks."""
    from structure_aware_retrieval.indexing import load_index
    from structure_aware_retrieval.relations import build_graph

    try:
        metadata = build_graph(load_index(index), output)
    except (OSError, ValueError, SyntaxError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(json.dumps(metadata, indent=2))


@app.command("pool")
def pool_review(
    config: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    runs: Annotated[list[Path], typer.Option("--run", exists=True, file_okay=False)],
    output: Annotated[Path, typer.Option(help="New review bundle directory")],
    depth: Annotated[int, typer.Option(min=1)] = 10,
) -> None:
    """Pool recorded symbols and existing labels into source-bound review templates."""
    from structure_aware_retrieval.evaluation.review import create_pool

    try:
        manifest = create_pool(config, runs, output, depth=depth)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Pooled {manifest['item_count']} candidates; all reviews pending.")
    typer.echo(f"Review: {output.resolve() / 'review.md'}")


@app.command("check-review")
def check_manual_review(
    bundle: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    judgments: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    queries: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option(help="New directory for the validated submission")],
) -> None:
    """Check review completeness and conflicts; preserve submitted decisions without relabeling."""
    from structure_aware_retrieval.evaluation.review import check_review

    try:
        result = check_review(bundle, judgments, queries, output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Ready for versioning: {result['ready_for_versioning']}")
    typer.echo(f"Review status: {output.resolve() / 'review-status.json'}")


@app.command("pool-labels")
def pool_labels(
    config: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option(help="New source review directory")],
) -> None:
    """Review existing labels before any test-set retrieval is executed."""
    from structure_aware_retrieval.evaluation.review import create_pool

    try:
        manifest = create_pool(config, [], output, depth=0)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Prepared {manifest['item_count']} labeled targets; all reviews pending.")
    typer.echo(f"Review: {output.resolve() / 'review.md'}")


@app.command("audit-suite")
def audit_benchmarks(
    suite: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option(help="New benchmark audit directory")],
) -> None:
    """Check frozen benchmark digests, source snapshots and repository-disjoint splits."""
    from structure_aware_retrieval.evaluation.suite import audit_suite

    try:
        result = audit_suite(suite, output)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(
        f"Audited {result['query_count']} queries in {result['repository_count']} repositories."
    )
    typer.echo(f"Report: {output.resolve() / 'report.md'}")
