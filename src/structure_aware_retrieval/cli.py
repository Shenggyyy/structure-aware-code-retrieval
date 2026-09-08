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
    json_output: Annotated[
        bool, typer.Option("--json", help="Print full results as JSON.")
    ] = False,
) -> None:
    """Retrieve matching code chunks with BM25 and snapshot source locations."""
    from structure_aware_retrieval.retrieval import BM25Retriever

    try:
        retriever = BM25Retriever.from_path(index)
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
                    "strategy": retriever.index.metadata["config"]["bm25"],
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
