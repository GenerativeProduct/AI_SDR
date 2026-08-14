import json
from pathlib import Path

from fastapi.testclient import TestClient

from ai_sdr_platform.src.agents.enrichment.repository import SQLAlchemyEnrichmentRepository
from ai_sdr_platform.src.agents.enrichment.service import EnrichmentService
from ai_sdr_platform.src.agents.icp.repository import SQLAlchemyICPRepository
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.agents.prospect_discovery.repository import SQLAlchemyProspectDiscoveryRepository
from ai_sdr_platform.src.agents.prospect_discovery.service import ProspectDiscoveryService
from ai_sdr_platform.src.api.app import create_app
from ai_sdr_platform.src.api.routes import routes_enrichment, routes_icp, routes_prospect_discovery
from ai_sdr_platform.src.api.routes import (
    routes_conversation,
    routes_crm,
    routes_follow_up,
    routes_meeting,
    routes_outreach,
    routes_prospect_intelligence,
    routes_qualification,
)
from ai_sdr_platform.src.agents.prospect_intelligence.repository import (
    SQLAlchemyProspectIntelligenceRepository,
)
from ai_sdr_platform.src.agents.prospect_intelligence.service import ProspectIntelligenceService
from ai_sdr_platform.src.agents.outreach.repository import SQLAlchemyOutreachRepository
from ai_sdr_platform.src.agents.outreach.service import OutreachService
from ai_sdr_platform.src.agents.follow_up.repository import SQLAlchemyFollowUpRepository
from ai_sdr_platform.src.agents.follow_up.service import FollowUpService
from ai_sdr_platform.src.agents.conversation.repository import (
    SQLAlchemyConversationRepository,
)
from ai_sdr_platform.src.agents.conversation.service import ConversationService
from ai_sdr_platform.src.agents.crm.providers import DryRunCRMProvider
from ai_sdr_platform.src.agents.crm.repository import SQLAlchemyCRMRepository
from ai_sdr_platform.src.agents.crm.service import CRMService
from ai_sdr_platform.src.agents.meeting.providers import DryRunMeetingProvider
from ai_sdr_platform.src.agents.meeting.repository import SQLAlchemyMeetingRepository
from ai_sdr_platform.src.agents.meeting.service import MeetingService
from ai_sdr_platform.src.agents.qualification.repository import (
    SQLAlchemyQualificationRepository,
)
from ai_sdr_platform.src.agents.qualification.service import QualificationService
from ai_sdr_platform.src.agents.qualification.models import QualificationResult


class FakeSearchProvider:
    def search(self, **kwargs):
        return {
            "hits": [
                {
                    "title": "Acme SaaS Products",
                    "url": "https://example.com/acme",
                    "snippet": "Acme SaaS offers revenue workflow tooling and sales automation.",
                    "score": 0.95,
                }
            ],
            "explanation": "Strong evidence for a SaaS revenue tooling company.",
        }


class FakeLLMRouter:
    def complete(self, **kwargs):
        return json.dumps(
            {
                "company_summary": "Acme SaaS sells revenue workflow tooling.",
                "products_services": ["Revenue workflow tooling"],
                "target_customers": ["Sales teams"],
                "signals": [],
                "pain_point_hypotheses": ["Pipeline visibility gaps"],
                "personalization_angles": ["Reference revenue operations efficiency"],
                "recommended_next_action": "Reach out to RevOps and VP Sales.",
                "confidence_score": 0.81,
            }
        )


class QualifiedTestService(QualificationService):
    def qualify(self, request):
        result = super().qualify(request)
        return self.repository.save(
            QualificationResult(
                **{
                    **result.model_dump(),
                    "qualification_score": 72,
                    "qualification_tier": "Tier 2",
                    "qualification_status": "MQL",
                    "sales_ready": False,
                    "next_action": "Assign SDR to validate missing qualification evidence",
                }
            )
        )


class NurtureTestService(QualificationService):
    def qualify(self, request):
        result = super().qualify(request)
        return self.repository.save(
            QualificationResult(
                **{
                    **result.model_dump(),
                    "qualification_score": 49,
                    "qualification_tier": "Tier 3",
                    "qualification_status": "Nurture",
                    "sales_ready": False,
                    "next_action": "Nurture and collect qualification evidence",
                }
            )
        )


