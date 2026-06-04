"""Naver Search API news adapter."""

from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from config import get_settings
from core.models import ArticleItem, StockIdentity
from services.news.base import NewsProvider
from services.news.errors import NewsProviderError

NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
TIMEOUT = 15.0


def _parse_pub_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def _in_date_range(dt: datetime | None, date_from: date, date_to: date) -> bool:
    if dt is None:
        return True
    d = dt.date()
    return date_from <= d <= date_to


class NaverNewsAdapter(NewsProvider):
    def __init__(self):
        settings = get_settings()
        self._client_id = settings.naver_client_id
        self._client_secret = settings.naver_client_secret

    @property
    def is_configured(self) -> bool:
        return bool(self._client_id and self._client_secret)

    async def search(
        self,
        stock: StockIdentity,
        date_from: date,
        date_to: date,
    ) -> list[ArticleItem]:
        if not self.is_configured:
            raise NewsProviderError(
                "Naver API keys are missing. Set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET in .env",
                status_code=503,
            )

        name = stock.name or stock.code
        queries = [
            f"{name} 주가",
            f"{name} 실적",
            f"{name} 공시",
        ]
        articles: list[ArticleItem] = []
        headers = {
            "X-Naver-Client-Id": self._client_id,
            "X-Naver-Client-Secret": self._client_secret,
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for q in queries:
                resp = await client.get(
                    NAVER_NEWS_URL,
                    headers=headers,
                    params={"query": q, "display": 20, "sort": "date"},
                )
                if resp.status_code == 401:
                    raise NewsProviderError(
                        "Naver API authentication failed (401). "
                        "Check NAVER_CLIENT_ID / NAVER_CLIENT_SECRET in workspace .env "
                        "and enable '검색' API in Naver Developers console.",
                        status_code=401,
                    )
                if resp.status_code >= 400:
                    raise NewsProviderError(
                        f"Naver API error (HTTP {resp.status_code}).",
                        status_code=502,
                    )
                for item in resp.json().get("items", []):
                    pub = _parse_pub_date(item.get("pubDate"))
                    if not _in_date_range(pub, date_from, date_to):
                        continue
                    title = (
                        item.get("title", "")
                        .replace("<b>", "")
                        .replace("</b>", "")
                    )
                    desc = (
                        item.get("description", "")
                        .replace("<b>", "")
                        .replace("</b>", "")
                    )
                    articles.append(
                        ArticleItem(
                            title=title,
                            url=item.get("link", ""),
                            publisher=item.get("originallink") or None,
                            published_at=pub,
                            summary=desc,
                        )
                    )
        return articles
