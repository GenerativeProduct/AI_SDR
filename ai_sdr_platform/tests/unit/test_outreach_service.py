from pathlib import Path

from ai_sdr_platform.src.agents.outreach.models import OutreachCampaignRequest
from ai_sdr_platform.src.agents.outreach.repository import SQLAlchemyOutreachRepository
from ai_sdr_platform.src.agents.outreach.service import OutreachService
from ai_sdr_platform.src.agents.outreach.providers import (
    BrevoEmailProvider,
    ResendEmailProvider,
)
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


def estimate(name: str, value: float) -> ProbabilityEstimate:
    return ProbabilityEstimate(
        value=value,
        mode="model",
        calibrated=True,
        model_name=name,
        model_version="test",
    )


def test_campaign_is_idempotent_and_requires_approval(tmp_path: Path) -> None:
    repository = SQLAlchemyOutreachRepository(
        db_url=f"sqlite:///{(tmp_path / 'outreach.db').resolve()}"
    )
    service = OutreachService(repository=repository)
    intelligence = ProspectIntelligenceResult(
        account_id="acc-1",
        contact_id="contact-1",
        company_name="Acme",
        contact_name="Alex Smith",
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
            probability=estimate("intent", 0.8),
            level="high",
            recommended_timing="within_24_hours",
        ),
        propensity=PropensityAssessment(
            reply_probability=estimate("reply", 0.6),
            meeting_probability=estimate("meeting", 0.4),
            qualification_probability=estimate("qualification", 0.5),
        ),
        ranking=RankingResult(
            priority_score=0.7,
            rank=1,
            priority_band="high",
        ),
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
    contact = DiscoveredContact(
        contact_id="contact-1",
        account_id="acc-1",
        full_name="Alex Smith",
        title="VP Sales",
        department="Sales",
        seniority="VP",
        email="alex@example.com",
        confidence=90,
        persona_match_score=90,
    )
    request = OutreachCampaignRequest(intelligence=intelligence, contact=contact)

    first = service.create_campaign(request)
    second = service.create_campaign(request)
    assert first.campaign_id == second.campaign_id
    assert first.status == "pending_approval"
    assert first.messages[0].review and first.messages[0].review.passed

    approved = service.approve_campaign(first.campaign_id, "reviewer")
    assert approved.status == "approved"
    sent = service.send_due(first.campaign_id, force=True)
    assert sent.status == "completed"
    assert sent.messages[0].provider == "dry_run"


def test_brevo_provider_builds_transactional_request(monkeypatch) -> None:
    captured = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"messageId": "<brevo-message-id>"}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(
        "ai_sdr_platform.src.agents.outreach.email_provider.requests.post", fake_post
    )
    provider = BrevoEmailProvider(
        api_key="test-key",
        from_email="verified@example.com",
        from_name="SDR Team",
        reply_to_email="replies@example.com",
    )
    from ai_sdr_platform.src.agents.outreach.models import OutreachMessage

    result = provider.send(
        OutreachMessage(
            campaign_id="campaign-1",
            intelligence_id="intelligence-1",
            contact_id="contact-1",
            channel="email",
            recipient="prospect@example.com",
            subject="A relevant idea",
            body="Hello from the SDR platform.",
            idempotency_key="idempotency-1",
        )
    )
    assert result.provider == "brevo"
    assert result.provider_message_id == "<brevo-message-id>"
    assert captured["url"] == "https://api.brevo.com/v3/smtp/email"
    assert captured["headers"]["api-key"] == "test-key"
    assert captured["json"]["to"][0]["email"] == "prospect@example.com"
    assert captured["json"]["headers"]["Idempotency-Key"] == "idempotency-1"


def test_resend_provider_uses_the_message_recipient(monkeypatch) -> None:
    captured = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"id": "resend-message-id"}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(
        "ai_sdr_platform.src.agents.outreach.email_provider.requests.post", fake_post
    )
    provider = ResendEmailProvider(
        api_key="test-key",
        from_email="verified@example.com",
        from_name="SDR Team",
    )
    from ai_sdr_platform.src.agents.outreach.models import OutreachMessage

    result = provider.send(
        OutreachMessage(
            campaign_id="campaign-1",
            intelligence_id="intelligence-1",
            contact_id="contact-1",
            channel="email",
            recipient="discovered.prospect@example.com",
            subject="A relevant idea",
            body="Hello from the SDR platform.",
            idempotency_key="idempotency-1",
        )
    )
    assert result.provider == "resend"
    assert result.provider_message_id == "resend-message-id"
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["to"] == ["discovered.prospect@example.com"]
