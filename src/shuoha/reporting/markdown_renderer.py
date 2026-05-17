from shuoha.schemas import AnalysisResult


VERDICT_LABELS = {
    "consider": "可以关注",
    "wait": "观望",
    "avoid_for_now": "暂时回避",
}

CONFIDENCE_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
}

STATUS_LABELS = {
    "ok": "正常",
    "partial": "部分完成",
    "error": "失败",
}


def _parse_metric_map(raw_value) -> dict[str, float]:
    if not isinstance(raw_value, str):
        return {}
    metrics = {}
    for part in raw_value.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        try:
            metrics[key.strip()] = float(value.strip())
        except ValueError:
            continue
    return metrics


def _verdict_label(result: AnalysisResult) -> str:
    if result.verdict is None:
        return "当前无法给出结论"
    if result.verdict.value == "consider":
        return "可以关注-偏强" if result.bias.value == "bullish" else "可以关注"
    if result.verdict.value == "wait":
        if result.bias.value == "bullish":
            return "观望-偏多"
        if result.bias.value == "bearish":
            return "观望-偏空"
        return "观望"
    if result.verdict.value == "avoid_for_now":
        return "暂时回避-偏空" if result.bias.value == "bearish" else "暂时回避"
    return VERDICT_LABELS.get(result.verdict.value, "当前无法给出结论")


def _top_positive(result: AnalysisResult) -> str:
    for item in result.technical_evidence + result.risk_evidence:
        if item.signal.value == "positive":
            return item.plain_text
    return "当前没有足够强的正向证据。"


def _top_risk(result: AnalysisResult) -> str:
    for item in result.risk_evidence + result.technical_evidence:
        if item.signal.value == "negative":
            return item.plain_text
    return "当前没有特别突出的单点风险。"


def _join_or_default(lines: list[str], default: str) -> str:
    return "\n".join(lines) if lines else default


def _find_evidence(result: AnalysisResult, name: str):
    for item in result.technical_evidence + result.risk_evidence:
        if item.name == name:
            return item
    return None


def _summary_sentence(result: AnalysisResult, verdict_label: str, confidence_label: str) -> str:
    if result.verdict is None:
        return "当前数据不足，暂时无法给出可靠结论。你现在更应该先确认数据是否完整，而不是急着做决定。"
    if result.verdict.value == "consider":
        return f"截至 `{result.as_of_date}`，这只股票当前可以继续关注，判断置信度为 `{confidence_label}`。更适合把它放进候选名单，而不是闭眼追进去。"
    if result.verdict.value == "wait":
        return f"截至 `{result.as_of_date}`，这只股票当前更适合 `{verdict_label}`，判断置信度为 `{confidence_label}`。意思不是它一定差，而是现在的证据还不够让新手舒服地下决定。"
    return f"截至 `{result.as_of_date}`，这只股票当前更适合 `{verdict_label}`，判断置信度为 `{confidence_label}`。核心原因通常不是没有机会，而是下行风险和不确定性对新手不友好。"


def _bias_explainer(result: AnalysisResult) -> str:
    if result.verdict is None:
        return "现在连主结论都不完整，更别谈什么偏多偏空，先把数据补齐。"
    if result.verdict.value == "wait" and result.bias.value == "bullish":
        return "这里的偏多不代表现在就能买，只代表利多略多于利空，但还没多到足以替你解决买点问题。"
    if result.verdict.value == "wait" and result.bias.value == "bearish":
        return "这里的偏空不代表马上会暴跌，只代表利空和不确定性已经开始压过利多。"
    if result.verdict.value == "consider" and result.bias.value == "bullish":
        return "这里的偏强也不是让你重仓冲进去，只代表证据链比普通“可以关注”更扎实一些。"
    if result.verdict.value == "avoid_for_now" and result.bias.value == "bearish":
        return "这里的偏空是在提醒你，当前风险不是抽象存在，而是已经明显压住了上行理由。"
    return "先看主结论，再看偏向。偏向只是告诉你证据往哪边稍微倾斜，不是替你自动下单。"


