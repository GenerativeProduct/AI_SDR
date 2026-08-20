from __future__ import annotations

import hmac
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from ai_sdr_platform.src.agents.outreach.composer import MessageComposer
from ai_sdr_platform.src.agents.outreach.models import (
    Channel,
    CampaignApprovalRequest,
    CampaignListResponse,
    CampaignPauseRequest,
    MessageEditRequest,
    OpenClawCommand,
    OpenClawCommandResult,
    OutreachCampaign,
    OutreachCampaignRequest,
    OutreachEvent,
    OutreachPerformance,
)
from ai_sdr_platform.src.agents.outreach.providers import (
    DryRunProvider,
    BrevoEmailProvider,
    HumanTaskProvider,
    ProviderRegistry,
    ResendEmailProvider,
    SESEmailProvider,
    SMTPEmailProvider,
    TwilioMessagingProvider,
)
from ai_sdr_platform.src.agents.outreach.rate_limit import OutreachRateLimiter
from ai_sdr_platform.src.agents.outreach.repository import SQLAlchemyOutreachRepository
from ai_sdr_platform.src.agents.outreach.service import OutreachService
from ai_sdr_platform.src.agents.enrichment.repository import SQLAlchemyEnrichmentRepository
from ai_sdr_platform.src.api.routes.routes_prospect_intelligence import (
    get_prospect_intelligence_service,
)
from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectOutcome
from ai_sdr_platform.src.shared.config import settings

router = APIRouter(prefix="/outreach", tags=["outreach"])
_repository = SQLAlchemyOutreachRepository()
_enrichment_repository = SQLAlchemyEnrichmentRepository()
_service = OutreachService(repository=_repository)


def configure_outreach_service(llm_router: object | None = None) -> OutreachService:
    global _service
    providers = _build_provider_registry()
    _service = OutreachService(
        repository=_repository,
        providers=providers,
        composer=MessageComposer(sender_name=settings.outreach_sender_name),
        rate_limiter=OutreachRateLimiter(
            max_per_minute=settings.outreach_max_per_minute,
            max_per_recipient_per_day=settings.outreach_max_per_recipient_per_day,
        ),
        llm_router=llm_router,                       # AI-written outreach copy
        enrichment_repository=_enrichment_repository,  # source data for the AI
    )
    return _service


def get_outreach_service() -> OutreachService:
    return _service


def _build_provider_registry() -> ProviderRegistry:
    dry = DryRunProvider()
    human = HumanTaskProvider()
    email = dry
    if settings.outreach_provider == "smtp":
        if not settings.outreach_smtp_host or not settings.outreach_from_email:
            raise RuntimeError("SMTP outreach requires host and from email configuration.")
        email = SMTPEmailProvider(
            host=settings.outreach_smtp_host,
            port=settings.outreach_smtp_port,
            username=settings.outreach_smtp_username,
            password=settings.outreach_smtp_password,
            from_email=settings.outreach_from_email,
        )
    elif settings.outreach_provider == "ses":
        if not settings.outreach_from_email:
            raise RuntimeError("SES outreach requires SDR_OUTREACH_FROM_EMAIL.")
        email = SESEmailProvider(
            region=settings.outreach_aws_region,
            from_email=settings.outreach_from_email,
        )
    elif settings.outreach_provider == "brevo":
        if not settings.outreach_brevo_api_key or not settings.outreach_from_email:
            raise RuntimeError(
                "Brevo outreach requires SDR_OUTREACH_BREVO_API_KEY and SDR_OUTREACH_FROM_EMAIL."
            )
        email = BrevoEmailProvider(
            api_key=settings.outreach_brevo_api_key,
            from_email=settings.outreach_from_email,
            from_name=settings.outreach_sender_name,
            reply_to_email=settings.outreach_reply_to_email or None,
        )
    elif settings.outreach_provider == "resend":
        if not settings.outreach_resend_api_key or not settings.outreach_from_email:
            raise RuntimeError(
                "Resend outreach requires SDR_OUTREACH_RESEND_API_KEY and SDR_OUTREACH_FROM_EMAIL."
            )
        email = ResendEmailProvider(
            api_key=settings.outreach_resend_api_key,
            from_email=settings.outreach_from_email,
            from_name=settings.outreach_sender_name,
            reply_to_email=settings.outreach_reply_to_email or None,
            base_url=settings.outreach_resend_base_url,
        )

    sms = dry
    whatsapp = dry
    if (
        settings.outreach_twilio_account_sid
        and settings.outreach_twilio_auth_token
        and settings.outreach_twilio_from_number
    ):
        sms = TwilioMessagingProvider(
            account_sid=settings.outreach_twilio_account_sid,
            auth_token=settings.outreach_twilio_auth_token,
            from_number=settings.outreach_twilio_from_number,
            channel="sms",
        )
        whatsapp = TwilioMessagingProvider(
            account_sid=settings.outreach_twilio_account_sid,
            auth_token=settings.outreach_twilio_auth_token,
            from_number=settings.outreach_twilio_from_number,
            channel="whatsapp",
        )
    return ProviderRegistry(
        email=email,
        sms=sms,
        whatsapp=whatsapp,
        linkedin=human,
        phone=human,
    )