def build_client(tmp_path: Path) -> TestClient:
    icp_repo = SQLAlchemyICPRepository(db_url=f"sqlite:///{(tmp_path / 'icp.db').resolve()}")
    discovery_repo = SQLAlchemyProspectDiscoveryRepository(db_url=f"sqlite:///{(tmp_path / 'discovery.db').resolve()}")
    enrichment_repo = SQLAlchemyEnrichmentRepository(db_url=f"sqlite:///{(tmp_path / 'enrichment.db').resolve()}")
    routes_icp._repository = icp_repo
    routes_icp._service = ICPService(repository=icp_repo)
    routes_prospect_discovery._repository = discovery_repo
    routes_prospect_discovery._service = ProspectDiscoveryService(repository=discovery_repo)
    routes_enrichment._repository = enrichment_repo
    routes_enrichment._service = EnrichmentService(
        repository=enrichment_repo,
        search_provider=FakeSearchProvider(),
        llm_router=FakeLLMRouter(),
    )
    app = create_app()
    routes_prospect_discovery._repository = discovery_repo
    routes_prospect_discovery._service = ProspectDiscoveryService(
        repository=discovery_repo
    )
    intelligence_repo = SQLAlchemyProspectIntelligenceRepository(
        db_url=f"sqlite:///{(tmp_path / 'intelligence.db').resolve()}"
    )
    routes_prospect_intelligence._repository = intelligence_repo
    routes_prospect_intelligence._service = ProspectIntelligenceService(
        repository=intelligence_repo
    )
    qualification_repo = SQLAlchemyQualificationRepository(
        db_url=f"sqlite:///{(tmp_path / 'qualification.db').resolve()}"
    )
    routes_qualification._repository = qualification_repo
    routes_qualification._service = QualifiedTestService(
        repository=qualification_repo
    )
    outreach_repo = SQLAlchemyOutreachRepository(
        db_url=f"sqlite:///{(tmp_path / 'outreach.db').resolve()}"
    )
    routes_outreach._repository = outreach_repo
    routes_outreach._service = OutreachService(repository=outreach_repo)
    follow_up_repo = SQLAlchemyFollowUpRepository(
        db_url=f"sqlite:///{(tmp_path / 'follow-up.db').resolve()}"
    )
    routes_follow_up._repository = follow_up_repo
    routes_follow_up._service = FollowUpService(
        repository=follow_up_repo,
        outreach_service=routes_outreach._service,
    )
    conversation_repo = SQLAlchemyConversationRepository(
        db_url=f"sqlite:///{(tmp_path / 'conversation.db').resolve()}"
    )
    routes_conversation._repository = conversation_repo
    routes_conversation._service = ConversationService(
        repository=conversation_repo,
        outreach_service=routes_outreach._service,
        follow_up_service=routes_follow_up._service,
    )
    crm_repo = SQLAlchemyCRMRepository(
        db_url=f"sqlite:///{(tmp_path / 'crm.db').resolve()}"
    )
    routes_crm._repository = crm_repo
    routes_crm._service = CRMService(
        repository=crm_repo,
        provider=DryRunCRMProvider(),
    )
    meeting_repo = SQLAlchemyMeetingRepository(
        db_url=f"sqlite:///{(tmp_path / 'meetings.db').resolve()}"
    )
    routes_meeting._repository = meeting_repo
    routes_meeting._service = MeetingService(
        repository=meeting_repo,
        provider=DryRunMeetingProvider(),
        conversation_service=routes_conversation._service,
        outreach_service=routes_outreach._service,
        crm_service=routes_crm._service,
        intelligence_service=routes_prospect_intelligence._service,
        temporal_enabled=False,
    )
    return TestClient(app)


