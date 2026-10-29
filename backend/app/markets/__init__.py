"""Market registry. Market folders never import each other; only this registry knows them all."""

from app.markets.base import Market
from app.markets.india import INDIA
from app.markets.us import US

MARKETS: dict[str, Market] = {INDIA.code: INDIA, US.code: US}
_BY_EXCHANGE = {exchange: market for market in MARKETS.values() for exchange in market.exchanges}


def get_market(code: str) -> Market:
    try:
        return MARKETS[code]
    except KeyError:
        raise ValueError(f"Unknown market {code!r}; use one of {', '.join(MARKETS)}") from None


def normalize_symbol(text: str, default: Market) -> str:
    """'reliance' -> 'NSE:RELIANCE' (default market); 'us:tsla' -> 'US:TSLA'."""
    symbol = text.strip().upper()
    if ":" not in symbol:
        return f"{default.exchanges[0]}:{symbol}"
    exchange, ticker = symbol.split(":", 1)
    if exchange not in _BY_EXCHANGE:
        raise ValueError(f"Unknown exchange {exchange!r}; use {', '.join(p + ':' for p in _BY_EXCHANGE)}")
    if not ticker:
        raise ValueError("Missing ticker after the exchange")
    return symbol


def market_for_symbol(symbol: str) -> Market:
    return _BY_EXCHANGE[symbol.split(":", 1)[0]]
