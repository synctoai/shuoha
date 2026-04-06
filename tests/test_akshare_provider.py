from shuoha.data.providers.akshare_provider import normalize_daily_history


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
