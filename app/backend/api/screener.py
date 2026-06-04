"""Screener API routes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from features.screener.schemas import ScreenerQuery
from features.screener.service import screener_service
from storage.db import get_db

router = APIRouter(prefix="/screener", tags=["screener"])


@router.get("/events/export.csv", response_class=PlainTextResponse)
async def export_events_csv(
    start_date: date = Query(...),
    end_date: date = Query(...),
    min_volume: int = Query(default=10_000_000, ge=0),
    include_upper_limit: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    query = ScreenerQuery(
        start_date=start_date,
        end_date=end_date,
        min_volume=min_volume,
        include_upper_limit=include_upper_limit,
    )
    result = await screener_service.find_events(db, query)
    csv_text = screener_service.events_to_csv(result.events)
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=screener_events.csv"
        },
    )


@router.get("/events")
async def get_events(
    start_date: date = Query(...),
    end_date: date = Query(...),
    min_volume: int = Query(default=10_000_000, ge=0),
    include_upper_limit: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    query = ScreenerQuery(
        start_date=start_date,
        end_date=end_date,
        min_volume=min_volume,
        include_upper_limit=include_upper_limit,
    )
    try:
        return await screener_service.find_events(db, query)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/events/{event_id}")
async def get_event(
    event_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    min_volume: int = Query(default=10_000_000, ge=0),
    include_upper_limit: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    query = ScreenerQuery(
        start_date=start_date,
        end_date=end_date,
        min_volume=min_volume,
        include_upper_limit=include_upper_limit,
    )
    event = await screener_service.get_event_by_id(db, event_id, query)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
