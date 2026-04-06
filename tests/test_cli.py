from typer.testing import CliRunner

from shuoha.cli import app


def test_help_smoke():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "分析一只 A 股股票" in result.stdout


def test_cli_requires_stock_code_format():
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "abc"])
    assert result.exit_code == 2
    assert "股票代码必须是 6 位数字" in result.stdout


def test_help_mentions_agent_flag():
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "--agent" in result.stdout
