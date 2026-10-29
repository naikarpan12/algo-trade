"""Turns Telegram command text into actions on the alert store and replies."""

from app.core.alerts import CONDITIONS, AlertStore
from app.feeds.mock import MockFeed
from app.markets import MARKETS, Market, market_for_symbol, normalize_symbol

HELP = """Commands:
/alert SYMBOL above|below PRICE  e.g. /alert RELIANCE above 3000
/list  show active alerts
/delete ID  remove an alert
/price SYMBOL  last known price
/clock  is each market open?
/setprice SYMBOL PRICE  (mock feed only) move the fake price to test alerts

Symbols: RELIANCE or NSE:RELIANCE, BSE:RELIANCE, US:TSLA"""


def _parse_price(text: str) -> float:
    price = float(text.replace(",", ""))
    if price <= 0:
        raise ValueError
    return price


def _price(symbol: str, price: float) -> str:
    return market_for_symbol(symbol).format_price(price)


class CommandHandler:
    def __init__(self, store: AlertStore, feed: MockFeed, default_market: Market):
        self.store = store
        self.feed = feed
        self.default_market = default_market

    def handle(self, text: str) -> str:
        parts = text.strip().split()
        if not parts:
            return HELP
        # "/alert@tradeRSIautomated_bot ..." in group chats
        command, args = parts[0].split("@")[0].lower(), parts[1:]
        handler = {
            "/start": self._help,
            "/help": self._help,
            "/alert": self._alert,
            "/list": self._list,
            "/delete": self._delete,
            "/price": self._price,
            "/clock": self._clock,
            "/setprice": self._setprice,
        }.get(command)
        if not handler:
            return f"Unknown command.\n\n{HELP}"
        try:
            return handler(args)
        except ValueError as error:
            return str(error)

    def _symbol(self, text: str) -> str:
        return normalize_symbol(text, self.default_market)

    def _help(self, args: list[str]) -> str:
        return HELP

    def _alert(self, args: list[str]) -> str:
        usage = "Usage: /alert SYMBOL above|below PRICE"
        if len(args) != 3 or args[1].lower() not in CONDITIONS:
            return usage
        try:
            level = _parse_price(args[2])
        except ValueError:
            return usage
        alert = self.store.add(self._symbol(args[0]), args[1].lower(), level)
        self.feed.subscribe([alert.symbol])
        reply = f"Alert set: {alert.describe()}"
        last = self.feed.last_price(alert.symbol)
        if last is not None:
            reply += f"\nLast price: {_price(alert.symbol, last)}"
        return reply

    def _list(self, args: list[str]) -> str:
        alerts = self.store.active()
        if not alerts:
            return "No active alerts."
        return "Active alerts:\n" + "\n".join(alert.describe() for alert in alerts)

    def _delete(self, args: list[str]) -> str:
        if len(args) != 1 or not args[0].lstrip("#").isdigit():
            return "Usage: /delete ID"
        alert_id = int(args[0].lstrip("#"))
        return f"Deleted alert #{alert_id}." if self.store.delete(alert_id) else f"No alert #{alert_id}."

    def _price(self, args: list[str]) -> str:
        if len(args) != 1:
            return "Usage: /price SYMBOL"
        symbol = self._symbol(args[0])
        self.feed.subscribe([symbol])
        return f"{symbol}: {_price(symbol, self.feed.last_price(symbol))}"

    def _clock(self, args: list[str]) -> str:
        return "\n".join(market.status() for market in MARKETS.values())

    def _setprice(self, args: list[str]) -> str:
        usage = "Usage: /setprice SYMBOL PRICE"
        if len(args) != 2:
            return usage
        try:
            price = _parse_price(args[1])
        except ValueError:
            return usage
        symbol = self._symbol(args[0])
        self.feed.set_price(symbol, price)
        return f"Mock price for {symbol} set to {_price(symbol, self.feed.last_price(symbol))}"
