"""LLM provider protocol and factory."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from config import get_settings
from services.llm.model_registry import LlmRole, normalize_role
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


def get_llm_provider(role: LlmRole | str | None = None) -> LlmProvider:
    settings = get_settings()
    provider = (settings.llm_provider or "openai").lower().strip()
    role = normalize_role(role)

    if provider == "openai":
        from services.llm.openai_provider import OpenAiLlmProvider

        return OpenAiLlmProvider()
    if provider == "google":
        from services.llm.google_provider import GoogleLlmProvider

        return GoogleLlmProvider(role=role)
    if provider == "anthropic":
        from services.llm.google_provider import GoogleAdvancedLlmProvider

        return GoogleAdvancedLlmProvider()
    if provider == "openrouter":
        from services.llm.openrouter_provider import OpenRouterLlmProvider

        return OpenRouterLlmProvider(role=role)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


class _LlmAdapterProxy:
    """Backward-compatible module-level `llm_adapter` accessor."""

    def for_role(self, role: LlmRole | str) -> LlmProvider:
        return get_llm_provider(role)

    def __getattr__(self, name: str):
        return getattr(get_llm_provider(), name)


llm_adapter = _LlmAdapterProxy()
