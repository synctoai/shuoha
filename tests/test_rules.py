from shuoha.rules import choose_structured_verdict, choose_verdict


def test_choose_verdict_returns_consider_for_positive_alignment():
    verdict, confidence, bias = choose_verdict(
        positives=4,
        negatives=0,
        veto=False,
        partial=False,
    )
    assert verdict == "consider"
    assert confidence == "high"
    assert bias == "bullish"


def test_choose_verdict_returns_none_for_partial():
    verdict, confidence, bias = choose_verdict(
        positives=2,
        negatives=1,
        veto=False,
        partial=True,
    )
    assert verdict is None
    assert confidence == "low"
    assert bias == "neutral"


def test_choose_verdict_returns_wait_with_bullish_bias_for_mixed_but_positive_skew():
    verdict, confidence, bias = choose_verdict(
        positives=3,
        negatives=1,
        veto=False,
        partial=False,
    )
    assert verdict == "wait"
    assert confidence == "medium"
    assert bias == "bullish"


def test_choose_structured_verdict_uses_hard_veto_before_positive_scores():
    verdict, confidence, bias = choose_structured_verdict(
        trend_score=85,
        risk_score=80,
        hard_veto=True,
        partial=False,
    )
    assert verdict == "avoid_for_now"
    assert confidence == "low"
    assert bias == "bearish"


def test_choose_structured_verdict_considers_strong_trend_only_when_risk_is_low():
    verdict, confidence, bias = choose_structured_verdict(
        trend_score=82,
        risk_score=20,
        hard_veto=False,
        partial=False,
    )
    assert verdict == "consider"
    assert confidence == "high"
    assert bias == "bullish"


def test_choose_structured_verdict_waits_when_risk_and_trend_conflict():
    verdict, confidence, bias = choose_structured_verdict(
        trend_score=74,
        risk_score=55,
        hard_veto=False,
        partial=False,
    )
    assert verdict == "wait"
    assert confidence == "medium"
    assert bias == "neutral"
