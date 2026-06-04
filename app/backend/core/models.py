"""Shared domain models."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class StockIdentity(BaseModel):
    code: str
    name: str | None = None
    market: str | None = None


class TradingDayStockEvent(BaseModel):
    id: str | None = None
    trade_date: date
    stock: StockIdentity
    event_types: list[Literal["HIGH_VOLUME", "UPPER_LIMIT", "CONDITION_MATCH"]] = Field(
        default_factory=list
    )
    price: int | None = None
    change_rate: float | None = None
    volume: int | None = None
    source: str = "kis"


class ArticleItem(BaseModel):
    id: str | None = None
    title: str
    url: str
    publisher: str | None = None
    published_at: datetime | None = None
    summary: str | None = None


class AnalysisReport(BaseModel):
    id: str | None = None
    stock: StockIdentity
    base_date: date
    report_type: Literal["NEWS_PRICE", "DART_PRICE", "CHART", "COMPOSITE"] = "NEWS_PRICE"
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    possible_reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    sources: list[str] = Field(default_factory=list)
    article_urls: list[str] = Field(default_factory=list)
