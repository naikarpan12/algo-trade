from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    kite_api_key: str = ""
    kite_api_secret: str = ""
    kite_redirect_url: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    trading_mode: Literal["paper", "live"] = "paper"
    price_feed: Literal["mock", "kite"] = "mock"

    max_capital_per_trade: float = 10_000
    max_daily_loss: float = 2_000
    max_open_positions: int = 3

    database_url: str = "sqlite:///./data/algo.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
