from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("sdr.pipeline")

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResearchRequest, EnrichmentResult
from ai_sdr_platform.src.agents.enrichment.service import EnrichmentService
from ai_sdr_platform.src.agents.icp.models import ICPCreateRequest, ICPDefinition
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredAccount, DiscoveredContact, DiscoveryRequest
from ai_sdr_platform.src.agents.prospect_discovery.service import ProspectDiscoveryService
from ai_sdr_platform.src.api.routes.routes_enrichment import get_enrichment_service
from ai_sdr_platform.src.api.routes.routes_icp import get_icp_service
from ai_sdr_platform.src.api.routes.routes_prospect_discovery import get_prospect_discovery_service
from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    ProspectIntelligenceRequest,
    ProspectIntelligenceResult,
)
from ai_sdr_platform.src.agents.prospect_intelligence.service import ProspectIntelligenceService
from ai_sdr_platform.src.api.routes.routes_prospect_intelligence import (
    get_prospect_intelligence_service,
)
from ai_sdr_platform.src.agents.outreach.models import OutreachCampaign, OutreachCampaignRequest
from ai_sdr_platform.src.agents.outreach.outreach_service import OutreachDraftEligibility
from ai_sdr_platform.src.agents.outreach.service import OutreachService
from ai_sdr_platform.src.api.routes.routes_outreach import get_outreach_service
from ai_sdr_platform.src.agents.follow_up.models import FollowUpPlan, FollowUpPlanRequest
from ai_sdr_platform.src.agents.follow_up.service import FollowUpService
from ai_sdr_platform.src.api.routes.routes_follow_up import get_follow_up_service
from ai_sdr_platform.src.agents.qualification.models import (
    QualificationRequest,
    QualificationResult,
)
from ai_sdr_platform.src.agents.qualification.service import QualificationService
from ai_sdr_platform.src.api.routes.routes_qualification import (
    get_qualification_service,
)
from ai_sdr_platform.src.auth.dependencies import get_current_user
from ai_sdr_platform.src.auth.models import AuthUser
from ai_sdr_platform.src.shared.jobs import JobCreateResponse, JobStatus, JobStatusResponse, job_store


class SDRPipelineRequest(BaseModel):
    icp_payload: ICPCreateRequest
    discovery_limit: int = 3
    enrich_top_accounts: int = 1
    collection: str | None = None
    search_provider: str | None = None
    top_k: int = 4
    auto_fetch_and_index: bool = True
    llm_provider: str = "ollama_local"
    llm_model: str | None = "llama3.2:3b"
    created_by: str = "system"


class SDRPipelineResponse(BaseModel):
    icp_definition: ICPDefinition
    discovered_accounts: list[DiscoveredAccount] = Field(default_factory=list)
    discovered_contacts: list[DiscoveredContact] = Field(default_factory=list)
    enriched_results: list[EnrichmentResult] = Field(default_factory=list)
    prospect_intelligence: list[ProspectIntelligenceResult] = Field(default_factory=list)
    qualification_results: list[QualificationResult] = Field(default_factory=list)
    outreach_campaigns: list[OutreachCampaign] = Field(default_factory=list)
    follow_up_plans: list[FollowUpPlan] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)


router = APIRouter(prefix="/sdr", tags=["sdr-pipeline"])


