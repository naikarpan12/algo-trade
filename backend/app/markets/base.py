"""What every market defines: exchanges, session hours, holidays, currency and tick size."""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Market:
    code: str
    name: str
    timezone: str
    open: time
    close: time
    currency: str
    # Symbol prefixes this market owns; the first one is the default ("RELIANCE" -> "NSE:RELIANCE").
    exchanges: tuple[str, ...]
    tick_size: float
    holidays: dict[int, frozenset[date]]
    early_closes: dict[date, time] = field(default_factory=dict)

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def local(self, at: datetime | None) -> datetime:
        return at.astimezone(self.tz) if at else self.now()

    def holidays_known(self, year: int) -> bool:
        return year in self.holidays

    def is_trading_day(self, day: date) -> bool:
        """Weekdays that are not listed holidays. A year with no list counts weekdays only."""
        return day.weekday() < 5 and day not in self.holidays.get(day.year, frozenset())

    def session(self, day: date) -> tuple[time, time] | None:
        if not self.is_trading_day(day):
            return None
        return self.open, self.early_closes.get(day, self.close)

    def is_open(self, at: datetime | None = None) -> bool:
        at = self.local(at)
        session = self.session(at.date())
        return bool(session) and session[0] <= at.time() < session[1]

    def status(self, at: datetime | None = None) -> str:
        at = self.local(at)
        stamp = at.strftime("%a %d %b %H:%M")
        session = self.session(at.date())
        if session is None:
            state = "closed (holiday)" if at.weekday() < 5 else "closed (weekend)"
        elif at.time() < session[0]:
            state = f"closed, opens {session[0]:%H:%M}"
        elif at.time() < session[1]:
            state = f"OPEN until {session[1]:%H:%M}"
        else:
            state = "closed for the day"
        line = f"{self.name}: {state} ({stamp} {self.timezone})"
        if not self.holidays_known(at.year):
            line += f"\nHoliday list for {at.year} not loaded: only weekends are known."
        return line

    def format_price(self, price: float) -> str:
        return f"{self.currency}{price:,.2f}"