def _scorecard(result: AnalysisResult) -> str:
    evidence = result.technical_evidence + result.risk_evidence
    positives = sum(item.signal.value == "positive" for item in evidence)
    negatives = sum(item.signal.value == "negative" for item in evidence)
    neutrals = sum(item.signal.value == "neutral" for item in evidence)
    score = positives - negatives
    if result.verdict is None:
        verdict_line = "- 当前没有足够完整的证据链，先别把这份报告当成判决书。"
    elif score >= 2 and negatives == 0:
        verdict_line = "- 账面上偏多，但还得看这些利多是不是继续被量能和价格兑现。"
    elif negatives >= positives:
        verdict_line = "- 利空和不确定性没有输给利多，所以这票现在更适合保守看待。"
    else:
        verdict_line = "- 利多不是没有，但还没多到可以压过风险和犹豫。"
    return "\n".join(
        [
            f"- 利多：`{positives}` 条",
            f"- 利空：`{negatives}` 条",
            f"- 中性：`{neutrals}` 条",
            f"- 证据总分：`{score}`",
            verdict_line,
        ]
    )


def _suitability_text(result: AnalysisResult) -> str:
    if result.verdict is None:
        return "- 更适合先观察数据是否恢复正常的人。\n- 不适合在信息不完整时立刻做交易决定。"
    if result.verdict.value == "consider":
        return "- 适合愿意继续跟踪、但会控制仓位的人。\n- 不适合只看一眼就想重仓的人。"
    if result.verdict.value == "wait":
        return "- 更适合稳一点、愿意再等信号更清楚的新手。\n- 如果你很怕回撤，现在先不急着出手会更舒服。"
    return "- 更适合风险承受能力高、并且知道自己为什么还要继续看的投资者。\n- 对投资小白来说，现在先回避通常更省心。"


def _change_conditions(result: AnalysisResult) -> str:
    conditions = []
    if any(item.signal.value == "positive" for item in result.technical_evidence):
        conditions.append("- 如果后续趋势继续走强，而且风险项没有恶化，结论可能会从保守转向积极。")
    if any(item.signal.value == "negative" for item in result.risk_evidence):
        conditions.append("- 如果回撤继续扩大、波动继续升高，当前判断大概率会变得更保守。")
    if result.data_warnings:
        conditions.append("- 如果后续数据恢复完整，系统可能给出比现在更明确的结论。")
    return _join_or_default(conditions, "- 如果后续技术面和风险面都没有明显变化，这次判断大概率会维持不变。")


def _sharp_review(result: AnalysisResult) -> str:
    volume_item = _find_evidence(result, "volume_confirmation")
    trend_item = _find_evidence(result, "ma_alignment")
    macd_item = _find_evidence(result, "macd_trend")
    risk_item = _find_evidence(result, "drawdown")
    if result.verdict is None:
        return "数据都不完整，还想急着下手，这不是分析，是拿真金白银赌接口心情。"
    if result.verdict.value == "consider":
        return "这票不是不能看，但还没强到值得你闭眼冲。真想做，也该把它当候选，不该当信仰。"
    if result.verdict.value == "avoid_for_now":
        return "现在去碰这票，不像抄底，更像主动往不确定性上扑。新手最忌讳的就是拿勇气代替证据。"
    if (
        trend_item
        and trend_item.signal.value == "positive"
        and macd_item
        and macd_item.signal.value == "positive"
        and volume_item
        and volume_item.signal.value != "positive"
    ):
        return "趋势和动量看着不丑，但量能没跟上，你现在冲进去，更像是在替别人接情绪。"
    if risk_item and risk_item.signal.value == "negative":
        return "它不是完全不能看，但回撤还摆在那里。新手现在硬上，多半不是在抓机会，而是在给自己找波动教育。"
    return "这票最会骗新手的地方，就是看着不弱，但也远没强到值得你现在冒险。"


def _why_not_buy_yet(result: AnalysisResult) -> str:
    reasons = []
    trend_item = _find_evidence(result, "ma_alignment")
    macd_item = _find_evidence(result, "macd_trend")
    volume_item = _find_evidence(result, "volume_confirmation")
    rsi_item = _find_evidence(result, "rsi_state")
    drawdown_item = _find_evidence(result, "drawdown")
    if trend_item and trend_item.signal.value == "positive":
        reasons.append("- 趋势不是坏消息，但趋势偏强不等于买点已经成熟。")
    if macd_item and macd_item.signal.value == "positive":
        reasons.append("- 动量有改善，说明这票还有人看，但还不足以单独支撑你现在出手。")
    if volume_item and volume_item.signal.value != "positive":
        reasons.append("- 量能没有把上涨态度坐实，说明市场更像是在试探，不是在一致看多。")
    if drawdown_item and drawdown_item.signal.value == "negative":
        reasons.append("- 回撤还偏深，说明上方套牢和情绪压力还没真正消化完。")
    if rsi_item and rsi_item.signal.value == "negative":
        reasons.append("- RSI 已经偏离舒适区，现在追进去，容易买在情绪而不是买在性价比。")
    return _join_or_default(reasons, "- 当前没有足够强的顺风，先别把“看得懂”误判成“该下单”。")


