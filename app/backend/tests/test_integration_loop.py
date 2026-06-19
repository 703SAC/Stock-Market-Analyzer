"""통합 E2E (Phase 5): 모니터링이 쓴 종합시황을 익일 시장판단이 읽는 루프 검증.

세 에이전트의 유기적 연동(맥락 저장소 read/write)을 mock LLM으로 끝까지 확인한다.
"""

from datetime import date

import pytest

from core.models import StockIdentity, TradingDayStockEvent
from features.briefing.schemas import BriefingRequest
from features.briefing.service import BriefingService
from features.monitor.service import MonitorService
from services.llm.schemas import DailyDigestJson, MarketBriefingJson


class MonitorLlm:
    async def generate_structured(self, s, u, schema):
        assert schema is DailyDigestJson
        return DailyDigestJson(
            title="반도체 주도 강세",
            summary="삼성전자 거래량 급증",
            key_themes=["반도체"],
        )


class BriefingLlm:
    def __init__(self):
        self.user_prompt = None

    async def generate_structured(self, s, u, schema):
        self.user_prompt = u
        assert schema is MarketBriefingJson
        return MarketBriefingJson(headline="연속성 확인", market_summary="")


class Notifier:
    async def send(self, text, dedupe_key=None):
        return {"status": "sent"}


@pytest.mark.asyncio
async def test_monitor_digest_flows_into_next_day_briefing(db):
    # 1) 모니터링 에이전트: 6/18 장마감 종합시황 → 맥락 저장소 역기록
    monitor = MonitorService(llm=MonitorLlm(), notifier=Notifier())
    await monitor.run_daily_close(
        db,
        date(2026, 6, 18),
        "KR_DAY",
        events=[
            TradingDayStockEvent(
                trade_date=date(2026, 6, 18),
                stock=StockIdentity(code="005930", name="삼성전자"),
                event_types=["HIGH_VOLUME"],
                volume=15_000_000,
            )
        ],
    )

    # 2) 시장 판단 에이전트: 6/19 장전 브리핑 → 어제 종합시황이 맥락으로 주입되는지
    brief_llm = BriefingLlm()
    briefing = BriefingService(llm=brief_llm)
    resp = await briefing.create_briefing(
        db, BriefingRequest(base_date=date(2026, 6, 19), timeline="PRE_MARKET")
    )

    assert resp.briefing.content.headline == "연속성 확인"
    # 루프 검증: 모니터링이 쓴 digest 제목이 브리핑 프롬프트 맥락 블록에 존재
    assert "반도체 주도 강세" in brief_llm.user_prompt
    assert "최근 종합 시황" in brief_llm.user_prompt
