import pytest

from app.markets import INDIA, US, get_market, market_for_symbol, normalize_symbol


def test_normalize_uses_default_market():
    assert normalize_symbol(" reliance ", INDIA) == "NSE:RELIANCE"
    assert normalize_symbol("tsla", US) == "US:TSLA"


def test_explicit_exchange_wins():
    assert normalize_symbol("bse:tcs", US) == "BSE:TCS"
    assert normalize_symbol("us:aapl", INDIA) == "US:AAPL"


def test_rejects_unknown_exchange_and_empty_ticker():
    with pytest.raises(ValueError, match="Unknown exchange 'LSE'"):
        normalize_symbol("LSE:BP", INDIA)
    with pytest.raises(ValueError, match="Missing ticker"):
        normalize_symbol("NSE:", INDIA)


def test_market_for_symbol():
    assert market_for_symbol("NSE:INFY") is INDIA
    assert market_for_symbol("BSE:INFY") is INDIA
    assert market_for_symbol("US:TSLA") is US


def test_get_market():
    assert get_market("india") is INDIA
    with pytest.raises(ValueError):
        get_market("japan")


def test_market_folders_do_not_import_each_other():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "app" / "markets"
    for market, other in (("india", "us"), ("us", "india")):
        for path in (root / market).rglob("*.py"):
            assert f"app.markets.{other}" not in path.read_text(), path
