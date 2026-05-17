from shuoha.backtesting import evaluate_signal_outcome
from shuoha.schemas import (
    AnalysisResult,
    AnalysisStatus,
    Confidence,
    RiskProfile,
    TrendSnapshot,
    Verdict,
    VerdictBias,
)


def _result(verdict: Verdict, risk_score: int = 20) -> AnalysisResult:
    return AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=verdict,
        bias=VerdictBias.BULLISH,
        confidence=Confidence.MEDIUM,
        technical_evidence=[],
        risk_evidence=[],
        unknowns=[],
        data_warnings=[],
        trend_snapshot=TrendSnapshot(
            current_price=100.0,
            ma5=99.0,
            ma10=98.0,
            ma20=97.0,
            ma60=95.0,
            bias_ma5=1.0,
            support_level=96.0,
            resistance_level=105.0,
            volume_ratio=1.2,
            trend_score=82,
            ma_alignment="bullish",
        ),
        risk_profile=RiskProfile(
            risk_level="low",
            risk_score=risk_score,
            hard_veto=False,
            chase_risk=False,
            volatility=0.18,
            max_drawdown=0.12,
            reasons=[],
        ),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )


def test_evaluate_signal_outcome_marks_consider_as_worked_when_forward_return_is_positive():
    outcome = evaluate_signal_outcome(_result(Verdict.CONSIDER), [100.0, 102.0, 106.0, 108.0])

    assert outcome.stock_code == "600519"
    assert outcome.forward_return == 0.08
    assert outcome.max_adverse_move == 0.0
    assert outcome.outcome == "worked"


def test_evaluate_signal_outcome_marks_high_risk_avoid_as_worked_when_price_falls():
    outcome = evaluate_signal_outcome(_result(Verdict.AVOID_FOR_NOW, risk_score=82), [100.0, 98.0, 94.0, 92.0])

    assert outcome.forward_return == -0.08
    assert outcome.max_adverse_move == -0.08
    assert outcome.outcome == "worked"
