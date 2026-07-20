from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

import httpx

from ai_sdr_platform.src.agents.crm.models import CRMSyncRequest


class CRMProvider(Protocol):
    name: str

    def configured(self) -> bool: ...
    def sync(self, request: CRMSyncRequest) -> dict[str, Any]: ...


@dataclass
class DryRunCRMProvider:
    name: str = "dry_run"

    def configured(self) -> bool:
        return True

    def sync(self, request: CRMSyncRequest) -> dict[str, Any]:
        return {
            "company_id": f"dry-company-{uuid4()}",
            "person_id": f"dry-person-{uuid4()}",
            "opportunity_id": f"dry-opportunity-{uuid4()}",
            "mode": "dry_run",
        }


@dataclass
class TwentyCRMProvider:
    base_url: str
    api_key: str
    people_object: str = "people"
    companies_object: str = "companies"
    opportunities_object: str = "opportunities"
    timeout_seconds: float = 20.0
    name: str = "twenty"

    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def sync(self, request: CRMSyncRequest) -> dict[str, Any]:
        if not self.configured():
            raise RuntimeError("Twenty CRM base URL and API key are required.")
        company = self._create(
            self.companies_object,
            {"name": request.company_name},
        )
        first_name, _, last_name = request.contact_name.partition(" ")
        person = self._create(
            self.people_object,
            {
                "name": {"firstName": first_name, "lastName": last_name},
                "emails": {
                    "primaryEmail": request.contact_email,
                    "additionalEmails": [],
                },
            },
        )
        opportunity = self._create(
            self.opportunities_object,
            {
                "name": f"{request.company_name} - SDR meeting",
            },
        )
        return {
            "company_id": self._id(company),
            "person_id": self._id(person),
            "opportunity_id": self._id(opportunity),
            "company": company,
            "person": person,
            "opportunity": opportunity,
        }

    def _create(self, object_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url.rstrip('/')}/rest/{object_name.strip('/')}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError(f"Twenty returned an invalid {object_name} response.")
        return body

    @staticmethod
    def _id(payload: dict[str, Any]) -> str:
        record = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        value = record.get("id") if isinstance(record, dict) else None
        if not value:
            raise RuntimeError("Twenty response did not contain a record ID.")
        return str(value)
