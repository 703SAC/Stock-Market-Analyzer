"""Shared domain models."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class StockIdentity(BaseModel):
    code: str
    name: str | None = None
    market: str | None = None


class TradingDayStockEvent(BaseModel):
    id: str | None = None
    trade_date: date
    stock: StockIdentity
    event_types: list[Literal["HIGH_VOLUME", "UPPER_LIMIT", "CONDITION_MATCH"]] = Field(
        default_factory=list
    )
    price: int | None = None
    change_rate: float | None = None
    volume: int | None = None
    source: str = "kis"


class ArticleItem(BaseModel):
    id: str | None = None
    title: str
    url: str
    publisher: str | None = None
    published_at: datetime | None = None
    summary: str | None = None


class AnalysisReport(BaseModel):
    id: str | None = None
    stock: StockIdentity
    base_date: date
    report_type: Literal["NEWS_PRICE", "DART_PRICE", "CHART", "COMPOSITE"] = "NEWS_PRICE"
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    possible_reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    sources: list[str] = Field(default_factory=list)
    article_urls: list[str] = Field(default_factory=list)


# --- 메가 내러티브 맥락 저장소 도메인 모델 (Phase 1) ---------------------------
# 당일 뉴스 파편이 아니라 누적된 시황/일정/그룹사 맥락을 주입하기 위한 표준 모델.

MarketSession = Literal["KR_DAY", "US_NIGHT", "GLOBAL"]
ImportanceLevel = Literal["LOW", "MEDIUM", "HIGH"]


class MarketDigest(BaseModel):
    """일별 종합 시황 스냅샷 (모니터링 에이전트가 장마감 후 기록)."""

    id: str | None = None
    digest_date: date
    session: MarketSession = "KR_DAY"
    title: str = ""
    summary: str = ""
    key_themes: list[str] = Field(default_factory=list)
    indices: dict[str, float] = Field(default_factory=dict)
    source: str = "monitor-agent"


class CalendarEvent(BaseModel):
    """주요 일정 (실적발표, 매크로 이벤트, 배당, IPO 등)."""

    id: str | None = None
    event_date: date
    category: Literal["EARNINGS", "MACRO", "DIVIDEND", "IPO", "POLICY", "OTHER"] = "OTHER"
    title: str
    stock_code: str | None = None
    description: str | None = None
    importance: ImportanceLevel = "MEDIUM"


class GroupMapEntry(BaseModel):
    """그룹사/테마 역학 매핑 (종목 -> 그룹, 테마, 연관 종목)."""

    stock_code: str
    stock_name: str | None = None
    group_name: str | None = None
    themes: list[str] = Field(default_factory=list)
    related_codes: list[str] = Field(default_factory=list)


class NarrativeMemory(BaseModel):
    """누적 내러티브 메모리 (여러 날에 걸친 큰 흐름)."""

    id: str | None = None
    as_of_date: date
    topic: str
    narrative: str
    stock_codes: list[str] = Field(default_factory=list)
    importance: ImportanceLevel = "MEDIUM"


class MarketContext(BaseModel):
    """프롬프트 주입용으로 조립된 메가 내러티브 맥락 묶음."""

    base_date: date
    stock_code: str | None = None
    recent_digests: list[MarketDigest] = Field(default_factory=list)
    relevant_events: list[CalendarEvent] = Field(default_factory=list)
    group: GroupMapEntry | None = None
    peer_group: list[GroupMapEntry] = Field(default_factory=list)
    narratives: list[NarrativeMemory] = Field(default_factory=list)
