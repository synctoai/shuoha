from enum import Enum
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

ROOT_HELP = "面向投资小白的 A 股分析 CLI：输入股票代码，输出中文报告、风险提示和观察点。"
ROOT_EPILOG = """常用示例：
  shuoha analyze 600519
  shuoha analyze 600519 --full
  shuoha analyze 000657 600105 --cli codex
"""
ANALYZE_HELP = "分析 A 股股票。默认使用本地确定性分析；需要多股票深度研究时使用 --cli codex。"
ANALYZE_EPILOG = """示例：
  shuoha analyze 600519
  shuoha analyze 600519 --brief
  shuoha analyze 600519 --full
  shuoha analyze 600519 --output-dir ./tmp/600519
  shuoha analyze 000657 600105 --cli codex

说明：
  local 模式只支持单只股票。
  codex 模式支持多股票，会复用本地 AKShare 和指标结果，再调用本机 Codex CLI 生成深度报告。
"""


class CliBackend(str, Enum):
    LOCAL = "local"
    CODEX = "codex"


app = typer.Typer(name="shuoha", help=ROOT_HELP, epilog=ROOT_EPILOG)


@app.callback()
def main() -> None:
    """Shuoha 命令行工具。"""


@app.command(help=ANALYZE_HELP, short_help="分析 A 股股票", epilog=ANALYZE_EPILOG)
def analyze(
    stock_codes: Annotated[
        list[str],
        typer.Argument(help="6 位 A 股股票代码。local 模式只支持 1 只，多股票请使用 --cli codex。"),
    ],
    output_dir: Annotated[Path | None, typer.Option(help="输出目录。local 默认 out/<股票代码>，codex 默认 out/codex/<日期>。")] = None,
    agent: Annotated[
        bool,
        typer.Option(help="使用 OpenAI 对本地确定性分析结果做中文 Markdown 改写，不改变底层证据。"),
    ] = False,
    cli_backend: Annotated[
        CliBackend,
        typer.Option(
            "--cli",
            help="分析后端：local 使用本地确定性分析，codex 使用 Codex CLI 深度分析。",
        ),
    ] = CliBackend.LOCAL,
    full: Annotated[
        bool,
        typer.Option(
            "--full/--brief",
            help="控制终端输出模式：完整报告或电梯摘要。",
        ),
    ] = False,
) -> None:
    for stock_code in stock_codes:
        if not (stock_code.isdigit() and len(stock_code) == 6):
            typer.echo("股票代码必须是 6 位数字")
            raise typer.Exit(2)
    if cli_backend == CliBackend.CODEX:
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
