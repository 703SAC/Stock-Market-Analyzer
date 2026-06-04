"""Telegram notification adapter stub (Sprint 9)."""

from config import get_settings


async def send_message(text: str) -> dict[str, str]:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return {"status": "not_configured", "message": "Telegram env vars missing"}
    raise NotImplementedError("Telegram alerts are planned for Sprint 9.")
