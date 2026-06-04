"""Report API schemas."""

from datetime import date

from pydantic import BaseModel, Field

from core.models import AnalysisReport, TradingDayStockEvent


class NewsPriceReportRequest(BaseModel):
    stock_code: str
    stock_name: str | None = None
    base_date: date
    article_ids: list[str] = Field(default_factory=list)
    screener_event: TradingDayStockEvent | None = None


class NewsPriceReportResponse(BaseModel):
    report: AnalysisReport
