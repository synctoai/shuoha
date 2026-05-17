from shuoha.engine import summarize_signals
from shuoha.reporting.markdown_renderer import render_markdown
from shuoha.schemas import CapitalFlowSnapshot, EventRisk, EventSeverity, FundamentalSnapshot


def _steady_uptrend_rows() -> list[dict]:
    rows = [
        {
            "date": f"2026-03-{day:02d}",
            "close": float(100 + day * 0.2),
            "volume": 1000.0,
        }
        for day in range(1, 31)
    ]
    rows += [
        {
            "date": f"2026-04-{day:02d}",
            "close": float(106 + day * 0.25),
            "volume": 1400.0,
        }
        for day in range(1, 31)
    ]
    return rows


def test_golden_report_keeps_event_risk_ahead_of_strong_technical_trend():
    result = summarize_signals(
        "600519",
        "贵州茅台",
        _steady_uptrend_rows(),
        event_risks=[
            EventRisk(
                event_type="regulatory_penalty",
                title="收到监管处罚事先告知书",
                event_date="2026-04-29",
                severity=EventSeverity.BLOCKER,
                source="company_announcement",
                summary="监管处罚可能改变市场风险偏好。",
            )
        ],
        capital_flow=CapitalFlowSnapshot(
            main_net_inflow=-120000000.0,
            main_net_inflow_rate=-8.5,
            retail_net_inflow=90000000.0,
            source="eastmoney_fund_flow",
        ),
        fundamentals=FundamentalSnapshot(
            pe_ttm=96.0,
            pb=8.5,
            roe=7.0,
            revenue_growth=-12.0,
            profit_growth=-35.0,
            source="eastmoney_financial",
        ),
    )

    markdown = render_markdown(result)

    assert result.verdict is not None
    assert result.verdict.value == "avoid_for_now"
    assert result.risk_profile is not None
    assert result.risk_profile.hard_veto is True
    assert "## 事件风险" in markdown
    assert "收到监管处罚事先告知书" in markdown
    assert "事件风险没有澄清前不要只看技术面" in markdown
    assert "## 资金与基本面" in markdown
    assert "主力净流入率：`-8.50%`" in markdown
    assert "利润增速：`-35.00%`" in markdown
