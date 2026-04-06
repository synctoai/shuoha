import os

from shuoha.schemas import AnalysisResult


def render_agent_markdown(result: AnalysisResult) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"""
你正在把一份确定性股票分析结果改写成适合投资小白阅读的中文 Markdown 报告。
不要修改结论。
不要编造证据。
全部使用中文。
表达要直白，避免术语堆砌。

股票：{result.company_name} ({result.stock_code})
结论：{result.verdict.value if result.verdict else 'no_verdict'}
置信度：{result.confidence.value}
技术证据：{[item.model_dump() for item in result.technical_evidence]}
风险证据：{[item.model_dump() for item in result.risk_evidence]}
不确定项：{result.unknowns}
数据告警：{result.data_warnings}
"""
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )
    return response.output_text
