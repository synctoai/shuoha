from shuoha.engine import summarize_signals
from shuoha.schemas import AnalysisResult, Verdict


def test_analysis_result_allows_partial_without_verdict():
    result = AnalysisResult(
        status="partial",
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=None,
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


def test_summarize_signals_yields_wait_for_mixed_signals():
    rows = [
        {"date": "2026-01-01", "close": 100.0},
        {"date": "2026-01-02", "close": 101.0},
        {"date": "2026-01-03", "close": 102.0},
        {"date": "2026-01-04", "close": 101.5},
        {"date": "2026-01-05", "close": 101.0},
    ] * 20
    result = summarize_signals("600519", "贵州茅台", rows)
    assert result.verdict.value == "wait"
