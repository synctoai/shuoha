from shuoha.data.providers.base import ProviderPayload
from shuoha.engine import run_analysis, summarize_signals
from shuoha.schemas import AnalysisResult, Verdict, VerdictBias


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
