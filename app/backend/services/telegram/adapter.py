"""Telegram 알림 어댑터 (모니터링 에이전트용).

원칙(IMPLEMENTATION_PROMPT_PLAN §5.3/5.5): timeout/retry, 중복 알림 방지.
httpx 클라이언트와 시계(clock)는 주입 가능 → 네트워크 없이 테스트.
미설정(env 없음) 시 예외 대신 status=not_configured 반환.
"""

from __future__ import annotations

import asyncio
import time as _time
from typing import Callable

import httpx

from config import get_settings

_API = "https://api.telegram.org/bot{token}/sendMessage"


class Deduplicator:
    """TTL 기반 중복 키 억제. 같은 키는 ttl 동안 1회만 통과."""

    def __init__(self, ttl_seconds: float = 3600, clock: Callable[[], float] | None = None):
        self._ttl = ttl_seconds
        self._clock = clock or _time.monotonic
        self._seen: dict[str, float] = {}

    def should_send(self, key: str) -> bool:
        now = self._clock()
        expired = [k for k, t in self._seen.items() if now - t > self._ttl]
        for k in expired:
            del self._seen[k]
        if key in self._seen:
            return False
        self._seen[key] = now
        return True


class TelegramNotifier:
    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
        client: httpx.AsyncClient | None = None,
        deduper: Deduplicator | None = None,
    ):
        settings = get_settings()
        self._token = token if token is not None else settings.telegram_bot_token
        self._chat_id = chat_id if chat_id is not None else settings.telegram_chat_id
        self._client = client
        self._dedup = deduper or Deduplicator()

    @property
    def is_configured(self) -> bool:
        return bool(self._token and self._chat_id)

    async def send(self, text: str, dedupe_key: str | None = None) -> dict:
        if not self.is_configured:
            return {"status": "not_configured", "message": "Telegram env vars missing"}
        if dedupe_key is not None and not self._dedup.should_send(dedupe_key):
            return {"status": "skipped_duplicate", "key": dedupe_key}

        url = _API.format(token=self._token)
        payload = {"chat_id": self._chat_id, "text": text}

        client = self._client or httpx.AsyncClient(timeout=10.0)
        own_client = self._client is None
        last_error: Exception | None = None
        try:
            for _ in range(2):
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        return {"status": "sent", "code": 200}
                    last_error = RuntimeError(f"HTTP {resp.status_code}")
                except Exception as exc:
                    last_error = exc
            return {"status": "error", "message": str(last_error)}
        finally:
            if own_client:
                await client.aclose()


_default_notifier: TelegramNotifier | None = None


def get_notifier() -> TelegramNotifier:
    global _default_notifier
    if _default_notifier is None:
        _default_notifier = TelegramNotifier()
    return _default_notifier


async def send_message(text: str, dedupe_key: str | None = None) -> dict:
    """모듈 레벨 호환 헬퍼."""
    return await get_notifier().send(text, dedupe_key=dedupe_key)
