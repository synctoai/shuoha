import os

from shuoha.schemas import AnalysisResult


def render_agent_markdown(result: AnalysisResult) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"""
You are rewriting a deterministic stock analysis report for a beginner investor.
Do not change the verdict.
Do not invent evidence.
Make the explanation plain language.

Stock: {result.company_name} ({result.stock_code})
Verdict: {result.verdict.value if result.verdict else 'no_verdict'}
Confidence: {result.confidence.value}
Technical evidence: {[item.model_dump() for item in result.technical_evidence]}
Risk evidence: {[item.model_dump() for item in result.risk_evidence]}
Unknowns: {result.unknowns}
Warnings: {result.data_warnings}
"""
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )
    return response.output_text
