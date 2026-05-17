from datetime import date

from typer.testing import CliRunner

from shuoha.cli import app
from shuoha.config import default_codex_output_dir
from shuoha.external_cli import ExternalCliError
from shuoha.schemas import AnalysisResult, AnalysisStatus, BasicContext, Confidence, Verdict, VerdictBias


def test_help_smoke():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "面向投资小白的 A 股分析 CLI" in result.stdout
    assert "shuoha analyze 600519" in result.stdout
    assert "000657 600105 --cli codex" in result.stdout


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
    assert "--full" in result.stdout
    assert "--brief" in result.stdout
    assert "OpenAI" in result.stdout
    assert "输出目录" in result.stdout
    assert "多股票" in result.stdout


def test_help_mentions_cli_backend_option():
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "--cli" in result.stdout
    assert "local" in result.stdout
    assert "codex" in result.stdout


def test_cli_backend_rejects_unknown_value():
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "600519", "--cli", "unknown"])
    assert result.exit_code == 2
    assert "local" in result.stderr
    assert "codex" in result.stderr


def test_local_cli_rejects_multiple_stock_codes():
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "600519", "000657", "--cli", "local"])
    assert result.exit_code == 2
    assert "多股票分析目前请使用 --cli codex" in result.stdout


def test_codex_cli_accepts_multiple_stock_codes(monkeypatch, tmp_path):
    written = {}

    def fake_write_markdown_report(report_markdown, output_dir):
        written["markdown"] = report_markdown
        written["output_dir"] = output_dir
        return tmp_path / "report.md"

    monkeypatch.setattr(
        "shuoha.cli.run_codex_analysis",
        lambda stock_codes: "🎯 2026-05-17 决策仪表盘\n共分析2只股票",
    )
    monkeypatch.setattr("shuoha.cli.write_markdown_report", fake_write_markdown_report)

    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "000657", "600105", "--cli", "codex"])

    assert result.exit_code == 0
    assert "决策仪表盘" in result.stdout
    assert "已生成" in result.stdout
    assert written["markdown"].startswith("🎯")
    assert "codex" in written["output_dir"].parts


def test_codex_cli_prints_external_cli_errors(monkeypatch):
    monkeypatch.setattr(
        "shuoha.cli.run_codex_analysis",
        lambda stock_codes: (_ for _ in ()).throw(ExternalCliError("未找到 codex 命令")),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "000657", "--cli", "codex"])

    assert result.exit_code == 2
    assert "未找到 codex 命令" in result.stdout


def test_default_codex_output_dir_uses_date_partition():
    assert default_codex_output_dir(today=date(2026, 5, 17)).parts[-3:] == ("out", "codex", "2026-05-17")


def test_analyze_prints_elevator_summary_before_output_paths(monkeypatch, tmp_path):
    result_model = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.BULLISH,
        confidence=Confidence.MEDIUM,
        technical_evidence=[],
        risk_evidence=[],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="白酒", company_summary="主营高端白酒。"),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )

    monkeypatch.setattr("shuoha.cli.run_analysis", lambda stock_code, agent=False: (result_model, "# report"))
    monkeypatch.setattr(
        "shuoha.cli.write_outputs",
        lambda result, report_markdown, output_dir: (tmp_path / "evidence.json", tmp_path / "report.md"),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "600519"])

    assert result.exit_code == 0
    assert "电梯摘要" in result.stdout
    assert "[结论] 观望-偏多" in result.stdout
    assert "已生成" in result.stdout


def test_analyze_full_prints_markdown_report_to_terminal(monkeypatch, tmp_path):
    result_model = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.BULLISH,
        confidence=Confidence.MEDIUM,
        technical_evidence=[],
        risk_evidence=[],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="白酒", company_summary="主营高端白酒。"),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )

    monkeypatch.setattr(
        "shuoha.cli.run_analysis",
        lambda stock_code, agent=False: (result_model, "# 贵州茅台\n\n## 快速结论\n结论：`观望-偏多`"),
    )
    monkeypatch.setattr(
        "shuoha.cli.write_outputs",
        lambda result, report_markdown, output_dir: (tmp_path / "evidence.json", tmp_path / "report.md"),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "600519", "--full"])

    assert result.exit_code == 0
    assert "股票报告 | 贵州茅台" in result.stdout
    assert "[快速结论]" in result.stdout
    assert "## 快速结论" not in result.stdout
    assert "已生成" in result.stdout
