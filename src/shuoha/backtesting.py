from dataclasses import dataclass

from shuoha.schemas import AnalysisResult, Verdict


@dataclass
class SignalOutcome:
    stock_code: str
    verdict: str
    forward_return: float
    max_adverse_move: float
    outcome: str


def _max_drawdown_from_entry(entry_price: float, closes: list[float]) -> float:
    if entry_price <= 0:
        return 0.0
    return min((close - entry_price) / entry_price for close in closes)


def evaluate_signal_outcome(result: AnalysisResult, future_closes: list[float]) -> SignalOutcome:
    if not future_closes:
        raise ValueError("future_closes cannot be empty")
    entry_price = future_closes[0]
    last_price = future_closes[-1]
    forward_return = round((last_price - entry_price) / entry_price, 4) if entry_price > 0 else 0.0
    max_adverse_move = round(_max_drawdown_from_entry(entry_price, future_closes), 4)
    verdict = result.verdict.value if result.verdict else "no_verdict"
    if result.verdict == Verdict.CONSIDER:
        outcome = "worked" if forward_return > 0.03 and max_adverse_move > -0.08 else "failed"
    elif result.verdict == Verdict.AVOID_FOR_NOW:
        outcome = "worked" if forward_return < 0 or max_adverse_move <= -0.08 else "failed"
    else:
        outcome = "neutral"
    return SignalOutcome(
        stock_code=result.stock_code,
        verdict=verdict,
        forward_return=forward_return,
        max_adverse_move=max_adverse_move,
        outcome=outcome,
    )
