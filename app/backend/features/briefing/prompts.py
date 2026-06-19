"""시장 판단 에이전트 — 메가 내러티브 종합 브리핑 프롬프트."""

from __future__ import annotations

from features.briefing.timeline import TimelineProfile

BRIEFING_SYSTEM_PROMPT = """You are a Korean market strategist writing a market-wide briefing.
Output ONLY valid JSON matching this schema:
{
  "headline": "one line",
  "market_summary": "short paragraph",
  "key_narratives": ["mega-narratives, not single-day fragments"],
  "sector_highlights": ["..."],
  "watch_items": ["things to verify/watch next"],
  "risks": ["..."],
  "confidence": "LOW|MEDIUM|HIGH"
}
Rules:
- Never give buy/sell advice. Use tentative language.
- See the forest: synthesize the provided cumulative context (digests, schedule, group dynamics, narratives), not just today's headlines.
- Only use facts from the provided context and news. Do not invent figures.
- If context is sparse, set confidence to LOW and say what is missing.
"""


def build_briefing_prompt(
    profile: TimelineProfile,
    base_date: str,
    context_block: str,
    articles_text: str,
) -> str:
    return f"""[{profile.label}] {base_date}

관점: {profile.emphasis}

{context_block}

[관련 뉴스]
{articles_text or "수집된 뉴스 없음"}

위 누적 맥락과 뉴스를 종합해 '숲'을 보는 시황 브리핑을 JSON으로만 작성하라."""
