from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ai_sdr_platform.src.agents.crm.models import (
    CRMStatus,
    CRMSyncRecord,
    CRMSyncRequest,
)
from ai_sdr_platform.src.agents.crm.providers import CRMProvider
from ai_sdr_platform.src.agents.crm.repository import SQLAlchemyCRMRepository


@dataclass
class CRMService:
    repository: SQLAlchemyCRMRepository
    provider: CRMProvider

    def sync(self, request: CRMSyncRequest) -> CRMSyncRecord:
        existing = self.repository.get_by_meeting(request.meeting_id)
        if existing and existing.status == "synced":
            return existing
        record = existing or CRMSyncRecord(
            meeting_id=request.meeting_id,
            provider=self.provider.name,
        )
        try:
            result = self.provider.sync(request)
            record.company_id = result.get("company_id")
            record.person_id = result.get("person_id")
            record.opportunity_id = result.get("opportunity_id")
            record.provider_payload = result
            record.status = "synced"
            record.error = None
        except Exception as exc:
            record.status = "failed"
            record.error = str(exc)
        record.updated_at = datetime.now(timezone.utc)
        return self.repository.save(record)

    def list(self) -> list[CRMSyncRecord]:
        return self.repository.list()

    def get_by_meeting(self, meeting_id: str) -> CRMSyncRecord | None:
        return self.repository.get_by_meeting(meeting_id)

    def status(self) -> CRMStatus:
        return CRMStatus(
            provider=self.provider.name,
            configured=self.provider.configured(),
            detail=(
                "CRM writes are sent to the configured provider."
                if self.provider.configured()
                else "CRM credentials are incomplete."
            ),
        )
