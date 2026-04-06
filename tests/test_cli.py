from typer.testing import CliRunner

from shuoha.cli import app


def test_help_smoke():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Analyze one A-share stock code" in result.stdout
