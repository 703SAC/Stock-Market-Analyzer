"""Chart condition JSON DSL schema (Sprint 7+)."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ConditionClause(BaseModel):
    indicator: str
    op: Literal[">", "<", ">=", "<=", "=="]
    value: float | int | None = None
    indicator_right: str | None = None


class ConditionDsl(BaseModel):
    all: list[ConditionClause] = Field(default_factory=list)


ALLOWED_INDICATORS = frozenset(
    {"volume", "close", "open", "high", "low", "ma20", "ma60", "rsi14", "change_rate"}
)
