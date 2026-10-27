"""Price threshold alerts: storage and evaluation against live ticks."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

Condition = Literal["above", "below"]
CONDITIONS: tuple[Condition, ...] = ("above", "below")


@dataclass
class Alert:
    id: int
    symbol: str
    condition: Condition
    level: float
    status: Literal["active", "triggered"]
    created_at: str
    triggered_at: str | None = None
    triggered_price: float | None = None

    def describe(self) -> str:
        return f"#{self.id} {self.symbol} {self.condition} ₹{self.level:,.2f}"


def is_met(condition: Condition, level: float, price: float) -> bool:
    return price >= level if condition == "above" else price <= level


def normalize_symbol(symbol: str) -> str:
    """'reliance' -> 'NSE:RELIANCE'; an explicit exchange prefix is kept."""
    symbol = symbol.strip().upper()
    return symbol if ":" in symbol else f"NSE:{symbol}"


def sqlite_path(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError(f"Only sqlite URLs are supported, got {database_url!r}")
    path = database_url[len(prefix):]
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AlertStore:
    def __init__(self, path: str = ":memory:"):
        self._db = sqlite3.connect(path)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                condition TEXT NOT NULL,
                level REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                triggered_at TEXT,
                triggered_price REAL
            )
            """
        )
        self._db.commit()

    def add(self, symbol: str, condition: Condition, level: float) -> Alert:
        if condition not in CONDITIONS:
            raise ValueError(f"condition must be one of {CONDITIONS}")
        cursor = self._db.execute(
            "INSERT INTO alerts (symbol, condition, level, created_at) VALUES (?, ?, ?, ?)",
            (normalize_symbol(symbol), condition, level, _now()),
        )
        self._db.commit()
        return self.get(cursor.lastrowid)

    def get(self, alert_id: int) -> Alert | None:
        row = self._db.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        return Alert(**dict(row)) if row else None

    def active(self, symbol: str | None = None) -> list[Alert]:
        query, params = "SELECT * FROM alerts WHERE status = 'active'", ()
        if symbol:
            query, params = query + " AND symbol = ?", (symbol,)
        rows = self._db.execute(query + " ORDER BY id", params).fetchall()
        return [Alert(**dict(row)) for row in rows]

    def active_symbols(self) -> set[str]:
        return {alert.symbol for alert in self.active()}

    def delete(self, alert_id: int) -> bool:
        cursor = self._db.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        self._db.commit()
        return cursor.rowcount > 0

    def mark_triggered(self, alert_id: int, price: float) -> None:
        self._db.execute(
            "UPDATE alerts SET status = 'triggered', triggered_at = ?, triggered_price = ? WHERE id = ?",
            (_now(), price, alert_id),
        )
        self._db.commit()


class AlertChecker:
    """Fires each active alert once, on the first tick that meets its condition."""

    def __init__(self, store: AlertStore):
        self.store = store

    def on_tick(self, symbol: str, price: float) -> list[Alert]:
        fired = []
        for alert in self.store.active(symbol):
            if is_met(alert.condition, alert.level, price):
                self.store.mark_triggered(alert.id, price)
                fired.append(self.store.get(alert.id))
        return fired
