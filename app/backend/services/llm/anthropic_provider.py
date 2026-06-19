"""Anthropic (Claude) LLM provider — 고차원 인사이트용 스위칭 자리.

비용 0원 원칙상 기본 provider는 Gemini(google)이며, 이 provider는 LLM_PROVIDER=anthropic +
ANTHROPIC_API_KEY가 설정됐을 때만 활성화된다(opt-in). anthropic SDK는 지연 import.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from config import get_settings
from services.llm.base import LlmProvider


class ClaudeLlmProvider(LlmProvider):
    def __init__(self):
        settings = get_settings()
        self._model = settings.llm_model_resolved
        self._api_key = settings.anthropic_api_key
        self._client = None
        if self._api_key:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(api_key=self._api_key)
            except Exception:
                self._client = None

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    @property
    def model_name(self) -> str:
        return self._model

    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> BaseModel:
        if not self.is_configured:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not configured "
                "(Claude provider is a reserved opt-in seat; default is Gemini)"
            )
        last_error: Exception | None = None
        for _ in range(2):
            try:
                resp = await self._client.messages.create(
                    model=self._model,
                    max_tokens=2048,
                    temperature=0.3,
                    system=system_prompt + "\nReturn ONLY valid JSON, no prose.",
                    messages=[{"role": "user", "content": user_prompt}],
                )
                text = "".join(getattr(b, "text", "") for b in resp.content) or "{}"
                return schema.model_validate(json.loads(text))
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"Claude response validation failed: {last_error}")
