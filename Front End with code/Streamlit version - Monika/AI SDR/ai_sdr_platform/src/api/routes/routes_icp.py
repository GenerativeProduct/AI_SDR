from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ai_sdr_platform.src.agents.icp.models import (
    ICPCreateRequest,
    ICPDefinition,
    ICPListResponse,
    ICPSuggestionRequest,
    ICPSuggestionResponse,
    ICPUpdateRequest,
    ICPValidationResult,
)
from ai_sdr_platform.src.agents.icp.repository import SQLAlchemyICPRepository
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.agents.icp.suggestions import LLMSuggestionProvider
from ai_sdr_platform.src.shared.exceptions import ICPValidationError

router = APIRouter(prefix="/icp", tags=["icp-agent"])
_repository = SQLAlchemyICPRepository()
_service = ICPService(repository=_repository)


def configure_icp_service(llm_router: object | None = None) -> ICPService:
    global _service
    _service = ICPService(
        repository=_repository,
        suggestion_provider=LLMSuggestionProvider(llm_router) if llm_router is not None else None,
    )
    return _service


def get_icp_service() -> ICPService:
    return _service


@router.post("/validate", response_model=ICPValidationResult)
def validate_icp(payload: ICPCreateRequest, service: ICPService = Depends(get_icp_service)) -> ICPValidationResult:
    try:
        return service.validate_only(payload)
    except ICPValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/suggest", response_model=ICPSuggestionResponse)
def suggest_icp(payload: ICPSuggestionRequest, service: ICPService = Depends(get_icp_service)) -> ICPSuggestionResponse:
    return service.suggest(payload)


@router.post("", response_model=ICPValidationResult)
def create_icp(payload: ICPCreateRequest, service: ICPService = Depends(get_icp_service)) -> ICPValidationResult:
    try:
        return service.create_icp(payload)
    except ICPValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{icp_id}", response_model=ICPValidationResult)
def update_icp(icp_id: str, payload: ICPUpdateRequest, service: ICPService = Depends(get_icp_service)) -> ICPValidationResult:
    try:
        return service.update_icp(icp_id, payload)
    except ICPValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=ICPListResponse)
def list_icps(service: ICPService = Depends(get_icp_service)) -> ICPListResponse:
    return service.list_icps()


@router.get("/{icp_id}", response_model=ICPDefinition)
def get_icp(icp_id: str, version: int | None = Query(default=None), service: ICPService = Depends(get_icp_service)) -> ICPDefinition:
    icp = service.get_icp(icp_id, version=version)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    return icp


@router.get("/{icp_id}/versions", response_model=list[ICPDefinition])
def get_icp_versions(icp_id: str, service: ICPService = Depends(get_icp_service)) -> list[ICPDefinition]:
    return service.list_versions(icp_id)
