from shuoha.schemas import Confidence, Verdict, VerdictBias


def choose_verdict(*, positives: int, negatives: int, veto: bool, partial: bool) -> tuple[str | None, str, str]:
    score = positives - negatives
    if partial:
        return None, Confidence.LOW.value, VerdictBias.NEUTRAL.value
    if veto:
        return Verdict.AVOID_FOR_NOW.value, Confidence.LOW.value, VerdictBias.BEARISH.value
    if positives >= 4 and negatives == 0:
        return Verdict.CONSIDER.value, Confidence.HIGH.value, VerdictBias.BULLISH.value
    if positives >= 3 and negatives == 0:
        return Verdict.CONSIDER.value, Confidence.HIGH.value, VerdictBias.NEUTRAL.value
    if negatives >= 4:
        return Verdict.AVOID_FOR_NOW.value, Confidence.LOW.value, VerdictBias.BEARISH.value
    if negatives >= 3:
        return Verdict.AVOID_FOR_NOW.value, Confidence.LOW.value, VerdictBias.NEUTRAL.value
    if score >= 2 or (positives >= 3 and negatives == 1):
        return Verdict.WAIT.value, Confidence.MEDIUM.value, VerdictBias.BULLISH.value
    if score <= -2:
        return Verdict.WAIT.value, Confidence.MEDIUM.value, VerdictBias.BEARISH.value
    return Verdict.WAIT.value, Confidence.MEDIUM.value, VerdictBias.NEUTRAL.value
