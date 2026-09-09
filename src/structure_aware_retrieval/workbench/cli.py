"""Local workbench commands over the existing import and retrieval services."""

import json
import sqlite3
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    help="Import repositories and compare five contexts in the CLI or browser; no model API calls.",
    add_completion=False,
    rich_markup_mode=None,
    no_args_is_help=True,
)


def _failure(error: Exception) -> None:
    typer.echo(f"Error: {error}", err=True)
    raise typer.Exit(1) from error


def _json(value: object) -> None:
    typer.echo(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False))


def _error_message(error: str | dict | None) -> str:
    if isinstance(error, dict):
        return f"{error.get('type', 'Error')}: {error.get('message', '')}"
    return error or ""


def _comparison(record: dict, workspace: Path) -> None:
    typer.echo(f"Run: {record['run_id']}; repository: {record['repository_id']}")
    typer.echo(
        f"Status: {record['status']}; mode: {record['mode']}; API calls: {record['api_calls']}"
    )
    typer.echo(f"Question: {record['question']}")
    for row in record["results"]:
        message = _error_message(row.get("error"))
        suffix = f"; {message}" if message else ""
        typer.echo(f"{row['strategy']}: {row['status']}; {len(row['hits'])} saved hits{suffix}")
    typer.echo(f"Saved comparison: {workspace.resolve() / 'runs' / record['run_id'] / 'run.json'}")


@app.command("serve")
def serve_browser(
    workspace: Annotated[Path, typer.Option(help="Local workbench directory")] = Path(
        "artifacts/workbench"
    ),
    model_cache: Annotated[
        Path, typer.Option(help="Already prepared local embedding model")
    ] = Path("artifacts/models"),
    port: Annotated[int, typer.Option(min=1, max=65535, help="Local HTTP port")] = 8765,
) -> None:
    """Open a local-only browser workflow for import, context comparison and history."""
    from structure_aware_retrieval.workbench.server import serve

    try:
        serve(workspace, model_cache=model_cache, port=port)
    except (OSError, ValueError, sqlite3.Error) as error:
        _failure(error)


@app.command("import")
def import_source(
    source: Annotated[str, typer.Argument(help="Local directory or public HTTPS Git URL")],
    ref: Annotated[
        str, typer.Option(help="Remote Git ref; local imports copy current files")
    ] = "HEAD",
    workspace: Annotated[Path, typer.Option(help="Local workbench directory")] = Path(
        "artifacts/workbench"
    ),
    as_json: Annotated[
        bool, typer.Option("--json", help="Print the complete saved manifest")
    ] = False,
) -> None:
    """Save a bounded Python source snapshot without running repository code."""
    from structure_aware_retrieval.workbench.importing import import_repository

    try:
        record = import_repository(source, workspace, ref=ref)
    except (OSError, ValueError, sqlite3.Error) as error:
        _failure(error)
    if as_json:
        _json(record)
        return
    provenance = record["source"]
    typer.echo(f"Repository: {record['repository_id']}; status: imported")
    typer.echo(f"Source: {provenance['location']}")
    typer.echo(f"Commit: {provenance['commit'] or 'unavailable'}")
    if provenance["working_tree"]:
        typer.echo(
            "Snapshot contains current local files; commit is an optional provenance anchor."
        )
    typer.echo(f"Saved files: {len(record['files'])}; API calls: 0")
    manifest = workspace.resolve() / "repositories" / record["repository_id"] / "manifest.json"
    typer.echo(f"Manifest: {manifest}")


@app.command("prepare")
def prepare(
    repository_id: Annotated[str, typer.Argument(help="Imported repository ID")],
    workspace: Annotated[Path, typer.Option()] = Path("artifacts/workbench"),
    model_cache: Annotated[
        Path, typer.Option(help="Already prepared local embedding model")
    ] = Path("artifacts/models"),
    as_json: Annotated[
        bool, typer.Option("--json", help="Print all resource and stage records")
    ] = False,
) -> None:
    """Prepare indexes, vectors and relations; retain independent stage failures."""
    from structure_aware_retrieval.workbench.preparation import prepare_repository

    try:
        record = prepare_repository(workspace, repository_id, model_cache=model_cache)
    except (OSError, ValueError, sqlite3.Error) as error:
        _failure(error)
    if as_json:
        _json(record)
    else:
        typer.echo(f"Repository: {record['repository_id']}; status: {record['status']}")
        for stage, result in record["stages"].items():
            message = _error_message(result.get("error"))
            typer.echo(f"{stage}: {result['status']}" + (f"; {message}" if message else ""))
        typer.echo("API calls: 0; embedding model is loaded from the local cache.")
        manifest = workspace.resolve() / "resources" / record["repository_id"] / "manifest.json"
        typer.echo(f"Resources: {manifest}")
    if record["status"] != "ready":
        raise typer.Exit(1)


@app.command("preview")
def preview(
    repository_id: Annotated[str, typer.Argument(help="Imported and prepared repository ID")],
    question: Annotated[str, typer.Argument(help="Question compared across all five strategies")],
    workspace: Annotated[Path, typer.Option()] = Path("artifacts/workbench"),
    model_cache: Annotated[
        Path, typer.Option(help="Already prepared local embedding model")
    ] = Path("artifacts/models"),
    top_k: Annotated[int, typer.Option(min=1, max=100)] = 10,
    max_context_bytes: Annotated[int, typer.Option(min=2, max=1_000_000)] = 16000,
    as_json: Annotated[
        bool, typer.Option("--json", help="Print all saved retrieval contexts")
    ] = False,
) -> None:
    """Save five context previews with no answer generation or model API calls."""
    from structure_aware_retrieval.workbench.comparison import preview_question

    try:
        record = preview_question(
            workspace,
            repository_id,
            question,
            model_cache=model_cache,
            top_k=top_k,
            max_context_bytes=max_context_bytes,
        )
    except (OSError, ValueError, sqlite3.Error) as error:
        _failure(error)
    if as_json:
        _json(record)
    else:
        _comparison(record, workspace)
    if record["status"] != "preview_complete":
        raise typer.Exit(1)


@app.command("history")
def history(
    workspace: Annotated[Path, typer.Option()] = Path("artifacts/workbench"),
    as_json: Annotated[bool, typer.Option("--json", help="Print saved run summaries")] = False,
) -> None:
    """List saved comparisons, including partial and unreadable records."""
    from structure_aware_retrieval.workbench.comparison import list_comparisons

    try:
        records = list_comparisons(workspace)
    except (OSError, ValueError, sqlite3.Error) as error:
        _failure(error)
    if as_json:
        _json(records)
        return
    if not records:
        typer.echo("No saved comparisons.")
    for record in records:
        if record.get("error"):
            detail = _error_message(record["error"])
        else:
            detail = f"repository: {record['repository_id']}; {record['question']}"
        typer.echo(f"{record['run_id']} | {record['status']} | {detail}")


@app.command("show")
def show(
    run_id: Annotated[str, typer.Argument(help="Saved comparison ID")],
    workspace: Annotated[Path, typer.Option()] = Path("artifacts/workbench"),
    as_json: Annotated[
        bool, typer.Option("--json", help="Print the complete stored comparison")
    ] = False,
) -> None:
    """Reopen a saved comparison without preparing resources or repeating retrieval."""
    from structure_aware_retrieval.workbench.comparison import load_comparison

    try:
        record = load_comparison(workspace, run_id)
    except (OSError, ValueError, sqlite3.Error) as error:
        _failure(error)
    if as_json:
        _json(record)
    else:
        _comparison(record, workspace)
