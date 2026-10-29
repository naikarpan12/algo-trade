import asyncio
import logging
import sys

from app.alerts_bot import RedactingFormatter, poll_commands, watch_prices
from app.core.alerts import AlertChecker, AlertStore
from app.feeds.mock import MockFeed
from app.markets import INDIA
from app.notify.commands import CommandHandler


class FakeTelegram:
    def __init__(self, updates):
        self.updates = updates
        self.sent: list[tuple[str, str]] = []

    async def get_updates(self, offset=None):
        if self.updates:
            batch, self.updates = self.updates, []
            return batch
        await asyncio.sleep(3600)

    async def send_message(self, chat_id, text):
        self.sent.append((str(chat_id), text))


def message(update_id, chat_id, text):
    return {"update_id": update_id, "message": {"chat": {"id": chat_id}, "text": text}}


async def run_briefly(coro, seconds=0.2):
    task = asyncio.create_task(coro)
    await asyncio.sleep(seconds)
    task.cancel()


def test_unconfigured_bot_replies_with_chat_id():
    telegram = FakeTelegram([message(1, 555, "/start")])
    handler = CommandHandler(AlertStore(), MockFeed(), INDIA)
    asyncio.run(run_briefly(poll_commands(telegram, handler, chat_id="")))
    assert telegram.sent[0][0] == "555"
    assert "TELEGRAM_CHAT_ID=555" in telegram.sent[0][1]


def test_ignores_other_chats():
    telegram = FakeTelegram([message(1, 999, "/alert INFY above 1"), message(2, 555, "/list")])
    store = AlertStore()
    asyncio.run(run_briefly(poll_commands(telegram, CommandHandler(store, MockFeed(), INDIA), chat_id="555")))
    assert store.active() == []
    assert telegram.sent == [("555", "No active alerts.")]


def test_end_to_end_alert_triggers_telegram_message():
    store, feed = AlertStore(), MockFeed(interval=0.01, volatility=0)
    handler = CommandHandler(store, feed, INDIA)
    telegram = FakeTelegram(
        [message(1, 555, "/setprice INFY 1390"), message(2, 555, "/alert INFY above 1400")]
    )

    async def scenario():
        asyncio.create_task(poll_commands(telegram, handler, "555"))
        asyncio.create_task(watch_prices(feed, AlertChecker(store), telegram, "555"))
        await asyncio.sleep(0.1)
        assert not any("🔔" in text for _, text in telegram.sent)
        feed.set_price("NSE:INFY", 1401)
        await asyncio.sleep(0.1)

    asyncio.run(scenario())
    triggers = [text for _, text in telegram.sent if "🔔" in text]
    assert triggers == ["🔔 NSE:INFY is above ₹1,400.00\nLTP ₹1,401.00 (alert #1)"]


def test_formatter_redacts_token_in_message_and_traceback():
    formatter = RedactingFormatter("123:SECRET", "%(message)s")
    try:
        raise RuntimeError("GET https://api.telegram.org/bot123:SECRET/getUpdates")
    except RuntimeError:
        record = logging.LogRecord("x", logging.ERROR, "", 0, "url bot123:SECRET", None, sys.exc_info())
    text = formatter.format(record)
    assert "SECRET" not in text
    assert "bot***/getUpdates" in text
