from fastapi import APIRouter, Depends, HTTPException

from ai_sdr_platform.src.agents.crm.models import (
    CRMStatus,
    CRMSyncListResponse,
    CRMSyncRecord,
)
from ai_sdr_platform.src.agents.crm.providers import (
    DryRunCRMProvider,
    TwentyCRMProvider,
)
from ai_sdr_platform.src.agents.crm.repository import SQLAlchemyCRMRepository
from ai_sdr_platform.src.agents.crm.service import CRMService
from ai_sdr_platform.src.shared.config import settings

router = APIRouter(prefix="/crm", tags=["crm"])
_repository = SQLAlchemyCRMRepository()


def _provider():
    if settings.crm_provider == "twenty":
        return TwentyCRMProvider(
            base_url=settings.crm_twenty_base_url,
            api_key=settings.crm_twenty_api_key,
            people_object=settings.crm_twenty_people_object,
            companies_object=settings.crm_twenty_companies_object,
            opportunities_object=settings.crm_twenty_opportunities_object,
        )
    return DryRunCRMProvider()


_service = CRMService(repository=_repository, provider=_provider())


def configure_crm_service() -> CRMService:
    global _service
    _service = CRMService(repository=_repository, provider=_provider())
    return _service


def get_crm_service() -> CRMService:
    return _service


@router.get("/status", response_model=CRMStatus)
def crm_status(service: CRMService = Depends(get_crm_service)) -> CRMStatus:
    return service.status()


@router.get("/syncs", response_model=CRMSyncListResponse)
def list_syncs(service: CRMService = Depends(get_crm_service)) -> CRMSyncListResponse:
    items = service.list()
    return CRMSyncListResponse(items=items, total=len(items))


@router.get("/syncs/{meeting_id}", response_model=CRMSyncRecord)
def get_sync(
    meeting_id: str, service: CRMService = Depends(get_crm_service)
) -> CRMSyncRecord:
    record = service.get_by_meeting(meeting_id)
    if record is None:
        raise HTTPException(status_code=404, detail="CRM sync not found.")
    return record
