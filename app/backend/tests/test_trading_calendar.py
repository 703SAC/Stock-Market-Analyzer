"""Trading calendar tests."""

from datetime import date

from services.kis.trading_calendar import _weekdays_between


def test_weekdays_between_excludes_weekend():
    start = date(2025, 5, 26)  # Monday
    end = date(2025, 6, 1)  # Sunday
    days = _weekdays_between(start, end)
    assert date(2025, 5, 31) not in days  # Saturday
    assert date(2025, 6, 1) not in days  # Sunday
    assert date(2025, 5, 26) in days
