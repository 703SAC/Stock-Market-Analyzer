"""브리핑 스키마."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from core.models import ArticleItem
from features.briefing.timeline import TimelinePhase
from services.llm.schemas import MarketBriefingJson


class BriefingRequest(BaseModel):
    base_date: date
    timeline: TimelinePhase = "CLOSE"
    articles: list[ArticleItem] = Field(default_factory=list)


class MarketBriefing(BaseModel):
    base_date: date
    timeline: TimelinePhase
    label: str
    content: MarketBriefingJson
    sources: list[str] = Field(default_factory=list)


class BriefingResponse(BaseModel):
    briefing: MarketBriefing
