from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.markets.india import INDIA

IST = ZoneInfo("Asia/Kolkata")


def ist(*args):
    return datetime(*args, tzinfo=IST)


def test_session_hours():
    assert not INDIA.is_open(ist(2026, 10, 29, 9, 14))
    assert INDIA.is_open(ist(2026, 10, 29, 9, 15))
    assert INDIA.is_open(ist(2026, 10, 29, 15, 29))
    assert not INDIA.is_open(ist(2026, 10, 29, 15, 30))


def test_holidays_and_weekends():
    assert not INDIA.is_trading_day(date(2026, 11, 10))  # Diwali Balipratipada
    assert not INDIA.is_trading_day(date(2026, 11, 24))  # Guru Nanak Jayanti
    assert not INDIA.is_trading_day(date(2026, 10, 31))  # Saturday
    assert INDIA.is_trading_day(date(2026, 11, 11))


def test_status_lines():
    assert INDIA.status(ist(2026, 10, 29, 8, 0)).startswith("NSE/BSE: closed, opens 09:15")
    assert INDIA.status(ist(2026, 10, 29, 11, 0)).startswith("NSE/BSE: OPEN until 15:30")
    assert INDIA.status(ist(2026, 11, 10, 11, 0)).startswith("NSE/BSE: closed (holiday)")
    assert "Holiday list for 2027 not loaded" in INDIA.status(ist(2027, 1, 4, 11, 0))


def test_converts_other_time_zones():
    # 10:00 New York = 19:30 IST: after the NSE close
    assert not INDIA.is_open(datetime(2026, 10, 29, 10, 0, tzinfo=ZoneInfo("America/New_York")))


def test_rupee_format():
    assert INDIA.format_price(123456.5) == "₹123,456.50"
