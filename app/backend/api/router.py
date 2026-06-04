"""API router aggregation."""

from fastapi import APIRouter

from api import health, news, reports, screener

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(screener.router)
api_router.include_router(news.router)
api_router.include_router(reports.router)
