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


def render_markdown(result: AnalysisResult) -> str:
    label = VERDICT_LABELS.get(result.verdict.value, "当前无法给出结论") if result.verdict else "当前无法给出结论"
    confidence = CONFIDENCE_LABELS.get(result.confidence.value, result.confidence.value)
    status = STATUS_LABELS.get(result.status.value, result.status.value)
    positives = "\n".join(
        f"- {item.plain_text}" for item in result.technical_evidence if item.signal.value == "positive"
    ) or "- 目前没有特别强的正向信号。"
    risks = "\n".join(f"- {item.plain_text}" for item in result.risk_evidence) or "- 当前没有额外风险提示。"
    unknowns = "\n".join(f"- {item}" for item in result.unknowns) or "- 当前没有额外不确定项。"
    warnings = "\n".join(f"- {item}" for item in result.data_warnings) or "- 当前没有数据告警。"
    company_summary = result.basic_context.company_summary if result.basic_context else "暂时没有拿到公司简介。"
    industry = result.basic_context.industry if result.basic_context and result.basic_context.industry else "未识别"
    return f"""# {result.company_name}（`{result.stock_code}`）

## 快速结论
结论：`{label}`

截至 `{result.as_of_date}`，当前判断置信度为 `{
confidence
}`。这份报告更适合帮助你快速理解“现在怎么看这只股票”，不是替你直接下单。

## 这家公司是做什么的
- 行业：{industry}
- 简介：{company_summary}

## 值得关注的点
{positives}

## 需要小心的点
{risks}

## 当前还不确定的地方
{unknowns}

## 数据状态
{warnings}

## 结论摘要
- 建议：`{label}`
- 置信度：`{confidence}`
- 状态：`{status}`

## 免责声明
{result.disclaimer}
"""
