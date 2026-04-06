from shuoha.schemas import AnalysisResult


VERDICT_LABELS = {
    "consider": "Consider",
    "wait": "Wait",
    "avoid_for_now": "Avoid for now",
}


def render_markdown(result: AnalysisResult) -> str:
    label = VERDICT_LABELS.get(result.verdict.value, "No verdict") if result.verdict else "No verdict"
    positives = "\n".join(
        f"- {item.plain_text}" for item in result.technical_evidence if item.signal.value == "positive"
    ) or "- No strong positive signals yet."
    risks = "\n".join(f"- {item.plain_text}" for item in result.risk_evidence) or "- No major risk notes."
    return f"""# {result.company_name} (`{result.stock_code}`)

## Quick Conclusion
Verdict: `{label}`

## What This Company Does
{result.basic_context.company_summary if result.basic_context else "No company summary available."}

## What Looks Good
{positives}

## What Looks Risky
{risks}

## Final Verdict and Evidence Summary
- Confidence: `{result.confidence.value}`
- Data warnings: {", ".join(result.data_warnings) if result.data_warnings else "none"}

## Disclaimer
{result.disclaimer}
"""