def _execute_pipeline(
    payload: SDRPipelineRequest,
    icp_service: ICPService,
    discovery_service: ProspectDiscoveryService,
    enrichment_service: EnrichmentService,
    intelligence_service: ProspectIntelligenceService,
    qualification_service: QualificationService,
    outreach_service: OutreachService,
    follow_up_service: FollowUpService,
) -> SDRPipelineResponse:
    icp_result = icp_service.create_icp(payload.icp_payload)
    icp_definition = icp_result.normalized_definition
    discovery = discovery_service.run_full_discovery(
        DiscoveryRequest(icp_definition=icp_definition, limit=payload.discovery_limit)
    )
    enriched_results: list[EnrichmentResult] = []
    intelligence_results: list[ProspectIntelligenceResult] = []
    qualification_results: list[QualificationResult] = []
    outreach_campaigns: list[OutreachCampaign] = []
    follow_up_plans: list[FollowUpPlan] = []
    warnings: list[str] = []
    outreach_draft_eligibility = OutreachDraftEligibility()
    contacts_by_id: dict[str, DiscoveredContact] = {
        contact.contact_id: contact for contact in discovery.contacts
    }
    contacts_by_account: dict[str, list[DiscoveredContact]] = {}
    for contact in discovery.contacts:
        contacts_by_account.setdefault(contact.account_id, []).append(contact)
    if discovery.accounts and not discovery.contacts:
        warnings.append(
            "Real accounts were discovered, but no contacts were returned. "
            "Enable SDR_DISCOVERY_SYNTHETIC_CONTACTS or configure web contact "
            "search to unlock intelligence and outreach."
        )
    # Spend the enrichment/intelligence budget on accounts that actually have
    # discovered contacts first — otherwise we could enrich the top-N accounts by
    # fit and find they have no people, leaving Prospect Intelligence nearly empty.
    accounts_with_contacts = [
        acc for acc in discovery.accounts if contacts_by_account.get(acc.account_id)
    ]
    accounts_without_contacts = [
        acc for acc in discovery.accounts if not contacts_by_account.get(acc.account_id)
    ]
    prioritized_accounts = accounts_with_contacts + accounts_without_contacts
    for account in prioritized_accounts[: payload.enrich_top_accounts]:
        try:
            enrichment_request = EnrichmentResearchRequest(
                account=account.model_dump(),
                contacts=[contact.model_dump() for contact in contacts_by_account.get(account.account_id, [])],
                icp_context=icp_definition.model_dump(mode="json"),
                collection=payload.collection,
                search_provider=payload.search_provider,
                top_k=payload.top_k,
                auto_fetch_and_index=payload.auto_fetch_and_index,
                llm_provider=payload.llm_provider,
                llm_model=payload.llm_model,
                created_by=payload.created_by,
            )
            enrichment_result = enrichment_service.research(enrichment_request)
            enriched_results.append(enrichment_result)
        except Exception as exc:
            logger.error("Enrichment agent failed for %s: %s", account.company_name, exc)
            warnings.append(
                f"Enrichment skipped for {account.company_name}: {exc}. "
                "Check that Ollama and the enrichment search provider are running."
            )
            continue
        for contact in contacts_by_account.get(account.account_id, []):
            try:
                intelligence = intelligence_service.analyze(
                    ProspectIntelligenceRequest(
                        account=account,
                        contact=contact,
                        enrichment=enrichment_result,
                        icp_definition=icp_definition,
                        llm_provider=payload.llm_provider,
                        llm_model=payload.llm_model,
                        created_by=payload.created_by,
                    )
                )
                intelligence_results.append(intelligence)
            except Exception as exc:
                logger.error("Intelligence agent failed for %s: %s", contact.full_name, exc)
                warnings.append(f"Prospect intelligence skipped for {contact.full_name}: {exc}.")
    try:
        intelligence_results = intelligence_service.rerank_results(intelligence_results)
    except Exception as exc:
        logger.error("Intelligence rerank failed: %s", exc)
        warnings.append(f"Prospect intelligence reranking skipped: {exc}.")
    enrichment_by_account = {result.account_id: result for result in enriched_results}
    for intelligence in intelligence_results:
        contact = contacts_by_id.get(intelligence.contact_id)
        if contact is None:
            warnings.append(
                f"Outreach draft skipped for {intelligence.contact_name}: contact handoff is missing."
            )
            continue
        enrichment = enrichment_by_account.get(intelligence.account_id)
        if enrichment is None:
            warnings.append(
                f"Qualification skipped for {intelligence.contact_name}: enrichment handoff is missing."
            )
            continue
        try:
            qualification = qualification_service.qualify(
                QualificationRequest(
                    intelligence=intelligence,
                    contact=contact,
                    enrichment=enrichment,
                    created_by=payload.created_by,
                )
            )
        except Exception as exc:
            logger.error("Qualification agent failed for %s: %s", contact.full_name, exc)
            warnings.append(f"Qualification skipped for {contact.full_name}: {exc}.")
            continue
        qualification_results.append(qualification)
        draft_request = OutreachCampaignRequest(
            intelligence=intelligence,
            contact=contact,
            require_approval=True,
            created_by=payload.created_by,
        )
        requested_channels = outreach_draft_eligibility.requested_channels(
            draft_request, outreach_service.policy_agent
        )
        nurture_draft = outreach_draft_eligibility.eligible_nurture_draft(
            qualification, contact, requested_channels
        )
        if not requested_channels:
            warnings.append(
                f"Outreach skipped for {intelligence.contact_name}: no valid email or "
                "policy-eligible SMS number is available."
            )
            continue
        if qualification.qualification_status not in {"SQL", "MQL"} and not nurture_draft:
            warnings.append(
                f"Outreach skipped for {intelligence.contact_name}: "
                f"Qualification Agent routed the prospect to "
                f"{qualification.qualification_status}."
            )
            continue
        try:
            outreach_campaigns.append(
                outreach_service.create_campaign(
                    draft_request.model_copy(
                        update={"requested_channels": requested_channels}
                    )
                )
            )
            follow_up_plans.append(
                follow_up_service.create_plan(
                    FollowUpPlanRequest(
                        campaign_id=outreach_campaigns[-1].campaign_id,
                        require_approval=True,
                    )
                )
            )
        except Exception as exc:
            logger.error("Outreach/follow-up agent failed for %s: %s", contact.full_name, exc)
            warnings.append(f"Outreach draft skipped for {contact.full_name}: {exc}")
    return SDRPipelineResponse(
        icp_definition=icp_definition,
        discovered_accounts=discovery.accounts,
        discovered_contacts=discovery.contacts,
        enriched_results=enriched_results,
        prospect_intelligence=intelligence_results,
        qualification_results=qualification_results,
        outreach_campaigns=outreach_campaigns,
        follow_up_plans=follow_up_plans,
        warnings=warnings,
        summary={
            "accounts_discovered": len(discovery.accounts),
            "contacts_discovered": len(discovery.contacts),
            "accounts_enriched": len(enriched_results),
            "prospects_analyzed": len(intelligence_results),
            "prospects_qualified": len(qualification_results),
            "campaigns_drafted": len(outreach_campaigns),
            "follow_up_plans_drafted": len(follow_up_plans),
        },
    )


