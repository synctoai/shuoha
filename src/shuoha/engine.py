from shuoha.data.providers.akshare_provider import AKShareProvider
from shuoha.reporting.markdown_renderer import render_markdown
from shuoha.schemas import AnalysisResult, AnalysisStatus, BasicContext, Confidence


def run_analysis(stock_code: str):
    provider = AKShareProvider()
    payload = provider.fetch(stock_code)
    result = AnalysisResult(
        status=AnalysisStatus.PARTIAL,
        stock_code=payload.stock_code,
        company_name=payload.company_name,
        as_of_date=payload.as_of_date,
        verdict=None,
        confidence=Confidence.LOW,
        technical_evidence=[],
        risk_evidence=[],
        unknowns=["indicator layer not wired yet"],
        data_warnings=[],
        basic_context=BasicContext(industry=payload.industry, company_summary=payload.company_summary),
        disclaimer="This report is educational only and is not investment advice.",
    )
    markdown = render_markdown(result)
    return result, markdown
