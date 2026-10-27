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
| 1 | Telegram threshold alerts on a mock price feed | ✅ |
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
2. The price feed streams ticks. An alert fires on the **first tick that meets its condition** (`above` means LTP ≥ level, `below` means LTP ≤ level). If the price already meets the condition when you set the alert, it fires on the next tick.
3. Telegram message: *"🔔 NSE:INFY is below ₹1,400.00 / LTP ₹1,398.60"*. The alert is then marked triggered and never repeats, so there is no spam. Re-arming after a cooldown can come later.

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
    alerts_bot.py  Telegram alert bot (entry point)
    config.py      settings loaded from .env
    kite/          login, ticker, orders, GTT
    engine/        alerts; later rules, indicators, risk, paper broker
    feeds/         price feeds (mock now, Kite later)
    notify/        Telegram client and command handling
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

## Try the Telegram alert bot (mock prices)

1. Put your bot token in `.env` as `TELEGRAM_BOT_TOKEN=...`.
2. `cd backend && python -m app.alerts_bot`
3. Send `/start` to the bot. Because `TELEGRAM_CHAT_ID` is empty, it replies with your chat id.
4. Put `TELEGRAM_CHAT_ID=<that id>` in `.env` and restart. From then on, the bot answers only your chat.
5. Test an alert:
   ```
   /setprice INFY 1390        # move the fake price
   /alert INFY above 1400
   /setprice INFY 1401        # 🔔 alert fires on Telegram
   ```

| Command | What it does |
|---|---|
| `/alert SYMBOL above\|below PRICE` | Create an alert (`RELIANCE` means `NSE:RELIANCE`; use `BSE:XYZ` for BSE) |
| `/list` | Active alerts |
| `/delete ID` | Remove an alert |
| `/price SYMBOL` | Last price from the feed |
| `/setprice SYMBOL PRICE` | Mock feed only: move the fake price to test triggers |

Mock prices are made up, starting from a fixed per-symbol value and then a random walk. They are **not** market prices. Alerts are stored in `backend/data/algo.db` and survive restarts.

## Running costs (estimate)

- Kite Connect: ₹500/month (check whether GST is extra)
- Small Mumbai-region VM with a static IP: about ₹500–800/month
- Telegram: free
