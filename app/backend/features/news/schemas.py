"""News API schemas."""

from datetime import date

from pydantic import BaseModel

from core.models import ArticleItem


class NewsSearchQuery(BaseModel):
    stock_code: str
    stock_name: str | None = None
    base_date: date


class NewsSearchResponse(BaseModel):
    articles: list[ArticleItem]
    total: int
    cached: bool = False


class NewsRefreshRequest(BaseModel):
    stock_code: str
    stock_name: str | None = None
    base_date: date
