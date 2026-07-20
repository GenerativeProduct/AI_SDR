from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from ai_sdr_platform.src.shared.types import ValidationStatus


class RangeInt(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None

    @model_validator(mode="after")
    def validate_range(self) -> "RangeInt":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min cannot be greater than max")
        return self


class RangeFloat(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None

    @model_validator(mode="after")
    def validate_range(self) -> "RangeFloat":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min cannot be greater than max")
        return self


class AccountCriteria(BaseModel):
    industries: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)
    employee_range: Optional[RangeInt] = None
    revenue_range_million: Optional[RangeFloat] = None
    company_types: list[str] = Field(default_factory=list)
    revenue_ranges: list[str] = Field(default_factory=list)
    company_size_ranges: list[str] = Field(default_factory=list)
    funding_stages: list[str] = Field(default_factory=list)
    tech_stack_signals: list[str] = Field(default_factory=list)


class PersonaCriteria(BaseModel):
    titles: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    seniorities: list[str] = Field(default_factory=list)
    seniority_levels: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)


class ExclusionCriteria(BaseModel):
    industries: list[str] = Field(default_factory=list)
    customer_statuses: list[str] = Field(default_factory=list)
    company_names: list[str] = Field(default_factory=list)
    employee_max_below: Optional[int] = None
    geographies: list[str] = Field(default_factory=list)


class ScoringWeights(BaseModel):
    industry_fit: float
    company_size_fit: float
    persona_fit: float
    geo_fit: float
    pain_point_fit: float

    @model_validator(mode="after")
    def validate_total(self) -> "ScoringWeights":
        total = (
            self.industry_fit
            + self.company_size_fit
            + self.persona_fit
            + self.geo_fit
            + self.pain_point_fit
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError("scoring weights must sum to 1.0")
        return self


class AuditFields(BaseModel):
    created_by: str = "system"
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    change_reason: Optional[str] = None


class ICPFilterCriteria(BaseModel):
    target_industries: list[str] = Field(default_factory=list)
    revenue_ranges: list[str] = Field(default_factory=list)
    company_size_ranges: list[str] = Field(default_factory=list)
    funding_stages: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)
    tech_stack_signals: list[str] = Field(default_factory=list)
    target_job_titles: list[str] = Field(default_factory=list)
    seniority_levels: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)


class ICPCreateRequest(BaseModel):
    icp_name: Optional[str] = None
    industries: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)
    employee_band: Optional[str] = None
    employee_range: Optional[RangeInt] = None
    revenue_band: Optional[str] = None
    revenue_range_million: Optional[RangeFloat] = None
    target_personas: list[str] = Field(default_factory=list)
    target_departments: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    offer_summary: Optional[str] = None
    exclusions: ExclusionCriteria = Field(default_factory=ExclusionCriteria)
    scoring_weights: Optional[ScoringWeights] = None
    notes: Optional[str] = None
    created_by: str = Field(default="system")
    filters: Optional[ICPFilterCriteria] = None


class ICPUpdateRequest(BaseModel):
    icp_name: Optional[str] = None
    industries: Optional[list[str]] = None
    geographies: Optional[list[str]] = None
    employee_band: Optional[str] = None
    employee_range: Optional[RangeInt] = None
    revenue_band: Optional[str] = None
    revenue_range_million: Optional[RangeFloat] = None
    target_personas: Optional[list[str]] = None
    target_departments: Optional[list[str]] = None
    pain_points: Optional[list[str]] = None
    offer_summary: Optional[str] = None
    exclusions: Optional[ExclusionCriteria] = None
    scoring_weights: Optional[ScoringWeights] = None
    notes: Optional[str] = None
    updated_by: str = Field(default="system")
    change_reason: Optional[str] = None
    filters: Optional[ICPFilterCriteria] = None


class ICPSuggestionRequest(BaseModel):
    prompt: Optional[str] = None
    filters: Optional[ICPFilterCriteria] = None
    industries: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)
    target_personas: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    offer_summary: Optional[str] = None
    notes: Optional[str] = None
    llm_provider: str = "auto"
    model_name: Optional[str] = None

    @model_validator(mode="after")
    def validate_request_source(self) -> "ICPSuggestionRequest":
        has_prompt = bool(self.prompt and self.prompt.strip())
        has_filters = self.filters is not None
        has_legacy = bool(
            self.industries
            or self.geographies
            or self.target_personas
            or self.pain_points
            or self.offer_summary
            or self.notes
        )
        if not (has_prompt or has_filters or has_legacy):
            raise ValueError(
                "ICP suggestion requires a prompt, structured filters, or criteria fields"
            )
        return self


class ICPSuggestionResponse(BaseModel):
    personas: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    exclusions: ExclusionCriteria = Field(default_factory=ExclusionCriteria)
    reasoning: str
    source: str = "deterministic"


class ICPDefinition(BaseModel):
    version_id: str = Field(default_factory=lambda: str(uuid4()))
    icp_id: str = Field(default_factory=lambda: str(uuid4()))
    icp_name: str
    version: int = 1
    status: ValidationStatus = "valid"
    account_criteria: AccountCriteria
    persona_criteria: PersonaCriteria
    pain_points: list[str] = Field(default_factory=list)
    offer_summary: Optional[str] = None
    exclusions: ExclusionCriteria = Field(default_factory=ExclusionCriteria)
    scoring_weights: ScoringWeights
    notes: Optional[str] = None
    audit: AuditFields = Field(default_factory=AuditFields)
    audit_metadata: dict[str, Any] = Field(default_factory=dict)


class ICPValidationResult(BaseModel):
    status: ValidationStatus
    warnings: list[str] = Field(default_factory=list)
    normalized_definition: ICPDefinition


class ICPListResponse(BaseModel):
    items: list[ICPDefinition]
    total: int
