from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class CRMSyncRequest(BaseModel):
    meeting_id: str
    account_id: str
    contact_id: str
    company_name: str
    contact_name: str
    contact_email: str
    meeting_start: datetime
    meeting_url: str
    qualification_status: str | None = None


class CRMSyncRecord(BaseModel):
    sync_id: str = Field(default_factory=lambda: str(uuid4()))
    meeting_id: str
    provider: str
    status: Literal["pending", "synced", "failed"] = "pending"
    company_id: str | None = None
    person_id: str | None = None
    opportunity_id: str | None = None
    provider_payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CRMSyncListResponse(BaseModel):
    items: list[CRMSyncRecord]
    total: int


class CRMStatus(BaseModel):
    provider: str
    configured: bool
    detail: str
