"""메가 내러티브 맥락 저장소 읽기/시드 API.

읽기 GET은 프론트의 맥락 뷰어(메가 내러티브 누적 검증)에, 시드 POST는
briefing/causality를 실맥락으로 테스트하기 위한 일정·그룹 입력에 사용한다.
라우터는 얇게 유지하고 storage.repositories.context에 위임한다.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.models import (
    CalendarEvent,
    GroupMapEntry,
    MarketDigest,
    MarketSession,
    NarrativeMemory,
)
from storage.db import get_db
from storage.repositories import context as repo

router = APIRouter(prefix="/context", tags=["context"])


@router.get("/digests")
async def list_digests(
    before: date | None = None,
    session: MarketSession | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[MarketDigest]:
    return repo.get_recent_digests(
        db, before_date=before or date.today(), session=session, limit=limit
    )


@router.get("/events")
async def list_events(
    start: date,
    end: date,
    stock_code: str | None = None,
    db: Session = Depends(get_db),
) -> list[CalendarEvent]:
    return repo.get_events_in_range(db, start=start, end=end, stock_code=stock_code)


@router.get("/group/{stock_code}")
async def get_group(
    stock_code: str,
    db: Session = Depends(get_db),
) -> GroupMapEntry | None:
    return repo.get_group_map(db, stock_code)


@router.get("/group")
async def get_group_peers(
    group_name: str,
    db: Session = Depends(get_db),
) -> list[GroupMapEntry]:
    return repo.get_group_peers(db, group_name)


@router.get("/narratives")
async def list_narratives(
    before: date | None = None,
    stock_code: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[NarrativeMemory]:
    return repo.get_recent_narratives(
        db, before_date=before or date.today(), stock_code=stock_code, limit=limit
    )


# --- 시드(seed) POST: briefing/causality 실맥락 테스트용 ---

@router.post("/digests")
async def seed_digest(
    body: MarketDigest, db: Session = Depends(get_db)
) -> MarketDigest:
    return repo.upsert_market_digest(db, body)


@router.post("/events")
async def seed_event(
    body: CalendarEvent, db: Session = Depends(get_db)
) -> CalendarEvent:
    return repo.add_calendar_event(db, body)


@router.post("/group")
async def seed_group(
    body: GroupMapEntry, db: Session = Depends(get_db)
) -> GroupMapEntry:
    return repo.upsert_group_map(db, body)


@router.post("/narratives")
async def seed_narrative(
    body: NarrativeMemory, db: Session = Depends(get_db)
) -> NarrativeMemory:
    return repo.add_narrative(db, body)
