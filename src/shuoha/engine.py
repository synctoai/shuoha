import os

from shuoha.data.providers.akshare_provider import AKShareProvider
from shuoha.indicators import annualized_volatility, max_drawdown, simple_moving_average
from shuoha.reporting.agent_renderer import render_agent_markdown
from shuoha.reporting.markdown_renderer import render_markdown
from shuoha.rules import choose_verdict
from shuoha.schemas import (
    AnalysisResult,
    AnalysisStatus,
    BasicContext,
    Confidence,
    EvidenceItem,
    EvidenceSignal,
    Verdict,
)


def summarize_signals(stock_code: str, company_name: str, rows: list[dict]) -> AnalysisResult:
    closes = [row["close"] for row in rows]
    ma20 = simple_moving_average(closes, 20)
    ma60 = simple_moving_average(closes, 60)
    volatility = annualized_volatility(closes)
    drawdown = max_drawdown(closes)

    technical_evidence = [
        EvidenceItem(
            name="ma_alignment",
            signal=EvidenceSignal.POSITIVE if closes[-1] > ma20 and ma20 > ma60 else EvidenceSignal.NEUTRAL,
            raw_value=f"close={closes[-1]},ma20={ma20},ma60={ma60}",
            plain_text="价格和均线关系暂时偏稳。" if closes[-1] > ma20 and ma20 > ma60 else "均线关系没有形成很强的顺风。",
        )
    ]
    risk_evidence = [
        EvidenceItem(
            name="volatility",
            signal=EvidenceSignal.NEGATIVE if volatility > 0.35 else EvidenceSignal.NEUTRAL,
            raw_value=round(volatility, 4),
            plain_text="波动偏大，对新手不太友好。" if volatility > 0.35 else "波动没有明显失控。",
        ),
        EvidenceItem(
            name="drawdown",
            signal=EvidenceSignal.NEGATIVE if drawdown > 0.20 else EvidenceSignal.NEUTRAL,
            raw_value=round(drawdown, 4),
            plain_text="距离高点回撤较深，需要更谨慎。" if drawdown > 0.20 else "回撤还没有到特别危险的程度。",
        ),
    ]
    positives = sum(item.signal == EvidenceSignal.POSITIVE for item in technical_evidence + risk_evidence)
    negatives = sum(item.signal == EvidenceSignal.NEGATIVE for item in technical_evidence + risk_evidence)
    verdict_value, confidence_value = choose_verdict(
        positives=positives,
        negatives=negatives,
        veto=False,
        partial=False,
    )
    return AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code=stock_code,
        company_name=company_name,
        as_of_date=rows[-1]["date"],
        verdict=Verdict(verdict_value),
        confidence=Confidence(confidence_value),
        technical_evidence=technical_evidence,
        risk_evidence=risk_evidence,
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry=None, company_summary=f"{company_name} 的公司简介暂未补全。"),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )


def run_analysis(stock_code: str, *, agent: bool = False):
    provider = AKShareProvider()
    try:
        payload = provider.fetch(stock_code)
    except Exception as exc:
        result = AnalysisResult(
            status=AnalysisStatus.PARTIAL,
            stock_code=stock_code,
            company_name=stock_code,
            as_of_date="未知",
            verdict=None,
            confidence=Confidence.LOW,
            technical_evidence=[],
            risk_evidence=[],
            unknowns=["数据源暂时不可用，当前只生成降级报告。"],
            data_warnings=[f"数据拉取失败：{exc}"],
            basic_context=BasicContext(industry=None, company_summary="暂时没有拿到公司简介。"),
            disclaimer="本报告仅供学习交流，不构成投资建议。",
        )
        markdown = render_markdown(result)
        return result, markdown

    result = summarize_signals(payload.stock_code, payload.company_name, payload.daily_history)
    result.basic_context = BasicContext(industry=payload.industry, company_summary=payload.company_summary)
    markdown = render_agent_markdown(result) if agent and os.environ.get("OPENAI_API_KEY") else render_markdown(result)
    return result, markdown
