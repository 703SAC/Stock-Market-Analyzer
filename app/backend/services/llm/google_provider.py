"""Google AI Studio (Gemini API) LLM provider."""

from __future__ import annotations

import asyncio
import json

from google import genai
from google.genai import types
from pydantic import BaseModel

from config import get_settings
from services.llm.base import LlmProvider


class GoogleLlmProvider(LlmProvider):
    def __init__(self):
        settings = get_settings()
        self._model = settings.llm_model_resolved
        self._client = (
            genai.Client(api_key=settings.google_api_key)
            if settings.google_api_key
            else None
        )

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    @property
    def model_name(self) -> str:
        return self._model

    def _generate_sync(
        self, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.3,
            ),
        )
        return response.text or "{}"

    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> BaseModel:
        if not self.is_configured:
            raise RuntimeError("GOOGLE_API_KEY is not configured")

        last_error: Exception | None = None
        for _ in range(2):
            try:
                text = await asyncio.to_thread(
                    self._generate_sync, system_prompt, user_prompt, schema
                )
                return schema.model_validate(json.loads(text))
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"Gemini response validation failed: {last_error}")
