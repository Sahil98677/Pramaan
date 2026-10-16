"""Command-line interface."""

from pathlib import Path

import typer

from . import __version__
from .engine import analyze_json, analyze_source
from .models import RunStatus
from .reporting import report_json, write_report

app = typer.Typer(
    name="pramaan",
    help="Evidence-first, deterministic local security analysis.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Pramaan CLI."""


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(f"Pramaan {__version__}")


@app.command()
def analyze(
    input_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write the JSON report to this path."
    ),
    kind: str = typer.Option(
        "auto", "--kind", help="Input kind: auto, json, or source."
    ),
) -> None:
    """Analyze a local JSON or source file without executing it."""
    selected = kind
    if selected == "auto":
        selected = "json" if input_path.suffix.lower() == ".json" else "source"
    if selected == "json":
        report = analyze_json(input_path)
    elif selected == "source":
        report = analyze_source(input_path)
    else:
        raise typer.BadParameter("kind must be auto, json, or source")

    if output is None:
        typer.echo(report_json(report), nl=False)
    else:
        write_report(report, output)
        typer.echo(f"Report written to {output}")

    if report.status is not RunStatus.COMPLETED:
        raise typer.Exit(code=2)
