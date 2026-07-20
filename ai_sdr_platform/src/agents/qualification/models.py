from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResult
from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredContact
from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    ProspectIntelligenceResult,
)

QualificationFramework = Literal["BANT", "MEDDIC"]
QualificationStatus = Literal["SQL", "MQL", "Nurture", "Disqualified"]
QualificationTier = Literal["Tier 1", "Tier 2", "Tier 3"]


class FrameworkCriterion(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class BANTAssessment(BaseModel):
    framework: Literal["BANT"] = "BANT"
    score: int = Field(ge=0, le=100)
    budget: FrameworkCriterion
    authority: FrameworkCriterion
    need: FrameworkCriterion
    timeline: FrameworkCriterion


class MEDDICAssessment(BaseModel):
    framework: Literal["MEDDIC"] = "MEDDIC"
    score: int = Field(ge=0, le=100)
    metrics: FrameworkCriterion
    economic_buyer: FrameworkCriterion
    decision_criteria: FrameworkCriterion
    decision_process: FrameworkCriterion
    identified_pain: FrameworkCriterion
    champion: FrameworkCriterion


class QualificationRequest(BaseModel):
    intelligence: ProspectIntelligenceResult
    contact: DiscoveredContact
    enrichment: EnrichmentResult
    frameworks: list[QualificationFramework] = Field(
        default_factory=lambda: ["BANT", "MEDDIC"]
    )
    created_by: str = "system"

    @model_validator(mode="after")
    def validate_handoff(self) -> "QualificationRequest":
        if self.contact.contact_id != self.intelligence.contact_id:
            raise ValueError("contact_id must match the prospect intelligence result")
        if self.contact.account_id != self.intelligence.account_id:
            raise ValueError("account_id must match the prospect intelligence result")
        if self.enrichment.account_id != self.intelligence.account_id:
            raise ValueError("enrichment account_id must match prospect intelligence")
        return self


class QualificationResult(BaseModel):
    qualification_id: str = Field(default_factory=lambda: str(uuid4()))
    intelligence_id: str
    account_id: str
    contact_id: str
    company_name: str
    contact_name: str
    bant: BANTAssessment | None = None
    meddic: MEDDICAssessment | None = None
    ml_qualification_probability: float = Field(ge=0.0, le=1.0)
    qualification_score: int = Field(ge=0, le=100)
    qualification_tier: QualificationTier
    qualification_status: QualificationStatus
    sales_ready: bool
    next_action: str
    reasoning: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    decision_source: Literal["hybrid_ml_framework"] = "hybrid_ml_framework"
    model_version: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QualificationListResponse(BaseModel):
    items: list[QualificationResult]
    total: int
