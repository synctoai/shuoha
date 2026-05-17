from shuoha.reporting.markdown_renderer import render_markdown
from shuoha.schemas import (
    ActionPlan,
    AnalysisResult,
    AnalysisStatus,
    BasicContext,
    Confidence,
    EvidenceItem,
    EvidenceSignal,
    RiskProfile,
    TrendSnapshot,
    Verdict,
    VerdictBias,
)


def test_render_markdown_contains_quick_conclusion():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.BULLISH,
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
    assert "## 电梯摘要" in markdown
    assert "## 快速结论" in markdown
    assert "结论：`观望-偏多`" in markdown
    assert "偏多不代表现在就能买" in markdown
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
        bias=VerdictBias.NEUTRAL,
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


def test_render_markdown_watch_points_include_threshold_style_conditions():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.NEUTRAL,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(
                name="ma_alignment",
                signal=EvidenceSignal.POSITIVE,
                raw_value="close=1500.00,ma20=1480.00,ma60=1450.00",
                plain_text="价格站在 20 日和 60 日均线之上，短中期趋势暂时偏强。",
            ),
            EvidenceItem(
                name="macd_trend",
                signal=EvidenceSignal.POSITIVE,
                raw_value="macd=1.2000,signal=0.8000,hist=0.4000",
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

    assert "1.15" in markdown
    assert "20%" in markdown
    assert "1480.00" in markdown or "1450.00" in markdown
    assert "0.8000" in markdown or "信号线" in markdown


def test_render_markdown_adds_evidence_scorecard():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.NEUTRAL,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(
                name="ma_alignment",
                signal=EvidenceSignal.POSITIVE,
                raw_value="close=1500.00,ma20=1480.00,ma60=1450.00",
                plain_text="价格站在 20 日和 60 日均线之上，短中期趋势暂时偏强。",
            ),
            EvidenceItem(
                name="macd_trend",
                signal=EvidenceSignal.POSITIVE,
                raw_value="macd=1.2000,signal=0.8000,hist=0.4000",
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
            ),
            EvidenceItem(
                name="volatility",
                signal=EvidenceSignal.NEUTRAL,
                raw_value=0.18,
                plain_text="波动没有明显失控。",
            ),
        ],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="白酒", company_summary="主营高端白酒。"),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )

    markdown = render_markdown(result)

    assert "## 证据判决书" in markdown
    assert "利多：`2` 条" in markdown
    assert "利空：`1` 条" in markdown
    assert "中性：`2` 条" in markdown
    assert "证据总分：`1`" in markdown


def test_render_markdown_explains_trade_location_terms_for_beginners():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.NEUTRAL,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(
                name="price_bias_ma5",
                signal=EvidenceSignal.NEGATIVE,
                raw_value="bias_ma5=8.00%",
                plain_text="股价距离 MA5 的乖离率为 8.00%，已经偏离短线均线，追高风险上升。",
            ),
            EvidenceItem(
                name="support_resistance",
                signal=EvidenceSignal.NEUTRAL,
                raw_value="support=1400.00,resistance=1520.00",
                plain_text="近 20 个交易日观察区间：支撑位约 1400.00，压力位约 1520.00。",
            ),
        ],
        risk_evidence=[],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="白酒", company_summary="主营高端白酒。"),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )

    markdown = render_markdown(result)

    assert "MA5 乖离率" in markdown
    assert "支撑位" in markdown
    assert "压力位" in markdown
    assert "追高" in markdown


def test_render_markdown_uses_structured_action_plan_when_available():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.NEUTRAL,
        confidence=Confidence.MEDIUM,
        technical_evidence=[],
        risk_evidence=[],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="白酒", company_summary="主营高端白酒。"),
        trend_snapshot=TrendSnapshot(
            current_price=1500.0,
            ma5=1490.0,
            ma10=1480.0,
            ma20=1460.0,
            ma60=1400.0,
            bias_ma5=0.67,
            support_level=1450.0,
            resistance_level=1520.0,
            volume_ratio=1.2,
            trend_score=72,
            ma_alignment="bullish",
        ),
        risk_profile=RiskProfile(
            risk_level="medium",
            risk_score=35,
            hard_veto=False,
            chase_risk=False,
            volatility=0.2,
            max_drawdown=0.18,
            reasons=["回撤接近警戒线。"],
        ),
        action_plan=ActionPlan(
            no_position="空仓者先等突破确认。",
            has_position="持仓者观察压力位。",
            trigger_condition="放量突破 1520.00。",
            invalidation_condition="跌破 1450.00。",
            stop_loss="1450.00 附近。",
            watch_points=["量比保持 1.15 以上", "MA5 乖离率不要超过 5%"],
        ),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )

    markdown = render_markdown(result)

    assert "## 行动计划" in markdown
    assert "空仓者先等突破确认" in markdown
    assert "持仓者观察压力位" in markdown
    assert "放量突破 1520.00" in markdown
    assert "风险评分：`35/100`" in markdown
    assert "趋势评分：`72/100`" in markdown


def test_render_markdown_adds_counterexample_section():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        bias=VerdictBias.NEUTRAL,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(
                name="ma_alignment",
                signal=EvidenceSignal.POSITIVE,
                raw_value="close=1500.00,ma20=1480.00,ma60=1450.00",
                plain_text="价格站在 20 日和 60 日均线之上，短中期趋势暂时偏强。",
            ),
            EvidenceItem(
                name="macd_trend",
                signal=EvidenceSignal.POSITIVE,
                raw_value="macd=1.2000,signal=0.8000,hist=0.4000",
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

    assert "## 这份报告最可能看错的地方" in markdown
    assert "如果后续突然放量" in markdown or "放量" in markdown
    assert "如果回撤快速收回" in markdown or "回撤" in markdown
