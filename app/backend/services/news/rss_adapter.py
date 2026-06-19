"""RSS + Trafilatura 뉴스 어댑터.

시장 판단 에이전트용 종합 시황 소스. 종목 한정이 아니라 시장 전반 피드(경제/증시)를
수집하므로 NaverNewsAdapter(종목 검색)와 상호보완적이다.

원칙: feedparser는 지연 import(선택적 의존성). parse_fn 주입으로 네트워크 없이 테스트.
본문 추출은 ArticleExtractor에 위임하며 실패해도 제목/요약만으로 진행한다.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Callable

from core.models import ArticleItem, StockIdentity
from services.news.base import NewsProvider
from services.news.extractor import ArticleExtractor

# 시장 전반 한국어 경제/증시 RSS (무료). 운영 시 config로 분리 가능.
DEFAULT_FEEDS = [
    "https://www.yna.co.kr/rss/economy.xml",
    "https://www.yna.co.kr/rss/market.xml",
]


class RssNewsAdapter(NewsProvider):
    def __init__(
        self,
        feeds: list[str] | None = None,
        parse_fn: Callable[[str], object] | None = None,
        extractor: ArticleExtractor | None = None,
        enrich_body: bool = False,
    ):
        self._feeds = feeds if feeds is not None else list(DEFAULT_FEEDS)
        self._parse_fn = parse_fn
        self._extractor = extractor
        self._enrich_body = enrich_body

    def _lazy_parse(self, url: str):
        if self._parse_fn is not None:
            return self._parse_fn(url)
        try:
            import feedparser  # noqa: PLC0415

            return feedparser.parse(url)
        except Exception:
            return None

    @staticmethod
    def _entry_dt(entry) -> datetime | None:
        st = getattr(entry, "published_parsed", None) or (
            entry.get("published_parsed") if isinstance(entry, dict) else None
        )
        if st is None:
            return None
        try:
            return datetime(*st[:6], tzinfo=timezone.utc)
        except Exception:
            return None

    @staticmethod
    def _get(entry, key: str) -> str | None:
        if isinstance(entry, dict):
            val = entry.get(key)
        else:
            val = getattr(entry, key, None)
        return str(val) if val else None

    async def search(
        self,
        stock: StockIdentity,
        date_from: date,
        date_to: date,
    ) -> list[ArticleItem]:
        out: list[ArticleItem] = []
        seen: set[str] = set()
        for feed_url in self._feeds:
            parsed = self._lazy_parse(feed_url)
            if parsed is None:
                continue
            entries = getattr(parsed, "entries", None)
            if entries is None and isinstance(parsed, dict):
                entries = parsed.get("entries", [])
            for entry in entries or []:
                link = self._get(entry, "link")
                title = self._get(entry, "title")
                if not link or not title or link in seen:
                    continue
                published = self._entry_dt(entry)
                if published is not None:
                    d = published.date()
                    if d < date_from or d > date_to:
                        continue
                seen.add(link)
                summary = self._get(entry, "summary")
                if self._enrich_body and self._extractor is not None:
                    body = self._extractor.extract(link)
                    if body:
                        summary = body
                out.append(
                    ArticleItem(
                        title=title,
                        url=link,
                        publisher=self._get(entry, "author"),
                        published_at=published,
                        summary=summary,
                    )
                )
        return out
