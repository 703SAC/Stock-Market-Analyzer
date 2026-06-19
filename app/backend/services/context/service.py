"""ContextService — 메가 내러티브 맥락 조립 및 프롬프트 주입.

목적: LLM이 당일 뉴스 파편만 보지 않고, 누적된 종합시황/일정/그룹사 역학/내러티브를
'맥락 블록'으로 함께 받도록 한다. 환각 방지를 위해 저장된 사실만 결정적으로 직렬화하며,
이 단계에서 LLM 호출이나 추론은 하지 않는다(순수 조립).
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from core.models import MarketContext, MarketSession
from storage.repositories import context as repo


class ContextService:
    """저장소에서 종목+날짜 기준 맥락을 조립하고 프롬프트 텍스트로 렌더링."""

    def __init__(self, db: Session):
        self.db = db

    def build_context(
        self,
        base_date: date,
        stock_code: str | None = None,
        digest_lookback_days: int = 5,
        digest_limit: int = 3,
        event_window_days: int = 7,
        max_narratives: int = 5,
        session: MarketSession | None = None,
    ) -> MarketContext:
        """base_date 기준으로 다차원 맥락을 조립한다.

        - recent_digests: 최근 종합시황(최신순)
        - relevant_events: [base_date - lookback, base_date + window] 범위 일정
        - group / peer_group: 종목의 그룹사·테마 및 동일 그룹 종목
        - narratives: 최근 누적 내러티브(종목 연관 필터)
        """
        digests = repo.get_recent_digests(
            self.db, before_date=base_date, session=session, limit=digest_limit
        )

        events = repo.get_events_in_range(
            self.db,
            start=base_date - timedelta(days=digest_lookback_days),
            end=base_date + timedelta(days=event_window_days),
            stock_code=stock_code,
        )

        group = None
        peers = []
        if stock_code is not None:
            group = repo.get_group_map(self.db, stock_code)
            if group is not None and group.group_name:
                peers = [
                    p
                    for p in repo.get_group_peers(self.db, group.group_name)
                    if p.stock_code != stock_code
                ]

        narratives = repo.get_recent_narratives(
            self.db, before_date=base_date, stock_code=stock_code, limit=max_narratives
        )

        return MarketContext(
            base_date=base_date,
            stock_code=stock_code,
            recent_digests=digests,
            relevant_events=events,
            group=group,
            peer_group=peers,
            narratives=narratives,
        )

    @staticmethod
    def to_prompt_block(ctx: MarketContext) -> str:
        """맥락을 결정적(deterministic) 한국어 텍스트 블록으로 직렬화.

        LLM 프롬프트에 그대로 삽입한다. 저장된 사실만 나열하며 추론을 추가하지 않는다.
        데이터가 없으면 빈 블록 대신 명시적 '없음'을 적어 환각을 억제한다.
        """
        lines: list[str] = ["[메가 내러티브 맥락]"]

        lines.append("## 최근 종합 시황")
        if ctx.recent_digests:
            for d in ctx.recent_digests:
                themes = ", ".join(d.key_themes) if d.key_themes else "-"
                lines.append(
                    f"- {d.digest_date} ({d.session}) {d.title}: {d.summary} [테마: {themes}]"
                )
        else:
            lines.append("- 기록된 종합 시황 없음")

        lines.append("## 관련 일정")
        if ctx.relevant_events:
            for e in ctx.relevant_events:
                tgt = f" 종목 {e.stock_code}" if e.stock_code else ""
                lines.append(
                    f"- {e.event_date} [{e.category}/{e.importance}]{tgt} {e.title}"
                )
        else:
            lines.append("- 등록된 일정 없음")

        lines.append("## 그룹사 / 테마 역학")
        if ctx.group is not None:
            themes = ", ".join(ctx.group.themes) if ctx.group.themes else "-"
            name = ctx.group.stock_name or ctx.group.stock_code
            lines.append(
                f"- 대상: {name}({ctx.group.stock_code}) / 그룹: {ctx.group.group_name or '-'} / 테마: {themes}"
            )
            if ctx.peer_group:
                peers = ", ".join(
                    f"{p.stock_name or p.stock_code}({p.stock_code})" for p in ctx.peer_group
                )
                lines.append(f"- 동일 그룹 종목: {peers}")
        else:
            lines.append("- 그룹/테마 매핑 없음")

        lines.append("## 누적 내러티브")
        if ctx.narratives:
            for n in ctx.narratives:
                codes = f" ({', '.join(n.stock_codes)})" if n.stock_codes else ""
                lines.append(f"- [{n.as_of_date}] {n.topic}{codes}: {n.narrative}")
        else:
            lines.append("- 누적 내러티브 없음")

        return "\n".join(lines)
