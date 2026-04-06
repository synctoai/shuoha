from shuoha.reporting.markdown_renderer import render_markdown
from shuoha.schemas import (
    AnalysisResult,
    AnalysisStatus,
    BasicContext,
    Confidence,
    EvidenceItem,
    EvidenceSignal,
    Verdict,
)


def test_render_markdown_contains_quick_conclusion():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(name="ma_cross", signal=EvidenceSignal.NEUTRAL, raw_value="mixed", plain_text="趋势一般。")
        ],
        risk_evidence=[],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="白酒", company_summary="主营高端白酒。"),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )
    markdown = render_markdown(result)
    assert "## 快速结论" in markdown
    assert "结论：`观望`" in markdown
    assert "状态：`正常`" in markdown
    assert "## 这次判断的主要依据" in markdown
    assert "## 这只股票更适合什么人" in markdown
    assert "## 什么情况下这次判断会变化" in markdown
    assert "## 指标翻译" in markdown
    assert "MACD" in markdown
    assert "RSI" in markdown
