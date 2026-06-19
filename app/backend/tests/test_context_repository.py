"""맥락 저장소 리포지토리 CRUD 테스트 (Phase 1)."""

from datetime import date

from core.models import (
    CalendarEvent,
    GroupMapEntry,
    MarketDigest,
    NarrativeMemory,
)
from storage.repositories import context as repo


# --- market_digest ----------------------------------------------------------

def test_market_digest_upsert_round_trip(db):
    d = MarketDigest(
        digest_date=date(2026, 6, 18),
        session="KR_DAY",
        title="코스피 반등",
        summary="반도체 주도 상승",
        key_themes=["반도체", "AI"],
        indices={"KOSPI": 2800.5},
    )
    saved = repo.upsert_market_digest(db, d)
    assert saved.id

    got = repo.get_recent_digests(db, before_date=date(2026, 6, 18))
    assert len(got) == 1
    assert got[0].title == "코스피 반등"
    assert got[0].key_themes == ["반도체", "AI"]


def test_market_digest_upsert_replaces_same_date_session(db):
    base = dict(digest_date=date(2026, 6, 18), session="KR_DAY")
    first = repo.upsert_market_digest(db, MarketDigest(**base, summary="v1"))
    second = repo.upsert_market_digest(db, MarketDigest(**base, summary="v2"))

    assert first.id == second.id  # 동일 (date, session) → 같은 행
    rows = repo.get_recent_digests(db, before_date=date(2026, 6, 18))
    assert len(rows) == 1
    assert rows[0].summary == "v2"


def test_get_recent_digests_orders_desc_and_limits(db):
    for day in (15, 16, 17):
        repo.upsert_market_digest(
            db, MarketDigest(digest_date=date(2026, 6, day), session="KR_DAY")
        )
    rows = repo.get_recent_digests(db, before_date=date(2026, 6, 17), limit=2)
    assert [r.digest_date.day for r in rows] == [17, 16]


# --- event_calendar ---------------------------------------------------------

def test_calendar_range_and_stock_filter(db):
    repo.add_calendar_event(
        db, CalendarEvent(event_date=date(2026, 6, 20), title="FOMC", category="MACRO")
    )
    repo.add_calendar_event(
        db,
        CalendarEvent(
            event_date=date(2026, 6, 21),
            title="삼성 실적",
            category="EARNINGS",
            stock_code="005930",
        ),
    )
    repo.add_calendar_event(
        db,
        CalendarEvent(
            event_date=date(2026, 6, 21),
            title="SK 실적",
            category="EARNINGS",
            stock_code="000660",
        ),
    )

    # 종목 지정 시: 해당 종목 + 종목무관(None) 일정만
    got = repo.get_events_in_range(
        db, start=date(2026, 6, 19), end=date(2026, 6, 22), stock_code="005930"
    )
    titles = {e.title for e in got}
    assert titles == {"FOMC", "삼성 실적"}
    assert got[0].event_date <= got[-1].event_date  # 오름차순


# --- group_map --------------------------------------------------------------

def test_group_map_and_peers(db):
    repo.upsert_group_map(
        db,
        GroupMapEntry(
            stock_code="005930", stock_name="삼성전자", group_name="삼성", themes=["반도체"]
        ),
    )
    repo.upsert_group_map(
        db,
        GroupMapEntry(
            stock_code="207940", stock_name="삼성바이오로직스", group_name="삼성", themes=["바이오"]
        ),
    )
    repo.upsert_group_map(
        db, GroupMapEntry(stock_code="000660", stock_name="SK하이닉스", group_name="SK")
    )

    entry = repo.get_group_map(db, "005930")
    assert entry is not None and entry.group_name == "삼성"

    peers = repo.get_group_peers(db, "삼성")
    assert {p.stock_code for p in peers} == {"005930", "207940"}


# --- narrative_memory -------------------------------------------------------

def test_narrative_recent_and_stock_filter(db):
    repo.add_narrative(
        db,
        NarrativeMemory(
            as_of_date=date(2026, 6, 17),
            topic="AI 슈퍼사이클",
            narrative="HBM 수요 지속",
            stock_codes=["005930", "000660"],
        ),
    )
    repo.add_narrative(
        db,
        NarrativeMemory(
            as_of_date=date(2026, 6, 18),
            topic="2차전지 조정",
            narrative="수요 둔화 우려",
            stock_codes=["373220"],
        ),
    )

    all_recent = repo.get_recent_narratives(db, before_date=date(2026, 6, 18))
    assert [n.as_of_date.day for n in all_recent] == [18, 17]

    filtered = repo.get_recent_narratives(
        db, before_date=date(2026, 6, 18), stock_code="000660"
    )
    assert len(filtered) == 1
    assert filtered[0].topic == "AI 슈퍼사이클"
