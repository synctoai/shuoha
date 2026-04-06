import math


def simple_moving_average(closes: list[float], window: int) -> float:
    values = closes[-window:]
    return sum(values) / len(values)


def exponential_moving_average(values: list[float], window: int) -> float:
    if not values:
        return 0.0
    multiplier = 2 / (window + 1)
    ema = values[0]
    for value in values[1:]:
        ema = (value - ema) * multiplier + ema
    return ema


def daily_returns(closes: list[float]) -> list[float]:
    return [
        (curr / prev) - 1
        for prev, curr in zip(closes, closes[1:], strict=False)
        if prev
    ]


def annualized_volatility(closes: list[float]) -> float:
    returns = daily_returns(closes)
    if not returns:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / len(returns)
    return math.sqrt(variance) * math.sqrt(252)


def max_drawdown(closes: list[float]) -> float:
    peak = closes[0]
    worst = 0.0
    for close in closes:
        peak = max(peak, close)
        drawdown = (peak - close) / peak
        worst = max(worst, drawdown)
    return worst


def moving_average_convergence_divergence(
    closes: list[float], fast_window: int = 12, slow_window: int = 26, signal_window: int = 9
) -> tuple[float, float, float]:
    if not closes:
        return 0.0, 0.0, 0.0
    macd_series = []
    for index in range(len(closes)):
        current = closes[: index + 1]
        fast_ema = exponential_moving_average(current, fast_window)
        slow_ema = exponential_moving_average(current, slow_window)
        macd_series.append(fast_ema - slow_ema)
    macd_line = macd_series[-1]
    signal_line = exponential_moving_average(macd_series, signal_window)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def relative_strength_index(closes: list[float], window: int = 14) -> float:
    if len(closes) < 2:
        return 50.0
    returns = [curr - prev for prev, curr in zip(closes, closes[1:], strict=False)]
    recent = returns[-window:]
    gains = [value for value in recent if value > 0]
    losses = [-value for value in recent if value < 0]
    average_gain = sum(gains) / window if gains else 0.0
    average_loss = sum(losses) / window if losses else 0.0
    if average_loss == 0:
        return 100.0 if average_gain > 0 else 50.0
    rs = average_gain / average_loss
    return 100 - (100 / (1 + rs))


def moving_average_volume(volumes: list[float], window: int = 20) -> float:
    values = volumes[-window:]
    return sum(values) / len(values) if values else 0.0


def volume_ratio(volumes: list[float], window: int = 20) -> float:
    if not volumes:
        return 1.0
    average_volume = moving_average_volume(volumes, window)
    if average_volume == 0:
        return 1.0
    return volumes[-1] / average_volume