@router.post("/pipeline/run")
def run_sdr_pipeline(
    payload: SDRPipelineRequest,
    sync: bool = Query(default=False, description="Run synchronously and return full result"),
    user: AuthUser = Depends(get_current_user),
    icp_service: ICPService = Depends(get_icp_service),
    discovery_service: ProspectDiscoveryService = Depends(get_prospect_discovery_service),
    enrichment_service: EnrichmentService = Depends(get_enrichment_service),
    intelligence_service: ProspectIntelligenceService = Depends(get_prospect_intelligence_service),
    qualification_service: QualificationService = Depends(get_qualification_service),
    outreach_service: OutreachService = Depends(get_outreach_service),
    follow_up_service: FollowUpService = Depends(get_follow_up_service),
):
    payload.created_by = user.user_id
    try:
        if sync:
            return _execute_pipeline(
                payload,
                icp_service,
                discovery_service,
                enrichment_service,
                intelligence_service,
                qualification_service,
                outreach_service,
                follow_up_service,
            )
        job_id = job_store.create_job("sdr_pipeline")

        def _run() -> dict:
            result = _execute_pipeline(
                payload,
                icp_service,
                discovery_service,
                enrichment_service,
                intelligence_service,
                qualification_service,
                outreach_service,
                follow_up_service,
            )
            return result.model_dump(mode="json")

        job_store.run_in_background(job_id, _run)
        return JobCreateResponse(job_id=job_id, status=JobStatus.PENDING)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SDR pipeline failed: {exc}") from exc


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_pipeline_job(job_id: str, _user: AuthUser = Depends(get_current_user)) -> JobStatusResponse:
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
