from shuoha.codex_analysis import (
    CodexStockContext,
    build_codex_prompt,
    parse_codex_dashboard,
    render_codex_dashboard_markdown,
    run_codex_analysis,
)
from shuoha.data.providers.base import ProviderPayload
from shuoha.schemas import (
    ActionPlan,
    AnalysisResult,
    AnalysisStatus,
    BasicContext,
    CapitalFlowSnapshot,
    Confidence,
    EventRisk,
    EventSeverity,
    EvidenceItem,
    EvidenceSignal,
    NewsRiskProfile,
    RiskProfile,
    FundamentalSnapshot,
    TrendSnapshot,
    Verdict,
    VerdictBias,
)


def _result(stock_code="000657"):
    return AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code=stock_code,
        company_name="中钨高新",
        as_of_date="2026-05-17",
        verdict=Verdict.WAIT,
        bias=VerdictBias.BULLISH,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(
                name="ma_alignment",
                signal=EvidenceSignal.POSITIVE,
                raw_value="close=10.00,ma20=9.00,ma60=8.00",
                plain_text="趋势暂时偏强。",
            )
        ],
        risk_evidence=[
            EvidenceItem(name="drawdown", signal=EvidenceSignal.NEGATIVE, raw_value=0.21, plain_text="回撤较深。")
        ],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="有色金属", company_summary="主营硬质合金。"),
        trend_snapshot=TrendSnapshot(
            current_price=10.0,
            ma5=9.8,
            ma10=9.5,
            ma20=9.0,
            ma60=8.0,
            bias_ma5=2.04,
            support_level=9.3,
            resistance_level=10.5,
            volume_ratio=1.2,
            trend_score=72,
            ma_alignment="bullish",
        ),
        risk_profile=RiskProfile(
            risk_level="medium",
            risk_score=35,
            hard_veto=False,
            chase_risk=False,
            volatility=0.18,
            max_drawdown=0.21,
            reasons=["回撤较深。"],
        ),
        action_plan=ActionPlan(
            no_position="空仓者等待触发条件。",
            has_position="持仓者盯住止损线。",
            trigger_condition="放量突破 10.50。",
            invalidation_condition="跌破 9.30。",
            stop_loss="9.30 附近。",
            watch_points=["量比保持 1.15 以上"],
        ),
        news_risk_profile=NewsRiskProfile(
            events=[
                EventRisk(
                    event_type="major_unlock",
                    title="限售股大额解禁",
                    event_date="2026-05-16",
                    severity=EventSeverity.RISK,
                    source="exchange_calendar",
                    summary="大额解禁可能带来短期抛压。",
                )
            ],
            hard_veto=False,
            risk_score_delta=35,
            unknowns=[],
        ),
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
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )


def test_build_codex_prompt_includes_dashboard_requirements_and_stock_context():
    prompt = build_codex_prompt([CodexStockContext(stock_code="000657", result=_result())])
    assert "000657" in prompt
    assert "中钨高新" in prompt
    assert "决策仪表盘" in prompt
    assert "重要信息速览" in prompt
    assert "风险警报" in prompt
    assert "利好催化" in prompt
    assert "未查到可靠来源" in prompt
    assert "不要编造" in prompt


def test_build_codex_prompt_requires_actionable_risk_first_dashboard_contract():
    prompt = build_codex_prompt([CodexStockContext(stock_code="000657", result=_result())])
    assert "空仓者" in prompt
    assert "持仓者" in prompt
    assert "触发条件" in prompt
    assert "止损位" in prompt
    assert "观察点" in prompt
    assert "减持" in prompt
    assert "业绩预亏" in prompt
    assert "监管处罚" in prompt
    assert "大额解禁" in prompt
    assert "YYYY-MM-DD" in prompt
    assert "超出时间窗口" in prompt
    assert "技术面一致性" in prompt
    assert "JSON 决策对象" in prompt
    assert "codex_schema_version" in prompt


def test_build_codex_prompt_includes_structured_snapshots_and_action_plan():
    prompt = build_codex_prompt([CodexStockContext(stock_code="000657", result=_result())])
    assert "结构化趋势快照" in prompt
    assert "趋势评分：72/100" in prompt
    assert "风险评分：35/100" in prompt
    assert "风险等级：medium" in prompt
    assert "结构化行动计划" in prompt
    assert "空仓者等待触发条件" in prompt
    assert "放量突破 10.50" in prompt


