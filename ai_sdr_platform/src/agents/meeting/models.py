from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


MeetingStatus = Literal[
    "awaiting_approval",
    "approved",
    "booking",
    "booked",
    "cancelled",
    "failed",
]


class MeetingDraftRequest(BaseModel):
    conversation_id: str


class MeetingScheduleRequest(BaseModel):
    start_at: datetime
    timezone: str = "UTC"
    duration_minutes: int = Field(default=30, ge=15, le=240)
    approved_by: str
    title: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_timezone_aware_start(self) -> "MeetingScheduleRequest":
        if self.start_at.tzinfo is None:
            raise ValueError("start_at must include a timezone offset.")
        return self


class MeetingBooking(BaseModel):
    meeting_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    campaign_id: str
    intelligence_id: str
    account_id: str
    contact_id: str
    company_name: str
    contact_name: str
    attendee_email: str
    organizer_email: str | None = None
    title: str
    description: str = ""
    timezone: str = "UTC"
    duration_minutes: int = Field(default=30, ge=15, le=240)
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: MeetingStatus = "awaiting_approval"
    provider: str = "dry_run"
    provider_event_id: str | None = None
    meeting_url: str | None = None
    calendar_url: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    crm_sync_status: Literal["not_started", "synced", "failed"] = "not_started"
    crm_sync_id: str | None = None
    temporal_workflow_id: str | None = None
    temporal_status: Literal["not_started", "started", "failed"] = "not_started"
    provider_payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("attendee_email", "organizer_email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is not None and ("@" not in value or value.startswith("@")):
            raise ValueError("A valid email address is required.")
        return value


class MeetingListResponse(BaseModel):
    items: list[MeetingBooking]
    total: int


class MeetingProviderStatus(BaseModel):
    provider: str
    configured: bool
    calendar_id: str | None = None
    crm_provider: str
    crm_configured: bool
    detail: str


class MeetingCancelRequest(BaseModel):
    reason: str = "Cancelled by SDR"
