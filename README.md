# algo-trade

Personal trading automation on **Zerodha Kite Connect**:

- **Price alerts on Telegram:** set a threshold (`/alert RELIANCE above 3000`) and get a Telegram message when it's crossed.
- **Criteria-based trading:** define entry/exit rules (price, indicators, volume, time windows). The engine evaluates them on live data and places orders, in paper mode first and live later.
- **UI (later):** a dashboard for alerts, strategies, positions, P&L and a kill switch.

> For my own account only. This is not investment advice and not a service for clients.

---

## Status

| Phase | What | Status |
|---|---|---|
| 0 | Project skeleton, config, health endpoint | ✅ |
| 1 | Telegram threshold alerts on a mock price feed | ⏳ next |
| 2 | Live prices from Kite WebSocket + daily login flow | ⏳ |
| 3 | JSON rule engine + paper trading + backtest | ⏳ |
| 4 | Semi-auto: engine proposes a trade, I approve on Telegram | ⏳ |
| 5 | Full auto with risk limits | ⏳ |
| 6 | Web UI | ⏳ |

Each phase is built on its own `feature/*` branch and merged into `main` through a pull request.

---

## Kite Connect: what we use

| Area | Used for | Kite plan |
|---|---|---|
| Login / session | Daily `access_token` (expires every morning) | Personal (free) / Connect |
| Orders | Place, modify and cancel orders: market, limit, SL; CNC, MIS, NRML | Free |
| GTT | Server-side triggers held by Zerodha (e.g. OCO target + stop-loss) | Free |
| Portfolio | Holdings, positions, margins, order history | Free |
| Live prices | WebSocket ticker (LTP, depth, OHLC), `quote`/`ltp` | **Connect, ₹500/month** |
| Historical candles | Seed indicators (RSI, SMA, …) and backtests | **Connect, ₹500/month** |
| Postbacks | Webhook when an order fills or is rejected | Both |

The free plan can trade but cannot see prices. Telegram alerts and the rule engine need the paid Connect plan for live data. Until then, development runs on a **mock price feed** (`PRICE_FEED=mock`).

## Regulatory constraints (SEBI retail algo framework, in force from April 2026)

- **Static IP:** API orders are accepted only from a whitelisted static IP mapped to the API key, so the engine runs on a cloud VM with a fixed IP, not a laptop.
- **Daily 2FA:** Zerodha login is needed once per trading day, with no long-lived refresh tokens. The bot sends a login link on Telegram each morning; I tap it and log in, and the engine is armed for the day. TOTP login is **not** automated.
- **At most 10 orders/second:** below this, no exchange registration is needed for a personal algo.
- Verify the exact setup on the Kite developer console before going live.

---

## Architecture

```
Telegram (me) ──commands──►  FastAPI backend  ◄── Kite login callback
                                   │
                    ┌──────────────┼───────────────┐
                    ▼              ▼               ▼
              Alerts store   Strategies store   Orders / trades log
                    │              │
Price feed ──ticks──►  Rule engine ──► Risk checks ──► Broker (paper | Kite)
(mock | Kite WS)          │                                │
                          └──────── Telegram notifications ◄┘
```

### Alert flow
1. `/alert INFY below 1400` → saved as an active alert.
2. The price feed streams ticks; the checker fires only on a **cross** (previous tick above the level, current tick at or below it), so there is no spam on every tick.
3. Telegram message: *"INFY crossed below ₹1400 (LTP 1398.6)"*. The alert is then disabled, or re-armed after a cooldown.

### Strategy format (planned)
```json
{
  "name": "RSI dip buy",
  "symbol": "NSE:HDFCBANK",
  "timeframe": "15minute",
  "entry": { "all": [ {"rsi_14": {"lt": 30}}, {"price": {"above": "sma_200"}} ] },
  "exit":  { "any": [ {"target_pct": 3}, {"stoploss_pct": 1.5}, {"rsi_14": {"gt": 70}} ] },
  "order": { "qty": 5, "product": "CNC", "type": "LIMIT" },
  "mode": "paper"
}
```

### Risk guardrails (always on)
- Maximum capital per trade, maximum open positions, daily loss limit (pauses everything)
- Global kill switch (`/killswitch`) and a per-strategy on/off toggle
- No duplicate entries; every live entry has a stop-loss
- Intraday (MIS) positions squared off by 15:15

---

## Layout

```
backend/
  app/
    main.py        FastAPI app
    config.py      settings loaded from .env
    kite/          login, ticker, orders, GTT
    engine/        rules, indicators, risk, paper broker
    notify/        Telegram bot
  tests/
ui/                dashboard (later)
```

## Running locally

```bash
cp .env.example .env          # fill in values; .env is git-ignored
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload # http://localhost:8000/health
pytest
```

## Running costs (estimate)

- Kite Connect: ₹500/month (check whether GST is extra)
- Small Mumbai-region VM with a static IP: about ₹500–800/month
- Telegram: free
