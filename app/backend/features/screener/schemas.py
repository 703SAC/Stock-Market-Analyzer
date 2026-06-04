"""Screener API schemas."""

from datetime import date

from pydantic import BaseModel, Field

from core.models import TradingDayStockEvent


class ScreenerQuery(BaseModel):
    start_date: date
    end_date: date
    min_volume: int = Field(default=10_000_000, ge=0)
    include_upper_limit: bool = True


class ScreenerEventsResponse(BaseModel):
    events: list[TradingDayStockEvent]
    total: int
    cached_days: list[str] = Field(default_factory=list)
