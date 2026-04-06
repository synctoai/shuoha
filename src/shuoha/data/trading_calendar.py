from datetime import date


def latest_expected_trading_day(today: date) -> date:
    if today.weekday() == 5:
        return today.fromordinal(today.toordinal() - 1)
    if today.weekday() == 6:
        return today.fromordinal(today.toordinal() - 2)
    return today
