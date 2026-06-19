"""LLM structured output schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class NewsPriceReportJson(BaseModel):
    summary: str = Field(description="One sentence summary")
    key_points: list[str] = Field(default_factory=list)
    possible_reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"


class CausalAnalysisJson(BaseModel):
    """전략 에이전트: 가격 이벤트의 인과관계 분석 (테마/일정/그룹사)."""

    summary: str = Field(description="One sentence summary")
    primary_driver: str = Field(default="", description="Most likely primary driver")
    causal_factors: list[str] = Field(default_factory=list)
    context_links: list[str] = Field(
        default_factory=list, description="Links to calendar/group/narrative context"
    )
    risks: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"


class MarketBriefingJson(BaseModel):
    """시장 판단 에이전트: 타임라인별 종합 시황 브리핑."""

    headline: str = Field(description="One line headline")
    market_summary: str = ""
    key_narratives: list[str] = Field(default_factory=list)
    sector_highlights: list[str] = Field(default_factory=list)
    watch_items: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"


class DailyDigestJson(BaseModel):
    """모니터링 에이전트: 장마감 일일 종합 시황(맥락 저장소에 역기록)."""

    title: str = Field(description="One line title")
    summary: str = ""
    key_themes: list[str] = Field(default_factory=list)
    watch_items: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
