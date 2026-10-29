from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.markets.us import US

NY = ZoneInfo("America/New_York")


def ny(*args):
    return datetime(*args, tzinfo=NY)


def test_session_hours():
    assert not US.is_open(ny(2026, 10, 29, 9, 29))
    assert US.is_open(ny(2026, 10, 29, 9, 30))
    assert not US.is_open(ny(2026, 10, 29, 16, 0))


def test_holidays_and_early_close():
    assert not US.is_trading_day(date(2026, 11, 26))  # Thanksgiving
    assert US.session(date(2026, 11, 27)) == (US.open, US.close.replace(hour=13))
    assert not US.is_open(ny(2026, 11, 27, 13, 0))


def test_daylight_saving_is_handled():
    # 9:30 New York is 19:00 IST in summer (EDT) and 20:00 IST in winter (EST)
    ist = ZoneInfo("Asia/Kolkata")
    assert US.is_open(datetime(2026, 10, 29, 19, 0, tzinfo=ist))
    assert not US.is_open(datetime(2026, 11, 12, 19, 0, tzinfo=ist))
    assert US.is_open(datetime(2026, 11, 12, 20, 0, tzinfo=ist))


def test_dollar_format():
    assert US.format_price(1234.5) == "$1,234.50"
