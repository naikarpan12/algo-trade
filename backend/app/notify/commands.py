"""Turns Telegram command text into actions on the alert store and replies."""

from app.engine.alerts import CONDITIONS, AlertStore, normalize_symbol
from app.feeds.mock import MockFeed

HELP = """Commands:
/alert SYMBOL above|below PRICE  e.g. /alert RELIANCE above 3000
/list  show active alerts
/delete ID  remove an alert
/price SYMBOL  last known price
/setprice SYMBOL PRICE  (mock feed only) move the fake price to test alerts"""


def _parse_price(text: str) -> float:
    price = float(text.replace(",", ""))
    if price <= 0:
        raise ValueError
    return price


class CommandHandler:
    def __init__(self, store: AlertStore, feed: MockFeed):
        self.store = store
        self.feed = feed

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
            "/setprice": self._setprice,
        }.get(command)
        return handler(args) if handler else f"Unknown command.\n\n{HELP}"

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
        alert = self.store.add(args[0], args[1].lower(), level)
        self.feed.subscribe([alert.symbol])
        reply = f"Alert set: {alert.describe()}"
        last = self.feed.last_price(alert.symbol)
        if last is not None:
            reply += f"\nLast price: ₹{last:,.2f}"
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
        symbol = normalize_symbol(args[0])
        self.feed.subscribe([symbol])
        return f"{symbol}: ₹{self.feed.last_price(symbol):,.2f}"

    def _setprice(self, args: list[str]) -> str:
        usage = "Usage: /setprice SYMBOL PRICE"
        if len(args) != 2:
            return usage
        try:
            price = _parse_price(args[1])
        except ValueError:
            return usage
        symbol = normalize_symbol(args[0])
        self.feed.set_price(symbol, price)
        return f"Mock price for {symbol} set to ₹{self.feed.last_price(symbol):,.2f}"
