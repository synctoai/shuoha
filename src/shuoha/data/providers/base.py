from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProviderPayload:
    stock_code: str
    company_name: str
    industry: str | None
    company_summary: str
    daily_history: list[dict]
    as_of_date: str


class StockDataProvider(Protocol):
    def fetch(self, stock_code: str) -> ProviderPayload: ...
