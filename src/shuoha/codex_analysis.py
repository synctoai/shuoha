from dataclasses import dataclass, field
from pathlib import Path

from shuoha.data.providers.akshare_provider import AKShareProvider
from shuoha.engine import summarize_signals
from shuoha.external_cli import run_codex_exec
from shuoha.schemas import AnalysisResult, BasicContext


@dataclass
class CodexStockContext:
    stock_code: str
    result: AnalysisResult | None = None
    data_warnings: list[str] = field(default_factory=list)


def _format_result(result: AnalysisResult) -> str:
    evidence = result.technical_evidence + result.risk_evidence
    evidence_lines = [
        f"- {item.name}: {item.signal.value}; raw={item.raw_value}; explanation={item.plain_text}"
        for item in evidence
    ]
    context = result.basic_context
    return "\n".join(
        [
            f"股票：{result.company_name} ({result.stock_code})",
            f"数据日期：{result.as_of_date}",
            f"行业：{context.industry if context else '未知'}",
            f"公司简介：{context.company_summary if context else '未知'}",
            f"本地确定性结论参考：{result.verdict.value if result.verdict else 'no_verdict'}",
            f"偏向：{result.bias.value}",
            f"置信度：{result.confidence.value}",
            "本地技术/风险证据：",
            "\n".join(evidence_lines) if evidence_lines else "- 无",
            f"本地数据告警：{result.data_warnings or []}",
        ]
    )


def build_codex_prompt(contexts: list[CodexStockContext]) -> str:
    sections = []
    for context in contexts:
        if context.result is None:
            sections.append(
                "\n".join(
                    [
                        f"股票：{context.stock_code}",
                        "本地 AKShare/指标上下文：不可用。",
                        f"数据告警：{context.data_warnings}",
                        "仍需继续研究该股票，但必须披露本地市场数据不可用。",
                    ]
                )
            )
        else:
            sections.append(_format_result(context.result))

    joined_sections = "\n".join(
        f"--- 股票上下文 {index + 1} ---\n{section}" for index, section in enumerate(sections)
    )
    return f"""你是 shuoha 的外部 CLI 深度研究分析器。

请基于下面由 shuoha 复用 AKShare 和本地指标层准备的上下文，继续研究这些 A 股股票的今日或最近交易日新闻、公告、资金流、舆情、行业催化和风险。

硬性要求：
- 用中文 Markdown 输出。
- 输出标题必须包含“决策仪表盘”。
- 包含“共分析N只股票 | 🟢买入:x 🟡观望:y 🔴卖出:z”格式的总览。
- 每只股票必须包含“重要信息速览”“风险警报”“利好催化”“最新动态”。
- 每只股票给出结论、0-100 评分和方向判断。
- 可以参考本地确定性结论，但最终结论允许结合新闻和基本面信息重新判断。
- 不要编造新闻、公告、资金数据、业绩数据或来源。
- 无法确认的信息必须写“未查到可靠来源”。
- 最后写“生成时间: HH:MM”。

股票上下文：

{joined_sections}
"""


def run_codex_analysis(stock_codes: list[str], *, cwd: Path | None = None) -> str:
    provider = AKShareProvider()
    contexts: list[CodexStockContext] = []
    for stock_code in stock_codes:
        try:
            payload = provider.fetch(stock_code)
            result = summarize_signals(payload.stock_code, payload.company_name, payload.daily_history)
            result.basic_context = BasicContext(industry=payload.industry, company_summary=payload.company_summary)
            contexts.append(CodexStockContext(stock_code=stock_code, result=result))
        except Exception as exc:
            contexts.append(
                CodexStockContext(
                    stock_code=stock_code,
                    result=None,
                    data_warnings=[f"本地 AKShare 数据拉取失败：{exc}"],
                )
            )
    prompt = build_codex_prompt(contexts)
    return run_codex_exec(prompt, cwd=cwd or Path.cwd())