def test_build_codex_prompt_includes_local_event_risk_profile():
    prompt = build_codex_prompt([CodexStockContext(stock_code="000657", result=_result())])
    assert "结构化事件风险" in prompt
    assert "限售股大额解禁" in prompt
    assert "2026-05-16" in prompt
    assert "risk_score_delta=35" in prompt


def test_build_codex_prompt_includes_capital_flow_and_fundamentals():
    prompt = build_codex_prompt([CodexStockContext(stock_code="000657", result=_result())])
    assert "结构化资金流" in prompt
    assert "main_net_inflow_rate=-8.50%" in prompt
    assert "结构化基本面" in prompt
    assert "pe_ttm=96.00" in prompt
    assert "profit_growth=-35.00%" in prompt


def test_parse_codex_dashboard_accepts_fenced_json_and_renders_markdown():
    raw = """```json
{
  "codex_schema_version": 1,
  "generated_time": "14:30",
  "summary": "共分析1只股票 | 🟢买入:0 🟡观望:1 🔴卖出:0",
  "decisions": [
    {
      "stock_code": "000657",
      "company_name": "中钨高新",
      "conclusion": "观望",
      "score": 62,
      "direction": "neutral",
      "one_sentence": "事件风险未确认前先等。",
      "no_position": "空仓者等待公告风险澄清。",
      "has_position": "持仓者盯住止损线。",
      "trigger_condition": "放量突破 10.50。",
      "stop_loss": "跌破 9.30。",
      "watch_points": ["公告风险", "资金流"],
      "risk_alerts": ["2026-05-16 大额解禁"],
      "good_news": ["未查到可靠来源"],
      "latest_updates": ["2026-05-17 未查到可靠来源"]
    }
  ]
}
```"""

    dashboard = parse_codex_dashboard(raw)
    markdown = render_codex_dashboard_markdown(dashboard)

    assert dashboard.decisions[0].stock_code == "000657"
    assert "# 决策仪表盘" in markdown
    assert "共分析1只股票" in markdown
    assert "空仓者等待公告风险澄清" in markdown
    assert "2026-05-16 大额解禁" in markdown


def test_run_codex_analysis_renders_valid_json_response(monkeypatch):
    payload = ProviderPayload(
        stock_code="000657",
        company_name="中钨高新",
        industry="有色金属",
        company_summary="主营硬质合金。",
        daily_history=[
            {"date": f"2026-04-{day:02d}", "close": float(10 + day / 10), "volume": float(1000 + day)}
            for day in range(1, 31)
        ]
        + [
            {"date": f"2026-05-{day:02d}", "close": float(13 + day / 10), "volume": float(1300 + day)}
            for day in range(1, 31)
        ],
        as_of_date="2026-05-17",
    )

    monkeypatch.setattr("shuoha.codex_analysis.AKShareProvider.fetch", lambda self, stock_code: payload)
    monkeypatch.setattr(
        "shuoha.codex_analysis.run_codex_exec",
        lambda prompt, cwd=None, progress=None: """
{
  "codex_schema_version": 1,
  "generated_time": "14:30",
  "summary": "共分析1只股票 | 🟢买入:0 🟡观望:1 🔴卖出:0",
  "decisions": [
    {
      "stock_code": "000657",
      "company_name": "中钨高新",
      "conclusion": "观望",
      "score": 62,
      "direction": "neutral",
      "one_sentence": "先等。",
      "no_position": "空仓者等待确认。",
      "has_position": "持仓者控制仓位。",
      "trigger_condition": "放量突破。",
      "stop_loss": "跌破支撑。",
      "watch_points": ["资金流"],
      "risk_alerts": ["未查到可靠来源"],
      "good_news": ["未查到可靠来源"],
      "latest_updates": ["2026-05-17 未查到可靠来源"]
    }
  ]
}
""",
    )

    markdown = run_codex_analysis(["000657"])

    assert "# 决策仪表盘" in markdown
    assert "空仓者等待确认" in markdown
    assert "```json" not in markdown


