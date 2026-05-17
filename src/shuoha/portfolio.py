from dataclasses import dataclass, field

from shuoha.schemas import AnalysisResult, Verdict


@dataclass
class RankedStock:
    stock_code: str
    company_name: str
    verdict: str
    trend_score: int
    risk_score: int
    local_score: int


@dataclass
class RankedPortfolio:
    candidates: list[RankedStock] = field(default_factory=list)
    watchlist: list[RankedStock] = field(default_factory=list)
    avoid: list[RankedStock] = field(default_factory=list)


def _ranked_stock(result: AnalysisResult) -> RankedStock:
    trend_score = result.trend_snapshot.trend_score if result.trend_snapshot else 0
    risk_score = result.risk_profile.risk_score if result.risk_profile else 100
    return RankedStock(
        stock_code=result.stock_code,
        company_name=result.company_name,
        verdict=result.verdict.value if result.verdict else "no_verdict",
        trend_score=trend_score,
        risk_score=risk_score,
        local_score=trend_score - risk_score,
    )


def rank_analysis_results(results: list[AnalysisResult]) -> RankedPortfolio:
    portfolio = RankedPortfolio()
    for result in results:
        ranked = _ranked_stock(result)
        hard_veto = bool(result.risk_profile and result.risk_profile.hard_veto)
        if result.verdict == Verdict.CONSIDER and not hard_veto and ranked.risk_score < 45:
            portfolio.candidates.append(ranked)
        elif result.verdict == Verdict.AVOID_FOR_NOW or hard_veto or ranked.risk_score >= 60:
            portfolio.avoid.append(ranked)
        else:
            portfolio.watchlist.append(ranked)
    portfolio.candidates.sort(key=lambda item: item.local_score, reverse=True)
    portfolio.watchlist.sort(key=lambda item: item.local_score, reverse=True)
    portfolio.avoid.sort(key=lambda item: item.risk_score, reverse=True)
    return portfolio


def _render_pool(title: str, items: list[RankedStock]) -> str:
    if not items:
        return f"[{title}]\n- 暂无"
    lines = [f"[{title}]"]
    lines.extend(
        f"- {item.stock_code} {item.company_name} | 本地分 {item.local_score} | 趋势 {item.trend_score} | 风险 {item.risk_score}"
        for item in items
    )
    return "\n".join(lines)


def render_portfolio_summary(portfolio: RankedPortfolio) -> str:
    return "\n\n".join(
        [
            "================ 本地多股票排序 ================",
            _render_pool("候选池", portfolio.candidates),
            _render_pool("观察池", portfolio.watchlist),
            _render_pool("回避池", portfolio.avoid),
        ]
    )
