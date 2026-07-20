from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class EnrichmentContact(BaseModel):
    contact_id: Optional[str] = None
    full_name: str
    title: Optional[str] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = None


class EnrichmentAccount(BaseModel):
    account_id: Optional[str] = None
    company_name: str
    website: Optional[HttpUrl | str] = None
    linkedin_url: Optional[HttpUrl | str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_range: Optional[str] = None
    source: Optional[str] = None
    fit_score: Optional[float] = None

    @field_validator("company_name")
    @classmethod
    def company_name_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("company_name is required")
        return value


class EnrichmentResearchRequest(BaseModel):
    account: EnrichmentAccount
    contacts: list[EnrichmentContact] = Field(default_factory=list)
    icp_context: dict[str, Any] = Field(default_factory=dict)
    collection: Optional[str] = None
    search_provider: Optional[str] = None
    top_k: int = 8
    auto_fetch_and_index: bool = True
    llm_provider: str = "ollama_local"
    llm_model: Optional[str] = "llama3.2:3b"
    created_by: str = "system"


class EnrichmentCitation(BaseModel):
    title: str = ""
    url: str = ""
    snippet: str = ""
    source: str = "opensearch"
    score: Optional[float] = None


class EnrichmentSignal(BaseModel):
    type: str
    detail: str
    confidence: float = 0.5
    source_url: Optional[str] = None


class EnrichmentResult(BaseModel):
    enrichment_id: str = Field(default_factory=lambda: str(uuid4()))
    account_id: str
    company_name: str
    status: str = "complete"
    collection: str = "sdr_enrichment"
    company_summary: str
    products_services: list[str] = Field(default_factory=list)
    target_customers: list[str] = Field(default_factory=list)
    signals: list[EnrichmentSignal] = Field(default_factory=list)
    pain_point_hypotheses: list[str] = Field(default_factory=list)
    personalization_angles: list[str] = Field(default_factory=list)
    contact_briefs: list[dict[str, Any]] = Field(default_factory=list)
    recommended_next_action: str
    confidence_score: float = 0.5
    citations: list[EnrichmentCitation] = Field(default_factory=list)
    raw_search: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EnrichmentListResponse(BaseModel):
    items: list[EnrichmentResult]
    total: int
