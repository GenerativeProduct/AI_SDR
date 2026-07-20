from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ai_sdr_platform.src.agents.qualification.models import (
    QualificationListResponse,
    QualificationRequest,
    QualificationResult,
)
from ai_sdr_platform.src.agents.qualification.repository import (
    SQLAlchemyQualificationRepository,
)
from ai_sdr_platform.src.agents.qualification.service import QualificationService

router = APIRouter(prefix="/qualification", tags=["qualification"])
_repository = SQLAlchemyQualificationRepository()
_service = QualificationService(repository=_repository)


def configure_qualification_service() -> QualificationService:
    global _service
    _service = QualificationService(repository=_repository)
    return _service


def get_qualification_service() -> QualificationService:
    return _service


@router.post("/evaluate", response_model=QualificationResult)
def evaluate_qualification(
    payload: QualificationRequest,
    service: QualificationService = Depends(get_qualification_service),
) -> QualificationResult:
    try:
        return service.qualify(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=QualificationListResponse)
def list_qualification_results(
    account_id: str | None = Query(default=None),
    service: QualificationService = Depends(get_qualification_service),
) -> QualificationListResponse:
    items = service.list_results(account_id)
    return QualificationListResponse(items=items, total=len(items))


@router.get("/{contact_id}", response_model=QualificationResult)
def get_qualification_result(
    contact_id: str,
    service: QualificationService = Depends(get_qualification_service),
) -> QualificationResult:
    result = service.get_latest(contact_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Qualification result not found.")
    return result
