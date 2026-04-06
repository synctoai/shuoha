from shuoha.rules import choose_verdict


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
