"""전략 에이전트 — 인과관계 분석 프롬프트.

정량 사실(가격/거래량/CAN SLIM)은 Pandas로 선계산하여 사실로 제공하고,
LLM은 그 사실 + 맥락(일정/그룹사/내러티브) + 뉴스로 '가능한 인과'만 추론한다.
"""

from __future__ import annotations

from core.models import TradingDayStockEvent
from features.strategy.schemas import CanSlimResult

CAUSAL_SYSTEM_PROMPT = """You are a Korean-equity causality analyst.
Output ONLY valid JSON matching this schema:
{
  "summary": "one sentence",
  "primary_driver": "most likely single driver",
  "causal_factors": ["..."],
  "context_links": ["links to schedule/group/narrative context"],
  "risks": ["..."],
  "confidence": "LOW|MEDIUM|HIGH"
}
Rules:
- Never give buy/sell advice. Use tentative language ("possible", "may", "needs verification").
- Quant facts (price/volume/CAN SLIM) are pre-computed and authoritative; do NOT recompute numbers.
- Prefer explanations grounded in the provided context (schedule, group/theme, narrative) and news.
- If evidence is weak or conflicting, set confidence to LOW.
"""


def _canslim_block(canslim: CanSlimResult | None) -> str:
    if canslim is None:
        return "CAN SLIM: 미계산"
    lines = [
        f"CAN SLIM 점수: {canslim.score}/{canslim.max_score} (통과: {canslim.passed})",
        f"지표: {canslim.metrics}",
        "항목: " + "; ".join(canslim.reasons),
        "펀더멘털 미평가(데이터 부재): " + ", ".join(canslim.pending_fundamentals),
    ]
    return "\n".join(lines)


def build_causal_prompt(
    event: TradingDayStockEvent,
    context_block: str,
    articles_text: str,
    canslim: CanSlimResult | None,
) -> str:
    """결정적 사용자 프롬프트 조립 (테스트 가능)."""
    quant = (
        f"이벤트: {', '.join(event.event_types) or '없음'}; "
        f"거래량: {event.volume}; 등락률: {event.change_rate}; 종가: {event.price}"
    )
    name = event.stock.name or event.stock.code
    return f"""다음 종목의 가격 이벤트에 대한 인과관계를 분석하라(관찰 보고서, 추천 금지).

종목: {name} ({event.stock.code})
관찰일: {event.trade_date.isoformat()}

[정량 사실 — 재계산 금지]
{quant}
{_canslim_block(canslim)}

{context_block}

[당일/전일 뉴스]
{articles_text or "선택된 기사 없음"}

JSON만 출력하라."""
