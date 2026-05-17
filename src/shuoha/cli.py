from pathlib import Path
from typing import Annotated

import typer
from rich import print

from shuoha.codex_analysis import run_codex_analysis
from shuoha.config import default_codex_output_dir, default_output_dir
from shuoha.engine import run_analysis
from shuoha.external_cli import ExternalCliError
from shuoha.reporting.output import write_markdown_report, write_outputs
from shuoha.reporting.terminal_renderer import render_terminal_report, render_terminal_summary

app = typer.Typer(help="分析一只 A 股股票，并输出适合投资小白阅读的报告。")


@app.callback()
def main() -> None:
    """Shuoha 命令行工具。"""


@app.command()
def analyze(
    stock_codes: Annotated[list[str], typer.Argument()],
    output_dir: Path | None = None,
    agent: bool = False,
    cli_backend: str = typer.Option(
        "local",
        "--cli",
        help="分析后端：local 使用本地确定性分析，codex 使用 Codex CLI 深度分析。",
    ),
    full: bool = typer.Option(
        False,
        "--full/--brief",
        help="控制终端输出模式：完整报告或电梯摘要。",
    ),
) -> None:
    if cli_backend not in {"local", "codex"}:
        typer.echo("cli 只能是 local 或 codex")
        raise typer.Exit(2)
    for stock_code in stock_codes:
        if not (stock_code.isdigit() and len(stock_code) == 6):
            typer.echo("股票代码必须是 6 位数字")
            raise typer.Exit(2)
    if cli_backend == "codex":
        try:
            markdown = run_codex_analysis(stock_codes)
        except ExternalCliError as exc:
            typer.echo(str(exc))
            raise typer.Exit(2) from exc
        print(markdown)
        report_path = write_markdown_report(markdown, output_dir or default_codex_output_dir())
        print(f"[green]已生成[/green] {report_path}")
        return
    if len(stock_codes) != 1:
        typer.echo("多股票分析目前请使用 --cli codex")
        raise typer.Exit(2)
    stock_code = stock_codes[0]
    result, markdown = run_analysis(stock_code, agent=agent)
    if full:
        print(render_terminal_report(markdown))
    else:
        print(render_terminal_summary(result))
    evidence_path, report_path = write_outputs(result, markdown, output_dir or default_output_dir(stock_code))
    print(f"[green]已生成[/green] {report_path}")
    print(f"[green]已生成[/green] {evidence_path}")