@router.post("/campaigns", response_model=OutreachCampaign)
def create_campaign(
    payload: OutreachCampaignRequest,
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    try:
        return service.create_campaign(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/campaigns", response_model=CampaignListResponse)
def list_campaigns(
    status: str | None = Query(default=None),
    service: OutreachService = Depends(get_outreach_service),
) -> CampaignListResponse:
    items = service.list_campaigns(status=status)
    return CampaignListResponse(items=items, total=len(items))


@router.get("/campaigns/{campaign_id}", response_model=OutreachCampaign)
def get_campaign(
    campaign_id: str,
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    campaign = service.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    return campaign


@router.post("/campaigns/{campaign_id}/approve", response_model=OutreachCampaign)
def approve_campaign(
    campaign_id: str,
    payload: CampaignApprovalRequest,
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    return _campaign_action(lambda: service.approve_campaign(campaign_id, payload.approved_by))


@router.post(
    "/campaigns/{campaign_id}/messages/{message_id}/regenerate",
    response_model=OutreachCampaign,
)
def regenerate_message(
    campaign_id: str,
    message_id: str,
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    return _campaign_action(lambda: service.regenerate_message(campaign_id, message_id))


@router.patch(
    "/campaigns/{campaign_id}/messages/{message_id}",
    response_model=OutreachCampaign,
)
def edit_message(
    campaign_id: str,
    message_id: str,
    payload: MessageEditRequest,
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    return _campaign_action(
        lambda: service.update_message(campaign_id, message_id, payload.subject, payload.body)
    )


@router.post("/campaigns/{campaign_id}/send", response_model=OutreachCampaign)
def send_campaign(
    campaign_id: str,
    force: bool = Query(default=False),
    channel: Channel | None = Query(default=None),
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    return _campaign_action(
        lambda: service.send_due(campaign_id, force=force, channel=channel)
    )


@router.post(
    "/campaigns/{campaign_id}/messages/{message_id}/send",
    response_model=OutreachCampaign,
)
def send_message(
    campaign_id: str,
    message_id: str,
    force: bool = Query(default=True),
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    return _campaign_action(
        lambda: service.send_message(campaign_id, message_id, force=force)
    )


@router.post("/campaigns/{campaign_id}/pause", response_model=OutreachCampaign)
def pause_campaign(
    campaign_id: str,
    payload: CampaignPauseRequest,
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    return _campaign_action(lambda: service.pause_campaign(campaign_id, payload.reason))


@router.post("/campaigns/{campaign_id}/resume", response_model=OutreachCampaign)
def resume_campaign(
    campaign_id: str,
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    return _campaign_action(lambda: service.resume_campaign(campaign_id))


@router.post("/campaigns/{campaign_id}/cancel", response_model=OutreachCampaign)
def cancel_campaign(
    campaign_id: str,
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign:
    return _campaign_action(lambda: service.cancel_campaign(campaign_id))


@router.post("/scheduler/run-due", response_model=list[OutreachCampaign])
def run_due(
    service: OutreachService = Depends(get_outreach_service),
) -> list[OutreachCampaign]:
    return service.process_due_campaigns()


@router.post("/events", response_model=OutreachCampaign | None)
def ingest_event(
    payload: OutreachEvent,
    x_outreach_webhook_secret: str | None = Header(default=None),
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign | None:
    expected = settings.outreach_webhook_secret
    if expected and not hmac.compare_digest(x_outreach_webhook_secret or "", expected):
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")
    campaign = service.ingest_event(payload)
    if campaign and payload.event_type in {
        "replied", "positive_reply", "meeting_booked", "qualified"
    }:
        intelligence_service = get_prospect_intelligence_service()
        intelligence_service.record_outcome(
            ProspectOutcome(
                intelligence_id=campaign.intelligence_id,
                account_id=campaign.account_id,
                contact_id=campaign.contact_id,
                replied=True,
                positive_reply=payload.event_type in {
                    "positive_reply", "meeting_booked", "qualified"
                },
                meeting_booked=payload.event_type in {"meeting_booked", "qualified"},
                qualified=payload.event_type == "qualified",
                source=payload.provider,
                metadata={
                    "campaign_id": campaign.campaign_id,
                    "event_id": payload.event_id,
                },
            )
        )
        snapshot = intelligence_service.get_latest(campaign.contact_id)
        intelligence_service.send_ranking_feedback(
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
                "type": payload.event_type,
                "timestamp": payload.occurred_at.isoformat(),
            }
        )
    return campaign


@router.post("/events/brevo", response_model=OutreachCampaign | None)
def ingest_brevo_event(
    payload: dict[str, Any],
    x_brevo_webhook_secret: str | None = Header(default=None),
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachCampaign | None:
    expected = settings.outreach_brevo_webhook_secret
    if expected and not hmac.compare_digest(x_brevo_webhook_secret or "", expected):
        raise HTTPException(status_code=401, detail="Invalid Brevo webhook secret.")
    event_name = str(payload.get("event", "")).lower()
    event_map = {
        "request": "queued",
        "delivered": "delivered",
        "opened": "opened",
        "unique_opened": "opened",
        "proxy_open": "opened",
        "click": "clicked",
        "soft_bounce": "bounced",
        "hard_bounce": "bounced",
        "invalid_email": "bounced",
        "blocked": "failed",
        "error": "failed",
        "spam": "unsubscribe",
        "unsubscribed": "unsubscribe",
    }
    normalized = event_map.get(event_name)
    if normalized is None:
        return None
    timestamp = payload.get("ts_event") or payload.get("ts")
    occurred_at = (
        datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
        if timestamp
        else datetime.now(timezone.utc)
    )
    event = OutreachEvent(
        provider="brevo",
        provider_event_id=str(
            payload.get("id")
            or f"{payload.get('message-id', '')}:{event_name}:{timestamp or ''}"
        ),
        provider_message_id=str(payload.get("message-id") or "") or None,
        event_type=normalized,
        occurred_at=occurred_at,
        payload=payload,
    )
    return service.ingest_event(event)


@router.get("/performance", response_model=OutreachPerformance)
def performance(
    service: OutreachService = Depends(get_outreach_service),
) -> OutreachPerformance:
    return service.performance()


@router.post("/operator/command", response_model=OpenClawCommandResult)
def openclaw_command(
    payload: OpenClawCommand,
    x_openclaw_key: str | None = Header(default=None),
    service: OutreachService = Depends(get_outreach_service),
) -> OpenClawCommandResult:
    expected = settings.outreach_openclaw_api_key
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="OpenClaw integration is disabled until SDR_OUTREACH_OPENCLAW_API_KEY is set.",
        )
    if not hmac.compare_digest(x_openclaw_key or "", expected):
        raise HTTPException(status_code=401, detail="Invalid OpenClaw API key.")

    if payload.action == "run_sdr_pipeline":
        if payload.icp_payload is None:
            raise HTTPException(status_code=400, detail="icp_payload is required.")
        from pydantic import ValidationError

        from ai_sdr_platform.src.api.routes.routes_enrichment import (
            get_enrichment_service,
        )
        from ai_sdr_platform.src.api.routes.routes_follow_up import (
            get_follow_up_service,
        )
        from ai_sdr_platform.src.api.routes.routes_icp import get_icp_service
        from ai_sdr_platform.src.api.routes.routes_prospect_discovery import (
            get_prospect_discovery_service,
        )
        from ai_sdr_platform.src.api.routes.routes_qualification import (
            get_qualification_service,
        )
        from ai_sdr_platform.src.api.routes.routes_sdr_pipeline import (
            SDRPipelineRequest,
            run_sdr_pipeline,
        )

        try:
            pipeline_payload = SDRPipelineRequest(
                icp_payload=payload.icp_payload,
                discovery_limit=payload.discovery_limit,
                enrich_top_accounts=payload.enrich_top_accounts,
                top_k=payload.top_k,
                llm_model=payload.llm_model,
                created_by=payload.actor,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=exc.errors()) from exc
        result = run_sdr_pipeline(
            pipeline_payload,
            icp_service=get_icp_service(),
            discovery_service=get_prospect_discovery_service(),
            enrichment_service=get_enrichment_service(),
            intelligence_service=get_prospect_intelligence_service(),
            qualification_service=get_qualification_service(),
            outreach_service=service,
            follow_up_service=get_follow_up_service(),
        )
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message=(
                "SDR pipeline completed. Outreach campaigns and follow-up plans "
                "were drafted and are waiting for approval."
            ),
            data=result.model_dump(mode="json"),
        )
    if payload.action == "draft_outreach":
        if payload.campaign is None:
            raise HTTPException(status_code=400, detail="campaign is required.")
        campaign = service.create_campaign(payload.campaign)
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message="Campaign drafted and held for approval.",
            data=campaign.model_dump(mode="json"),
        )
    if payload.action == "approve_campaign":
        campaign = service.approve_campaign(_required_campaign_id(payload), payload.actor)
        return _command_campaign(payload.action, "Campaign approved.", campaign)
    if payload.action == "send_campaign":
        campaign = service.send_due(_required_campaign_id(payload))
        return _command_campaign(payload.action, "Due messages processed.", campaign)
    if payload.action == "pause_campaign":
        campaign = service.pause_campaign(
            _required_campaign_id(payload), f"Paused by {payload.actor}"
        )
        return _command_campaign(payload.action, "Campaign paused.", campaign)
    if payload.action == "show_attention_replies":
        campaigns = service.attention_replies()[: payload.limit]
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message=f"{len(campaigns)} campaigns require attention.",
            data={"campaigns": [item.model_dump(mode="json") for item in campaigns]},
        )
    if payload.action == "performance_summary":
        summary = service.performance()
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message="Outreach performance summary generated.",
            data=summary.model_dump(),
        )
    if payload.action == "list_conversations":
        from ai_sdr_platform.src.api.routes.routes_conversation import (
            get_conversation_service,
        )

        conversations = get_conversation_service().list()[: payload.limit]
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message=f"Returned {len(conversations)} conversations.",
            data={
                "conversations": [
                    item.model_dump(mode="json") for item in conversations
                ]
            },
        )
    if payload.action == "approve_conversation_reply":
        if not payload.conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id is required.")
        from ai_sdr_platform.src.api.routes.routes_conversation import (
            get_conversation_service,
        )

        conversation = get_conversation_service().approve_reply(
            payload.conversation_id,
            payload.actor,
            body=payload.reply_body,
        )
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message="Conversation reply approved.",
            data=conversation.model_dump(mode="json"),
        )
    if payload.action == "send_conversation_reply":
        if not payload.conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id is required.")
        from ai_sdr_platform.src.api.routes.routes_conversation import (
            get_conversation_service,
        )

        conversation = get_conversation_service().send_approved_reply(
            payload.conversation_id
        )
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message="Approved conversation reply processed.",
            data=conversation.model_dump(mode="json"),
        )
    if payload.action == "list_follow_up_plans":
        from ai_sdr_platform.src.api.routes.routes_follow_up import (
            get_follow_up_service,
        )

        plans = get_follow_up_service().list()[: payload.limit]
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message=f"Returned {len(plans)} follow-up plans.",
            data={"plans": [item.model_dump(mode="json") for item in plans]},
        )
    if payload.action == "approve_follow_up_plan":
        if not payload.follow_up_plan_id:
            raise HTTPException(status_code=400, detail="follow_up_plan_id is required.")
        from ai_sdr_platform.src.api.routes.routes_follow_up import (
            get_follow_up_service,
        )

        plan = get_follow_up_service().approve(
            payload.follow_up_plan_id, payload.actor
        )
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message="Follow-up plan approved.",
            data=plan.model_dump(mode="json"),
        )
    if payload.action == "run_due_follow_ups":
        from ai_sdr_platform.src.api.routes.routes_follow_up import (
            get_follow_up_service,
        )

        plans = get_follow_up_service().process_due()
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message=f"Processed {len(plans)} active follow-up plans.",
            data={"plans": [item.model_dump(mode="json") for item in plans]},
        )
    if payload.action == "list_priority_prospects":
        intelligence = get_prospect_intelligence_service().list_results()
        intelligence.sort(key=lambda item: item.ranking.priority_score, reverse=True)
        items = intelligence[: payload.limit]
        return OpenClawCommandResult(
            action=payload.action,
            success=True,
            message=f"Returned {len(items)} prioritized prospects.",
            data={"prospects": [item.model_dump(mode="json") for item in items]},
        )
    raise HTTPException(status_code=400, detail="Unsupported operator action.")


def _campaign_action(action: object) -> OutreachCampaign:
    try:
        return action()  # type: ignore[operator]
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _required_campaign_id(payload: OpenClawCommand) -> str:
    if not payload.campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required.")
    return payload.campaign_id


def _command_campaign(
    action: str, message: str, campaign: OutreachCampaign
) -> OpenClawCommandResult:
    return OpenClawCommandResult(
        action=action,
        success=True,
        message=message,
        data=campaign.model_dump(mode="json"),
    )
