from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ai_sdr_platform.src.agents.conversation.classifier import (
    ComplianceGuardrailClassifier,
    SafeFallbackClassifier,
)
from ai_sdr_platform.src.agents.conversation.llm_agent import (
    StructuredConversationLLMAgent,
    fallback_decision,
)
from ai_sdr_platform.src.agents.conversation.models import (
    ConversationAgentDecision,
    ConversationAgentStatus,
    ConversationMessage,
    ConversationThread,
    InboundReplyRequest,
)
from ai_sdr_platform.src.agents.conversation.observability import (
    ConversationObservability,
)
from ai_sdr_platform.src.agents.conversation.repository import (
    SQLAlchemyConversationRepository,
)
from ai_sdr_platform.src.agents.outreach.models import OutreachCampaign
from ai_sdr_platform.src.agents.outreach.service import OutreachService


@dataclass
class ConversationService:
    repository: SQLAlchemyConversationRepository
    outreach_service: OutreachService
    llm_agent: StructuredConversationLLMAgent = field(
        default_factory=lambda: StructuredConversationLLMAgent(
            base_url="http://127.0.0.1:11434",
            model_name="llama3.1:8b",
        )
    )
    compliance_classifier: ComplianceGuardrailClassifier = field(
        default_factory=ComplianceGuardrailClassifier
    )
    fallback_classifier: SafeFallbackClassifier = field(
        default_factory=SafeFallbackClassifier
    )
    follow_up_service: object | None = None
    intelligence_service: object | None = None
    observability: ConversationObservability = field(
        default_factory=ConversationObservability
    )

    def ingest_reply(self, request: InboundReplyRequest) -> ConversationThread:
        campaign = self.outreach_service.get_campaign(request.campaign_id)
        if campaign is None:
            raise LookupError("Campaign not found.")
        thread = self.repository.get_by_campaign(request.campaign_id) or ConversationThread(
            campaign_id=campaign.campaign_id,
            intelligence_id=campaign.intelligence_id,
            account_id=campaign.account_id,
            contact_id=campaign.contact_id,
            contact_name=campaign.contact_name,
            company_name=campaign.company_name,
        )
        context = self._retrieve_context(campaign, thread)
        with self.observability.trace(
            "ingest_reply",
            input_data={"reply": request.body, "context": context},
            metadata={
                "campaign_id": campaign.campaign_id,
                "contact_id": campaign.contact_id,
                "provider": request.provider,
            },
        ) as observation:
            decision, degraded_reason = self._decide(request.body, context, thread)
            classification = decision.classification
            thread.messages.append(
                ConversationMessage(
                    direction="inbound",
                    channel=request.channel,
                    body=request.body,
                    subject=request.subject,
                    provider=request.provider,
                    provider_message_id=request.provider_message_id,
                    created_at=request.received_at,
                    metadata=request.metadata,
                )
            )
            thread.latest_classification = classification
            thread.status = self._status(
                classification.intent, classification.requires_human
            )
            thread.suggested_reply = decision.suggested_reply
            thread.reply_approved = False
            thread.agent_mode = (
                "hybrid" if classification.source in {"rules", "hybrid"} else "llm"
            )
            thread.model_name = decision.model_name
            thread.evidence_used = decision.evidence_used
            thread.guardrail_notes = decision.guardrail_notes
            thread.observability_trace_id = observation.trace_id
            thread.degraded_reason = degraded_reason
            thread.updated_at = datetime.now(timezone.utc)
            if classification.stop_follow_up and self.follow_up_service is not None:
                stop = getattr(self.follow_up_service, "stop_for_campaign", None)
                if stop:
                    stop(
                        campaign.campaign_id,
                        f"Inbound reply classified as {classification.intent}",
                    )
            saved = self.repository.save(thread)
            observation.output = {
                "conversation_id": saved.conversation_id,
                "intent": classification.intent,
                "confidence": classification.confidence,
                "source": classification.source,
                "degraded": bool(degraded_reason),
            }
        self.observability.flush()
        return saved

    def approve_reply(
        self, conversation_id: str, approved_by: str, body: str | None = None
    ) -> ConversationThread:
        thread = self._require(conversation_id)
        if body:
            thread.suggested_reply = body
        if not thread.suggested_reply:
            raise ValueError("No suggested reply is available.")
        thread.reply_approved = True
        thread.messages.append(
            ConversationMessage(
                direction="outbound",
                channel=thread.messages[-1].channel if thread.messages else "email",
                body=thread.suggested_reply,
                metadata={"approved_by": approved_by, "status": "approved_draft"},
            )
        )
        thread.updated_at = datetime.now(timezone.utc)
        return self.repository.save(thread)

    def send_approved_reply(self, conversation_id: str) -> ConversationThread:
        thread = self._require(conversation_id)
        if not thread.reply_approved or not thread.suggested_reply:
            raise ValueError("The conversation reply must be approved before sending.")
        with self.observability.trace(
            "send_approved_reply",
            input_data={
                "conversation_id": conversation_id,
                "campaign_id": thread.campaign_id,
            },
        ) as observation:
            result = self.outreach_service.send_follow_up(
                campaign_id=thread.campaign_id,
                channel=thread.messages[-1].channel if thread.messages else "email",
                subject="Re: your reply",
                body=thread.suggested_reply,
                sequence_order=1000 + len(thread.messages),
            )
            for message in reversed(thread.messages):
                if message.direction == "outbound":
                    message.provider = result.provider
                    message.provider_message_id = result.provider_message_id
                    message.metadata["status"] = result.status
                    break
            thread.reply_approved = False
            thread.updated_at = datetime.now(timezone.utc)
            saved = self.repository.save(thread)
            observation.output = {
                "provider": result.provider,
                "status": result.status,
                "provider_message_id": result.provider_message_id,
            }
        self.observability.flush()
        return saved

    def status(self) -> ConversationAgentStatus:
        reachable = self.llm_agent.reachable()
        return ConversationAgentStatus(
            mode="hybrid",
            llm_configured=bool(self.llm_agent.base_url and self.llm_agent.model_name),
            llm_reachable=reachable,
            model_name=self.llm_agent.model_name,
            langfuse_configured=self.observability.langfuse_configured,
            detail=(
                "Structured LLM classification/drafting is active; deterministic rules are "
                "limited to compliance guardrails."
                if reachable
                else "Structured LLM is unavailable. Compliance guardrails remain active and "
                "nuanced replies use degraded human-review fallback."
            ),
        )

    def list(self, status: str | None = None) -> list[ConversationThread]:
        return self.repository.list(status)

    def get(self, conversation_id: str) -> ConversationThread | None:
        return self.repository.get(conversation_id)

    def _decide(
        self,
        reply_text: str,
        context: dict[str, Any],
        thread: ConversationThread,
    ) -> tuple[ConversationAgentDecision, str | None]:
        compliance = self.compliance_classifier.classify(reply_text)
        if compliance is not None:
            return (
                ConversationAgentDecision(
                    classification=compliance,
                    suggested_reply=self._safe_draft(thread, compliance.intent),
                    guardrail_notes=[
                        "Compliance-critical intent handled by deterministic guardrail."
                    ],
                    model_name="compliance-guardrails-v1",
                ),
                None,
            )
        try:
            decision = self.llm_agent.decide(reply_text=reply_text, context=context)
            if not decision.suggested_reply:
                decision.suggested_reply = self._safe_draft(
                    thread, decision.classification.intent
                )
                decision.guardrail_notes.append(
                    "Structured model omitted a draft; validated safe draft was supplied."
                )
            return decision, None
        except Exception as exc:
            classification = self.fallback_classifier.classify(reply_text)
            reason = f"Structured LLM unavailable: {exc}"
            return (
                fallback_decision(
                    classification,
                    self._safe_draft(thread, classification.intent),
                    model_name=self.llm_agent.model_name,
                    reason=reason,
                ),
                reason,
            )

    def _retrieve_context(
        self,
        campaign: OutreachCampaign,
        thread: ConversationThread,
    ) -> dict[str, Any]:
        intelligence = None
        if self.intelligence_service is not None:
            getter = getattr(self.intelligence_service, "get_latest", None)
            if getter:
                intelligence = getter(campaign.contact_id)
        return {
            "campaign": campaign.model_dump(mode="json"),
            "prospect_intelligence": (
                intelligence.model_dump(mode="json") if intelligence else None
            ),
            "conversation_history": [
                message.model_dump(mode="json") for message in thread.messages[-12:]
            ],
            "response_policy": {
                "human_approval_required": True,
                "do_not_invent_pricing": True,
                "do_not_invent_meeting_times": True,
                "stop_follow_up_on_human_reply": True,
            },
        }

    def _require(self, conversation_id: str) -> ConversationThread:
        thread = self.repository.get(conversation_id)
        if thread is None:
            raise LookupError("Conversation not found.")
        return thread

    @staticmethod
    def _status(intent: str, requires_human: bool) -> str:
        if intent == "unsubscribe":
            return "unsubscribed"
        if intent == "meeting_request":
            return "meeting_requested"
        if intent in {"not_now", "out_of_office"}:
            return "nurture"
        if intent == "wrong_person":
            return "closed"
        return "needs_human" if requires_human else "open"

    @staticmethod
    def _safe_draft(thread: ConversationThread, intent: str) -> str | None:
        first_name = thread.contact_name.split()[0]
        drafts = {
            "interested": f"Hi {first_name}, thanks for the interest. I can share a concise overview tailored to your priorities. Would a short call next week be useful?",
            "meeting_request": f"Hi {first_name}, happy to coordinate. I will have the team send a few available times shortly.",
            "pricing_request": f"Hi {first_name}, thanks for asking. Pricing depends on scope and rollout needs, so I would like to confirm a few details before giving you an accurate answer.",
            "objection": f"Hi {first_name}, understood, and thank you for the context. I will not push this further. If useful, I can send one short comparison focused on the concern you raised.",
            "not_now": f"Hi {first_name}, understood. I will pause outreach and follow up at a more suitable time.",
            "wrong_person": f"Hi {first_name}, thanks for letting me know. Could you point me to the person who owns this area?",
        }
        return drafts.get(intent)
