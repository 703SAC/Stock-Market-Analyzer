"""모니터링 에이전트 — 장마감 일일 리포트 파이프라인.

흐름(루프를 닫는 핵심): 특징주 로그 → Gemini 일일 종합시황 → **맥락 저장소(market_digest)에
역기록** → 텔레그램 발송. 이렇게 쓰인 종합시황을 다음날 시장판단/전략 에이전트가 읽는다.
LLM/notifier는 주입 가능(테스트). 스케줄러가 session별로 run_daily_close를 호출한다.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from core.models import MarketDigest, MarketSession
from features.monitor.prompts import DAILY_SYSTEM_PROMPT, build_daily_report_prompt
from features.monitor.schemas import DailyReportRequest, DailyReportResult
from services.llm.adapter import llm_adapter
from services.llm.schemas import DailyDigestJson
from services.telegram.adapter import get_notifier
from storage.repositories import context as ctx_repo


def _format_telegram(digest: MarketDigest) -> str:
    themes = ", ".join(digest.key_themes) if digest.key_themes else "-"
    return (
        f"[{digest.digest_date} {digest.session}] {digest.title}\n"
        f"{digest.summary}\n"
        f"테마: {themes}"
    )


class MonitorService:
    def __init__(self, llm=None, notifier=None):
        self._llm = llm if llm is not None else llm_adapter
        self._notifier = notifier  # None이면 호출 시점에 기본 notifier 사용

    async def run_daily_close(
        self,
        db: Session,
        base_date: date,
        session: MarketSession = "KR_DAY",
        events=None,
        persist: bool = True,
    ) -> DailyReportResult:
        events = events or []
        user_prompt = build_daily_report_prompt(
            base_date.isoformat(), session, events
        )
        result: DailyDigestJson = await self._llm.generate_structured(
            DAILY_SYSTEM_PROMPT, user_prompt, DailyDigestJson
        )

        digest = MarketDigest(
            digest_date=base_date,
            session=session,
            title=result.title,
            summary=result.summary,
            key_themes=result.key_themes,
            source="monitor-agent",
        )

        persisted = False
        if persist:
            digest = ctx_repo.upsert_market_digest(db, digest)  # ← 맥락 저장소 역기록
            persisted = True

        notifier = self._notifier or get_notifier()
        telegram = await notifier.send(
            _format_telegram(digest),
            dedupe_key=f"digest:{base_date.isoformat()}:{session}",
        )

        return DailyReportResult(digest=digest, telegram=telegram, persisted=persisted)

    async def run_for_request(
        self, db: Session, req: DailyReportRequest, persist: bool = True
    ) -> DailyReportResult:
        return await self.run_daily_close(
            db, req.base_date, req.session, events=req.events, persist=persist
        )


monitor_service = MonitorService()
