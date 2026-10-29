"""US equities (NYSE/Nasdaq). Optional: an experiment area for ideas from the day-trader skill."""

from datetime import date, time

from app.markets.base import Market

# From nyse.com/markets/hours-calendars, as listed in the day-trader skill (read 2026-10-13).
HOLIDAYS = {
    2026: frozenset(
        {
            date(2026, 1, 1),
            date(2026, 1, 19),
            date(2026, 2, 16),
            date(2026, 4, 3),
            date(2026, 5, 25),
            date(2026, 6, 19),
            date(2026, 7, 3),
            date(2026, 9, 7),
            date(2026, 11, 26),
            date(2026, 12, 25),
        }
    ),
    2027: frozenset(
        {
            date(2027, 1, 1),
            date(2027, 1, 18),
            date(2027, 2, 15),
            date(2027, 3, 26),
            date(2027, 5, 31),
            date(2027, 6, 18),
            date(2027, 7, 5),
            date(2027, 9, 6),
            date(2027, 11, 25),
            date(2027, 12, 24),
        }
    ),
}

EARLY_CLOSES = {
    date(2026, 11, 27): time(13, 0),
    date(2026, 12, 24): time(13, 0),
    date(2027, 11, 26): time(13, 0),
}

US = Market(
    code="us",
    name="NYSE/Nasdaq",
    timezone="America/New_York",
    open=time(9, 30),
    close=time(16, 0),
    currency="$",
    exchanges=("US",),
    tick_size=0.01,
    holidays=HOLIDAYS,
    early_closes=EARLY_CLOSES,
)
