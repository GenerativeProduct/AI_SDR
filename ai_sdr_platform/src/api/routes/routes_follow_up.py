from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ai_sdr_platform.src.agents.follow_up.models import (
    FollowUpApprovalRequest,
    FollowUpListResponse,
    FollowUpPlan,
    FollowUpPlanRequest,
    FollowUpSchedulerStatus,
)
from ai_sdr_platform.src.agents.follow_up.repository import SQLAlchemyFollowUpRepository
from ai_sdr_platform.src.agents.follow_up.service import FollowUpService
from ai_sdr_platform.src.api.routes.routes_outreach import get_outreach_service

router = APIRouter(prefix="/follow-up", tags=["follow-up"])
_repository = SQLAlchemyFollowUpRepository()
_service = FollowUpService(
    repository=_repository,
    outreach_service=get_outreach_service(),
    scheduler_backend="temporal",
)


def configure_follow_up_service() -> FollowUpService:
    global _service
    _service = FollowUpService(
        repository=_repository,
        outreach_service=get_outreach_service(),
        scheduler_backend="temporal",
    )
    return _service


def get_follow_up_service() -> FollowUpService:
    return _service


@router.post("/plans", response_model=FollowUpPlan)
def create_plan(
    payload: FollowUpPlanRequest,
    service: FollowUpService = Depends(get_follow_up_service),
) -> FollowUpPlan:
    try:
        return service.create_plan(payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/plans", response_model=FollowUpListResponse)
def list_plans(
    status: str | None = Query(default=None),
    service: FollowUpService = Depends(get_follow_up_service),
) -> FollowUpListResponse:
    items = service.list(status)
    return FollowUpListResponse(items=items, total=len(items))


@router.get("/scheduler/status", response_model=FollowUpSchedulerStatus)
def scheduler_status(
    service: FollowUpService = Depends(get_follow_up_service),
) -> FollowUpSchedulerStatus:
    return service.scheduler_status()


@router.get("/plans/{plan_id}", response_model=FollowUpPlan)
def get_plan(
    plan_id: str,
    service: FollowUpService = Depends(get_follow_up_service),
) -> FollowUpPlan:
    plan = service.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Follow-up plan not found.")
    return plan


@router.post("/plans/{plan_id}/approve", response_model=FollowUpPlan)
def approve_plan(
    plan_id: str,
    payload: FollowUpApprovalRequest,
    service: FollowUpService = Depends(get_follow_up_service),
) -> FollowUpPlan:
    try:
        return service.approve(plan_id, payload.approved_by)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/scheduler/run-due", response_model=list[FollowUpPlan])
def process_due(
    force: bool = Query(default=False),
    service: FollowUpService = Depends(get_follow_up_service),
) -> list[FollowUpPlan]:
    return service.process_due(force=force)


@router.post("/scheduler/run-plan/{plan_id}", response_model=FollowUpPlan)
def process_plan(
    plan_id: str,
    force: bool = Query(default=False),
    service: FollowUpService = Depends(get_follow_up_service),
) -> FollowUpPlan:
    try:
        return service.process_plan(plan_id, force=force)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
