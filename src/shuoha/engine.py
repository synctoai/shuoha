import os

from shuoha.data.providers.akshare_provider import AKShareProvider
from shuoha.indicators import (
    annualized_volatility,
    max_drawdown,
    moving_average_convergence_divergence,
    relative_strength_index,
    simple_moving_average,
    volume_ratio,
)
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
    volumes = [float(row.get("volume", 0.0)) for row in rows]
    ma20 = simple_moving_average(closes, 20)
    ma60 = simple_moving_average(closes, 60)
    macd_line, signal_line, macd_histogram = moving_average_convergence_divergence(closes)
    rsi14 = relative_strength_index(closes, 14)
    latest_volume_ratio = volume_ratio(volumes, 20)
    volatility = annualized_volatility(closes)
    drawdown = max_drawdown(closes)
    latest_close = closes[-1]
    previous_close = closes[-2] if len(closes) >= 2 else closes[-1]

    technical_evidence = [
        EvidenceItem(
            name="ma_alignment",
            signal=(
                EvidenceSignal.POSITIVE
                if latest_close > ma20 and ma20 > ma60
                else EvidenceSignal.NEGATIVE
                if latest_close < ma20 and ma20 < ma60
                else EvidenceSignal.NEUTRAL
            ),
            raw_value=f"close={latest_close:.2f},ma20={ma20:.2f},ma60={ma60:.2f}",
            plain_text=(
                "价格站在 20 日和 60 日均线之上，短中期趋势暂时偏强。"
                if latest_close > ma20 and ma20 > ma60
                else "价格跌到 20 日和 60 日均线下方，趋势暂时偏弱。"
                if latest_close < ma20 and ma20 < ma60
                else "均线关系还没有形成特别清晰的方向。"
            ),
        ),
        EvidenceItem(
            name="macd_trend",
            signal=(
                EvidenceSignal.POSITIVE
                if macd_line > signal_line and macd_histogram > 0
                else EvidenceSignal.NEGATIVE
                if macd_line < signal_line and macd_histogram < 0
                else EvidenceSignal.NEUTRAL
            ),
            raw_value=f"macd={macd_line:.4f},signal={signal_line:.4f},hist={macd_histogram:.4f}",
            plain_text=(
                "MACD 站在信号线上方，动量暂时偏多。"
                if macd_line > signal_line and macd_histogram > 0
                else "MACD 落在信号线下方，短期动量偏弱。"
                if macd_line < signal_line and macd_histogram < 0
                else "MACD 没有给出特别明确的方向。"
            ),
        ),
        EvidenceItem(
            name="rsi_state",
            signal=(
                EvidenceSignal.POSITIVE
                if 50 <= rsi14 <= 70
                else EvidenceSignal.NEGATIVE
                if rsi14 < 40 or rsi14 > 75
                else EvidenceSignal.NEUTRAL
            ),
            raw_value=round(rsi14, 2),
            plain_text=(
                "RSI 处在相对健康的区间，说明买卖力量暂时没有明显失衡。"
                if 50 <= rsi14 <= 70
                else "RSI 已经偏离舒适区，说明走势要么偏弱，要么有点过热。"
                if rsi14 < 40 or rsi14 > 75
                else "RSI 目前没有释放特别强的信号。"
            ),
        ),
        EvidenceItem(
            name="volume_confirmation",
            signal=(
                EvidenceSignal.POSITIVE
                if latest_close > previous_close and latest_volume_ratio >= 1.15
                else EvidenceSignal.NEGATIVE
                if latest_close < previous_close and latest_volume_ratio >= 1.15
                else EvidenceSignal.NEUTRAL
            ),
            raw_value=f"volume_ratio={latest_volume_ratio:.2f}",
            plain_text=(
                "最近一次上涨伴随明显放量，说明买盘有一定跟随。"
                if latest_close > previous_close and latest_volume_ratio >= 1.15
                else "最近一次下跌伴随明显放量，说明抛压还没有完全释放。"
                if latest_close < previous_close and latest_volume_ratio >= 1.15
                else "成交量没有明显放大，市场态度还偏谨慎。"
            ),
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
        veto=drawdown > 0.35 and volatility > 0.45,
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
