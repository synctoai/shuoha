from shuoha.indicators import annualized_volatility, max_drawdown, simple_moving_average


def test_simple_moving_average_uses_trailing_window():
    closes = [1, 2, 3, 4, 5]
    assert simple_moving_average(closes, 3) == 4.0


def test_max_drawdown_returns_fraction():
    closes = [10, 12, 9, 11]
    assert round(max_drawdown(closes), 4) == 0.25


def test_annualized_volatility_non_negative():
    closes = [10, 10.5, 10.2, 10.8, 10.4]
    assert annualized_volatility(closes) >= 0
