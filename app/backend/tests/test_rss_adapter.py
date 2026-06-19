"""RSS 어댑터 테스트 (Phase 3). feedparser 없이 parse_fn 주입으로 검증."""

from datetime import date
from types import SimpleNamespace

import pytest

from core.models import StockIdentity
from services.news.extractor import ArticleExtractor
from services.news.rss_adapter import RssNewsAdapter


def _feed(entries):
    return SimpleNamespace(entries=entries)


def _entry(link, title, ymd, summary="요약", author="연합뉴스"):
    return {
        "link": link,
        "title": title,
        "summary": summary,
        "author": author,
        "published_parsed": (*ymd, 9, 0, 0, 0, 0, 0),
    }


@pytest.mark.asyncio
async def test_date_filter_and_dedupe():
    entries = [
        _entry("https://n/1", "기사1", (2026, 6, 18)),
        _entry("https://n/2", "기사2(범위밖)", (2026, 5, 1)),
        _entry("https://n/1", "기사1(중복링크)", (2026, 6, 18)),
    ]
    adapter = RssNewsAdapter(feeds=["f1"], parse_fn=lambda url: _feed(entries))
    out = await adapter.search(
        StockIdentity(code="000000"), date_from=date(2026, 6, 15), date_to=date(2026, 6, 20)
    )
    assert [a.title for a in out] == ["기사1"]
    assert out[0].publisher == "연합뉴스"


@pytest.mark.asyncio
async def test_parse_failure_yields_empty():
    adapter = RssNewsAdapter(feeds=["f1"], parse_fn=lambda url: None)
    out = await adapter.search(
        StockIdentity(code="000000"), date_from=date(2026, 6, 1), date_to=date(2026, 6, 30)
    )
    assert out == []


@pytest.mark.asyncio
async def test_enrich_body_replaces_summary():
    entries = [_entry("https://n/1", "기사1", (2026, 6, 18))]
    extractor = ArticleExtractor(
        fetch_fn=lambda url: "html", extract_fn=lambda h: "추출된 본문 전문"
    )
    adapter = RssNewsAdapter(
        feeds=["f1"],
        parse_fn=lambda url: _feed(entries),
        extractor=extractor,
        enrich_body=True,
    )
    out = await adapter.search(
        StockIdentity(code="000000"), date_from=date(2026, 6, 15), date_to=date(2026, 6, 20)
    )
    assert out[0].summary == "추출된 본문 전문"
