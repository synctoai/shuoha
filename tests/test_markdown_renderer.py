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


def test_render_markdown_adds_sharp_review_action_and_beginner_mistakes():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(
                name="ma_alignment",
                signal=EvidenceSignal.POSITIVE,
                raw_value="close=1500,ma20=1480,ma60=1450",
                plain_text="价格站在 20 日和 60 日均线之上，短中期趋势暂时偏强。",
            ),
            EvidenceItem(
                name="macd_trend",
                signal=EvidenceSignal.POSITIVE,
                raw_value="macd=1.2,signal=0.8,hist=0.4",
                plain_text="MACD 站在信号线上方，动量暂时偏多。",
            ),
            EvidenceItem(
                name="volume_confirmation",
                signal=EvidenceSignal.NEUTRAL,
                raw_value="volume_ratio=0.95",
                plain_text="成交量没有明显放大，市场态度还偏谨慎。",
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

    markdown = render_markdown(result)

    assert "## 锐评" in markdown
    assert "## 为什么先别急着买" in markdown
    assert "## 接下来盯什么" in markdown
    assert "## 新手最容易犯的错" in markdown
    assert "接情绪" in markdown or "不值得" in markdown
    assert "如果后续" in markdown or "如果" in markdown