def _watch_points(result: AnalysisResult) -> str:
    points = []
    volume_item = _find_evidence(result, "volume_confirmation")
    drawdown_item = _find_evidence(result, "drawdown")
    macd_item = _find_evidence(result, "macd_trend")
    trend_item = _find_evidence(result, "ma_alignment")
    volume_metrics = _parse_metric_map(volume_item.raw_value) if volume_item else {}
    macd_metrics = _parse_metric_map(macd_item.raw_value) if macd_item else {}
    trend_metrics = _parse_metric_map(trend_item.raw_value) if trend_item else {}
    volume_ratio = volume_metrics.get("volume_ratio")
    macd_signal = macd_metrics.get("signal")
    ma20 = trend_metrics.get("ma20")
    ma60 = trend_metrics.get("ma60")
    if volume_item and volume_item.signal.value != "positive":
        threshold = "1.15 倍近 20 日均量"
        if volume_ratio is not None:
            if ma20 is not None and ma60 is not None:
                points.append(
                    f"- 如果后续量能从现在的 `{volume_ratio:.2f}` 提升到至少 `{threshold}`，而且价格还能站稳 `MA20={ma20:.2f}` 和 `MA60={ma60:.2f}` 上方，说明资金态度比现在更真。"
                )
            else:
                points.append(
                    f"- 如果后续量能从现在的 `{volume_ratio:.2f}` 提升到至少 `{threshold}`，而且价格还能站稳均线，说明资金态度比现在更真。"
                )
        else:
            points.append(f"- 如果后续上涨开始放量，最好至少达到 `{threshold}`，结论才更有机会转积极。")
    else:
        points.append("- 如果后续量能继续维持在放量区，同时价格不跌破关键均线，说明这波走势至少不是纯情绪硬拉。")
    if drawdown_item and drawdown_item.signal.value == "negative":
        drawdown_value = float(drawdown_item.raw_value) if isinstance(drawdown_item.raw_value, int | float) else None
        if drawdown_value is not None:
            points.append(
                f"- 这票当前回撤已经到 `{drawdown_value:.0%}`，高于系统警戒线 `20%`；如果继续扩大并往 `35%` 靠近，说明压力还没出清，那现在的观望都可能不够保守。"
            )
        else:
            points.append("- 如果回撤高于 `20%` 后还继续扩大并逼近 `35%`，说明压力还没出清，那现在的观望都可能不够保守。")
    else:
        if ma20 is not None and ma60 is not None:
            points.append(
                f"- 如果价格重新跌回 `MA20={ma20:.2f}` 或 `MA60={ma60:.2f}` 下方，说明当前趋势强度需要重新评估。"
            )
        else:
            points.append("- 如果价格重新跌回关键均线下方，说明当前趋势强度需要重新评估。")
    if macd_item and macd_item.signal.value == "positive":
        if macd_signal is not None:
            points.append(
                f"- 如果 MACD 继续维持在信号线 `{macd_signal:.4f}` 上方，说明动量没散；一旦重新掉下去，就别再自我安慰。"
            )
        else:
            points.append("- 如果 MACD 继续维持在信号线上方，说明动量没散；一旦重新掉下去，就别再自我安慰。")
    else:
        points.append("- 如果 MACD 重新转强，再配合量能改善，才更像一个像样的右侧信号。")
    return "\n".join(points[:3])


