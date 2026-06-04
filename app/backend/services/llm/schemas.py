"""LLM structured output schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class NewsPriceReportJson(BaseModel):
    summary: str = Field(description="One sentence summary")
    key_points: list[str] = Field(default_factory=list)
    possible_reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
