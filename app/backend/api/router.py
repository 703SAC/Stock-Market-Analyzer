"""API router aggregation."""

from fastapi import APIRouter

from api import briefing, health, monitor, news, reports, screener, strategy

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(screener.router)
api_router.include_router(news.router)
api_router.include_router(reports.router)
api_router.include_router(strategy.router)
api_router.include_router(briefing.router)
api_router.include_router(monitor.router)