def _structured_action_plan(result: AnalysisResult) -> str:
    lines = []
    trend = result.trend_snapshot
    risk = result.risk_profile
    plan = result.action_plan
    if trend is not None:
        lines.extend(
            [
                f"- 趋势评分：`{trend.trend_score}/100`",
                (
                    "- 价格位置："
                    f"现价 `{trend.current_price:.2f}`，"
                    f"支撑位 `{trend.support_level:.2f}`，"
                    f"压力位 `{trend.resistance_level:.2f}`，"
                    f"MA5 乖离率 `{trend.bias_ma5:.2f}%`。"
                ),
                (
                    "- 均线结构："
                    f"MA5 `{trend.ma5:.2f}` / MA10 `{trend.ma10:.2f}` / "
                    f"MA20 `{trend.ma20:.2f}` / MA60 `{trend.ma60:.2f}`，"
                    f"结构 `{trend.ma_alignment}`。"
                ),
            ]
        )
    if risk is not None:
        lines.extend(
            [
                f"- 风险评分：`{risk.risk_score}/100`",
                f"- 风险等级：`{risk.risk_level}`",
            ]
        )
        if risk.reasons:
            lines.append(f"- 风险原因：{'；'.join(risk.reasons)}")
    if plan is not None:
        lines.extend(
            [
                f"- 空仓者：{plan.no_position}",
                f"- 持仓者：{plan.has_position}",
                f"- 触发条件：{plan.trigger_condition}",
                f"- 失效条件：{plan.invalidation_condition}",
                f"- 止损位：{plan.stop_loss}",
            ]
        )
        if plan.watch_points:
            lines.append(f"- 观察点：{'；'.join(plan.watch_points)}")
    return _join_or_default(lines, "- 当前还没有生成结构化行动计划，先按下方观察条件执行。")


def _event_risk_section(result: AnalysisResult) -> str:
    profile = result.news_risk_profile
    if profile is None or not profile.events:
        return "- 当前没有结构化事件风险输入；仍需关注公告、减持、解禁、处罚和业绩预警。"
    lines = [
        f"- 硬性风险：`{'是' if profile.hard_veto else '否'}`",
        f"- 事件风险加分：`{profile.risk_score_delta}/100`",
    ]
    lines.extend(
        [
            (
                f"- `{event.event_date}` {event.title}："
                f"{event.summary} 来源 `{event.source}`，级别 `{event.severity.value}`。"
            )
            for event in profile.events
        ]
    )
    if profile.unknowns:
        lines.extend(f"- 未确认：{item}" for item in profile.unknowns)
    return "\n".join(lines)


def _beginner_mistakes(result: AnalysisResult) -> str:
    mistakes = []
    trend_item = _find_evidence(result, "ma_alignment")
    volume_item = _find_evidence(result, "volume_confirmation")
    drawdown_item = _find_evidence(result, "drawdown")
    if trend_item and trend_item.signal.value == "positive":
        mistakes.append("- 看到均线和 MACD 偏强，就以为已经到了可以闭眼买的阶段。")
    if volume_item and volume_item.signal.value != "positive":
        mistakes.append("- 忽略量能没跟上，只因为图形不难看就急着冲进去。")
    if drawdown_item and drawdown_item.signal.value == "negative":
        mistakes.append("- 低估回撤带来的心理压力，计划拿长线，结果一震荡就先把自己洗出去。")
    mistakes.append("- 把“这票还能看”误听成“这票现在就该买”。")
    return "\n".join(mistakes[:3])


def _counterexamples(result: AnalysisResult) -> str:
    examples = []
    volume_item = _find_evidence(result, "volume_confirmation")
    drawdown_item = _find_evidence(result, "drawdown")
    macd_item = _find_evidence(result, "macd_trend")
    if volume_item and volume_item.signal.value != "positive":
        examples.append("- 如果后续突然放量，而且价格还能稳稳站在关键均线上方，那这次偏保守的看法就可能过于谨慎。")
    if drawdown_item and drawdown_item.signal.value == "negative":
        examples.append("- 如果回撤快速收回，说明上方压力消化得比报告预期更快，这次对风险的判断就可能偏重。")
    if macd_item and macd_item.signal.value == "positive":
        examples.append("- 如果 MACD 继续走强、信号线同步抬升，而量能又跟上，那现在的观望结论就有被上修的可能。")
    if result.data_warnings:
        examples.append("- 如果后续补齐的数据和现在不一致，那这份报告最大的误差来源可能根本不是判断，而是底层样本。")
    return _join_or_default(examples, "- 如果后续没有出现更强的新证据，这份报告大概率不会离当前判断太远。")


