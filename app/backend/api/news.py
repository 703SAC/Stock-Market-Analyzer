"""News API routes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from features.news.schemas import NewsRefreshRequest, NewsSearchQuery
from features.news.service import news_service
from services.news.errors import NewsProviderError
from storage.db import get_db

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/search")
async def search_news(
    stock_code: str = Query(...),
    base_date: date = Query(...),
    stock_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = NewsSearchQuery(
        stock_code=stock_code,
        stock_name=stock_name,
        base_date=base_date,
    )
    try:
        return await news_service.search(db, query)
    except NewsProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/refresh")
async def refresh_news(
    body: NewsRefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        return await news_service.refresh(db, body)
    except NewsProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
