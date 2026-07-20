from __future__ import annotations

import hmac
import re
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from ai_sdr_platform.src.agents.conversation.models import (
    ApproveConversationReplyRequest,
    ConversationAgentStatus,
    ConversationListResponse,
    ConversationThread,
    InboundReplyRequest,
)
from ai_sdr_platform.src.agents.conversation.llm_agent import (
    StructuredConversationLLMAgent,
)
from ai_sdr_platform.src.agents.conversation.repository import (
    SQLAlchemyConversationRepository,
)
from ai_sdr_platform.src.agents.conversation.service import ConversationService
from ai_sdr_platform.src.agents.outreach.models import OutreachEvent
from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectOutcome
from ai_sdr_platform.src.api.routes.routes_follow_up import get_follow_up_service
from ai_sdr_platform.src.api.routes.routes_outreach import get_outreach_service
from ai_sdr_platform.src.api.routes.routes_prospect_intelligence import (
    get_prospect_intelligence_service,
)
from ai_sdr_platform.src.shared.config import settings

router = APIRouter(prefix="/conversations", tags=["conversations"])
_repository = SQLAlchemyConversationRepository()
_service = ConversationService(
    repository=_repository,
    outreach_service=get_outreach_service(),
    follow_up_service=get_follow_up_service(),
    intelligence_service=get_prospect_intelligence_service(),
    llm_agent=StructuredConversationLLMAgent(
        base_url=settings.conversation_llm_base_url,
        model_name=settings.conversation_llm_model,
        timeout_seconds=settings.conversation_llm_timeout_seconds,
    ),
)


def configure_conversation_service() -> ConversationService:
    global _service
    _service = ConversationService(
        repository=_repository,
        outreach_service=get_outreach_service(),
        follow_up_service=get_follow_up_service(),
        intelligence_service=get_prospect_intelligence_service(),
        llm_agent=StructuredConversationLLMAgent(
            base_url=settings.conversation_llm_base_url,
            model_name=settings.conversation_llm_model,
            timeout_seconds=settings.conversation_llm_timeout_seconds,
        ),
    )
    return _service


def get_conversation_service() -> ConversationService:
    return _service


@router.post("/inbound", response_model=ConversationThread)
def ingest_inbound_reply(
    payload: InboundReplyRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationThread:
    try:
        thread = service.ingest_reply(payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    campaign = get_outreach_service().ingest_event(
        OutreachEvent(
            provider=payload.provider,
            provider_event_id=payload.provider_event_id,
            provider_message_id=payload.provider_message_id,
            event_type=(
                "positive_reply"
                if thread.latest_classification
                and thread.latest_classification.intent
                in {"interested", "meeting_request", "pricing_request"}
                else "replied"
            ),
            occurred_at=payload.received_at,
            payload=payload.model_dump(mode="json"),
        )
    )
    if campaign:
        classification = thread.latest_classification
        intelligence = get_prospect_intelligence_service()
        intelligence.record_outcome(
            ProspectOutcome(
                intelligence_id=campaign.intelligence_id,
                account_id=campaign.account_id,
                contact_id=campaign.contact_id,
                replied=True,
                positive_reply=bool(
                    classification
                    and classification.intent
                    in {"interested", "meeting_request", "pricing_request"}
                ),
                meeting_booked=False,
                source=payload.provider,
                metadata={
                    "campaign_id": campaign.campaign_id,
                    "conversation_id": thread.conversation_id,
                    "intent": classification.intent if classification else "neutral",
                },
            )
        )
        snapshot = intelligence.get_latest(campaign.contact_id)
        intelligence.send_ranking_feedback(
            {
                "event": "interaction",
                "id": payload.provider_event_id,
                "ranking": (
                    snapshot.ranking.ranking_event_id
                    if snapshot and snapshot.ranking.ranking_event_id
                    else campaign.intelligence_id
                ),
                "user": campaign.created_by,
                "item": campaign.contact_id,
                "type": (
                    classification.intent if classification else "reply"
                ),
                "timestamp": payload.received_at.isoformat(),
            }
        )
        if classification and classification.intent == "meeting_request":
            try:
                from ai_sdr_platform.src.api.routes.routes_meeting import (
                    get_meeting_service,
                )

                get_meeting_service().ensure_from_conversation(thread.conversation_id)
            except (LookupError, ValueError):
                # The meeting remains visible in Conversation; an operator can add
                # a valid attendee email before creating the booking request.
                pass
    return thread


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    status: str | None = Query(default=None),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    items = service.list(status)
    return ConversationListResponse(items=items, total=len(items))


@router.get("/agent/status", response_model=ConversationAgentStatus)
def agent_status(
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationAgentStatus:
    return service.status()


@router.get("/{conversation_id}", response_model=ConversationThread)
def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationThread:
    thread = service.get(conversation_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return thread


@router.post("/{conversation_id}/approve-reply", response_model=ConversationThread)
def approve_reply(
    conversation_id: str,
    payload: ApproveConversationReplyRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationThread:
    try:
        return service.approve_reply(
            conversation_id, payload.approved_by, body=payload.body
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = 502 if "Brevo rejected" in detail else 409
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/{conversation_id}/send-reply", response_model=ConversationThread)
def send_reply(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationThread:
    try:
        return service.send_approved_reply(conversation_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/inbound/brevo", response_model=ConversationThread)
def ingest_brevo_inbound(
    payload: dict[str, Any],
    x_brevo_secret: str | None = Header(default=None),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationThread:
    expected = settings.outreach_brevo_inbound_secret
    if expected and not hmac.compare_digest(x_brevo_secret or "", expected):
        raise HTTPException(status_code=401, detail="Invalid Brevo inbound secret.")
    references = str(
        payload.get("references")
        or payload.get("References")
        or payload.get("inReplyTo")
        or payload.get("in_reply_to")
        or ""
    )
    candidates = re.findall(r"<[^>]+>|[A-Za-z0-9._-]{8,}", references)
    campaign = next(
        (
            get_outreach_service().find_campaign_by_provider_message_id(candidate)
            for candidate in candidates
            if get_outreach_service().find_campaign_by_provider_message_id(candidate)
        ),
        None,
    )
    if campaign is None and payload.get("campaign_id"):
        campaign = get_outreach_service().get_campaign(str(payload["campaign_id"]))
    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Could not match the inbound email to an outreach campaign.",
        )
    sender = str(
        payload.get("from")
        or payload.get("sender")
        or payload.get("sender_email")
        or ""
    )
    body = str(
        payload.get("text")
        or payload.get("body_text")
        or payload.get("body")
        or payload.get("textContent")
        or ""
    ).strip()
    if not body:
        raise HTTPException(status_code=400, detail="Inbound email body is empty.")
    request = InboundReplyRequest(
        campaign_id=campaign.campaign_id,
        body=body,
        subject=str(payload.get("subject") or "") or None,
        channel="email",
        provider="brevo",
        provider_message_id=str(
            payload.get("Message-Id")
            or payload.get("message_id")
            or payload.get("messageId")
            or ""
        )
        or None,
        sender=sender or None,
        metadata=payload,
    )
    return ingest_inbound_reply(request, service)
