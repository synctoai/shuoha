from shuoha.reporting.terminal_renderer import render_terminal_report, render_terminal_summary
from shuoha.schemas import (
    AnalysisResult,
    AnalysisStatus,
    BasicContext,
    Confidence,
    EvidenceItem,
    EvidenceSignal,
    Verdict,
    VerdictBias,
)


def _sample_result() -> AnalysisResult:
    return AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.BULLISH,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(
                name="ma_alignment",
                signal=EvidenceSignal.POSITIVE,
                raw_value="close=1500.00,ma20=1480.00,ma60=1450.00",
                plain_text="价格站在 20 日和 60 日均线之上，短中期趋势暂时偏强。",
            ),
        ],
        risk_evidence=[
            EvidenceItem(
                name="drawdown",
                signal=EvidenceSignal.NEGATIVE,
                raw_value=0.22,
                plain_text="距离高点回撤较深，需要更谨慎。",
            )
        ],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="白酒", company_summary="主营高端白酒。"),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )


def test_render_terminal_summary_uses_card_like_labels():
    text = render_terminal_summary(_sample_result())

    assert "电梯摘要" in text
    assert "[结论] 观望-偏多" in text
    assert "[最大理由]" in text
    assert "[最大风险]" in text
    assert "[下一步]" in text
    assert "=" in text


def test_render_terminal_report_strips_markdown_syntax_and_adds_sections():
    text = render_terminal_report("# 贵州茅台（`600519`）\n\n## 快速结论\n结论：`观望-偏多`\n\n- 第一条")

    assert "股票报告 | 贵州茅台（600519）" in text
    assert "[快速结论]" in text
    assert "结论：观望-偏多" in text
    assert "## 快速结论" not in text
    assert "`600519`" not in text
