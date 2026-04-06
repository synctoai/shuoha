from shuoha.rules import choose_verdict


def test_choose_verdict_returns_consider_for_positive_alignment():
    verdict, confidence = choose_verdict(
        positives=4,
        negatives=0,
        veto=False,
        partial=False,
    )
    assert verdict == "consider"
    assert confidence == "high"


def test_choose_verdict_returns_none_for_partial():
    verdict, confidence = choose_verdict(
        positives=2,
        negatives=1,
        veto=False,
        partial=True,
    )
    assert verdict is None
    assert confidence == "low"
