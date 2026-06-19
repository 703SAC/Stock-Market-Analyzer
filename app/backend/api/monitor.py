"""모니터링 에이전트 API 라우트."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from features.monitor.schemas import DailyReportRequest
from features.monitor.service import monitor_service
from storage.db import get_db

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.post("/daily-report")
async def run_daily_report(
    body: DailyReportRequest,
    db: Session = Depends(get_db),
):
    """장마감 일일 리포트 생성 → 맥락 저장소 역기록 → 텔레그램(설정 시)."""
    try:
        return await monitor_service.run_for_request(db, body)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
