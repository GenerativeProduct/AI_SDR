from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ai_sdr_platform.src.agents.conversation.repository import SQLAlchemyConversationRepository
from ai_sdr_platform.src.agents.crm.repository import SQLAlchemyCRMRepository
from ai_sdr_platform.src.agents.enrichment.repository import SQLAlchemyEnrichmentRepository
from ai_sdr_platform.src.agents.follow_up.repository import SQLAlchemyFollowUpRepository
from ai_sdr_platform.src.agents.icp.repository import SQLAlchemyICPRepository
from ai_sdr_platform.src.agents.meeting.repository import SQLAlchemyMeetingRepository
from ai_sdr_platform.src.agents.outreach.repository import SQLAlchemyOutreachRepository
from ai_sdr_platform.src.agents.prospect_discovery.repository import SQLAlchemyProspectDiscoveryRepository
from ai_sdr_platform.src.agents.prospect_intelligence.repository import SQLAlchemyProspectIntelligenceRepository
from ai_sdr_platform.src.agents.qualification.repository import SQLAlchemyQualificationRepository
from ai_sdr_platform.src.auth.dependencies import get_current_user
from ai_sdr_platform.src.shared.config import settings
from pydantic import BaseModel, Field

router = APIRouter(prefix="/sdr", tags=["sdr-dashboard"])


class DashboardResponse(BaseModel):
    icp_count: int = 0
    accounts_count: int = 0
    contacts_count: int = 0
    enrichments_count: int = 0
    intelligence_count: int = 0
    qualified_sql_mql: int = 0
    pending_campaigns: int = 0
    active_conversations: int = 0
    upcoming_meetings: int = 0
    crm_sync_failures: int = 0
    follow_up_plans_pending: int = 0


def _safe_count(repo_factory, list_method: str = "list_latest") -> int:
    try:
        repo = repo_factory()
        items = getattr(repo, list_method)()
        return len(items)
    except Exception:
        return 0


def _safe_list(repo_factory, list_method: str = "list_latest", filter_fn=None) -> int:
    try:
        repo = repo_factory()
        items = getattr(repo, list_method)()
        if filter_fn:
            items = [item for item in items if filter_fn(item)]
        return len(items)
    except Exception:
        return 0


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(_user=Depends(get_current_user)) -> DashboardResponse:
    icp_repo = SQLAlchemyICPRepository()
    discovery_repo = SQLAlchemyProspectDiscoveryRepository()
    enrichment_repo = SQLAlchemyEnrichmentRepository()
    intelligence_repo = SQLAlchemyProspectIntelligenceRepository()
    qualification_repo = SQLAlchemyQualificationRepository()
    outreach_repo = SQLAlchemyOutreachRepository()
    conversation_repo = SQLAlchemyConversationRepository()
    meeting_repo = SQLAlchemyMeetingRepository()
    crm_repo = SQLAlchemyCRMRepository()
    follow_up_repo = SQLAlchemyFollowUpRepository()

    accounts = discovery_repo.list_accounts() if hasattr(discovery_repo, "list_accounts") else []
    contacts = discovery_repo.list_contacts() if hasattr(discovery_repo, "list_contacts") else []

    qualified = 0
    try:
        for item in qualification_repo.list_latest():
            status = getattr(item, "qualification_status", None)
            if status in {"SQL", "MQL"}:
                qualified += 1
    except Exception:
        pass

    pending_campaigns = 0
    try:
        for campaign in outreach_repo.list_campaigns():
            if getattr(campaign, "status", "") == "pending_approval":
                pending_campaigns += 1
    except Exception:
        pass

    active_conversations = 0
    try:
        for thread in conversation_repo.list():
            if getattr(thread, "status", "") in {"needs_review", "awaiting_reply", "active"}:
                active_conversations += 1
    except Exception:
        pass

    upcoming_meetings = 0
    try:
        for meeting in meeting_repo.list():
            if getattr(meeting, "status", "") in {"draft", "approved", "booked"}:
                upcoming_meetings += 1
    except Exception:
        pass

    crm_failures = 0
    try:
        for sync in crm_repo.list():
            if getattr(sync, "status", "") == "failed":
                crm_failures += 1
    except Exception:
        pass

    follow_up_pending = 0
    try:
        for plan in follow_up_repo.list():
            if getattr(plan, "status", "") == "pending_approval":
                follow_up_pending += 1
    except Exception:
        pass

    return DashboardResponse(
        icp_count=_safe_count(lambda: icp_repo),
        accounts_count=len(accounts),
        contacts_count=len(contacts),
        enrichments_count=_safe_count(lambda: enrichment_repo),
        intelligence_count=_safe_count(lambda: intelligence_repo),
        qualified_sql_mql=qualified,
        pending_campaigns=pending_campaigns,
        active_conversations=active_conversations,
        upcoming_meetings=upcoming_meetings,
        crm_sync_failures=crm_failures,
        follow_up_plans_pending=follow_up_pending,
    )
