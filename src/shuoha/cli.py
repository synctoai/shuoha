from pathlib import Path

import typer
from rich import print

from shuoha.config import default_output_dir
from shuoha.engine import run_analysis
from shuoha.reporting.output import write_outputs

app = typer.Typer(help="分析一只 A 股股票，并输出适合投资小白阅读的报告。")


@app.callback()
def main() -> None:
    """Shuoha 命令行工具。"""


@app.command()
def analyze(stock_code: str, output_dir: Path | None = None, agent: bool = False) -> None:
    if not (stock_code.isdigit() and len(stock_code) == 6):
        typer.echo("股票代码必须是 6 位数字")
        raise typer.Exit(2)
    result, markdown = run_analysis(stock_code, agent=agent)
    evidence_path, report_path = write_outputs(result, markdown, output_dir or default_output_dir(stock_code))
    print(f"[green]已生成[/green] {report_path}")
    print(f"[green]已生成[/green] {evidence_path}")
