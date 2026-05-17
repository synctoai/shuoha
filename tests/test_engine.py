from shuoha.data.providers.base import ProviderPayload
from shuoha.engine import run_analysis, summarize_signals
from shuoha.schemas import AnalysisResult, EventRisk, EventSeverity, Verdict, VerdictBias


def test_analysis_result_allows_partial_without_verdict():
    result = AnalysisResult(
        status="partial",
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=None,
        bias="neutral",
        confidence="low",
        technical_evidence=[],
        risk_evidence=[],
        unknowns=[],
        data_warnings=["missing history"],
        disclaimer="Educational only.",
    )
    assert result.status == "partial"
    assert result.verdict is None


def test_verdict_enum_machine_values():
    assert Verdict.CONSIDER.value == "consider"
    assert Verdict.WAIT.value == "wait"
    assert Verdict.AVOID_FOR_NOW.value == "avoid_for_now"


def test_verdict_bias_enum_machine_values():
    assert VerdictBias.BULLISH.value == "bullish"
    assert VerdictBias.NEUTRAL.value == "neutral"
    assert VerdictBias.BEARISH.value == "bearish"


def test_summarize_signals_yields_wait_for_mixed_signals():
    rows = [
        {"date": "2026-01-01", "close": 100.0, "volume": 1000.0},
        {"date": "2026-01-02", "close": 101.0, "volume": 1000.0},
        {"date": "2026-01-03", "close": 102.0, "volume": 1000.0},
        {"date": "2026-01-04", "close": 101.5, "volume": 1000.0},
        {"date": "2026-01-05", "close": 101.0, "volume": 1000.0},
    ] * 20
    result = summarize_signals("600519", "贵州茅台", rows)
    assert result.verdict.value == "wait"
    assert result.bias.value in {"neutral", "bearish", "bullish"}


def test_summarize_signals_includes_macd_rsi_and_volume_evidence():
    rows = [
        {
            "date": f"2026-03-{day:02d}",
            "close": float(100 + day),
            "volume": float(1000 + day * 10),
        }
        for day in range(1, 31)
    ]
    rows += [
        {
            "date": f"2026-04-{day:02d}",
            "close": float(130 + day * 1.5),
            "volume": float(1500 + day * 40),
        }
        for day in range(1, 31)
    ]
    result = summarize_signals("600519", "贵州茅台", rows)
    evidence_names = {item.name for item in result.technical_evidence}
    assert "macd_trend" in evidence_names
    assert "rsi_state" in evidence_names
    assert "volume_confirmation" in evidence_names


def test_summarize_signals_adds_trade_location_and_trend_structure_evidence():
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
            "volume": 980.0 if day < 30 else 850.0,
        }
        for day in range(1, 31)
    ]

    result = summarize_signals("600519", "贵州茅台", rows)

    evidence_names = {item.name for item in result.technical_evidence + result.risk_evidence}
    assert "ma_stack" in evidence_names
    assert "price_bias_ma5" in evidence_names
    assert "support_resistance" in evidence_names
    assert "trend_score" in evidence_names
    assert any("MA5" in item.plain_text and "MA10" in item.plain_text for item in result.technical_evidence)
    assert result.trend_snapshot is not None
    assert result.trend_snapshot.ma5 > 0
    assert result.trend_snapshot.ma10 > 0
    assert result.trend_snapshot.ma20 > 0
    assert result.trend_snapshot.ma60 > 0
    assert result.trend_snapshot.support_level <= result.trend_snapshot.resistance_level
    assert 0 <= result.trend_snapshot.trend_score <= 100
    assert result.risk_profile is not None
    assert 0 <= result.risk_profile.risk_score <= 100
    assert result.action_plan is not None
    assert "空仓" in result.action_plan.no_position
    assert "持仓" in result.action_plan.has_position
    assert result.action_plan.watch_points


def test_summarize_signals_flags_chase_risk_when_price_is_extended_from_ma5():
    rows = [
        {
            "date": f"2026-03-{day:02d}",
            "close": 100.0 + day * 0.1,
            "volume": 1000.0,
        }
        for day in range(1, 31)
    ]
    rows += [
        {
            "date": f"2026-04-{day:02d}",
            "close": 103.0 + day * 0.1,
            "volume": 1000.0,
        }
        for day in range(1, 30)
    ]
    rows.append({"date": "2026-04-30", "close": 125.0, "volume": 3000.0})

    result = summarize_signals("600519", "贵州茅台", rows)

    chase_risk = next(item for item in result.risk_evidence if item.name == "chase_risk")
    assert chase_risk.signal.value == "negative"
    assert "乖离率" in chase_risk.plain_text
    assert "追高" in chase_risk.plain_text
    assert result.verdict.value != "consider"
    assert result.risk_profile is not None
    assert result.risk_profile.chase_risk is True
    assert result.risk_profile.hard_veto is True
    assert result.risk_profile.risk_level in {"high", "extreme"}
    assert result.action_plan is not None
    assert "追高" in result.action_plan.no_position
    assert "跌破" in result.action_plan.invalidation_condition


def test_summarize_signals_event_risk_can_hard_veto_strong_trend():
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
    event = EventRisk(
        event_type="regulatory_penalty",
        title="收到监管处罚事先告知书",
        event_date="2026-04-29",
        severity=EventSeverity.BLOCKER,
        source="company_announcement",
        summary="监管处罚可能改变市场风险偏好。",
    )

    result = summarize_signals("600519", "贵州茅台", rows, event_risks=[event])

    assert result.news_risk_profile is not None
    assert result.news_risk_profile.hard_veto is True
    assert result.risk_profile is not None
    assert result.risk_profile.hard_veto is True
    assert result.verdict.value == "avoid_for_now"
    assert any(item.name == "event_risk" and item.signal.value == "negative" for item in result.risk_evidence)
    assert result.action_plan is not None
    assert "事件风险" in result.action_plan.no_position


def test_run_analysis_returns_partial_when_provider_fails(monkeypatch):
    def _boom(self, stock_code: str):
        raise RuntimeError("network down")

    monkeypatch.setattr("shuoha.engine.AKShareProvider.fetch", _boom)
    result, markdown = run_analysis("600519")
    assert result.status.value == "partial"
    assert result.verdict is None
    assert result.bias.value == "neutral"
    assert "network down" in result.data_warnings[0]
    assert "当前无法给出结论" in markdown


def test_run_analysis_falls_back_to_local_renderer_when_agent_path_unavailable(monkeypatch):
    payload = ProviderPayload(
        stock_code="600519",
        company_name="贵州茅台",
        industry="白酒",
        company_summary="主营高端白酒。",
        daily_history=[
            {"date": f"2026-03-{day:02d}", "close": float(100 + day), "volume": float(1000 + day * 10)}
            for day in range(1, 31)
        ]
        + [
            {"date": f"2026-04-{day:02d}", "close": float(130 + day), "volume": float(1500 + day * 40)}
            for day in range(1, 31)
        ],
        as_of_date="2026-04-30",
    )

    monkeypatch.setattr("shuoha.engine.AKShareProvider.fetch", lambda self, stock_code: payload)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("shuoha.engine.render_markdown", lambda result: "fallback markdown")
    monkeypatch.setattr(
        "shuoha.engine.render_agent_markdown",
        lambda result: (_ for _ in ()).throw(ModuleNotFoundError("openai")),
    )

    result, markdown = run_analysis("600519", agent=True)

    assert markdown == "fallback markdown"
    assert any("LLM 改写不可用" in warning for warning in result.data_warnings)
