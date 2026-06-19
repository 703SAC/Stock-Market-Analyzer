"""모니터링 일일 리포트 파이프라인 테스트 (Phase 4). LLM/notifier fake 주입."""

from datetime import date

import pytest

from core.models import StockIdentity, TradingDayStockEvent
from features.monitor.service import MonitorService
from services.llm.schemas import DailyDigestJson
from storage.repositories import context as ctx_repo


class FakeLlm:
    def __init__(self):
        self.user_prompt = None

    async def generate_structured(self, system_prompt, user_prompt, schema):
        self.user_prompt = user_prompt
        assert schema is DailyDigestJson
        return DailyDigestJson(
            title="반도체 주도 강세",
            summary="대형주 거래량 급증",
            key_themes=["반도체", "AI"],
            watch_items=["수급 지속 확인"],
            risks=["과열"],
            confidence="MEDIUM",
        )


class FakeNotifier:
    def __init__(self):
        self.sent = []

    async def send(self, text, dedupe_key=None):
        self.sent.append((text, dedupe_key))
        return {"status": "sent", "code": 200}


@pytest.mark.asyncio
async def test_daily_close_writes_digest_and_sends(db):
    events = [
        TradingDayStockEvent(
            trade_date=date(2026, 6, 18),
            stock=StockIdentity(code="005930", name="삼성전자"),
            event_types=["HIGH_VOLUME"],
            volume=15_000_000,
        )
    ]
    fake_llm, notifier = FakeLlm(), FakeNotifier()
    svc = MonitorService(llm=fake_llm, notifier=notifier)
    res = await svc.run_daily_close(db, date(2026, 6, 18), "KR_DAY", events=events)

    assert res.persisted is True
    assert res.telegram["status"] == "sent"
    assert "삼성전자" in fake_llm.user_prompt  # 특징주 로그가 프롬프트에 주입

    # 맥락 저장소(market_digest)에 역기록됐는지 — 루프를 닫는 핵심
    stored = ctx_repo.get_recent_digests(db, before_date=date(2026, 6, 18), session="KR_DAY")
    assert len(stored) == 1
    assert stored[0].title == "반도체 주도 강세"
    assert stored[0].key_themes == ["반도체", "AI"]


@pytest.mark.asyncio
async def test_daily_close_uses_dedupe_key():
    notifier = FakeNotifier()
    svc = MonitorService(llm=FakeLlm(), notifier=notifier)
    # persist=False로 DB 미사용
    await svc.run_daily_close(None, date(2026, 6, 18), "US_NIGHT", persist=False)
    assert notifier.sent[0][1] == "digest:2026-06-18:US_NIGHT"