def test_run_codex_analysis_never_returns_raw_json_when_schema_validation_fails(monkeypatch):
    payload = ProviderPayload(
        stock_code="000657",
        company_name="中钨高新",
        industry="有色金属",
        company_summary="主营硬质合金。",
        daily_history=[
            {"date": f"2026-04-{day:02d}", "close": float(10 + day / 10), "volume": float(1000 + day)}
            for day in range(1, 31)
        ]
        + [
            {"date": f"2026-05-{day:02d}", "close": float(13 + day / 10), "volume": float(1300 + day)}
            for day in range(1, 31)
        ],
        as_of_date="2026-05-17",
    )

    monkeypatch.setattr("shuoha.codex_analysis.AKShareProvider.fetch", lambda self, stock_code: payload)
    monkeypatch.setattr(
        "shuoha.codex_analysis.run_codex_exec",
        lambda prompt, cwd=None, progress=None: '{"unexpected": "json"}',
    )

    markdown = run_codex_analysis(["000657"])

    assert markdown.startswith("# 决策仪表盘")
    assert "结构化校验失败" in markdown
    assert not markdown.lstrip().startswith("{")


def test_build_codex_prompt_includes_partial_context_warning():
    prompt = build_codex_prompt(
        [
            CodexStockContext(
                stock_code="600105",
                result=None,
                data_warnings=["本地 AKShare 数据拉取失败：network down"],
            )
        ]
    )
    assert "600105" in prompt
    assert "本地 AKShare 数据拉取失败" in prompt
    assert "仍需继续研究该股票" in prompt


def test_run_codex_analysis_continues_when_one_stock_fetch_fails(monkeypatch):
    payload = ProviderPayload(
        stock_code="000657",
        company_name="中钨高新",
        industry="有色金属",
        company_summary="主营硬质合金。",
        daily_history=[
            {"date": f"2026-04-{day:02d}", "close": float(10 + day / 10), "volume": float(1000 + day)}
            for day in range(1, 31)
        ]
        + [
            {"date": f"2026-05-{day:02d}", "close": float(13 + day / 10), "volume": float(1300 + day)}
            for day in range(1, 31)
        ],
        as_of_date="2026-05-17",
        event_risks=[],
    )

    def fake_fetch(self, stock_code):
        if stock_code == "600105":
            raise RuntimeError("network down")
        return payload

    def fake_run_codex_exec(prompt, cwd, progress=None):
        captured["prompt"] = prompt
        return "# codex report"

    captured = {}
    monkeypatch.setattr("shuoha.codex_analysis.AKShareProvider.fetch", fake_fetch)
    monkeypatch.setattr("shuoha.codex_analysis.run_codex_exec", fake_run_codex_exec)

    report = run_codex_analysis(["000657", "600105"])

    assert report == "# codex report"
    assert "000657" in captured["prompt"]
    assert "600105" in captured["prompt"]
    assert "network down" in captured["prompt"]


def test_run_codex_analysis_reports_progress(monkeypatch):
    payload = ProviderPayload(
        stock_code="002050",
        company_name="三花智控",
        industry="家电零部件",
        company_summary="主营制冷控制元器件。",
        daily_history=[
            {"date": f"2026-04-{day:02d}", "close": float(20 + day / 10), "volume": float(1000 + day)}
            for day in range(1, 31)
        ]
        + [
            {"date": f"2026-05-{day:02d}", "close": float(23 + day / 10), "volume": float(1300 + day)}
            for day in range(1, 31)
        ],
        as_of_date="2026-05-17",
    )
    events = []

    def fake_run_codex_exec(prompt, cwd, progress=None):
        if progress:
            progress("Codex 仍在分析中，已等待 30 秒...")
        return "# codex report"

    monkeypatch.setattr("shuoha.codex_analysis.AKShareProvider.fetch", lambda self, stock_code: payload)
    monkeypatch.setattr("shuoha.codex_analysis.run_codex_exec", fake_run_codex_exec)

    report = run_codex_analysis(["002050"], progress=events.append)

    assert report == "# codex report"
    assert any("正在准备 002050" in event for event in events)
    assert any("已准备 002050" in event for event in events)
    assert any("正在调用 Codex CLI" in event for event in events)
    assert any("已等待 30 秒" in event for event in events)
