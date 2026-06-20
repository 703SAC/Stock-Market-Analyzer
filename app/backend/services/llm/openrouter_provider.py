"""OpenRouter LLM provider with role-based model routing."""

from __future__ import annotations

import json

import httpx
from pydantic import BaseModel

from config import get_settings
from services.llm.base import LlmProvider
from services.llm.model_registry import LlmRole, model_for_role, normalize_role


class OpenRouterLlmProvider(LlmProvider):
    def __init__(self, role: LlmRole | str | None = None, client: httpx.AsyncClient | None = None):
        settings = get_settings()
        self._role = normalize_role(role)
        self._model = model_for_role(self._role, "openrouter", settings)
        self._api_key = settings.openrouter_api_key
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._client = client

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def role(self) -> LlmRole:
        return self._role

    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> BaseModel:
        if not self.is_configured:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt + "\nReturn ONLY valid JSON matching the schema.",
                },
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": schema.model_json_schema(),
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost/stock-market-analyzer",
            "X-Title": "Stock Market Analyzer",
        }

        client = self._client or httpx.AsyncClient(timeout=45.0)
        own_client = self._client is None
        last_error: Exception | None = None
        try:
            for _ in range(2):
                try:
                    response = await client.post(
                        f"{self._base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    body = response.json()
                    content = body["choices"][0]["message"].get("content") or "{}"
                    return schema.model_validate(json.loads(content))
                except Exception as exc:
                    last_error = exc
            raise RuntimeError(f"OpenRouter response validation failed: {last_error}")
        finally:
            if own_client:
                await client.aclose()
