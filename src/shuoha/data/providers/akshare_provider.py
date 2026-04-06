import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import akshare as ak

from shuoha.config import default_cache_dir
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


def normalize_company_profile(row: dict[str, object] | None, stock_code: str) -> dict[str, str | None]:
    if not row:
        return {
            "company_name": stock_code,
            "industry": None,
            "company_summary": f"A 股上市公司 {stock_code}。",
        }
    company_name = _clean_text(row.get("A股简称")) or _clean_text(row.get("公司名称")) or stock_code
    industry = _clean_text(row.get("所属行业"))
    company_summary = (
        _clean_text(row.get("主营业务"))
        or _clean_text(row.get("经营范围"))
        or _clean_text(row.get("机构简介"))
        or f"A 股上市公司 {stock_code}。"
    )
    return {
        "company_name": company_name,
        "industry": industry,
        "company_summary": company_summary,
    }


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
    def __init__(self, cache_dir: Path | None = None, cache_ttl_seconds: int = 6 * 60 * 60):
        self.cache_dir = cache_dir or default_cache_dir()
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, prefix: str, stock_code: str) -> Path:
        return self.cache_dir / f"{prefix}_{stock_code}.json"

    def _read_cache(self, prefix: str, stock_code: str) -> dict | list[dict] | None:
        cache_path = self._cache_path(prefix, stock_code)
        if not cache_path.exists():
            return None
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if time.time() - payload["fetched_at"] > self.cache_ttl_seconds:
            return None
        return payload["data"]

    def _write_cache(self, prefix: str, stock_code: str, data: dict | list[dict]) -> None:
        cache_path = self._cache_path(prefix, stock_code)
        cache_path.write_text(
            json.dumps({"fetched_at": time.time(), "data": data}, ensure_ascii=False),
            encoding="utf-8",
        )

    def _fetch_history_remote(self, stock_code: str) -> list[dict]:
        try:
            hist = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="")
            rows = hist.to_dict(orient="records")
        except Exception:
            start_date, end_date = tx_history_window()
            hist = ak.stock_zh_a_hist_tx(symbol=to_tx_symbol(stock_code), start_date=start_date, end_date=end_date)
            rows = hist.to_dict(orient="records")
        return normalize_daily_history(rows)

    def _fetch_history(self, stock_code: str) -> list[dict]:
        cached = self._read_cache("history", stock_code)
        if cached:
            return cached
        daily_history = self._fetch_history_remote(stock_code)
        self._write_cache("history", stock_code, daily_history)
        return daily_history

    def _fetch_profile_remote(self, stock_code: str) -> dict[str, str | None]:
        try:
            profile = ak.stock_profile_cninfo(symbol=stock_code)
            if profile.empty:
                raise ValueError("empty profile")
            row = profile.to_dict(orient="records")[0]
            return normalize_company_profile(row, stock_code)
        except Exception:
            return normalize_company_profile(None, stock_code)

    def _fetch_profile(self, stock_code: str) -> dict[str, str | None]:
        cached = self._read_cache("profile", stock_code)
        if cached:
            return cached
        profile = self._fetch_profile_remote(stock_code)
        self._write_cache("profile", stock_code, profile)
        return profile

    def fetch(self, stock_code: str) -> ProviderPayload:
        with ThreadPoolExecutor(max_workers=2) as executor:
            history_future = executor.submit(self._fetch_history, stock_code)
            profile_future = executor.submit(self._fetch_profile, stock_code)
            daily_history = history_future.result()
            profile = profile_future.result()
        return ProviderPayload(
            stock_code=stock_code,
            company_name=profile["company_name"] or stock_code,
            industry=profile["industry"],
            company_summary=profile["company_summary"] or f"A 股上市公司 {stock_code}。",
            daily_history=daily_history,
            as_of_date=str(daily_history[-1]["date"]),
        )
