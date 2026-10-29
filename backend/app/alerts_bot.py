"""Runs the Telegram alert bot: polls for commands and checks alerts on every tick.

    cd backend && python -m app.alerts_bot
"""

import asyncio
import logging

from app.config import get_settings
from app.core.alerts import Alert, AlertChecker, AlertStore, sqlite_path
from app.feeds.mock import MockFeed
from app.markets import get_market, market_for_symbol
from app.notify.commands import CommandHandler
from app.notify.telegram import TelegramClient

log = logging.getLogger("alerts_bot")


class RedactingFormatter(logging.Formatter):
    """Masks a secret anywhere in a log line, tracebacks included (Telegram URLs contain the bot token)."""

    def __init__(self, secret: str, fmt: str):
        super().__init__(fmt)
        self.secret = secret

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        return text.replace(self.secret, "***") if self.secret else text


def configure_logging(secret: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(RedactingFormatter(secret, "%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    # httpx logs every request URL at INFO.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def format_trigger(alert: Alert) -> str:
    market = market_for_symbol(alert.symbol)
    return (
        f"🔔 {alert.symbol} is {alert.condition} {market.format_price(alert.level)}\n"
        f"LTP {market.format_price(alert.triggered_price)} (alert #{alert.id})"
    )


async def poll_commands(telegram: TelegramClient, handler: CommandHandler, chat_id: str) -> None:
    offset = None
    while True:
        try:
            updates = await telegram.get_updates(offset)
        except Exception:
            log.exception("getUpdates failed; retrying in 5s")
            await asyncio.sleep(5)
            continue
        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message") or {}
            text, sender = message.get("text"), str(message.get("chat", {}).get("id", ""))
            if not text or not sender:
                continue
            if not chat_id:
                reply = (
                    f"Your chat id is {sender}.\n"
                    f"Add TELEGRAM_CHAT_ID={sender} to .env and restart the bot."
                )
            elif sender != chat_id:
                log.warning("Ignoring message from unauthorised chat %s", sender)
                continue
            else:
                reply = handler.handle(text)
            await telegram.send_message(sender, reply)


async def watch_prices(feed: MockFeed, checker: AlertChecker, telegram: TelegramClient, chat_id: str) -> None:
    async for symbol, price in feed.ticks():
        for alert in checker.on_tick(symbol, price):
            log.info("Triggered %s at %s", alert.describe(), price)
            if chat_id:
                try:
                    await telegram.send_message(chat_id, format_trigger(alert))
                except Exception:
                    log.exception("Failed to send trigger for alert #%s", alert.id)


async def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set in .env")
    if settings.price_feed != "mock":
        raise SystemExit("Only PRICE_FEED=mock is supported until the Kite feed is added")

    store = AlertStore(sqlite_path(settings.database_url))
    feed = MockFeed()
    feed.subscribe(store.active_symbols())
    telegram = TelegramClient(settings.telegram_bot_token)
    market = get_market(settings.market)
    handler = CommandHandler(store, feed, market)
    chat_id = settings.telegram_chat_id

    if not chat_id:
        log.warning("TELEGRAM_CHAT_ID not set: send /start to the bot to get your chat id")
    log.info(
        "Alert bot running (market=%s, feed=%s, %d active alerts)",
        market.code,
        settings.price_feed,
        len(store.active()),
    )
    try:
        await asyncio.gather(
            poll_commands(telegram, handler, chat_id),
            watch_prices(feed, AlertChecker(store), telegram, chat_id),
        )
    finally:
        await telegram.close()


if __name__ == "__main__":
    configure_logging(get_settings().telegram_bot_token)
    asyncio.run(main())
