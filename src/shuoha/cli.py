from pathlib import Path

import typer
from rich import print

from shuoha.config import default_output_dir
from shuoha.engine import run_analysis
from shuoha.reporting.output import write_outputs

app = typer.Typer(help="Analyze one A-share stock code and produce beginner-friendly output.")


@app.callback()
def main() -> None:
    """Shuoha CLI."""


@app.command()
def analyze(stock_code: str, output_dir: Path | None = None) -> None:
    if not (stock_code.isdigit() and len(stock_code) == 6):
        typer.echo("Stock code must be 6 digits")
        raise typer.Exit(2)
    result, markdown = run_analysis(stock_code)
    evidence_path, report_path = write_outputs(result, markdown, output_dir or default_output_dir(stock_code))
    print(f"[green]Saved[/green] {report_path}")
    print(f"[green]Saved[/green] {evidence_path}")
