"""메가 내러티브 맥락 저장소 리포지토리.

세 에이전트가 공유하는 맥락(종합시황/일정/그룹사/내러티브)의 영속화 계층.
저장은 도메인 모델의 JSON 페이로드 + 조회용 인덱스 컬럼 패턴(기존 캐시 리포와 동일).
"""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import (
    CalendarEvent,
    GroupMapEntry,
    MarketDigest,
    MarketSession,
    NarrativeMemory,
)
from storage.models import (
    CalendarEventRow,
    GroupMapRow,
    MarketDigestRow,
    NarrativeMemoryRow,
    dumps_json,
    loads_json,
)


# --- market_digest ----------------------------------------------------------

def upsert_market_digest(db: Session, digest: MarketDigest) -> MarketDigest:
    """(digest_date, session) 단위로 종합시황을 upsert."""
    row = db.execute(
        select(MarketDigestRow).where(
            MarketDigestRow.digest_date == digest.digest_date,
            MarketDigestRow.session == digest.session,
        )
    ).scalar_one_or_none()

    digest.id = (row.id if row else None) or digest.id or str(uuid.uuid4())
    payload = dumps_json(digest.model_dump(mode="json"))
    if row:
        row.payload_json = payload
    else:
        db.add(
            MarketDigestRow(
                id=digest.id,
                digest_date=digest.digest_date,
                session=digest.session,
                payload_json=payload,
            )
        )
    db.commit()
    return digest


def get_recent_digests(
    db: Session,
    before_date: date,
    session: MarketSession | None = None,
    limit: int = 5,
) -> list[MarketDigest]:
    """before_date 이전(포함)의 최신 종합시황을 최신순으로 반환."""
    stmt = select(MarketDigestRow).where(MarketDigestRow.digest_date <= before_date)
    if session is not None:
        stmt = stmt.where(MarketDigestRow.session == session)
    stmt = stmt.order_by(MarketDigestRow.digest_date.desc()).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [MarketDigest.model_validate(loads_json(r.payload_json)) for r in rows]


# --- event_calendar ---------------------------------------------------------

def add_calendar_event(db: Session, event: CalendarEvent) -> CalendarEvent:
    event.id = event.id or str(uuid.uuid4())
    db.merge(
        CalendarEventRow(
            id=event.id,
            event_date=event.event_date,
            category=event.category,
            stock_code=event.stock_code,
            payload_json=dumps_json(event.model_dump(mode="json")),
        )
    )
    db.commit()
    return event


def get_events_in_range(
    db: Session,
    start: date,
    end: date,
    stock_code: str | None = None,
) -> list[CalendarEvent]:
    """[start, end] 범위 일정. stock_code 지정 시 해당 종목 + 종목무관(None) 일정 포함."""
    stmt = select(CalendarEventRow).where(
        CalendarEventRow.event_date >= start,
        CalendarEventRow.event_date <= end,
    )
    if stock_code is not None:
        stmt = stmt.where(
            (CalendarEventRow.stock_code == stock_code)
            | (CalendarEventRow.stock_code.is_(None))
        )
    stmt = stmt.order_by(CalendarEventRow.event_date.asc())
    rows = db.execute(stmt).scalars().all()
    return [CalendarEvent.model_validate(loads_json(r.payload_json)) for r in rows]


# --- group_map --------------------------------------------------------------

def upsert_group_map(db: Session, entry: GroupMapEntry) -> GroupMapEntry:
    db.merge(
        GroupMapRow(
            stock_code=entry.stock_code,
            group_name=entry.group_name,
            payload_json=dumps_json(entry.model_dump(mode="json")),
        )
    )
    db.commit()
    return entry


def get_group_map(db: Session, stock_code: str) -> GroupMapEntry | None:
    row = db.get(GroupMapRow, stock_code)
    if row is None:
        return None
    return GroupMapEntry.model_validate(loads_json(row.payload_json))


def get_group_peers(db: Session, group_name: str) -> list[GroupMapEntry]:
    """같은 그룹명에 속한 종목들(그룹사 역학 역인덱스)."""
    rows = db.execute(
        select(GroupMapRow)
        .where(GroupMapRow.group_name == group_name)
        .order_by(GroupMapRow.stock_code.asc())
    ).scalars().all()
    return [GroupMapEntry.model_validate(loads_json(r.payload_json)) for r in rows]


# --- narrative_memory -------------------------------------------------------

def add_narrative(db: Session, narrative: NarrativeMemory) -> NarrativeMemory:
    narrative.id = narrative.id or str(uuid.uuid4())
    db.merge(
        NarrativeMemoryRow(
            id=narrative.id,
            as_of_date=narrative.as_of_date,
            topic=narrative.topic,
            payload_json=dumps_json(narrative.model_dump(mode="json")),
        )
    )
    db.commit()
    return narrative


def get_recent_narratives(
    db: Session,
    before_date: date,
    stock_code: str | None = None,
    limit: int = 5,
) -> list[NarrativeMemory]:
    """최근 내러티브. stock_code 지정 시 해당 종목이 연관된 것만 필터링."""
    stmt = (
        select(NarrativeMemoryRow)
        .where(NarrativeMemoryRow.as_of_date <= before_date)
        .order_by(NarrativeMemoryRow.as_of_date.desc())
    )
    rows = db.execute(stmt).scalars().all()
    out: list[NarrativeMemory] = []
    for r in rows:
        n = NarrativeMemory.model_validate(loads_json(r.payload_json))
        if stock_code is not None and n.stock_codes and stock_code not in n.stock_codes:
            continue
        out.append(n)
        if len(out) >= limit:
            break
    return out
