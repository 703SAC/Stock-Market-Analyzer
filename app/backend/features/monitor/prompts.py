"""모니터링 에이전트 — 장마감 일일 리포트 프롬프트."""

from __future__ import annotations

from core.models import TradingDayStockEvent

DAILY_SYSTEM_PROMPT = """You are a Korean market desk assistant writing an end-of-session digest.
Output ONLY valid JSON matching this schema:
{
  "title": "one line",
  "summary": "short paragraph",
  "key_themes": ["..."],
  "watch_items": ["things to watch next session"],
  "risks": ["..."],
  "confidence": "LOW|MEDIUM|HIGH"
}
Rules:
- Never give buy/sell advice. Use tentative language.
- Base the digest ONLY on the provided event log (volume/limit-up movers). Do not invent tickers or figures.
- If the event log is empty, say so and set confidence to LOW.
"""

_SESSION_LABEL = {"KR_DAY": "국내장 마감", "US_NIGHT": "미국장 마감", "GLOBAL": "글로벌"}


def _events_text(events: list[TradingDayStockEvent]) -> str:
    if not events:
        return "특징주 로그 없음"
    lines = []
    for e in events[:30]:
        name = e.stock.name or e.stock.code
        lines.append(
            f"- {name}({e.stock.code}) [{', '.join(e.event_types)}] "
            f"거래량={e.volume} 등락률={e.change_rate} 종가={e.price}"
        )
    return "\n".join(lines)


def build_daily_report_prompt(
    base_date: str, session: str, events: list[TradingDayStockEvent]
) -> str:
    label = _SESSION_LABEL.get(session, session)
    return f"""[{label} 일일 종합] {base_date}

특징주 로그(거래량/상한가):
{_events_text(events)}

위 로그를 근거로 오늘 시장의 종합 시황을 JSON으로만 작성하라."""
