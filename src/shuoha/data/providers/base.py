from dataclasses import dataclass, field
from typing import Protocol

from shuoha.schemas import EventRisk


@dataclass
class ProviderPayload:
    stock_code: str
    company_name: str
    industry: str | None
    company_summary: str
    daily_history: list[dict]
    as_of_date: str
    event_risks: list[EventRisk] = field(default_factory=list)


class StockDataProvider(Protocol):
    def fetch(self, stock_code: str) -> ProviderPayload: ...
