from pathlib import Path

import pytest

from ai_sdr_platform.src.agents.outreach.models import OutreachCampaignRequest
from ai_sdr_platform.src.agents.outreach.outreach_service import OutreachDraftEligibility
from ai_sdr_platform.src.agents.outreach.policy import CampaignPolicyAgent
from ai_sdr_platform.src.agents.outreach.repository import SQLAlchemyOutreachRepository
from ai_sdr_platform.src.agents.outreach.service import OutreachService
from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredContact
from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    IntentAssessment,
    PersonalizationPackage,
    ProbabilityEstimate,
    PropensityAssessment,
    ProspectFeatures,
    ProspectIntelligenceResult,
    RankingResult,
)


def _estimate(name: str, value: float) -> ProbabilityEstimate:
    return ProbabilityEstimate(
        value=value,
        mode="model",
        calibrated=True,
        model_name=name,
        model_version="test",
    )


def _request(*, email: str | None, phone: str | None) -> OutreachCampaignRequest:
    contact = DiscoveredContact(
        contact_id="contact-1",
        account_id="account-1",
        full_name="Alex Smith",
        title="VP Sales",
        department="Sales",
        seniority="VP",
        email=email,
        phone=phone,
        confidence=90,
        persona_match_score=90,
    )
    intelligence = ProspectIntelligenceResult(
        account_id=contact.account_id,
        contact_id=contact.contact_id,
        company_name="Acme",
        contact_name=contact.full_name,
        signals=[],
        features=ProspectFeatures(
            account_fit_score=0.9,
            persona_match_score=0.9,
            contact_confidence=0.9,
            enrichment_confidence=0.8,
            enrichment_completeness=0.8,
            positive_signal_strength=0.8,
            negative_signal_strength=0.0,
            high_intent_signal_strength=0.8,
            buying_readiness_strength=0.7,
            signal_count=1,
            verified_signal_count=1,
        ),
        intent=IntentAssessment(
            probability=_estimate("intent", 0.8),
            level="high",
            recommended_timing="within_24_hours",
        ),
        propensity=PropensityAssessment(
            reply_probability=_estimate("reply", 0.6),
            meeting_probability=_estimate("meeting", 0.4),
            qualification_probability=_estimate("qualification", 0.5),
        ),
        ranking=RankingResult(priority_score=0.7, rank=1, priority_band="high"),
        personalization=PersonalizationPackage(
            primary_angle="Revenue workflow",
            value_proposition="Reduce manual revenue work.",
            email_subjects=["Revenue workflow"],
            email_opening="Your team appears to be improving revenue operations.",
            linkedin_message="Relevant revenue workflow idea.",
            call_opener="Calling about revenue workflow.",
            recommended_channel="email",
            call_to_action="Would a short conversation next week be useful?",
        ),
    )
    return OutreachCampaignRequest(intelligence=intelligence, contact=contact)


@pytest.mark.parametrize(
    ("email", "phone", "expected_channels"),
    [
        ("alex@example.com", "+1 (415) 555-0100", ["email", "sms"]),
        ("alex@example.com", None, ["email"]),
        (None, "+14155550100", ["sms"]),
    ],
)
def test_requested_channels_match_contact_endpoints_and_policy(
    email: str | None,
    phone: str | None,
    expected_channels: list[str],
) -> None:
    request = _request(email=email, phone=phone)

    channels = OutreachDraftEligibility().requested_channels(
        request, CampaignPolicyAgent()
    )

    assert channels == expected_channels


def test_email_and_sms_campaign_drafts_remain_pending_approval(tmp_path: Path) -> None:
    request = _request(email="alex@example.com", phone="+14155550100")
    channels = OutreachDraftEligibility().requested_channels(
        request, CampaignPolicyAgent()
    )
    service = OutreachService(
        repository=SQLAlchemyOutreachRepository(
            db_url=f"sqlite:///{(tmp_path / 'outreach.db').resolve()}"
        )
    )

    campaign = service.create_campaign(
        request.model_copy(update={"requested_channels": channels})
    )

    assert campaign.status == "pending_approval"
    assert [message.channel for message in campaign.messages] == ["email", "sms"]
    assert campaign.messages[0].recipient == request.contact.email
    assert campaign.messages[1].recipient == request.contact.phone
    assert all(message.status == "draft" for message in campaign.messages)
    assert all(message.provider == "dry_run" for message in campaign.messages)
