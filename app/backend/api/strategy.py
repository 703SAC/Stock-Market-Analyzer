"""전략 에이전트 API 라우트."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from features.strategy.causality import causality_service
from features.strategy.schemas import CausalityRequest
from storage.db import get_db

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.post("/causality")
async def analyze_causality(
    body: CausalityRequest,
    db: Session = Depends(get_db),
):
    try:
        return await causality_service.analyze(db, body)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
