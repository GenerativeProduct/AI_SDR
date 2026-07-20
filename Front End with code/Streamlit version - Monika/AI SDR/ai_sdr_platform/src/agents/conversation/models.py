from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

ReplyIntent = Literal[
    "interested",
    "meeting_request",
    "pricing_request",
    "objection",
    "not_now",
    "unsubscribe",
    "wrong_person",
    "out_of_office",
    "neutral",
]
ConversationStatus = Literal[
    "open", "needs_human", "meeting_requested", "nurture", "closed", "unsubscribed"
]


class InboundReplyRequest(BaseModel):
    campaign_id: str
    body: str = Field(min_length=1)
    subject: str | None = None
    channel: Literal["email", "linkedin", "sms", "whatsapp", "phone"] = "email"
    provider: str = "manual"
    provider_message_id: str | None = None
    provider_event_id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str | None = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReplyClassification(BaseModel):
    intent: ReplyIntent
    confidence: float = Field(ge=0.0, le=1.0)
    sentiment: Literal["positive", "neutral", "negative"]
    requires_human: bool
    stop_follow_up: bool
    next_action: str
    detected_entities: dict[str, str] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    source: Literal["rules", "llm", "hybrid"] = "rules"


class ConversationAgentDecision(BaseModel):
    classification: ReplyClassification
    suggested_reply: str | None = None
    evidence_used: list[str] = Field(default_factory=list)
    guardrail_notes: list[str] = Field(default_factory=list)
    model_name: str | None = None


class ConversationMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    direction: Literal["inbound", "outbound"]
    channel: str
    body: str
    subject: str | None = None
    provider: str = "internal"
    provider_message_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationThread(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    intelligence_id: str
    account_id: str
    contact_id: str
    contact_name: str
    company_name: str
    status: ConversationStatus = "open"
    latest_classification: ReplyClassification | None = None
    suggested_reply: str | None = None
    reply_approved: bool = False
    agent_mode: Literal["rules", "llm", "hybrid"] = "rules"
    model_name: str | None = None
    evidence_used: list[str] = Field(default_factory=list)
    guardrail_notes: list[str] = Field(default_factory=list)
    observability_trace_id: str | None = None
    degraded_reason: str | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationListResponse(BaseModel):
    items: list[ConversationThread]
    total: int


class ApproveConversationReplyRequest(BaseModel):
    approved_by: str
    body: str | None = None


class ConversationAgentStatus(BaseModel):
    mode: Literal["hybrid"]
    llm_configured: bool
    llm_reachable: bool
    model_name: str
    compliance_guardrails: bool = True
    langfuse_configured: bool
    retrieval_context_enabled: bool = True
    detail: str
