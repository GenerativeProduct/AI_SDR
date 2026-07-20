from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from ai_sdr_platform.src.agents.outreach.composer import MessageComposer
from ai_sdr_platform.src.agents.outreach.models import (
    OutreachCampaign,
    OutreachCampaignRequest,
    OutreachEvent,
    OutreachPerformance,
    ProviderSendResult,
)
from ai_sdr_platform.src.agents.outreach.observability import OutreachObservability
from ai_sdr_platform.src.agents.outreach.policy import CampaignPolicyAgent
from ai_sdr_platform.src.agents.outreach.providers import ProviderRegistry
from ai_sdr_platform.src.agents.outreach.rate_limit import OutreachRateLimiter
from ai_sdr_platform.src.agents.outreach.repository import OutreachRepository
from ai_sdr_platform.src.agents.outreach.review import ReviewApprovalAgent


@dataclass
class OutreachService:
    repository: OutreachRepository
    providers: ProviderRegistry = field(default_factory=ProviderRegistry.dry_run)
    policy_agent: CampaignPolicyAgent = field(default_factory=CampaignPolicyAgent)
    composer: MessageComposer = field(default_factory=MessageComposer)
    reviewer: ReviewApprovalAgent = field(default_factory=ReviewApprovalAgent)
    rate_limiter: OutreachRateLimiter = field(default_factory=OutreachRateLimiter)
    observability: OutreachObservability = field(default_factory=OutreachObservability)

    def create_campaign(self, request: OutreachCampaignRequest) -> OutreachCampaign:
        with self.observability.span(
            "create_campaign", intelligence_id=request.intelligence.intelligence_id
        ):
            existing = self.repository.get_by_intelligence(
                request.intelligence.intelligence_id
            )
            if existing is not None:
                return existing
            decision = self.policy_agent.evaluate(request)
            if not decision.allowed:
                raise ValueError("; ".join(decision.reasons))

            requested = request.requested_channels or [
                self._map_recommended_channel(
                    request.intelligence.personalization.recommended_channel
                )
            ]
            channels = [
                channel for channel in requested if channel in decision.eligible_channels
            ]
            if not channels:
                raise ValueError("None of the requested channels are eligible under campaign policy.")

            campaign_id = str(uuid4())
            messages = self.composer.compose(campaign_id, request, channels)
            for message in messages:
                message.review = self.reviewer.review(message, request.intelligence)
                if not message.review.passed:
                    message.status = "suppressed"

            sendable = [message for message in messages if message.review and message.review.passed]
            if not sendable:
                raise ValueError("All generated messages failed the review gate.")

            approval_required = (
                request.require_approval or decision.requires_human_approval
            )
            campaign = OutreachCampaign(
                campaign_id=campaign_id,
                intelligence_id=request.intelligence.intelligence_id,
                account_id=request.intelligence.account_id,
                contact_id=request.intelligence.contact_id,
                company_name=request.intelligence.company_name,
                contact_name=request.intelligence.contact_name,
                name=request.name or f"{request.intelligence.company_name} outreach",
                status="pending_approval" if approval_required else "approved",
                require_approval=approval_required,
                policy=decision,
                messages=messages,
                created_by=request.created_by,
            )
            return self.repository.save_campaign(campaign)

    def approve_campaign(self, campaign_id: str, approved_by: str) -> OutreachCampaign:
        campaign = self._require_campaign(campaign_id)
        if campaign.status not in {"pending_approval", "draft"}:
            raise ValueError(f"Campaign cannot be approved from status {campaign.status}.")
        now = datetime.now(timezone.utc)
        campaign.status = "approved"
        campaign.approved_by = approved_by
        campaign.approved_at = now
        campaign.updated_at = now
        for message in campaign.messages:
            if message.status == "draft":
                message.status = "approved"
                message.updated_at = now
        return self.repository.save_campaign(campaign)

    def send_due(self, campaign_id: str, *, force: bool = False) -> OutreachCampaign:
        campaign = self._require_campaign(campaign_id)
        if campaign.status not in {"approved", "running"}:
            raise ValueError(f"Campaign cannot send from status {campaign.status}.")
        now = datetime.now(timezone.utc)
        campaign.status = "running"
        for message in campaign.messages:
            if message.status not in {"approved", "queued"}:
                continue
            if not force and message.scheduled_at > now:
                message.status = "queued"
                continue
            allowed, reason = self.rate_limiter.acquire(message.recipient)
            if not allowed:
                message.status = "queued"
                message.metadata["rate_limit_reason"] = reason
                continue
            try:
                provider = self.providers.for_message(message)
                result = provider.send(message)
                message.provider = result.provider
                message.provider_message_id = result.provider_message_id
                message.status = result.status
                message.metadata["provider_detail"] = result.detail
            except Exception as exc:
                message.status = "failed"
                message.metadata["provider_error"] = str(exc)
            message.updated_at = now
        if all(
            message.status in {
                "sent", "delivered", "replied", "failed", "suppressed", "human_task"
            }
            for message in campaign.messages
        ):
            campaign.status = "completed"
        campaign.updated_at = now
        return self.repository.save_campaign(campaign)

    def process_due_campaigns(self) -> list[OutreachCampaign]:
        processed: list[OutreachCampaign] = []
        for campaign in self.repository.list_campaigns():
            if campaign.status in {"approved", "running"}:
                processed.append(self.send_due(campaign.campaign_id))
        return processed

    def pause_campaign(self, campaign_id: str, reason: str) -> OutreachCampaign:
        campaign = self._require_campaign(campaign_id)
        if campaign.status in {"completed", "cancelled"}:
            raise ValueError(f"Campaign cannot be paused from status {campaign.status}.")
        campaign.status = "paused"
        campaign.paused_reason = reason
        campaign.updated_at = datetime.now(timezone.utc)
        return self.repository.save_campaign(campaign)

    def resume_campaign(self, campaign_id: str) -> OutreachCampaign:
        campaign = self._require_campaign(campaign_id)
        if campaign.status != "paused":
            raise ValueError("Only a paused campaign can be resumed.")
        campaign.status = "approved"
        campaign.paused_reason = None
        campaign.updated_at = datetime.now(timezone.utc)
        return self.repository.save_campaign(campaign)

    def cancel_campaign(self, campaign_id: str) -> OutreachCampaign:
        campaign = self._require_campaign(campaign_id)
        campaign.status = "cancelled"
        campaign.updated_at = datetime.now(timezone.utc)
        for message in campaign.messages:
            if message.status in {"draft", "approved", "queued"}:
                message.status = "suppressed"
        return self.repository.save_campaign(campaign)

    def ingest_event(self, event: OutreachEvent) -> OutreachCampaign | None:
        if not self.repository.save_event(event):
            return None
        campaigns = self.repository.list_campaigns()
        for campaign in campaigns:
            message = next(
                (
                    candidate
                    for candidate in campaign.messages
                    if (event.message_id and candidate.message_id == event.message_id)
                    or (
                        event.provider_message_id
                        and candidate.provider_message_id == event.provider_message_id
                    )
                ),
                None,
            )
            if message is None:
                continue
            status_map = {
                "queued": "queued",
                "sent": "sent",
                "delivered": "delivered",
                "bounced": "bounced",
                "replied": "replied",
                "positive_reply": "replied",
                "meeting_booked": "replied",
                "qualified": "replied",
                "unsubscribe": "suppressed",
                "failed": "failed",
            }
            if event.event_type in status_map:
                message.status = status_map[event.event_type]  # type: ignore[assignment]
            message.metadata.setdefault("events", []).append(event.model_dump(mode="json"))
            message.updated_at = event.occurred_at
            if event.event_type in {
                "replied", "positive_reply", "meeting_booked", "qualified", "unsubscribe"
            }:
                campaign.status = "completed"
                for other in campaign.messages:
                    if other.status in {"draft", "approved", "queued"}:
                        other.status = "suppressed"
            campaign.updated_at = datetime.now(timezone.utc)
            return self.repository.save_campaign(campaign)
        return None

    def get_campaign(self, campaign_id: str) -> OutreachCampaign | None:
        return self.repository.get_campaign(campaign_id)

    def list_campaigns(self, status: str | None = None) -> list[OutreachCampaign]:
        return self.repository.list_campaigns(status=status)

    def find_campaign_by_provider_message_id(
        self, provider_message_id: str
    ) -> OutreachCampaign | None:
        return self.repository.find_by_provider_message_id(provider_message_id)

    def attention_replies(self) -> list[OutreachCampaign]:
        return [
            campaign
            for campaign in self.repository.list_campaigns()
            if any(message.status == "replied" for message in campaign.messages)
        ]

    def performance(self) -> OutreachPerformance:
        campaigns = self.repository.list_campaigns()
        messages = [message for campaign in campaigns for message in campaign.messages]
        return OutreachPerformance(
            campaigns=len(campaigns),
            messages=len(messages),
            sent=sum(message.status in {"sent", "delivered", "replied"} for message in messages),
            delivered=sum(message.status in {"delivered", "replied"} for message in messages),
            replied=sum(message.status == "replied" for message in messages),
            bounced=sum(message.status == "bounced" for message in messages),
            failed=sum(message.status == "failed" for message in messages),
            human_tasks=sum(message.status == "human_task" for message in messages),
        )

    def send_follow_up(
        self,
        *,
        campaign_id: str,
        channel: str,
        subject: str | None,
        body: str,
        sequence_order: int,
    ) -> ProviderSendResult:
        from hashlib import sha256

        from ai_sdr_platform.src.agents.outreach.models import OutreachMessage

        campaign = self._require_campaign(campaign_id)
        source = next(
            (message for message in campaign.messages if message.channel == channel),
            campaign.messages[0] if campaign.messages else None,
        )
        if source is None:
            raise ValueError("Campaign has no recipient for follow-up.")
        message = OutreachMessage(
            campaign_id=campaign.campaign_id,
            intelligence_id=campaign.intelligence_id,
            contact_id=campaign.contact_id,
            channel=channel,  # type: ignore[arg-type]
            recipient=source.recipient,
            subject=subject,
            body=body,
            sequence_order=sequence_order,
            status="approved",
            idempotency_key=sha256(
                f"follow-up:{campaign_id}:{sequence_order}".encode()
            ).hexdigest(),
        )
        allowed, reason = self.rate_limiter.acquire(message.recipient)
        if not allowed:
            message.status = "queued"
            message.metadata["rate_limit_reason"] = reason
            campaign.messages.append(message)
            self.repository.save_campaign(campaign)
            return ProviderSendResult(
                accepted=False,
                provider="rate_limiter",
                status="queued",
                detail=reason,
            )
        result = self.providers.for_message(message).send(message)
        message.provider = result.provider
        message.provider_message_id = result.provider_message_id
        message.status = result.status
        message.updated_at = datetime.now(timezone.utc)
        campaign.messages.append(message)
        campaign.updated_at = message.updated_at
        self.repository.save_campaign(campaign)
        return result

    def _require_campaign(self, campaign_id: str) -> OutreachCampaign:
        campaign = self.repository.get_campaign(campaign_id)
        if campaign is None:
            raise LookupError("Campaign not found.")
        return campaign

    @staticmethod
    def _map_recommended_channel(channel: str) -> str:
        if channel == "multi_channel":
            return "email"
        return channel
