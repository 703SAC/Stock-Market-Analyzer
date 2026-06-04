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


def dumps_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def loads_json(text: str):
    return json.loads(text)
