from shuoha.indicators import (
    annualized_volatility,
    max_drawdown,
    moving_average_volume,
    relative_strength_index,
    simple_moving_average,
    moving_average_convergence_divergence,
    volume_ratio,
)


def test_simple_moving_average_uses_trailing_window():
    closes = [1, 2, 3, 4, 5]
    assert simple_moving_average(closes, 3) == 4.0


def test_max_drawdown_returns_fraction():
    closes = [10, 12, 9, 11]
    assert round(max_drawdown(closes), 4) == 0.25


def test_annualized_volatility_non_negative():
    closes = [10, 10.5, 10.2, 10.8, 10.4]
    assert annualized_volatility(closes) >= 0


def test_relative_strength_index_stays_within_range():
    closes = [float(value) for value in range(100, 130)]
    rsi = relative_strength_index(closes, window=14)
    assert 0.0 <= rsi <= 100.0
    assert rsi > 50.0


def test_macd_histogram_positive_for_uptrend():
    closes = [float(value) for value in range(100, 180)]
    macd_line, signal_line, histogram = moving_average_convergence_divergence(closes)
    assert macd_line > signal_line
    assert histogram > 0


def test_volume_ratio_compares_latest_volume_with_average_window():
    volumes = [1000.0] * 19 + [1500.0]
    assert moving_average_volume(volumes, 20) == 1025.0
    assert round(volume_ratio(volumes, 20), 4) == round(1500.0 / 1025.0, 4)
