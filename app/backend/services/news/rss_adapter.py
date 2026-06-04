"""RSS + trafilatura adapter stub for future international markets."""

from datetime import date

from core.models import ArticleItem, StockIdentity
from services.news.base import NewsProvider


class RssNewsAdapter(NewsProvider):
    """Not implemented in MVP — extension slot for overseas RSS feeds."""

    async def search(
        self,
        stock: StockIdentity,
        date_from: date,
        date_to: date,
    ) -> list[ArticleItem]:
        raise NotImplementedError(
            "RSS news provider is reserved for future overseas market expansion."
        )
