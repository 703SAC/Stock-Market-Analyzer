"""News search orchestration."""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from core.models import ArticleItem, StockIdentity
from features.news.schemas import NewsRefreshRequest, NewsSearchQuery, NewsSearchResponse
from services.news.base import get_news_provider
from storage.repositories import news_cache as cache_repo


def _search_dates(base: date, days_back: int = 7) -> tuple[date, date]:
    """Include articles from (base - days_back) through base (inclusive)."""
    return base - timedelta(days=days_back), base


class NewsService:
    async def search(
        self, db: Session, query: NewsSearchQuery, force_refresh: bool = False
    ) -> NewsSearchResponse:
        key = cache_repo.cache_key(query.stock_code, query.base_date.isoformat())
        if not force_refresh:
            cached = cache_repo.get_cached(db, key)
            if cached:
                articles = [ArticleItem.model_validate(a) for a in cached]
                return NewsSearchResponse(articles=articles, total=len(articles), cached=True)

        provider = get_news_provider()
        name = query.stock_name or query.stock_code
        date_from, date_to = _search_dates(query.base_date)
        raw = await provider.search(
            stock=StockIdentity(code=query.stock_code, name=name),
            date_from=date_from,
            date_to=date_to,
        )
        articles = self._dedupe(raw)
        if articles:
            cache_repo.set_cached(
                db, key, [a.model_dump(mode="json") for a in articles]
            )
        return NewsSearchResponse(articles=articles, total=len(articles), cached=False)

    async def refresh(self, db: Session, body: NewsRefreshRequest) -> NewsSearchResponse:
        query = NewsSearchQuery(
            stock_code=body.stock_code,
            stock_name=body.stock_name,
            base_date=body.base_date,
        )
        return await self.search(db, query, force_refresh=True)

    def _dedupe(self, articles: list[ArticleItem]) -> list[ArticleItem]:
        seen: set[str] = set()
        result: list[ArticleItem] = []
        for i, article in enumerate(articles):
            if article.url in seen:
                continue
            seen.add(article.url)
            article.id = article.id or f"article_{i}"
            result.append(article)
        return sorted(
            result,
            key=lambda a: a.published_at or datetime.min,
            reverse=True,
        )


news_service = NewsService()
