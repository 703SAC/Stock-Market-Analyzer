"""Stock Market Analyzer API entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from config import get_settings
from storage.db import SessionLocal, init_db


async def _run_daily_close(session: str) -> None:
    """스케줄러 콜백: 모니터링 에이전트 일일 마감 리포트 실행."""
    from datetime import date

    from features.monitor.service import monitor_service

    db = SessionLocal()
    try:
        await monitor_service.run_daily_close(db, date.today(), session=session)  # type: ignore[arg-type]
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    scheduler = None
    if settings.scheduler_enabled:
        from services.scheduler import build_scheduler

        scheduler = build_scheduler(_run_daily_close, tz=settings.market_tz)
        scheduler.start()
        app.state.scheduler = scheduler
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Stock Market Analyzer",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
