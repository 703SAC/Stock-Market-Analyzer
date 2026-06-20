"""Context store inspection API routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.models import MarketSession
from services.context import ContextService
from storage.db import get_db
from storage.repositories import context as context_repo

router = APIRouter(prefix="/context", tags=["context"])


@router.get("/digests")
async def list_digests(
    before_date: date = Query(...),
    session: MarketSession | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return {
        "digests": context_repo.get_recent_digests(
            db, before_date=before_date, session=session, limit=limit
        )
    }


@router.get("/events")
async def list_calendar_events(
    start_date: date = Query(...),
    end_date: date = Query(...),
    stock_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return {
        "events": context_repo.get_events_in_range(
            db, start=start_date, end=end_date, stock_code=stock_code
        )
    }


@router.get("/stock/{stock_code}")
async def get_stock_context(
    stock_code: str,
    base_date: date = Query(...),
    db: Session = Depends(get_db),
):
    service = ContextService(db)
    context = service.build_context(base_date=base_date, stock_code=stock_code)
    return {
        "context": context,
        "prompt_block": ContextService.to_prompt_block(context),
    }


@router.get("/overview")
async def get_context_overview(
    base_date: date = Query(...),
    session: MarketSession | None = Query(default=None),
    db: Session = Depends(get_db),
):
    start = base_date - timedelta(days=14)
    end = base_date + timedelta(days=14)
    return {
        "digests": context_repo.get_recent_digests(
            db, before_date=base_date, session=session, limit=10
        ),
        "events": context_repo.get_events_in_range(db, start=start, end=end),
        "narratives": context_repo.get_recent_narratives(db, before_date=base_date, limit=10),
    }

