"""타임라인 메가 내러티브 브리핑 테스트 (Phase 3). LLM은 fake 주입."""

from datetime import date

import pytest

from core.models import ArticleItem, CalendarEvent, MarketDigest
from features.briefing.schemas import BriefingRequest
from features.briefing.service import BriefingService
from features.briefing.timeline import get_profile
from services.llm.schemas import MarketBriefingJson
from storage.repositories import context as ctx_repo


class FakeLlm:
    def __init__(self):
        self.user_prompt = None

    async def generate_structured(self, system_prompt, user_prompt, schema):
        self.user_prompt = user_prompt
        assert schema is MarketBriefingJson
        return MarketBriefingJson(
            headline="반도체 주도 강세 지속",
            market_summary="외국인 순매수 유입",
            key_narratives=["AI 슈퍼사이클"],
            sector_highlights=["반도체"],
            watch_items=["다음 거래일 수급 지속 확인"],
            risks=["과열 가능성"],
            confidence="MEDIUM",
        )


def test_get_profile_invalid_raises():
    with pytest.raises(ValueError, match="Unknown timeline"):
        get_profile("LUNCH")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_close_briefing_assembles_context_and_news(db):
    ctx_repo.upsert_market_digest(
        db, MarketDigest(digest_date=date(2026, 6, 18), session="KR_DAY", title="강세", summary="반도체 주도")
    )
    ctx_repo.add_calendar_event(
        db, CalendarEvent(event_date=date(2026, 6, 20), title="FOMC", category="MACRO")
    )

    fake = FakeLlm()
    svc = BriefingService(llm=fake)
    req = BriefingRequest(
        base_date=date(2026, 6, 19),
        timeline="CLOSE",
        articles=[ArticleItem(title="증시 마감 특징주", url="https://x/1")],
    )
    resp = await svc.create_briefing(db, req)

    assert resp.briefing.timeline == "CLOSE"
    assert resp.briefing.label == "장 마감 종합 시황"
    assert resp.briefing.content.headline == "반도체 주도 강세 지속"
    assert set(resp.briefing.sources) == {"context", "news"}

    # 타임라인 관점 + 누적 맥락 + 뉴스가 프롬프트에 주입됐는지
    assert "장 마감 종합 시황" in fake.user_prompt
    assert "메가 내러티브 맥락" in fake.user_prompt
    assert "증시 마감 특징주" in fake.user_prompt


@pytest.mark.asyncio
async def test_premarket_profile_used(db):
    fake = FakeLlm()
    svc = BriefingService(llm=fake)
    resp = await svc.create_briefing(
        db, BriefingRequest(base_date=date(2026, 6, 19), timeline="PRE_MARKET")
    )
    assert resp.briefing.label == "장 시작 전 브리핑"
    assert resp.briefing.sources == ["context"]  # 뉴스 없음
