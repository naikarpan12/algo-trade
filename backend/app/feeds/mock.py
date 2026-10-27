"""Fake random-walk prices for development without a Kite data subscription."""

import asyncio
import random
import zlib
from collections.abc import AsyncIterator, Iterable

TICK_SIZE = 0.05


def round_to_tick(price: float) -> float:
    return round(round(price / TICK_SIZE) * TICK_SIZE, 2)


class MockFeed:
    def __init__(self, interval: float = 1.0, volatility: float = 0.001, seed: int | None = None):
        self.interval = interval
        self.volatility = volatility
        self._rng = random.Random(seed)
        self._prices: dict[str, float] = {}

    @staticmethod
    def _base_price(symbol: str) -> float:
        # Stable per symbol so restarts start from the same made-up price.
        return round_to_tick(100 + zlib.crc32(symbol.encode()) % 2900)

    def subscribe(self, symbols: Iterable[str]) -> None:
        for symbol in symbols:
            self._prices.setdefault(symbol, self._base_price(symbol))

    def last_price(self, symbol: str) -> float | None:
        return self._prices.get(symbol)

    def set_price(self, symbol: str, price: float) -> None:
        self._prices[symbol] = round_to_tick(price)

    def step(self) -> list[tuple[str, float]]:
        for symbol, price in self._prices.items():
            move = price * self._rng.gauss(0, self.volatility)
            self._prices[symbol] = max(TICK_SIZE, round_to_tick(price + move))
        return list(self._prices.items())

    async def ticks(self) -> AsyncIterator[tuple[str, float]]:
        while True:
            for tick in self.step():
                yield tick
            await asyncio.sleep(self.interval)
