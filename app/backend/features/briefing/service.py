"""시장 판단 에이전트 — 타임라인별 메가 내러티브 종합 브리핑.

흐름: 타임라인 프로파일 선택 → 시장 전반 맥락 조립(Phase1 ContextService, stock_code=None)
→ 뉴스 결합 → LLM 구조화 브리핑(JSON Schema). LLM/맥락서비스는 주입 가능(테스트).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from features.briefing.prompts import BRIEFING_SYSTEM_PROMPT, build_briefing_prompt
from features.briefing.schemas import BriefingRequest, BriefingResponse, MarketBriefing
from features.briefing.timeline import get_profile
from services.context import ContextService
from services.llm.adapter import llm_adapter
from services.llm.schemas import MarketBriefingJson


class BriefingService:
    def __init__(self, llm=None, context_service_factory=None):
        self._llm = llm if llm is not None else llm_adapter
        self._ctx_factory = context_service_factory or ContextService

    async def create_briefing(
        self, db: Session, req: BriefingRequest
    ) -> BriefingResponse:
        profile = get_profile(req.timeline)

        ctx = self._ctx_factory(db).build_context(
            base_date=req.base_date,
            stock_code=None,  # 시장 전반
            digest_lookback_days=profile.digest_lookback_days,
            event_window_days=profile.event_window_days,
        )
        context_block = ContextService.to_prompt_block(ctx)

        articles_text = "\n".join(f"- {a.title} ({a.url})" for a in req.articles)
        user_prompt = build_briefing_prompt(
            profile, req.base_date.isoformat(), context_block, articles_text
        )

        content: MarketBriefingJson = await self._llm.generate_structured(
            BRIEFING_SYSTEM_PROMPT, user_prompt, MarketBriefingJson
        )

        sources = ["context"]
        if req.articles:
            sources.append("news")

        briefing = MarketBriefing(
            base_date=req.base_date,
            timeline=req.timeline,
            label=profile.label,
            content=content,
            sources=sources,
        )
        return BriefingResponse(briefing=briefing)


briefing_service = BriefingService()
