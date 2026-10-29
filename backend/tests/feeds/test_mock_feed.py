from app.feeds.mock import MockFeed, round_to_tick


def test_round_to_tick():
    assert round_to_tick(100.02, 0.05) == 100.0
    assert round_to_tick(100.03, 0.05) == 100.05
    assert round_to_tick(100.034, 0.01) == 100.03


def test_base_price_is_stable_per_symbol():
    first, second = MockFeed(), MockFeed()
    first.subscribe(["NSE:INFY"])
    second.subscribe(["NSE:INFY"])
    assert first.last_price("NSE:INFY") == second.last_price("NSE:INFY")


def test_step_moves_prices_on_tick_grid():
    feed = MockFeed(seed=42, volatility=0.01)
    feed.subscribe(["NSE:INFY", "NSE:TCS"])
    for _ in range(50):
        for symbol, price in feed.step():
            assert price > 0
            assert abs(price * 20 - round(price * 20)) < 1e-6


def test_set_price_overrides_walk():
    feed = MockFeed()
    feed.set_price("NSE:INFY", 1500)
    assert feed.last_price("NSE:INFY") == 1500