def test_full_sdr_pipeline_runs_icp_discovery_and_enrichment(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/sdr/pipeline/run?sync=true",
        json={
            "icp_payload": {
                "industries": ["SaaS"],
                "geographies": ["Europe"],
                "target_personas": ["RevOps"],
                "pain_points": ["pipeline visibility"],
                "created_by": "integration-test",
            },
            "discovery_limit": 3,
            "enrich_top_accounts": 2,
            "llm_provider": "ollama_local",
            "llm_model": "llama3.2:3b",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["accounts_discovered"] >= 1
    assert body["summary"]["contacts_discovered"] >= 1
    assert body["summary"]["accounts_enriched"] >= 1
    assert body["summary"]["prospects_analyzed"] >= 1
    assert body["summary"]["prospects_qualified"] >= 1
    assert body["summary"]["campaigns_drafted"] >= 1
    assert body["summary"]["follow_up_plans_drafted"] >= 1
    assert body["enriched_results"][0]["company_summary"] == "Acme SaaS sells revenue workflow tooling."
    assert body["prospect_intelligence"][0]["personalization"]["email_opening"]
    assert body["prospect_intelligence"][0]["ranking"]["rank"] >= 1
    assert body["qualification_results"][0]["decision_source"] == "hybrid_ml_framework"
    assert body["qualification_results"][0]["bant"]["score"] >= 0
    assert body["qualification_results"][0]["meddic"]["score"] >= 0
    assert body["outreach_campaigns"][0]["status"] == "pending_approval"
    assert body["outreach_campaigns"][0]["messages"][0]["review"]["passed"] is True
    assert body["follow_up_plans"][0]["status"] == "pending_approval"


def test_pipeline_creates_approval_required_email_drafts_for_nurture_contacts(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    nurture_repo = SQLAlchemyQualificationRepository(
        db_url=f"sqlite:///{(tmp_path / 'nurture-qualification.db').resolve()}"
    )
    routes_qualification._repository = nurture_repo
    routes_qualification._service = NurtureTestService(repository=nurture_repo)

    response = client.post(
        "/sdr/pipeline/run?sync=true",
        json={
            "icp_payload": {
                "industries": ["SaaS"],
                "geographies": ["Europe"],
                "target_personas": ["RevOps"],
                "pain_points": ["pipeline visibility"],
            },
            "discovery_limit": 3,
            "enrich_top_accounts": 2,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["qualification_results"][0]["qualification_status"] == "Nurture"
    assert body["summary"]["campaigns_drafted"] >= 1
    campaign = body["outreach_campaigns"][0]
    assert campaign["status"] == "pending_approval"
    assert campaign["messages"][0]["channel"] == "email"
    contact_by_id = {
        contact["contact_id"]: contact for contact in body["discovered_contacts"]
    }
    assert campaign["messages"][0]["recipient"] == contact_by_id[
        campaign["contact_id"]
    ]["email"]

    campaign_id = body["outreach_campaigns"][0]["campaign_id"]
    approved = client.post(
        f"/outreach/campaigns/{campaign_id}/approve",
        json={"approved_by": "integration-test"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    sent = client.post(f"/outreach/campaigns/{campaign_id}/send", params={"force": True})
    assert sent.status_code == 200
    sent_body = sent.json()
    assert sent_body["status"] == "completed"
    assert sent_body["messages"][0]["provider"] == "dry_run"
    assert sent_body["messages"][0]["status"] == "sent"

    follow_up_id = body["follow_up_plans"][0]["plan_id"]
    follow_up_approved = client.post(
        f"/follow-up/plans/{follow_up_id}/approve",
        json={"approved_by": "integration-test"},
    )
    assert follow_up_approved.status_code == 200
    assert follow_up_approved.json()["status"] == "active"

    reply = client.post(
        "/conversations/inbound",
        json={
            "campaign_id": campaign_id,
            "body": "Yes, this sounds useful. Can we schedule a meeting next week?",
            "provider": "manual-test",
            "provider_event_id": "reply-event-1",
            "provider_message_id": sent_body["messages"][0]["provider_message_id"],
        },
    )
    assert reply.status_code == 200
    reply_body = reply.json()
    assert reply_body["latest_classification"]["intent"] == "meeting_request"
    assert reply_body["status"] == "meeting_requested"
    assert reply_body["suggested_reply"]

    meeting_list = client.get("/meetings")
    assert meeting_list.status_code == 200
    meetings = meeting_list.json()["items"]
    assert len(meetings) == 1
    assert meetings[0]["status"] == "awaiting_approval"
    meeting_id = meetings[0]["meeting_id"]

    before_booking = routes_prospect_intelligence._repository.list_training_rows()
    assert before_booking[0][1].meeting_booked is False

    booking = client.post(
        f"/meetings/{meeting_id}/approve-and-book",
        json={
            "start_at": "2026-06-20T10:00:00+00:00",
            "timezone": "UTC",
            "duration_minutes": 30,
            "approved_by": "integration-test",
        },
    )
    assert booking.status_code == 200
    booking_body = booking.json()
    assert booking_body["status"] == "booked"
    assert booking_body["provider_event_id"]
    assert booking_body["meeting_url"]
    assert booking_body["crm_sync_status"] == "synced"

    crm_sync = client.get(f"/crm/syncs/{meeting_id}")
    assert crm_sync.status_code == 200
    assert crm_sync.json()["company_id"]
    assert crm_sync.json()["person_id"]
    assert crm_sync.json()["opportunity_id"]

    stopped_plan = client.get(f"/follow-up/plans/{follow_up_id}")
    assert stopped_plan.status_code == 200
    assert stopped_plan.json()["status"] == "stopped"
    assert all(
        touch["status"] == "suppressed"
        for touch in stopped_plan.json()["touches"]
    )

    approved_reply = client.post(
        f"/conversations/{reply_body['conversation_id']}/approve-reply",
        json={"approved_by": "integration-test"},
    )
    assert approved_reply.status_code == 200
    assert approved_reply.json()["reply_approved"] is True

    sent_reply = client.post(
        f"/conversations/{reply_body['conversation_id']}/send-reply"
    )
    assert sent_reply.status_code == 200
    assert sent_reply.json()["reply_approved"] is False
    outbound = [
        message
        for message in sent_reply.json()["messages"]
        if message["direction"] == "outbound"
    ]
    assert outbound[-1]["provider"] == "dry_run"
    assert outbound[-1]["metadata"]["status"] == "sent"

    training_rows = routes_prospect_intelligence._repository.list_training_rows()
    assert len(training_rows) == 1
    assert training_rows[0][1].positive_reply is True
    assert training_rows[0][1].meeting_booked is True
