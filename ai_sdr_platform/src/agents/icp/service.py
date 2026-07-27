from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from ai_sdr_platform.src.agents.icp.models import (
    AccountCriteria,
    AuditFields,
    ICPCreateRequest,
    ICPDefinition,
    ICPFilterCriteria,
    ICPListResponse,
    ICPSuggestionRequest,
    ICPSuggestionResponse,
    ICPUpdateRequest,
    ICPValidationResult,
    PersonaCriteria,
    RangeFloat,
    RangeInt,
    ScoringWeights,
)
from ai_sdr_platform.src.agents.icp.repository import ICPRepository
from ai_sdr_platform.src.agents.icp.tools import (
    EMPLOYEE_BANDS,
    PERSONA_ALIASES,
    REVENUE_BANDS_MILLION,
    expand_persona_alias,
    normalize_geo,
    normalize_industry,
    slugify_name,
)
from ai_sdr_platform.src.shared.config import settings
from ai_sdr_platform.src.shared.exceptions import ICPValidationError


class SuggestionProvider(Protocol):
    def suggest(self, request: ICPSuggestionRequest) -> ICPSuggestionResponse:
        ...


@dataclass
class ICPService:
    repository: ICPRepository
    suggestion_provider: SuggestionProvider | None = None

    def create_icp(self, request: ICPCreateRequest) -> ICPValidationResult:
        definition, warnings = self._normalize_request(request)
        saved = self.repository.save(definition)
        return ICPValidationResult(status=saved.status, warnings=warnings, normalized_definition=saved)

    def update_icp(self, icp_id: str, request: ICPUpdateRequest) -> ICPValidationResult:
        current = self.repository.get_latest(icp_id)
        if not current:
            raise ICPValidationError("ICP not found")
        merged = self._merge_with_existing(current, request)
        definition, warnings = self._normalize_request(merged, existing_icp_id=icp_id, next_version=current.version + 1)
        definition.audit.created_at = current.audit.created_at
        definition.audit.updated_by = request.updated_by
        definition.audit.change_reason = request.change_reason
        saved = self.repository.save(definition)
        return ICPValidationResult(status=saved.status, warnings=warnings, normalized_definition=saved)

    def validate_only(self, request: ICPCreateRequest) -> ICPValidationResult:
        definition, warnings = self._normalize_request(request)
        return ICPValidationResult(status=definition.status, warnings=warnings, normalized_definition=definition)

    def suggest(self, request: ICPSuggestionRequest) -> ICPSuggestionResponse:
        request = self._suggestion_with_filter_defaults(request)
        if self.suggestion_provider:
            return self.suggestion_provider.suggest(request)
        return self._deterministic_suggestion(request)

    def get_icp(self, icp_id: str, version: int | None = None) -> ICPDefinition | None:
        if version is not None:
            return self.repository.get_version(icp_id, version)
        return self.repository.get_latest(icp_id)

    def list_icps(self) -> ICPListResponse:
        items = self.repository.list_latest()
        return ICPListResponse(items=items, total=len(items))

    def list_versions(self, icp_id: str) -> list[ICPDefinition]:
        return self.repository.list_versions(icp_id)

    def _merge_with_existing(self, current: ICPDefinition, update: ICPUpdateRequest) -> ICPCreateRequest:
        account = current.account_criteria
        persona = current.persona_criteria
        exclusions = current.exclusions
        filters = update.filters or ICPFilterCriteria(
            target_industries=account.industries,
            revenue_ranges=account.revenue_ranges,
            company_size_ranges=account.company_size_ranges,
            funding_stages=account.funding_stages,
            geographies=account.geographies,
            tech_stack_signals=account.tech_stack_signals,
            target_job_titles=persona.titles,
            seniority_levels=persona.seniority_levels or persona.seniorities,
            pain_points=current.pain_points,
            buying_signals=persona.buying_signals,
        )
        return ICPCreateRequest(
            icp_name=update.icp_name or current.icp_name,
            industries=update.industries if update.industries is not None else account.industries,
            geographies=update.geographies if update.geographies is not None else account.geographies,
            employee_band=update.employee_band,
            employee_range=update.employee_range or account.employee_range,
            revenue_band=update.revenue_band,
            revenue_range_million=update.revenue_range_million or account.revenue_range_million,
            target_personas=update.target_personas if update.target_personas is not None else persona.titles,
            target_departments=update.target_departments if update.target_departments is not None else persona.departments,
            pain_points=update.pain_points if update.pain_points is not None else current.pain_points,
            offer_summary=update.offer_summary if update.offer_summary is not None else current.offer_summary,
            exclusions=update.exclusions or exclusions,
            scoring_weights=update.scoring_weights or current.scoring_weights,
            notes=update.notes if update.notes is not None else current.notes,
            created_by=current.audit.created_by,
            filters=filters,
        )

    def _normalize_request(
        self,
        request: ICPCreateRequest,
        *,
        existing_icp_id: str | None = None,
        next_version: int = 1,
    ) -> tuple[ICPDefinition, list[str]]:
        warnings: list[str] = []

        filters = request.filters
        raw_industries = request.industries or (
            filters.target_industries if filters else []
        )
        raw_geographies = request.geographies or (
            filters.geographies if filters else []
        )
        raw_personas = request.target_personas or (
            filters.target_job_titles if filters else []
        )
        pain_points = request.pain_points or (filters.pain_points if filters else [])

        industries = [normalize_industry(v) for v in raw_industries if v.strip()]
        geographies = [normalize_geo(v) for v in raw_geographies if v.strip()]

        employee_range = request.employee_range
        if employee_range is None and request.employee_band:
            band = EMPLOYEE_BANDS.get(request.employee_band.strip().lower())
            if band:
                employee_range = RangeInt(min=band[0], max=band[1])
            else:
                # Also accept numeric ranges typed straight from the UI dropdown,
                # e.g. "100 to 1000", "100-1000", "100 - 1,000", "100+".
                numbers = re.findall(r"\d[\d,]*", request.employee_band)
                parsed = [int(n.replace(",", "")) for n in numbers]
                if len(parsed) >= 2:
                    employee_range = RangeInt(min=min(parsed), max=max(parsed))
                elif len(parsed) == 1:
                    employee_range = RangeInt(min=parsed[0], max=None)
                else:
                    warnings.append(f"Unknown employee band: {request.employee_band}")

        revenue_range = request.revenue_range_million
        if revenue_range is None and request.revenue_band:
            band = REVENUE_BANDS_MILLION.get(request.revenue_band.strip().lower())
            if band:
                revenue_range = RangeFloat(min=band[0], max=band[1])
            else:
                warnings.append(f"Unknown revenue band: {request.revenue_band}")

        expanded_titles: list[str] = []
        for persona in raw_personas:
            expanded_titles.extend(expand_persona_alias(persona))
        titles = sorted({title for title in expanded_titles if title})

        if not industries and not geographies and not titles:
            raise ICPValidationError(
                "ICP must include at least one account-level or persona-level targeting signal"
            )

        scoring_weights = request.scoring_weights or ScoringWeights(
            industry_fit=settings.default_weight_industry_fit,
            company_size_fit=settings.default_weight_company_size_fit,
            persona_fit=settings.default_weight_persona_fit,
            geo_fit=settings.default_weight_geo_fit,
            pain_point_fit=settings.default_weight_pain_point_fit,
        )

        if not pain_points:
            warnings.append("No pain points were provided; personalization quality may be weaker")

        icp_name = request.icp_name or self._build_default_name(industries, geographies, titles)

        definition = ICPDefinition(
            icp_id=existing_icp_id or __import__("uuid").uuid4().__str__(),
            icp_name=icp_name,
            version=next_version,
            account_criteria=AccountCriteria(
                industries=industries,
                geographies=geographies,
                employee_range=employee_range,
                revenue_range_million=revenue_range,
                revenue_ranges=filters.revenue_ranges if filters else [],
                company_size_ranges=filters.company_size_ranges if filters else [],
                funding_stages=filters.funding_stages if filters else [],
                tech_stack_signals=filters.tech_stack_signals if filters else [],
            ),
            persona_criteria=PersonaCriteria(
                titles=titles,
                departments=request.target_departments,
                seniorities=filters.seniority_levels if filters else [],
                seniority_levels=filters.seniority_levels if filters else [],
                buying_signals=filters.buying_signals if filters else [],
            ),
            pain_points=pain_points,
            offer_summary=request.offer_summary,
            exclusions=request.exclusions,
            scoring_weights=scoring_weights,
            notes=request.notes,
            audit=AuditFields(created_by=request.created_by),
            audit_metadata={
                "source": "icp_agent_v1",
                "slug": slugify_name([icp_name]),
                "deterministic_core": True,
                "has_structured_filters": filters is not None,
            },
        )
        return definition, warnings

    @staticmethod
    def _suggestion_with_filter_defaults(
        request: ICPSuggestionRequest,
    ) -> ICPSuggestionRequest:
        if request.filters is None:
            return request
        filters = request.filters
        return request.model_copy(
            update={
                "industries": request.industries or filters.target_industries,
                "geographies": request.geographies or filters.geographies,
                "target_personas": request.target_personas
                or filters.target_job_titles,
                "pain_points": request.pain_points or filters.pain_points,
            }
        )

    def _build_default_name(self, industries: list[str], geographies: list[str], titles: list[str]) -> str:
        industry_label = industries[0].replace("_", " ").title() if industries else "General"
        geo_label = geographies[0] if geographies else "Global"
        persona_label = titles[0] if titles else "Multi-Persona"
        return f"{industry_label} - {geo_label} - {persona_label}"

    def _deterministic_suggestion(self, request: ICPSuggestionRequest) -> ICPSuggestionResponse:
        persona_suggestions: list[str] = []
        for persona in request.target_personas:
            persona_suggestions.extend(expand_persona_alias(persona))
        if not persona_suggestions and any("revenue" in p.lower() for p in request.pain_points):
            persona_suggestions.extend(PERSONA_ALIASES.get("revops", []))

        exclusions = {
            "industries": [],
            "customer_statuses": ["existing_customer"],
            "company_names": [],
            "employee_max_below": 20,
            "geographies": [],
        }
        if any(ind.lower() in {"agency", "consulting"} for ind in request.industries):
            exclusions["industries"].append("agency")

        suggested_pain_points = list(dict.fromkeys(request.pain_points))
        if request.offer_summary and "pipeline" in request.offer_summary.lower():
            suggested_pain_points.append("poor pipeline visibility")
        if request.notes and "forecast" in request.notes.lower():
            suggested_pain_points.append("forecasting inconsistency")

        return ICPSuggestionResponse(
            personas=sorted(set(persona_suggestions)),
            pain_points=suggested_pain_points,
            exclusions=exclusions,
            reasoning="Generated from deterministic rules using persona aliases, offer summary hints, and conservative exclusion defaults.",
            source="deterministic",
        )
