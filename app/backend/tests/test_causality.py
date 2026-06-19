"""인과관계 분석 오케스트레이션 테스트 (Phase 2). LLM은 fake로 주입."""

from datetime import date, timedelta

import pytest

from core.models import (
    ArticleItem,
    CalendarEvent,
    GroupMapEntry,
    StockIdentity,
    TradingDayStockEvent,
)
from features.strategy.causality import CausalityService
from features.strategy.schemas import CausalityRequest
from services.chart.models import DailyCandle
from services.llm.schemas import CausalAnalysisJson
from storage.repositories import context as ctx_repo
from storage.repositories import reports as report_repo


class FakeLlm:
    def __init__(self):
        self.user_prompt = None

    async def generate_structured(self, system_prompt, user_prompt, schema):
        self.user_prompt = user_prompt
        assert schema is CausalAnalysisJson
        return CausalAnalysisJson(
            summary="거래량 급증은 실적 기대 가능성",
            primary_driver="실적 발표 기대",
            causal_factors=["반도체 업황 개선"],
            context_links=["삼성 실적발표 일정"],
            risks=["기사 기반 추정, 확인 필요"],
            confidence="MEDIUM",
        )


def _uptrend(n=70):
    return [
        DailyCandle(
            date=date(2026, 6, 1) + timedelta(days=i),
            open=float(i + 1), high=float(i + 1), low=float(i + 1),
            close=float(i + 1), volume=5_000_000 if i == n - 1 else 1_000_000,
        )
        for i in range(n)
    ]


@pytest.mark.asyncio
async def test_causality_analyze_persists_composite_report(db):
    # 맥락 시드
    ctx_repo.upsert_group_map(
        db, GroupMapEntry(stock_code="005930", stock_name="삼성전자", group_name="삼성", themes=["반도체"])
    )
    ctx_repo.add_calendar_event(
        db, CalendarEvent(event_date=date(2026, 6, 20), title="삼성 실적발표", category="EARNINGS", stock_code="005930")
    )

    event = TradingDayStockEvent(
        trade_date=date(2026, 6, 18),
        stock=StockIdentity(code="005930", name="삼성전자"),
        event_types=["HIGH_VOLUME", "UPPER_LIMIT"],
        volume=15_000_000,
        change_rate=12.5,
        price=80000,
    )
    req = CausalityRequest(
        event=event,
        articles=[ArticleItem(title="삼성전자 반도체 호조", url="https://x/1")],
        candles=_uptrend(),
    )

    fake = FakeLlm()
    svc = CausalityService(llm=fake)
    resp = await svc.analyze(db, req, persist=True)

    assert resp.report.report_type == "COMPOSITE"
    assert resp.report.confidence == "MEDIUM"
    assert set(["price", "news", "canslim", "context"]).issubset(set(resp.report.sources))
    assert resp.canslim is not None and resp.canslim.passed is True

    # 프롬프트에 정량 사실과 맥락 블록이 주입됐는지
    assert "[정량 사실" in fake.user_prompt
    assert "메가 내러티브 맥락" in fake.user_prompt
    assert "삼성 실적발표" in fake.user_prompt

    # 저장 확인
    saved = report_repo.get_report(db, resp.report.id)
    assert saved is not None and saved.report_type == "COMPOSITE"


@pytest.mark.asyncio
async def test_causality_without_candles_has_no_canslim(db):
    event = TradingDayStockEvent(
        trade_date=date(2026, 6, 18),
        stock=StockIdentity(code="000660", name="SK하이닉스"),
        event_types=["HIGH_VOLUME"],
        volume=20_000_000,
    )
    svc = CausalityService(llm=FakeLlm())
    resp = await svc.analyze(db, CausalityRequest(event=event), persist=False)
    assert resp.canslim is None
    assert "canslim" not in resp.report.sources
