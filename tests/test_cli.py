from typer.testing import CliRunner

from shuoha.cli import app
from shuoha.schemas import AnalysisResult, AnalysisStatus, BasicContext, Confidence, Verdict, VerdictBias


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
    assert "结论：观望-偏多" in result.stdout
    assert "已生成" in result.stdout
