from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from ai_sdr_platform.src.agents.icp.models import ICPDefinition


class DiscoveredAccount(BaseModel):
    account_id: str
    icp_id: str
    company_name: str
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    industry: str
    location: str
    employee_count: int
    revenue_range: Optional[str] = None
    source: str = "mock"
    fit_score: int = 0
    fit_reasons: list[str] = Field(default_factory=list)
    status: str = "new"
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DiscoveredContact(BaseModel):
    contact_id: str
    account_id: str
    full_name: str
    title: str
    department: str
    seniority: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    email_verification_status: str = "unknown"
    phone_verification_status: str = "unknown"
    contact_status: str = "active"
    is_former_employee: bool = False
    confidence: int = 0
    persona_match_score: int = 0
    source: str = "mock"
    status: str = "new"
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DiscoveryRequest(BaseModel):
    icp_definition: ICPDefinition
    limit: int = 10


class ContactDiscoveryRequest(BaseModel):
    account_ids: list[str]
    target_titles: list[str] = Field(default_factory=list)
    target_seniorities: list[str] = Field(default_factory=list)


class AccountDiscoveryResult(BaseModel):
    accounts: list[DiscoveredAccount]
    total: int


class ContactDiscoveryResult(BaseModel):
    contacts: list[DiscoveredContact]
    total: int


class ProspectDiscoveryRunResult(BaseModel):
    accounts: list[DiscoveredAccount]
    contacts: list[DiscoveredContact]
    account_total: int
    contact_total: int
