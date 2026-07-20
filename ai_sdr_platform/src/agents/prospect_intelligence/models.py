from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResult
from ai_sdr_platform.src.agents.icp.models import ICPDefinition
from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredAccount, DiscoveredContact

SignalType = Literal[
    "funding",
    "hiring",
    "leadership_change",
    "expansion",
    "technology_change",
    "product",
    "web_intent",
    "outreach_engagement",
    "growth",
    "news",
    "risk",
    "other",
]
SignalPolarity = Literal["positive", "neutral", "negative"]
PredictionMode = Literal["heuristic", "model"]


class IntelligenceSignal(BaseModel):
    signal_id: str = Field(default_factory=lambda: str(uuid4()))
    account_id: str
    signal_type: SignalType
    detail: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_reliability: float = Field(default=0.5, ge=0.0, le=1.0)
    source_url: str | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    polarity: SignalPolarity = "neutral"
    verified: bool = False
    raw_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProspectFeatures(BaseModel):
    account_fit_score: float = Field(ge=0.0, le=1.0)
    persona_match_score: float = Field(ge=0.0, le=1.0)
    contact_confidence: float = Field(ge=0.0, le=1.0)
    enrichment_confidence: float = Field(ge=0.0, le=1.0)
    enrichment_completeness: float = Field(ge=0.0, le=1.0)
    positive_signal_strength: float = Field(ge=0.0, le=1.0)
    negative_signal_strength: float = Field(ge=0.0, le=1.0)
    high_intent_signal_strength: float = Field(ge=0.0, le=1.0)
    buying_readiness_strength: float = Field(ge=0.0, le=1.0)
    signal_count: int = Field(ge=0)
    verified_signal_count: int = Field(ge=0)
    feature_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProbabilityEstimate(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    mode: PredictionMode
    calibrated: bool = False
    model_name: str
    model_version: str
    reasons: list[str] = Field(default_factory=list)
    feature_contributions: dict[str, float] = Field(default_factory=dict)


class IntentAssessment(BaseModel):
    probability: ProbabilityEstimate
    level: Literal["high", "medium", "low"]
    detected_signals: list[IntelligenceSignal] = Field(default_factory=list)
    recommended_timing: str


class PropensityAssessment(BaseModel):
    reply_probability: ProbabilityEstimate
    meeting_probability: ProbabilityEstimate
    qualification_probability: ProbabilityEstimate


class RankingResult(BaseModel):
    priority_score: float = Field(ge=0.0, le=1.0)
    rank: int | None = Field(default=None, ge=1)
    priority_band: Literal["high", "medium", "low"]
    provider: str = "local"
    ranking_event_id: str | None = None
    reasons: list[str] = Field(default_factory=list)


class RankingSystemStatus(BaseModel):
    configured: bool
    reachable: bool
    model_name: str
    active_provider: Literal["metarank", "local"]
    learned_reranking_active: bool
    detail: str


class PersonalizationPackage(BaseModel):
    primary_angle: str
    value_proposition: str
    email_subjects: list[str] = Field(default_factory=list)
    email_opening: str
    linkedin_message: str
    call_opener: str
    recommended_channel: Literal["email", "linkedin", "phone", "multi_channel"]
    call_to_action: str
    evidence_signal_ids: list[str] = Field(default_factory=list)
    guardrail_notes: list[str] = Field(default_factory=list)
    source: Literal["llm", "deterministic"] = "deterministic"


class ProspectIntelligenceRequest(BaseModel):
    account: DiscoveredAccount
    contact: DiscoveredContact
    enrichment: EnrichmentResult
    icp_definition: ICPDefinition | None = None
    llm_provider: str = "ollama_local"
    llm_model: str | None = "llama3.2:3b"
    created_by: str = "system"

    @model_validator(mode="after")
    def validate_handoff_ids(self) -> "ProspectIntelligenceRequest":
        if self.contact.account_id != self.account.account_id:
            raise ValueError("contact.account_id must match account.account_id")
        if self.enrichment.account_id != self.account.account_id:
            raise ValueError("enrichment.account_id must match account.account_id")
        return self


class ProspectIntelligenceResult(BaseModel):
    intelligence_id: str = Field(default_factory=lambda: str(uuid4()))
    account_id: str
    contact_id: str
    company_name: str
    contact_name: str
    signals: list[IntelligenceSignal]
    features: ProspectFeatures
    intent: IntentAssessment
    propensity: PropensityAssessment
    ranking: RankingResult
    personalization: PersonalizationPackage
    model_versions: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    created_by: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProspectIntelligenceListResponse(BaseModel):
    items: list[ProspectIntelligenceResult]
    total: int


class ProspectOutcome(BaseModel):
    outcome_id: str = Field(default_factory=lambda: str(uuid4()))
    intelligence_id: str
    account_id: str
    contact_id: str
    replied: bool = False
    positive_reply: bool = False
    meeting_booked: bool = False
    qualified: bool = False
    opportunity_created: bool = False
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "outreach"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelTrainingRequest(BaseModel):
    targets: list[Literal["reply", "meeting", "qualification"]] = Field(
        default_factory=lambda: ["reply", "meeting", "qualification"]
    )
    minimum_samples: int = Field(default=50, ge=10)
    artifact_dir: str = "ai_sdr_platform/models/prospect_intelligence"


class TrainedModelSummary(BaseModel):
    target: str
    trained: bool
    sample_count: int
    positive_count: int
    artifact_path: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    calibrated: bool = False
    metrics: dict[str, float] = Field(default_factory=dict)
    reason: str | None = None


class ModelTrainingResponse(BaseModel):
    models: list[TrainedModelSummary]
