import akshare as ak

from shuoha.data.providers.base import ProviderPayload


def to_tx_symbol(stock_code: str) -> str:
    return f"sh{stock_code}" if stock_code.startswith("6") else f"sz{stock_code}"


def normalize_daily_history(rows: list[dict]) -> list[dict]:
    normalized = [
        {
            "date": str(row.get("日期", row.get("date"))),
            "open": float(row.get("开盘", row.get("open"))),
            "high": float(row.get("最高", row.get("high"))),
            "low": float(row.get("最低", row.get("low"))),
            "close": float(row.get("收盘", row.get("close"))),
            "volume": float(row.get("成交量", row.get("volume", row.get("amount", 0)))),
        }
        for row in rows
    ]
    normalized.sort(key=lambda row: row["date"])
    return normalized


class AKShareProvider:
    def fetch(self, stock_code: str) -> ProviderPayload:
        try:
            hist = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="")
            rows = hist.to_dict(orient="records")
        except Exception:
            hist = ak.stock_zh_a_hist_tx(symbol=to_tx_symbol(stock_code), start_date="19700101", end_date="20500101")
            rows = hist.to_dict(orient="records")
        daily_history = normalize_daily_history(rows)
        company_name = stock_code
        return ProviderPayload(
            stock_code=stock_code,
            company_name=company_name,
            industry=None,
            company_summary=f"A 股上市公司 {stock_code}。",
            daily_history=daily_history,
            as_of_date=str(daily_history[-1]["date"]),
        )
