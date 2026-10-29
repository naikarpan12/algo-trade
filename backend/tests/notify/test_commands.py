from app.core.alerts import AlertStore
from app.feeds.mock import MockFeed
from app.markets import INDIA, US
from app.notify.commands import HELP, CommandHandler


def make_handler(market=INDIA):
    store = AlertStore()
    return CommandHandler(store, MockFeed(seed=1), market), store


def test_alert_command_creates_alert_and_subscribes():
    handler, store = make_handler()
    reply = handler.handle("/alert reliance above 3,000")
    assert reply.startswith("Alert set: #1 NSE:RELIANCE above ₹3,000.00")
    assert "Last price" in reply
    assert store.active()[0].level == 3000
    assert handler.feed.last_price("NSE:RELIANCE") is not None


def test_alert_command_with_bot_mention():
    handler, store = make_handler()
    handler.handle("/alert@tradeRSIautomated_bot INFY below 1400")
    assert store.active()[0].condition == "below"


def test_alert_command_rejects_bad_input():
    handler, store = make_handler()
    for text in ("/alert", "/alert INFY near 1400", "/alert INFY above abc", "/alert INFY above -5"):
        assert handler.handle(text).startswith("Usage")
    assert store.active() == []


def test_list_and_delete():
    handler, _ = make_handler()
    assert handler.handle("/list") == "No active alerts."
    handler.handle("/alert TCS above 4000")
    assert "#1 NSE:TCS above ₹4,000.00" in handler.handle("/list")
    assert handler.handle("/delete #1") == "Deleted alert #1."
    assert handler.handle("/delete 1") == "No alert #1."
    assert handler.handle("/delete x") == "Usage: /delete ID"


def test_price_and_setprice():
    handler, _ = make_handler()
    assert handler.handle("/setprice infy 1399.98") == "Mock price for NSE:INFY set to ₹1,400.00"
    assert handler.handle("/price INFY") == "NSE:INFY: ₹1,400.00"


def test_help_and_unknown():
    handler, _ = make_handler()
    assert handler.handle("/start") == HELP
    assert handler.handle("/foo").startswith("Unknown command.")


def test_us_symbols_use_dollars_and_cent_ticks():
    handler, store = make_handler()
    assert handler.handle("/alert us:tsla below 350.5").startswith("Alert set: #1 US:TSLA below $350.50")
    assert handler.handle("/setprice US:TSLA 351.234") == "Mock price for US:TSLA set to $351.23"


def test_default_market_us():
    handler, store = make_handler(US)
    handler.handle("/alert TSLA above 400")
    assert store.active()[0].symbol == "US:TSLA"


def test_bse_symbol_is_india():
    handler, _ = make_handler()
    assert handler.handle("/setprice bse:reliance 2999.98") == "Mock price for BSE:RELIANCE set to ₹3,000.00"


def test_unknown_exchange_is_explained():
    handler, store = make_handler()
    assert handler.handle("/alert LSE:BP above 5").startswith("Unknown exchange 'LSE'")
    assert store.active() == []


def test_clock_lists_both_markets():
    reply = make_handler()[0].handle("/clock")
    assert reply.startswith("NSE/BSE: ") and "\nNYSE/Nasdaq: " in reply
