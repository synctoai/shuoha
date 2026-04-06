from datetime import date, timedelta
import time

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


def test_provider_falls_back_to_tx_when_eastmoney_fails(monkeypatch, tmp_path):
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
    monkeypatch.setattr(
        "shuoha.data.providers.akshare_provider.ak.stock_profile_cninfo",
        lambda **kwargs: pd.DataFrame(
            [
                {
                    "公司名称": "贵州茅台酒股份有限公司",
                    "A股简称": "贵州茅台",
                    "所属行业": "酒、饮料和精制茶制造业",
                    "主营业务": "贵州茅台酒系列产品的产品研制、酿造生产、包装和销售。",
                    "机构简介": "公司主要从事高端白酒生产经营。",
                }
            ]
        ),
    )

    payload = AKShareProvider(cache_dir=tmp_path).fetch("600519")
    assert payload.stock_code == "600519"
    assert payload.company_name == "贵州茅台"
    assert payload.industry == "酒、饮料和精制茶制造业"
    assert payload.company_summary == "贵州茅台酒系列产品的产品研制、酿造生产、包装和销售。"
    assert payload.daily_history[-1]["close"] == 10.0
    assert captured_kwargs["symbol"] == "sh600519"
    assert captured_kwargs["end_date"] == date.today().strftime("%Y%m%d")
    assert captured_kwargs["start_date"] == (date.today() - timedelta(days=730)).strftime("%Y%m%d")


def test_provider_keeps_placeholder_metadata_when_profile_lookup_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "shuoha.data.providers.akshare_provider.ak.stock_zh_a_hist",
        lambda **kwargs: pd.DataFrame(
            [
                {
                    "日期": "2026-04-01",
                    "开盘": 9.0,
                    "最高": 11.0,
                    "最低": 8.0,
                    "收盘": 10.0,
                    "成交量": 1234.0,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        "shuoha.data.providers.akshare_provider.ak.stock_profile_cninfo",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("cninfo down")),
    )

    payload = AKShareProvider(cache_dir=tmp_path).fetch("600519")
    assert payload.company_name == "600519"
    assert payload.industry is None
    assert payload.company_summary == "A 股上市公司 600519。"


def test_provider_uses_local_cache_after_first_fetch(tmp_path, monkeypatch):
    call_counts = {"history": 0, "profile": 0}

    def fake_history(**kwargs):
        call_counts["history"] += 1
        return pd.DataFrame(
            [
                {
                    "日期": "2026-04-01",
                    "开盘": 9.0,
                    "最高": 11.0,
                    "最低": 8.0,
                    "收盘": 10.0,
                    "成交量": 1234.0,
                }
            ]
        )

    def fake_profile(**kwargs):
        call_counts["profile"] += 1
        return pd.DataFrame(
            [
                {
                    "公司名称": "贵州茅台酒股份有限公司",
                    "A股简称": "贵州茅台",
                    "所属行业": "酒、饮料和精制茶制造业",
                    "主营业务": "贵州茅台酒系列产品的产品研制、酿造生产、包装和销售。",
                }
            ]
        )

    monkeypatch.setattr("shuoha.data.providers.akshare_provider.ak.stock_zh_a_hist", fake_history)
    monkeypatch.setattr("shuoha.data.providers.akshare_provider.ak.stock_profile_cninfo", fake_profile)

    provider = AKShareProvider(cache_dir=tmp_path, cache_ttl_seconds=3600)
    first = provider.fetch("600519")
    second = provider.fetch("600519")

    assert first.company_name == "贵州茅台"
    assert second.company_name == "贵州茅台"
    assert call_counts == {"history": 1, "profile": 1}
    assert (tmp_path / "history_600519.json").exists()
    assert (tmp_path / "profile_600519.json").exists()


def test_provider_fetches_history_and_profile_concurrently(tmp_path, monkeypatch):
    def fake_history(**kwargs):
        time.sleep(0.2)
        return pd.DataFrame(
            [
                {
                    "日期": "2026-04-01",
                    "开盘": 9.0,
                    "最高": 11.0,
                    "最低": 8.0,
                    "收盘": 10.0,
                    "成交量": 1234.0,
                }
            ]
        )

    def fake_profile(**kwargs):
        time.sleep(0.2)
        return pd.DataFrame(
            [
                {
                    "公司名称": "贵州茅台酒股份有限公司",
                    "A股简称": "贵州茅台",
                    "所属行业": "酒、饮料和精制茶制造业",
                    "主营业务": "贵州茅台酒系列产品的产品研制、酿造生产、包装和销售。",
                }
            ]
        )

    monkeypatch.setattr("shuoha.data.providers.akshare_provider.ak.stock_zh_a_hist", fake_history)
    monkeypatch.setattr("shuoha.data.providers.akshare_provider.ak.stock_profile_cninfo", fake_profile)

    provider = AKShareProvider(cache_dir=tmp_path, cache_ttl_seconds=3600)
    start = time.perf_counter()
    payload = provider.fetch("600519")
    elapsed = time.perf_counter() - start

    assert payload.company_name == "贵州茅台"
    assert elapsed < 0.35
