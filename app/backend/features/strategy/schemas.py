"""전략 에이전트 스키마."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from core.models import AnalysisReport, ArticleItem, StockIdentity, TradingDayStockEvent
from services.chart.models import DailyCandle


class CanSlimResult(BaseModel):
    """CAN SLIM 스타일 정량 스크리닝 결과 (전부 Pandas 수식 산출)."""

    stock: StockIdentity
    as_of: date
    checks: dict[str, bool] = Field(default_factory=dict)
    score: int = 0
    max_score: int = 0
    passed: bool = False
    metrics: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    # 펀더멘털 기반 기준(C/A/N/I)은 DART 연동(향후) 전까지 미평가
    pending_fundamentals: list[str] = Field(default_factory=list)


class CausalityRequest(BaseModel):
    event: TradingDayStockEvent
    articles: list[ArticleItem] = Field(default_factory=list)
    candles: list[DailyCandle] = Field(default_factory=list)


class CausalityResponse(BaseModel):
    report: AnalysisReport
    canslim: CanSlimResult | None = None
