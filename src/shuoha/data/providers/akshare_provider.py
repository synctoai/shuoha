import akshare as ak

from shuoha.data.providers.base import ProviderPayload


def normalize_daily_history(rows: list[dict]) -> list[dict]:
    normalized = [
        {
            "date": row["日期"],
            "open": float(row["开盘"]),
            "high": float(row["最高"]),
            "low": float(row["最低"]),
            "close": float(row["收盘"]),
            "volume": float(row["成交量"]),
        }
        for row in rows
    ]
    normalized.sort(key=lambda row: row["date"])
    return normalized


class AKShareProvider:
    def fetch(self, stock_code: str) -> ProviderPayload:
        hist = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="")
        rows = hist.to_dict(orient="records")
        daily_history = normalize_daily_history(rows)
        company_name = stock_code
        return ProviderPayload(
            stock_code=stock_code,
            company_name=company_name,
            industry=None,
            company_summary=f"A-share company {stock_code}",
            daily_history=daily_history,
            as_of_date=daily_history[-1]["date"],
        )
