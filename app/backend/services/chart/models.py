"""차트 도메인 모델 (일봉)."""

from datetime import date

from pydantic import BaseModel


class DailyCandle(BaseModel):
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float
    volume: int | None = None
