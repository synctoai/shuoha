from datetime import date, timedelta

import pandas as pd

from shuoha.data.providers.akshare_provider import AKShareProvider, normalize_daily_history


def test_normalize_daily_history_sorts_and_keeps_required_fields():
    rows = [
        {"日期": "2026-04-02", "收盘": 1680.0, "开盘": 1670.0, "最高": 1692.0, "最低": 1668.0, "成交量": 1000},
        {"日期": "2026-04-01", "收盘": 1662.0, "开盘": 1650.0, "最高": 1668.0, "最低": 1640.0, "成交量": 900},
    ]
    out = normalize_daily_history(rows)
    assert out[0]["date"] == "2026-04-01"
    assert out[-1]["close"] == 1680.0


def test_normalize_daily_history_stringifies_date_values():
    rows = [
        {"日期": __import__("datetime").date(2026, 4, 2), "收盘": 10, "开盘": 9, "最高": 11, "最低": 8, "成交量": 1}
    ]
    out = normalize_daily_history(rows)
    assert out[0]["date"] == "2026-04-02"


def test_provider_falls_back_to_tx_when_eastmoney_fails(monkeypatch):
    captured_kwargs = {}

    monkeypatch.setattr(
        "shuoha.data.providers.akshare_provider.ak.stock_zh_a_hist",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("eastmoney down")),
    )

    def fake_tx(**kwargs):
        captured_kwargs.update(kwargs)
        return pd.DataFrame(
            [
                {
                    "date": date(2026, 4, 1),
                    "open": 9.0,
                    "high": 11.0,
                    "low": 8.0,
                    "close": 10.0,
                    "amount": 1234.0,
                }
            ]
        )

    monkeypatch.setattr("shuoha.data.providers.akshare_provider.ak.stock_zh_a_hist_tx", fake_tx)

    payload = AKShareProvider().fetch("600519")
    assert payload.stock_code == "600519"
    assert payload.daily_history[-1]["close"] == 10.0
    assert payload.company_summary == "A 股上市公司 600519。"
    assert captured_kwargs["symbol"] == "sh600519"
    assert captured_kwargs["end_date"] == date.today().strftime("%Y%m%d")
    assert captured_kwargs["start_date"] == (date.today() - timedelta(days=730)).strftime("%Y%m%d")
