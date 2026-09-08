"""Command-line entry point; retrieval commands arrive in later milestones."""

from importlib.metadata import version
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
    """Display CLI information until retrieval commands are implemented."""
    if show_version:
        typer.echo(f"sacr {version('structure-aware-code-retrieval')}")
    elif ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
