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


def _join_or_default(lines: list[str], default: str) -> str:
    return "\n".join(lines) if lines else default


def _summary_sentence(result: AnalysisResult, verdict_label: str, confidence_label: str) -> str:
    if result.verdict is None:
        return "当前数据不足，暂时无法给出可靠结论。你现在更应该先确认数据是否完整，而不是急着做决定。"
    if result.verdict.value == "consider":
        return f"截至 `{result.as_of_date}`，这只股票当前可以继续关注，判断置信度为 `{confidence_label}`。更适合把它放进候选名单，而不是闭眼追进去。"
    if result.verdict.value == "wait":
        return f"截至 `{result.as_of_date}`，这只股票当前更适合 `{verdict_label}`，判断置信度为 `{confidence_label}`。意思不是它一定差，而是现在的证据还不够让新手舒服地下决定。"
    return f"截至 `{result.as_of_date}`，这只股票当前更适合 `{verdict_label}`，判断置信度为 `{confidence_label}`。核心原因通常不是没有机会，而是下行风险和不确定性对新手不友好。"


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


def _indicator_glossary() -> str:
    return "\n".join(
        [
            "- `均线关系`：可以粗略理解为股价最近是不是站得更稳，短期趋势有没有压过长期趋势。",
            "- `MACD`：看价格动量是在变强还是变弱。站上信号线通常更偏强，掉到信号线下通常更偏弱。",
            "- `RSI`：看买卖力量是不是失衡。太低可能偏弱，太高可能过热，都不适合小白无脑追。",
            "- `量能确认`：看上涨或下跌有没有成交量配合。放量上涨更健康，放量下跌要更小心。",
            "- `波动`：价格上下跳得有多厉害。波动越大，新手越容易拿不住。",
            "- `回撤`：从之前高点跌下来多少。回撤越深，说明短期压力越大。",
        ]
    )


def render_markdown(result: AnalysisResult) -> str:
    label = VERDICT_LABELS.get(result.verdict.value, "当前无法给出结论") if result.verdict else "当前无法给出结论"
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

## 快速结论
结论：`{label}`

{_summary_sentence(result, label, confidence)}

## 这家公司是做什么的
- 行业：{industry}
- 简介：{company_summary}

## 值得关注的点
{positives}

## 需要小心的点
{risks}

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
