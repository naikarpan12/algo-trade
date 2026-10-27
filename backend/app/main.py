from fastapi import FastAPI

from app.config import get_settings

app = FastAPI(title="algo-trade")


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "trading_mode": settings.trading_mode,
        "price_feed": settings.price_feed,
    }
