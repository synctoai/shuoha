from shuoha.portfolio import rank_analysis_results, render_portfolio_summary
from shuoha.schemas import (
    AnalysisResult,
    AnalysisStatus,
    Confidence,
    RiskProfile,
    TrendSnapshot,
    Verdict,
    VerdictBias,
)


def _result(stock_code: str, verdict: Verdict, trend_score: int, risk_score: int) -> AnalysisResult:
    return AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code=stock_code,
        company_name=stock_code,
        as_of_date="2026-05-17",
        verdict=verdict,
        bias=VerdictBias.NEUTRAL,
        confidence=Confidence.MEDIUM,
        technical_evidence=[],
        risk_evidence=[],
        unknowns=[],
        data_warnings=[],
        trend_snapshot=TrendSnapshot(
            current_price=10.0,
            ma5=9.8,
            ma10=9.6,
            ma20=9.4,
            ma60=9.0,
            bias_ma5=2.0,
            support_level=9.3,
            resistance_level=10.5,
            volume_ratio=1.2,
            trend_score=trend_score,
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


def test_rank_analysis_results_groups_by_local_score_and_risk():
    ranked = rank_analysis_results(
        [
            _result("000001", Verdict.WAIT, trend_score=72, risk_score=35),
            _result("000002", Verdict.CONSIDER, trend_score=86, risk_score=18),
            _result("000003", Verdict.AVOID_FOR_NOW, trend_score=80, risk_score=82),
        ]
    )

    assert [item.stock_code for item in ranked.candidates] == ["000002"]
    assert [item.stock_code for item in ranked.watchlist] == ["000001"]
    assert [item.stock_code for item in ranked.avoid] == ["000003"]
    assert ranked.candidates[0].local_score == 68


def test_render_portfolio_summary_shows_three_pools():
    ranked = rank_analysis_results(
        [
            _result("000001", Verdict.WAIT, trend_score=72, risk_score=35),
            _result("000002", Verdict.CONSIDER, trend_score=86, risk_score=18),
            _result("000003", Verdict.AVOID_FOR_NOW, trend_score=80, risk_score=82),
        ]
    )

    summary = render_portfolio_summary(ranked)

    assert "候选池" in summary
    assert "观察池" in summary
    assert "回避池" in summary
    assert "000002" in summary
    assert "本地分" in summary
