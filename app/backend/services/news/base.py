"""News provider protocol."""

from abc import ABC, abstractmethod
from datetime import date

from config import get_settings
from core.models import ArticleItem, StockIdentity


class NewsProvider(ABC):
    @abstractmethod
    async def search(
        self,
        stock: StockIdentity,
        date_from: date,
        date_to: date,
    ) -> list[ArticleItem]:
        ...


def get_news_provider() -> NewsProvider:
    settings = get_settings()
    if settings.news_provider == "naver":
        from services.news.naver_adapter import NaverNewsAdapter

        return NaverNewsAdapter()
    raise ValueError(f"Unsupported news provider: {settings.news_provider}")
