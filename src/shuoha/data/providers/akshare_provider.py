from datetime import date, timedelta

import akshare as ak

from shuoha.data.providers.base import ProviderPayload


def to_tx_symbol(stock_code: str) -> str:
    return f"sh{stock_code}" if stock_code.startswith("6") else f"sz{stock_code}"


def tx_history_window(today: date | None = None, lookback_days: int = 730) -> tuple[str, str]:
    current_day = today or date.today()
    start_day = current_day - timedelta(days=lookback_days)
    return start_day.strftime("%Y%m%d"), current_day.strftime("%Y%m%d")


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text and text.lower() != "none" else None


def fetch_company_profile(stock_code: str) -> tuple[str, str | None, str]:
    try:
        profile = ak.stock_profile_cninfo(symbol=stock_code)
        if profile.empty:
            raise ValueError("empty profile")
        row = profile.to_dict(orient="records")[0]
        company_name = _clean_text(row.get("A股简称")) or _clean_text(row.get("公司名称")) or stock_code
        industry = _clean_text(row.get("所属行业"))
        company_summary = (
            _clean_text(row.get("主营业务"))
            or _clean_text(row.get("经营范围"))
            or _clean_text(row.get("机构简介"))
            or f"A 股上市公司 {stock_code}。"
        )
        return company_name, industry, company_summary
    except Exception:
        return stock_code, None, f"A 股上市公司 {stock_code}。"


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
            start_date, end_date = tx_history_window()
            hist = ak.stock_zh_a_hist_tx(symbol=to_tx_symbol(stock_code), start_date=start_date, end_date=end_date)
            rows = hist.to_dict(orient="records")
        daily_history = normalize_daily_history(rows)
        company_name, industry, company_summary = fetch_company_profile(stock_code)
        return ProviderPayload(
            stock_code=stock_code,
            company_name=company_name,
            industry=industry,
            company_summary=company_summary,
            daily_history=daily_history,
            as_of_date=str(daily_history[-1]["date"]),
        )
