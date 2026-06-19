"""LLM provider protocol and factory."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from config import get_settings
from services.llm.schemas import NewsPriceReportJson

T = TypeVar("T", bound=BaseModel)


class LlmProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @abstractmethod
    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: type[T]
    ) -> T:
        """JSON Schema(Pydantic 모델)로 강제된 구조화 출력 생성. 환각 방지 핵심."""
        ...

    async def generate_news_price_report(
        self, system_prompt: str, user_prompt: str
    ) -> NewsPriceReportJson:
        return await self.generate_structured(
            system_prompt, user_prompt, NewsPriceReportJson
        )


def get_llm_provider() -> LlmProvider:
    settings = get_settings()
    provider = (settings.llm_provider or "openai").lower().strip()

    if provider == "openai":
        from services.llm.openai_provider import OpenAiLlmProvider

        return OpenAiLlmProvider()
    if provider == "google":
        from services.llm.google_provider import GoogleLlmProvider

        return GoogleLlmProvider()
    if provider == "anthropic":
        from services.llm.anthropic_provider import ClaudeLlmProvider

        return ClaudeLlmProvider()
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


class _LlmAdapterProxy:
    """Backward-compatible module-level `llm_adapter` accessor."""

    def __getattr__(self, name: str):
        return getattr(get_llm_provider(), name)


llm_adapter = _LlmAdapterProxy()
