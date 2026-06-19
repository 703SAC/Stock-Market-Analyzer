"""시장 판단 에이전트 API 라우트."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from features.briefing.schemas import BriefingRequest
from features.briefing.service import briefing_service
from storage.db import get_db

router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.post("")
async def create_briefing(
    body: BriefingRequest,
    db: Session = Depends(get_db),
):
    try:
        return await briefing_service.create_briefing(db, body)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
