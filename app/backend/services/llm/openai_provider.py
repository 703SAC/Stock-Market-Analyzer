"""OpenAI LLM provider."""

import json

from openai import AsyncOpenAI

from config import get_settings
from services.llm.base import LlmProvider
from services.llm.schemas import NewsPriceReportJson


class OpenAiLlmProvider(LlmProvider):
    def __init__(self):
        settings = get_settings()
        self._model = settings.llm_model_resolved
        self._client = (
            AsyncOpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    @property
    def model_name(self) -> str:
        return self._model

    async def generate_news_price_report(
        self, system_prompt: str, user_prompt: str
    ) -> NewsPriceReportJson:
        if not self.is_configured:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        last_error: Exception | None = None
        for _ in range(2):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                )
                content = response.choices[0].message.content or "{}"
                data = json.loads(content)
                return NewsPriceReportJson.model_validate(data)
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"LLM response validation failed: {last_error}")