def _indicator_glossary() -> str:
    return "\n".join(
        [
            "- `均线关系`：可以粗略理解为股价最近是不是站得更稳，短期趋势有没有压过长期趋势。",
            "- `MA5 乖离率`：看股价离 5 日均线有多远。离得太远通常不是舒服买点，而是追高风险。",
            "- `支撑位/压力位`：支撑位是近期容易被资金接住的位置，压力位是近期容易遇到卖压的位置。",
            "- `MACD`：看价格动量是在变强还是变弱。站上信号线通常更偏强，掉到信号线下通常更偏弱。",
            "- `RSI`：看买卖力量是不是失衡。太低可能偏弱，太高可能过热，都不适合小白无脑追。",
            "- `量能确认`：看上涨或下跌有没有成交量配合。放量上涨更健康，放量下跌要更小心。",
            "- `波动`：价格上下跳得有多厉害。波动越大，新手越容易拿不住。",
            "- `回撤`：从之前高点跌下来多少。回撤越深，说明短期压力越大。",
        ]
    )


def render_elevator_summary(result: AnalysisResult) -> str:
    label = _verdict_label(result)
    watch_points = _watch_points(result).splitlines()
    next_step = watch_points[0].removeprefix("- ").strip() if watch_points else "先继续观察，不要急着下单。"
    return "\n".join(
        [
            "电梯摘要",
            f"结论：{label}",
            f"最大理由：{_top_positive(result)}",
            f"最大风险：{_top_risk(result)}",
            f"下一步：{next_step}",
        ]
    )


def render_markdown(result: AnalysisResult) -> str:
    label = _verdict_label(result)
    confidence = CONFIDENCE_LABELS.get(result.confidence.value, result.confidence.value)
    status = STATUS_LABELS.get(result.status.value, result.status.value)
    positives = _join_or_default(
        [f"- {item.plain_text}" for item in result.technical_evidence if item.signal.value == "positive"],
        "- 目前没有特别强的正向信号。",
    )
    decision_basis = _join_or_default(
        [f"- {item.plain_text}" for item in result.technical_evidence + result.risk_evidence],
        "- 当前还没有足够证据支撑明确判断。",
    )
    risks = _join_or_default(
        [f"- {item.plain_text}" for item in result.risk_evidence],
        "- 当前没有额外风险提示。",
    )
    unknowns = _join_or_default([f"- {item}" for item in result.unknowns], "- 当前没有额外不确定项。")
    warnings = _join_or_default([f"- {item}" for item in result.data_warnings], "- 当前没有数据告警。")
    company_summary = result.basic_context.company_summary if result.basic_context else "暂时没有拿到公司简介。"
    industry = result.basic_context.industry if result.basic_context and result.basic_context.industry else "未识别"
    return f"""# {result.company_name}（`{result.stock_code}`）

## 电梯摘要
- 结论：`{label}`
- 最大理由：{_top_positive(result)}
- 最大风险：{_top_risk(result)}
- 下一步：{_watch_points(result).splitlines()[0].removeprefix("- ").strip() if _watch_points(result).splitlines() else "先继续观察，不要急着下单。"}

## 快速结论
结论：`{label}`

{_summary_sentence(result, label, confidence)}

{_bias_explainer(result)}

## 锐评
{_sharp_review(result)}

## 证据判决书
{_scorecard(result)}

## 行动计划
{_structured_action_plan(result)}

## 这家公司是做什么的
- 行业：{industry}
- 简介：{company_summary}

## 值得关注的点
{positives}

## 需要小心的点
{risks}

## 事件风险
{_event_risk_section(result)}

## 为什么先别急着买
{_why_not_buy_yet(result)}

## 接下来盯什么
{_watch_points(result)}

## 新手最容易犯的错
{_beginner_mistakes(result)}

## 这份报告最可能看错的地方
{_counterexamples(result)}

## 这次判断的主要依据
{decision_basis}

## 这只股票更适合什么人
{_suitability_text(result)}

## 什么情况下这次判断会变化
{_change_conditions(result)}

## 当前还不确定的地方
{unknowns}

## 数据状态
{warnings}

## 指标翻译
{_indicator_glossary()}

## 结论摘要
- 建议：`{label}`
- 置信度：`{confidence}`
- 状态：`{status}`

## 免责声明
{result.disclaimer}
"""
