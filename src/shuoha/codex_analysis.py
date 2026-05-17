from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from shuoha.data.providers.akshare_provider import AKShareProvider
from shuoha.engine import summarize_signals
from shuoha.external_cli import run_codex_exec
from shuoha.schemas import AnalysisResult, BasicContext

ProgressReporter = Callable[[str], None]


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
    trend_lines: list[str] = []
    if result.trend_snapshot is not None:
        trend = result.trend_snapshot
        trend_lines = [
            "结构化趋势快照：",
            f"- 当前价格：{trend.current_price:.2f}",
            (
                "- 均线："
                f"MA5={trend.ma5:.2f}, MA10={trend.ma10:.2f}, "
                f"MA20={trend.ma20:.2f}, MA60={trend.ma60:.2f}"
            ),
            f"- MA5 乖离率：{trend.bias_ma5:.2f}%",
            f"- 支撑/压力：{trend.support_level:.2f}/{trend.resistance_level:.2f}",
            f"- 量能比：{trend.volume_ratio:.2f}",
            f"- 趋势评分：{trend.trend_score}/100",
            f"- 均线结构：{trend.ma_alignment}",
        ]
    risk_lines: list[str] = []
    if result.risk_profile is not None:
        risk = result.risk_profile
        risk_lines = [
            "结构化风险画像：",
            f"- 风险评分：{risk.risk_score}/100",
            f"- 风险等级：{risk.risk_level}",
            f"- 硬性否决：{risk.hard_veto}",
            f"- 追高风险：{risk.chase_risk}",
            f"- 波动率：{risk.volatility:.2%}",
            f"- 最大回撤：{risk.max_drawdown:.2%}",
            f"- 风险原因：{'；'.join(risk.reasons) if risk.reasons else '暂无'}",
        ]
    action_lines: list[str] = []
    if result.action_plan is not None:
        plan = result.action_plan
        action_lines = [
            "结构化行动计划：",
            f"- 空仓者建议：{plan.no_position}",
            f"- 持仓者建议：{plan.has_position}",
            f"- 触发条件：{plan.trigger_condition}",
            f"- 失效条件：{plan.invalidation_condition}",
            f"- 止损位：{plan.stop_loss}",
            f"- 观察点：{'；'.join(plan.watch_points) if plan.watch_points else '暂无'}",
        ]
    event_lines: list[str] = []
    if result.news_risk_profile is not None:
        profile = result.news_risk_profile
        event_lines = [
            "结构化事件风险：",
            f"- hard_veto={profile.hard_veto}",
            f"- risk_score_delta={profile.risk_score_delta}",
        ]
        event_lines.extend(
            [
                (
                    f"- {event.event_date} {event.title}: "
                    f"type={event.event_type}; severity={event.severity.value}; "
                    f"source={event.source}; summary={event.summary}"
                )
                for event in profile.events
            ]
        )
        if profile.unknowns:
            event_lines.append(f"- unknowns={'；'.join(profile.unknowns)}")
    capital_lines: list[str] = []
    if result.capital_flow is not None:
        flow = result.capital_flow
        capital_lines = [
            "结构化资金流：",
            f"- main_net_inflow={flow.main_net_inflow:.2f}",
            f"- main_net_inflow_rate={flow.main_net_inflow_rate:.2f}%",
            f"- retail_net_inflow={flow.retail_net_inflow}",
            f"- source={flow.source}",
        ]
    fundamental_lines: list[str] = []
    if result.fundamentals is not None:
        fundamentals = result.fundamentals
        fundamental_lines = [
            "结构化基本面：",
            f"- pe_ttm={fundamentals.pe_ttm:.2f}" if fundamentals.pe_ttm is not None else "- pe_ttm=未知",
            f"- pb={fundamentals.pb:.2f}" if fundamentals.pb is not None else "- pb=未知",
            f"- roe={fundamentals.roe:.2f}%" if fundamentals.roe is not None else "- roe=未知",
            (
                f"- revenue_growth={fundamentals.revenue_growth:.2f}%"
                if fundamentals.revenue_growth is not None
                else "- revenue_growth=未知"
            ),
            (
                f"- profit_growth={fundamentals.profit_growth:.2f}%"
                if fundamentals.profit_growth is not None
                else "- profit_growth=未知"
            ),
            f"- source={fundamentals.source}",
        ]
    return "\n".join(
        [
            f"股票：{result.company_name} ({result.stock_code})",
            f"数据日期：{result.as_of_date}",
            f"行业：{context.industry if context else '未知'}",
            f"公司简介：{context.company_summary if context else '未知'}",
            f"本地确定性结论参考：{result.verdict.value if result.verdict else 'no_verdict'}",
            f"偏向：{result.bias.value}",
            f"置信度：{result.confidence.value}",
            "\n".join(trend_lines) if trend_lines else "结构化趋势快照：暂无",
            "\n".join(risk_lines) if risk_lines else "结构化风险画像：暂无",
            "\n".join(action_lines) if action_lines else "结构化行动计划：暂无",
            "\n".join(event_lines) if event_lines else "结构化事件风险：暂无",
            "\n".join(capital_lines) if capital_lines else "结构化资金流：暂无",
            "\n".join(fundamental_lines) if fundamental_lines else "结构化基本面：暂无",
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

决策仪表盘结构要求：
- 每只股票必须先给“一句话核心结论”，直接说明该买、该等、还是该回避。
- 每只股票必须分别给出“空仓者建议”和“持仓者建议”，不能用同一句话糊弄两类人。
- 每只股票必须给出“触发条件”“止损位”“观察点”，价格条件要尽量具体；数据不足时说明缺口。
- 每只股票必须包含检查清单，逐条标记技术结构、入场位置、量价配合、风险事件、估值/业绩、资金流。

风险优先排查：
- 必须主动搜索并核对：减持、业绩预亏、监管处罚、行业政策利空、大额解禁、诉讼/立案、主力资金持续流出。
- 任何高可信风险都必须进入“风险警报”，并说明它如何改变结论。
- 若风险与技术面冲突，优先写清“事件先行，技术待确认”，不能只看技术指标给积极结论。

新闻与来源规则：
- `最新动态`、`风险警报`、`利好催化` 中的每条新闻/公告必须带具体日期，格式为 YYYY-MM-DD。
- 超出时间窗口、时间未知、无法确认来源的信息不得当作事实使用；需要写“未查到可靠来源”。
- 不得把搜索结果里的标题党当作事实；需要区分新闻、公告、研报观点和市场传闻。

技术面一致性：
- 不得把“空头排列”和“多头排列”等互斥结论同时当作有效依据。
- 股价明显偏离 MA5 时，不得把上涨直接解释为舒服买点，必须评估追高风险。
- 接近压力位且资金流出时不得追买；接近支撑但未放量跌破时，优先给观察/持有/等待确认。

股票上下文：

{joined_sections}
"""


def _notify(progress: ProgressReporter | None, message: str) -> None:
    if progress is not None:
        progress(message)


def run_codex_analysis(
    stock_codes: list[str],
    *,
    cwd: Path | None = None,
    progress: ProgressReporter | None = None,
) -> str:
    provider = AKShareProvider()
    contexts: list[CodexStockContext] = []
    for stock_code in stock_codes:
        _notify(progress, f"正在准备 {stock_code} 的本地行情和指标上下文...")
        try:
            payload = provider.fetch(stock_code)
            result = summarize_signals(
                payload.stock_code,
                payload.company_name,
                payload.daily_history,
                event_risks=payload.event_risks,
            )
            result.basic_context = BasicContext(industry=payload.industry, company_summary=payload.company_summary)
            contexts.append(CodexStockContext(stock_code=stock_code, result=result))
            _notify(progress, f"已准备 {payload.stock_code}：本地数据日期 {result.as_of_date}")
        except Exception as exc:
            contexts.append(
                CodexStockContext(
                    stock_code=stock_code,
                    result=None,
                    data_warnings=[f"本地 AKShare 数据拉取失败：{exc}"],
                )
            )
            _notify(progress, f"{stock_code} 本地数据准备失败，仍会交给 Codex 继续研究：{exc}")
    prompt = build_codex_prompt(contexts)
    _notify(progress, "正在调用 Codex CLI 进行新闻、公告、资金流和舆情研究...")
    return run_codex_exec(prompt, cwd=cwd or Path.cwd(), progress=progress)
