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
