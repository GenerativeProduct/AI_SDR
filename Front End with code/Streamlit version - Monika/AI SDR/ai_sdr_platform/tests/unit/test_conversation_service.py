from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from ai_sdr_platform.src.agents.conversation.models import (
    ConversationAgentDecision,
    InboundReplyRequest,
    ReplyClassification,
)
from ai_sdr_platform.src.agents.conversation.service import ConversationService


class MemoryConversationRepository:
    def __init__(self) -> None:
        self.thread = None

    def get_by_campaign(self, campaign_id):
        return self.thread if self.thread and self.thread.campaign_id == campaign_id else None

    def save(self, thread):
        self.thread = thread
        return thread

    def get(self, conversation_id):
        return self.thread if self.thread and self.thread.conversation_id == conversation_id else None

    def list(self, status=None):
        if self.thread is None or (status and self.thread.status != status):
            return []
        return [self.thread]


class FakeCampaign:
    campaign_id = "campaign-1"
    intelligence_id = "intelligence-1"
    account_id = "account-1"
    contact_id = "contact-1"
    contact_name = "Sarah Chen"
    company_name = "Acme"

    def model_dump(self, mode="json"):
        return {
            "campaign_id": self.campaign_id,
            "contact_id": self.contact_id,
            "messages": [{"body": "Original outreach"}],
        }


class FakeOutreachService:
    def get_campaign(self, campaign_id):
        return FakeCampaign() if campaign_id == "campaign-1" else None


class FakeFollowUpService:
    def __init__(self):
        self.stopped = None

    def stop_for_campaign(self, campaign_id, reason):
        self.stopped = (campaign_id, reason)


class FakeLLMAgent:
    base_url = "http://example"
    model_name = "conversation-test-model"

    def __init__(self):
        self.calls = 0

    def decide(self, *, reply_text, context):
        self.calls += 1
        return ConversationAgentDecision(
            classification=ReplyClassification(
                intent="pricing_request",
                confidence=0.91,
                sentiment="positive",
                requires_human=True,
                stop_follow_up=True,
                next_action="Prepare a grounded pricing response.",
                reasons=["Structured model identified pricing intent."],
                source="llm",
            ),
            suggested_reply="Thanks for asking. I can confirm scope before sharing pricing.",
            evidence_used=["Original outreach"],
            model_name=self.model_name,
        )

    def reachable(self):
        return True


def request(body: str) -> InboundReplyRequest:
    return InboundReplyRequest(
        campaign_id="campaign-1",
        body=body,
        provider="test",
        received_at=datetime.now(timezone.utc),
    )


def test_nuanced_reply_uses_structured_llm_and_stops_follow_up():
    llm = FakeLLMAgent()
    follow_up = FakeFollowUpService()
    service = ConversationService(
        repository=MemoryConversationRepository(),
        outreach_service=FakeOutreachService(),
        llm_agent=llm,
        follow_up_service=follow_up,
    )

    thread = service.ingest_reply(request("Could you explain how pricing changes by scope?"))

    assert llm.calls == 1
    assert thread.latest_classification.intent == "pricing_request"
    assert thread.latest_classification.source == "llm"
    assert thread.agent_mode == "llm"
    assert thread.model_name == "conversation-test-model"
    assert thread.suggested_reply
    assert follow_up.stopped[0] == "campaign-1"


def test_unsubscribe_uses_compliance_guardrail_without_llm():
    llm = FakeLLMAgent()
    service = ConversationService(
        repository=MemoryConversationRepository(),
        outreach_service=FakeOutreachService(),
        llm_agent=llm,
        follow_up_service=FakeFollowUpService(),
    )

    thread = service.ingest_reply(request("Please unsubscribe me and stop emailing."))

    assert llm.calls == 0
    assert thread.latest_classification.intent == "unsubscribe"
    assert thread.latest_classification.source == "rules"
    assert thread.status == "unsubscribed"
    assert thread.agent_mode == "hybrid"
