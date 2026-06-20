"""맥락 저장소 API 라우트 테스트 (TestClient + get_db 오버라이드)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import storage.models  # noqa: F401  (테이블 등록)
from main import create_app
from storage.db import Base, get_db


@pytest.fixture
def client():
    # StaticPool: TestClient가 별도 스레드에서 접근해도 단일 :memory: 연결 공유
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    def _override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c


def test_seed_and_list_digests(client):
    r = client.post(
        "/api/context/digests",
        json={"digest_date": "2026-06-18", "session": "KR_DAY", "title": "강세", "summary": "반도체"},
    )
    assert r.status_code == 200
    got = client.get("/api/context/digests", params={"before": "2026-06-18"})
    assert got.status_code == 200
    data = got.json()
    assert len(data) == 1 and data[0]["title"] == "강세"


def test_seed_and_filter_events(client):
    client.post(
        "/api/context/events",
        json={"event_date": "2026-06-21", "title": "삼성 실적", "category": "EARNINGS", "stock_code": "005930"},
    )
    client.post(
        "/api/context/events",
        json={"event_date": "2026-06-20", "title": "FOMC", "category": "MACRO"},
    )
    r = client.get(
        "/api/context/events",
        params={"start": "2026-06-19", "end": "2026-06-22", "stock_code": "005930"},
    )
    titles = {e["title"] for e in r.json()}
    assert titles == {"삼성 실적", "FOMC"}  # 종목일정 + 종목무관


def test_group_seed_and_peers(client):
    for code, name in [("005930", "삼성전자"), ("207940", "삼성바이오로직스")]:
        client.post(
            "/api/context/group",
            json={"stock_code": code, "stock_name": name, "group_name": "삼성"},
        )
    one = client.get("/api/context/group/005930").json()
    assert one["group_name"] == "삼성"
    peers = client.get("/api/context/group", params={"group_name": "삼성"}).json()
    assert {p["stock_code"] for p in peers} == {"005930", "207940"}


def test_health_exposes_new_flags(client):
    body = client.get("/api/health").json()
    assert "telegram_configured" in body
    assert "scheduler_enabled" in body
    assert "llm" in body
