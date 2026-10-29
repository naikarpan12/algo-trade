"""Indian equities: NSE and BSE cash segment. Kite Connect feed and broker will live here."""

from datetime import date, time

from app.markets.base import Market

# NSE equity segment trading holidays falling on weekdays (circular NSE/CMTR/71775 plus the
# 12 Jan 2026 addendum for 15 Jan). Compiled from broker summaries of the circular:
# re-check against nseindia.com when it is updated, and add each new year here.
HOLIDAYS_2026 = frozenset(
    {
        date(2026, 1, 15),  # Municipal Corporation elections, Maharashtra (addendum)
        date(2026, 1, 26),  # Republic Day
        date(2026, 3, 3),  # Holi
        date(2026, 3, 26),  # Shri Ram Navami
        date(2026, 3, 31),  # Shri Mahavir Jayanti
        date(2026, 4, 3),  # Good Friday
        date(2026, 4, 14),  # Dr. Baba Saheb Ambedkar Jayanti
        date(2026, 5, 1),  # Maharashtra Day
        date(2026, 5, 28),  # Bakri Id
        date(2026, 6, 26),  # Muharram
        date(2026, 9, 14),  # Ganesh Chaturthi
        date(2026, 10, 2),  # Mahatma Gandhi Jayanti
        date(2026, 10, 20),  # Dussehra
        date(2026, 11, 10),  # Diwali Balipratipada
        date(2026, 11, 24),  # Guru Nanak Jayanti
        date(2026, 12, 25),  # Christmas
    }
)
# Muhurat trading (Sun 8 Nov 2026) is a special evening session whose timing NSE announces
# separately; it is not modelled.

INDIA = Market(
    code="india",
    name="NSE/BSE",
    timezone="Asia/Kolkata",
    open=time(9, 15),
    close=time(15, 30),
    currency="₹",
    exchanges=("NSE", "BSE"),
    # Most NSE stocks trade in 0.05 steps; low-priced stocks can have smaller ticks.
    tick_size=0.05,
    holidays={2026: HOLIDAYS_2026},
)
