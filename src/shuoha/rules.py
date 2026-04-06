from shuoha.schemas import Confidence, Verdict


def choose_verdict(*, positives: int, negatives: int, veto: bool, partial: bool) -> tuple[str | None, str]:
    if partial:
        return None, Confidence.LOW.value
    if veto:
        return Verdict.AVOID_FOR_NOW.value, Confidence.LOW.value
    if positives >= 3 and negatives == 0:
        return Verdict.CONSIDER.value, Confidence.HIGH.value
    if negatives >= 3:
        return Verdict.AVOID_FOR_NOW.value, Confidence.LOW.value
    if positives >= 3 and negatives == 1:
        return Verdict.WAIT.value, Confidence.MEDIUM.value
    return Verdict.WAIT.value, Confidence.MEDIUM.value
