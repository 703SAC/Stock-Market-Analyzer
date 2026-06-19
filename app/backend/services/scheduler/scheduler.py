"""APScheduler 기반 낮(국장)/밤(미장) 교대 스케줄.

잡 정의(JobSpec)는 순수 데이터라 테스트 가능. APScheduler import는 build_scheduler
안에서만 발생하여, 스케줄러 미사용 환경/테스트가 강제 의존하지 않게 한다.
실제 기동은 config.scheduler_enabled가 True일 때만(main.py lifespan).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from core.models import MarketSession


@dataclass(frozen=True)
class JobSpec:
    id: str
    session: MarketSession
    hour: int
    minute: int
    day_of_week: str  # APScheduler cron 표기, 예: "mon-fri"


# KR_DAY: 국장 마감(15:30) 직후 정리. US_NIGHT: 미장 마감 후 KST 아침에 정리.
DEFAULT_JOBS: list[JobSpec] = [
    JobSpec(id="kr_day_close", session="KR_DAY", hour=15, minute=40, day_of_week="mon-fri"),
    JobSpec(id="us_night_close", session="US_NIGHT", hour=6, minute=30, day_of_week="tue-sat"),
]


def build_scheduler(
    run_callback: Callable[..., Awaitable[None]],
    jobs: list[JobSpec] | None = None,
    tz: str = "Asia/Seoul",
):
    """주어진 잡을 등록한 AsyncIOScheduler 반환(미기동 상태). run_callback(session=...)."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    jobs = jobs if jobs is not None else DEFAULT_JOBS
    scheduler = AsyncIOScheduler(timezone=tz)
    for spec in jobs:
        scheduler.add_job(
            run_callback,
            CronTrigger(
                day_of_week=spec.day_of_week,
                hour=spec.hour,
                minute=spec.minute,
                timezone=tz,
            ),
            id=spec.id,
            kwargs={"session": spec.session},
            replace_existing=True,
        )
    return scheduler
