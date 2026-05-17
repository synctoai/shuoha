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
    VerdictBias,
)


def summarize_signals(stock_code: str, company_name: str, rows: list[dict]) -> AnalysisResult:
    closes = [row["close"] for row in rows]
    highs = [float(row.get("high", row["close"])) for row in rows]
    lows = [float(row.get("low", row["close"])) for row in rows]
    volumes = [float(row.get("volume", 0.0)) for row in rows]
    ma5 = simple_moving_average(closes, 5)
    ma10 = simple_moving_average(closes, 10)
    ma20 = simple_moving_average(closes, 20)
    ma60 = simple_moving_average(closes, 60)
    macd_line, signal_line, macd_histogram = moving_average_convergence_divergence(closes)
    rsi14 = relative_strength_index(closes, 14)
    latest_volume_ratio = volume_ratio(volumes, 20)
    volatility = annualized_volatility(closes)
    drawdown = max_drawdown(closes)
    latest_close = closes[-1]
    previous_close = closes[-2] if len(closes) >= 2 else closes[-1]
    bias_ma5 = ((latest_close - ma5) / ma5 * 100) if ma5 else 0.0
    support_level = min(lows[-20:]) if lows else latest_close
    resistance_level = max(highs[-20:]) if highs else latest_close
    ma_stack_signal = (
        EvidenceSignal.POSITIVE
        if latest_close > ma5 > ma10 > ma20
        else EvidenceSignal.NEGATIVE
        if latest_close < ma5 < ma10 < ma20
        else EvidenceSignal.NEUTRAL
    )
    chase_risk_active = bias_ma5 > 5.0
    trend_score = 50
    if ma_stack_signal == EvidenceSignal.POSITIVE:
        trend_score += 20
    elif ma_stack_signal == EvidenceSignal.NEGATIVE:
        trend_score -= 20
    if 0 <= bias_ma5 <= 2:
        trend_score += 15
    elif 2 < bias_ma5 <= 5:
        trend_score += 5
    elif chase_risk_active or bias_ma5 < -5:
        trend_score -= 15
    if latest_close > previous_close and latest_volume_ratio >= 1.15:
        trend_score += 10
    elif latest_close < previous_close and latest_volume_ratio >= 1.15:
        trend_score -= 10
    trend_score = max(0, min(100, trend_score))

    technical_evidence = [
        EvidenceItem(
            name="ma_stack",
            signal=ma_stack_signal,
            raw_value=f"close={latest_close:.2f},ma5={ma5:.2f},ma10={ma10:.2f},ma20={ma20:.2f},ma60={ma60:.2f}",
            plain_text=(
                "价格站在 MA5、MA10、MA20 之上，短线结构呈多头排列。"
                if ma_stack_signal == EvidenceSignal.POSITIVE
                else "价格跌到 MA5、MA10、MA20 之下，短线结构偏空。"
                if ma_stack_signal == EvidenceSignal.NEGATIVE
                else "MA5、MA10、MA20 还没有形成清晰顺势结构。"
            ),
        ),
        EvidenceItem(
            name="price_bias_ma5",
            signal=(
                EvidenceSignal.POSITIVE
                if 0 <= bias_ma5 <= 2
                else EvidenceSignal.NEGATIVE
                if chase_risk_active or bias_ma5 < -5
                else EvidenceSignal.NEUTRAL
            ),
            raw_value=f"bias_ma5={bias_ma5:.2f}%",
            plain_text=(
                f"股价距离 MA5 的乖离率为 {bias_ma5:.2f}%，位置贴近短线支撑，买点不算追。"
                if 0 <= bias_ma5 <= 2
                else f"股价距离 MA5 的乖离率为 {bias_ma5:.2f}%，已经偏离短线均线，追高风险上升。"
                if chase_risk_active
                else f"股价距离 MA5 的乖离率为 {bias_ma5:.2f}%，位置不算理想，先等确认更稳。"
            ),
        ),
        EvidenceItem(
            name="support_resistance",
            signal=EvidenceSignal.NEUTRAL,
            raw_value=f"support={support_level:.2f},resistance={resistance_level:.2f}",
            plain_text=f"近 20 个交易日观察区间：支撑位约 {support_level:.2f}，压力位约 {resistance_level:.2f}。",
        ),
        EvidenceItem(
            name="trend_score",
            signal=(
                EvidenceSignal.POSITIVE
                if trend_score >= 70
                else EvidenceSignal.NEGATIVE
                if trend_score <= 35
                else EvidenceSignal.NEUTRAL
            ),
            raw_value=trend_score,
            plain_text=f"趋势位置综合评分为 {trend_score}/100，已同时考虑均线结构、MA5 乖离率和量价配合。",
        ),
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
            name="chase_risk",
            signal=EvidenceSignal.NEGATIVE if chase_risk_active else EvidenceSignal.NEUTRAL,
            raw_value=f"bias_ma5={bias_ma5:.2f}%",
            plain_text=(
                f"股价相对 MA5 的乖离率已达 {bias_ma5:.2f}%，对新手来说这更像追高，不适合把它当作舒服买点。"
                if chase_risk_active
                else f"股价相对 MA5 的乖离率为 {bias_ma5:.2f}%，暂未触发追高警报。"
            ),
        ),
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
    verdict_value, confidence_value, bias_value = choose_verdict(
        positives=positives,
        negatives=negatives,
        veto=(drawdown > 0.35 and volatility > 0.45) or chase_risk_active,
        partial=False,
    )
    return AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code=stock_code,
        company_name=company_name,
        as_of_date=rows[-1]["date"],
        verdict=Verdict(verdict_value),
        bias=VerdictBias(bias_value),
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
            bias=VerdictBias.NEUTRAL,
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

    if agent and os.environ.get("OPENAI_API_KEY"):
        try:
            markdown = render_agent_markdown(result)
        except Exception as exc:
            result.data_warnings.append(f"LLM 改写不可用，已回退到本地报告：{exc}")
            markdown = render_markdown(result)
    else:
        markdown = render_markdown(result)
    return result, markdown
