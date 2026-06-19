"""SQLAlchemy ORM models."""

import json
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class ScreenerCacheRow(Base):
    __tablename__ = "screener_cache"

    cache_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NewsCacheRow(Base):
    __tablename__ = "news_cache"

    cache_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReportRow(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(12))
    base_date: Mapped[date] = mapped_column(Date)
    report_type: Mapped[str] = mapped_column(String(32))
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketDigestRow(Base):
    """일별 종합 시황 (메가 내러티브 백본). (date, session) 단위로 upsert."""

    __tablename__ = "market_digest"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    digest_date: Mapped[date] = mapped_column(Date, index=True)
    session: Mapped[str] = mapped_column(String(16), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CalendarEventRow(Base):
    """주요 일정. 날짜 범위 + 종목코드로 조회."""

    __tablename__ = "event_calendar"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    category: Mapped[str] = mapped_column(String(16))
    stock_code: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GroupMapRow(Base):
    """그룹사/테마 역학 매핑. 종목코드 PK, 그룹명 인덱스."""

    __tablename__ = "group_map"

    stock_code: Mapped[str] = mapped_column(String(12), primary_key=True)
    group_name: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NarrativeMemoryRow(Base):
    """누적 내러티브 메모리."""

    __tablename__ = "narrative_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    topic: Mapped[str] = mapped_column(String(128), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def dumps_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def loads_json(text: str):
    return json.loads(text)
