"""전략 에이전트 — 상한가/거래량 폭발 종목의 인과관계 분석 오케스트레이션.

흐름: 정량(Pandas CAN SLIM) → 맥락 주입(Phase1 ContextService) → 뉴스 →
LLM 구조화 추론(JSON Schema) → AnalysisReport(COMPOSITE) 저장.
LLM은 주입(injectable)이라 테스트에서 fake로 대체 가능.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from core.models import AnalysisReport
from features.strategy.canslim import screen_canslim
from features.strategy.prompts import CAUSAL_SYSTEM_PROMPT, build_causal_prompt
from features.strategy.schemas import CausalityRequest, CausalityResponse
from services.context import ContextService
from services.llm.adapter import llm_adapter
from services.llm.schemas import CausalAnalysisJson
from storage.repositories import reports as report_repo


class CausalityService:
    def __init__(self, llm=None, context_service_factory=None):
        self._llm = llm if llm is not None else llm_adapter
        self._ctx_factory = context_service_factory or ContextService

    async def analyze(
        self, db: Session, req: CausalityRequest, persist: bool = True
    ) -> CausalityResponse:
        event = req.event

        canslim = None
        if req.candles:
            canslim = screen_canslim(event.stock, req.candles)

        ctx = self._ctx_factory(db).build_context(
            base_date=event.trade_date, stock_code=event.stock.code
        )
        context_block = ContextService.to_prompt_block(ctx)

        articles_text = "\n".join(f"- {a.title} ({a.url})" for a in req.articles)
        user_prompt = build_causal_prompt(event, context_block, articles_text, canslim)

        result: CausalAnalysisJson = await self._llm.generate_structured(
            CAUSAL_SYSTEM_PROMPT, user_prompt, CausalAnalysisJson
        )

        sources = ["price"]
        if req.articles:
            sources.append("news")
        if canslim is not None:
            sources.append("canslim")
        if ctx.relevant_events or ctx.group or ctx.narratives or ctx.recent_digests:
            sources.append("context")

        report = AnalysisReport(
            stock=event.stock,
            base_date=event.trade_date,
            report_type="COMPOSITE",
            summary=result.summary,
            key_points=([result.primary_driver] if result.primary_driver else [])
            + result.causal_factors,
            possible_reasons=result.causal_factors + result.context_links,
            risks=result.risks,
            confidence=result.confidence,
            sources=sources,
            article_urls=[a.url for a in req.articles],
        )
        if persist:
            report = report_repo.save_report(db, report)
        return CausalityResponse(report=report, canslim=canslim)


causality_service = CausalityService()
