"""ContextService 조립/프롬프트 주입 테스트 (Phase 1)."""

from datetime import date

from core.models import (
    CalendarEvent,
    GroupMapEntry,
    MarketDigest,
    NarrativeMemory,
)
from services.context import ContextService
from storage.repositories import context as repo


def _seed(db):
    repo.upsert_market_digest(
        db,
        MarketDigest(
            digest_date=date(2026, 6, 18),
            session="KR_DAY",
            title="코스피 강세",
            summary="반도체 주도",
            key_themes=["반도체"],
        ),
    )
    repo.add_calendar_event(
        db,
        CalendarEvent(
            event_date=date(2026, 6, 21),
            title="삼성 실적발표",
            category="EARNINGS",
            stock_code="005930",
        ),
    )
    repo.upsert_group_map(
        db,
        GroupMapEntry(
            stock_code="005930", stock_name="삼성전자", group_name="삼성", themes=["반도체"]
        ),
    )
    repo.upsert_group_map(
        db,
        GroupMapEntry(
            stock_code="207940", stock_name="삼성바이오로직스", group_name="삼성"
        ),
    )
    repo.add_narrative(
        db,
        NarrativeMemory(
            as_of_date=date(2026, 6, 17),
            topic="AI 슈퍼사이클",
            narrative="HBM 수요 지속",
            stock_codes=["005930"],
        ),
    )


def test_build_context_assembles_all_dimensions(db):
    _seed(db)
    svc = ContextService(db)
    ctx = svc.build_context(base_date=date(2026, 6, 19), stock_code="005930")

    assert len(ctx.recent_digests) == 1
    assert any(e.title == "삼성 실적발표" for e in ctx.relevant_events)
    assert ctx.group is not None and ctx.group.group_name == "삼성"
    assert [p.stock_code for p in ctx.peer_group] == ["207940"]  # 자기 자신 제외
    assert len(ctx.narratives) == 1


def test_build_context_without_stock_has_no_group(db):
    _seed(db)
    svc = ContextService(db)
    ctx = svc.build_context(base_date=date(2026, 6, 19))
    assert ctx.group is None
    assert ctx.peer_group == []


def test_to_prompt_block_is_deterministic_and_complete(db):
    _seed(db)
    svc = ContextService(db)
    ctx = svc.build_context(base_date=date(2026, 6, 19), stock_code="005930")
    block1 = ContextService.to_prompt_block(ctx)
    block2 = ContextService.to_prompt_block(ctx)

    assert block1 == block2  # 결정적
    assert "[메가 내러티브 맥락]" in block1
    for header in ["최근 종합 시황", "관련 일정", "그룹사 / 테마 역학", "누적 내러티브"]:
        assert header in block1
    assert "삼성 실적발표" in block1
    assert "207940" in block1  # 동일 그룹 종목 노출


def test_to_prompt_block_empty_context_states_absence(db):
    svc = ContextService(db)
    ctx = svc.build_context(base_date=date(2026, 6, 19), stock_code="999999")
    block = ContextService.to_prompt_block(ctx)
    # 환각 억제: 빈 블록이 아니라 명시적 '없음'을 적는다
    assert "기록된 종합 시황 없음" in block
    assert "등록된 일정 없음" in block
    assert "그룹/테마 매핑 없음" in block
    assert "누적 내러티브 없음" in block
