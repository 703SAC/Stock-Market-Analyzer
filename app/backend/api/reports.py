"""Reports API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from features.reports.schemas import NewsPriceReportRequest
from features.reports.service import report_service
from storage.db import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/news-price")
async def create_news_price_report(
    body: NewsPriceReportRequest,
    db: Session = Depends(get_db),
):
    try:
        return await report_service.create_news_price_report(db, body)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    report = await report_service.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
