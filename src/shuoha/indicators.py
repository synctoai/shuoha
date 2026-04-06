import math


def simple_moving_average(closes: list[float], window: int) -> float:
    values = closes[-window:]
    return sum(values) / len(values)


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
