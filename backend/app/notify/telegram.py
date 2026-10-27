"""Minimal Telegram Bot API client (long polling)."""

import httpx


class TelegramClient:
    def __init__(self, token: str):
        self._http = httpx.AsyncClient(base_url=f"https://api.telegram.org/bot{token}/", timeout=40)

    async def send_message(self, chat_id: str | int, text: str) -> None:
        response = await self._http.post("sendMessage", json={"chat_id": chat_id, "text": text})
        response.raise_for_status()

    async def get_updates(self, offset: int | None = None, timeout: int = 30) -> list[dict]:
        params = {"timeout": timeout, "allowed_updates": '["message"]'}
        if offset is not None:
            params["offset"] = offset
        response = await self._http.get("getUpdates", params=params)
        response.raise_for_status()
        return response.json()["result"]

    async def close(self) -> None:
        await self._http.aclose()
