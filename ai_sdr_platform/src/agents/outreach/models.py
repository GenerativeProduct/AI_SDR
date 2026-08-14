from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredContact
from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectIntelligenceResult

Channel = Literal["email", "linkedin", "phone", "sms", "whatsapp"]
CampaignStatus = Literal[
    "draft", "pending_approval", "approved", "running", "paused", "completed", "cancelled"
]
MessageStatus = Literal[
    "draft", "approved", "queued", "sent", "delivered", "bounced", "replied",
    "failed", "suppressed", "human_task",
]


class OutreachCadenceStep(BaseModel):
    channel: Channel
    delay_hours: int = Field(default=0, ge=0, le=24 * 90)


class OutreachCampaignRequest(BaseModel):
    intelligence: ProspectIntelligenceResult
    contact: DiscoveredContact
    name: str | None = None
    requested_channels: list[Channel] = Field(default_factory=list)
    cadence: list[OutreachCadenceStep] = Field(default_factory=list)
    require_approval: bool = True
    consent_status: Literal["unknown", "opted_in", "opted_out"] = "unknown"
    territory: str | None = None
    created_by: str = "system"

    @model_validator(mode="after")
    def validate_handoff(self) -> "OutreachCampaignRequest":
        if self.contact.contact_id != self.intelligence.contact_id:
            raise ValueError("contact_id must match the prospect intelligence result")
        if self.contact.account_id != self.intelligence.account_id:
            raise ValueError("account_id must match the prospect intelligence result")
        return self


class MessageEditRequest(BaseModel):
    subject: str | None = None
    body: str | None = None


class PolicyDecision(BaseModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)
    eligible_channels: list[Channel] = Field(default_factory=list)
    requires_human_approval: bool = True


class ReviewResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)
    evidence_signal_ids: list[str] = Field(default_factory=list)


class OutreachMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    intelligence_id: str
    contact_id: str
    channel: Channel
    recipient: str
    subject: str | None = None
    body: str
    sequence_order: int = Field(default=0, ge=0)
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: MessageStatus = "draft"
    idempotency_key: str
    provider: str = "dry_run"
    provider_message_id: str | None = None
    review: ReviewResult | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OutreachCampaign(BaseModel):
    campaign_id: str = Field(default_factory=lambda: str(uuid4()))
    intelligence_id: str
    account_id: str
    contact_id: str
    company_name: str
    contact_name: str
    name: str
    status: CampaignStatus = "draft"
    require_approval: bool = True
    policy: PolicyDecision
    messages: list[OutreachMessage] = Field(default_factory=list)
    approved_by: str | None = None
    approved_at: datetime | None = None
    paused_reason: str | None = None
    created_by: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CampaignListResponse(BaseModel):
    items: list[OutreachCampaign]
    total: int


class CampaignApprovalRequest(BaseModel):
    approved_by: str


class CampaignPauseRequest(BaseModel):
    reason: str = "Paused by operator"


class ProviderSendResult(BaseModel):
    accepted: bool
    provider: str
    provider_message_id: str | None = None
    status: MessageStatus
    detail: str | None = None


class OutreachEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    provider: str
    provider_event_id: str
    provider_message_id: str | None = None
    message_id: str | None = None
    event_type: Literal[
        "queued", "sent", "delivered", "opened", "clicked", "bounced",
        "replied", "positive_reply", "meeting_booked", "qualified",
        "unsubscribe", "failed",
    ]
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)


class OutreachPerformance(BaseModel):
    campaigns: int = 0
    messages: int = 0
    sent: int = 0
    delivered: int = 0
    replied: int = 0
    bounced: int = 0
    failed: int = 0
    human_tasks: int = 0


class OpenClawCommand(BaseModel):
    action: Literal[
        "list_priority_prospects",
        "run_sdr_pipeline",
        "draft_outreach",
        "approve_campaign",
        "send_campaign",
        "pause_campaign",
        "show_attention_replies",
        "performance_summary",
        "list_conversations",
        "approve_conversation_reply",
        "send_conversation_reply",
        "list_follow_up_plans",
        "approve_follow_up_plan",
        "run_due_follow_ups",
    ]
    campaign_id: str | None = None
    conversation_id: str | None = None
    follow_up_plan_id: str | None = None
    reply_body: str | None = None
    actor: str = "openclaw-operator"
    limit: int = Field(default=10, ge=1, le=100)
    campaign: OutreachCampaignRequest | None = None
    icp_payload: dict[str, Any] | None = None
    discovery_limit: int = Field(default=5, ge=1, le=25)
    enrich_top_accounts: int = Field(default=3, ge=1, le=10)
    top_k: int = Field(default=8, ge=1, le=25)
    llm_model: str | None = "llama3.2:3b"


class OpenClawCommandResult(BaseModel):
    action: str
    success: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
