"""Real-time monitor schemas stub (Sprint 9)."""

from pydantic import BaseModel

from services.chart.condition_schema import ConditionDsl


class MonitorRuleStub(BaseModel):
    id: str | None = None
    name: str
    stock_codes: list[str]
    condition: ConditionDsl
    enabled: bool = True
