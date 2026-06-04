"""LLM provider protocol and factory."""

from abc import ABC, abstractmethod

from config import get_settings
from services.llm.schemas import NewsPriceReportJson


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
    async def generate_news_price_report(
        self, system_prompt: str, user_prompt: str
    ) -> NewsPriceReportJson:
        ...


def get_llm_provider() -> LlmProvider:
    settings = get_settings()
    provider = (settings.llm_provider or "openai").lower().strip()

    if provider == "openai":
        from services.llm.openai_provider import OpenAiLlmProvider

        return OpenAiLlmProvider()
    if provider == "google":
        from services.llm.google_provider import GoogleLlmProvider

        return GoogleLlmProvider()
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


class _LlmAdapterProxy:
    """Backward-compatible module-level `llm_adapter` accessor."""

    def __getattr__(self, name: str):
        return getattr(get_llm_provider(), name)


llm_adapter = _LlmAdapterProxy()
