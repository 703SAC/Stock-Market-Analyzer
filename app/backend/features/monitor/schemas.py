"""모니터링 에이전트 스키마."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from core.models import MarketDigest, MarketSession, TradingDayStockEvent
from services.chart.condition_schema import ConditionDsl


class MonitorRuleStub(BaseModel):
    id: str | None = None
    name: str
    stock_codes: list[str]
    condition: ConditionDsl
    enabled: bool = True


class DailyReportRequest(BaseModel):
    base_date: date
    session: MarketSession = "KR_DAY"
    events: list[TradingDayStockEvent] = Field(default_factory=list)


class DailyReportResult(BaseModel):
    digest: MarketDigest
    telegram: dict = Field(default_factory=dict)
    persisted: bool = False
