from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class FollowUpTouch(BaseModel):
    touch_id: str = Field(default_factory=lambda: str(uuid4()))
    sequence_order: int = Field(ge=1)
    delay_hours: int = Field(ge=1, le=24 * 90)
    channel: Literal["email", "linkedin", "phone", "sms", "whatsapp"] = "email"
    subject: str | None = None
    body: str
    scheduled_at: datetime
    status: Literal[
        "pending_approval", "approved", "queued", "sent", "human_task",
        "failed", "suppressed",
    ] = "pending_approval"
    provider_message_id: str | None = None
    sent_at: datetime | None = None


class FollowUpPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    contact_id: str
    status: Literal["pending_approval", "active", "paused", "stopped", "completed"] = (
        "pending_approval"
    )
    touches: list[FollowUpTouch] = Field(default_factory=list)
    approved_by: str | None = None
    stop_reason: str | None = None
    scheduler_backend: Literal["local", "temporal"] = "local"
    temporal_workflow_id: str | None = None
    temporal_schedule_status: Literal["not_started", "started", "failed"] = (
        "not_started"
    )
    temporal_error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FollowUpPlanRequest(BaseModel):
    campaign_id: str
    delays_hours: list[int] = Field(default_factory=lambda: [72, 168])
    require_approval: bool = True


class FollowUpApprovalRequest(BaseModel):
    approved_by: str


class FollowUpListResponse(BaseModel):
    items: list[FollowUpPlan]
    total: int


class FollowUpSchedulerStatus(BaseModel):
    configured_backend: Literal["local", "temporal"]
    temporal_enabled: bool
    temporal_host: str
    temporal_namespace: str
    temporal_task_queue: str
    detail: str
