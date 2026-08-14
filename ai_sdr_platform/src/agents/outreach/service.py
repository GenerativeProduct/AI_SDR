from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

import logging

from ai_sdr_platform.src.agents.outreach import ai_writer
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
from ai_sdr_platform.src.shared.config import settings

logger = logging.getLogger("sdr.outreach")


@dataclass
class OutreachService:
    repository: OutreachRepository
    providers: ProviderRegistry = field(default_factory=ProviderRegistry.dry_run)
    policy_agent: CampaignPolicyAgent = field(default_factory=CampaignPolicyAgent)
    composer: MessageComposer = field(default_factory=MessageComposer)
    reviewer: ReviewApprovalAgent = field(default_factory=ReviewApprovalAgent)
    rate_limiter: OutreachRateLimiter = field(default_factory=OutreachRateLimiter)
    observability: OutreachObservability = field(default_factory=OutreachObservability)
    llm_router: object | None = None            # for AI-written copy
    enrichment_repository: object | None = None  # to fetch enrichment by account_id

    # ------------------------------------------------------------------
    def _ai_context(self, account_id: str) -> tuple[str, list[str], list[str]]:
        """Pull company summary / signals / pain points from the latest enrichment."""
        summary, signals, pains = "", [], []
        repo = self.enrichment_repository
        if repo is not None and hasattr(repo, "get_latest"):
            try:
                enr = repo.get_latest(account_id)
            except Exception as exc:
                logger.error("Could not load enrichment for %s: %s", account_id, exc)
                enr = None
            if enr is not None:
                summary = getattr(enr, "company_summary", "") or ""
                pains = list(getattr(enr, "pain_point_hypotheses", []) or [])
                for s in getattr(enr, "signals", []) or []:
                    detail = getattr(s, "detail", None) or (s.get("detail") if isinstance(s, dict) else None)
                    if detail:
                        signals.append(str(detail))
        return summary, signals, pains

    def _ai_rewrite(self, request: OutreachCampaignRequest, messages: list) -> None:
        """Replace each message body/subject with LLM-written copy (best effort)."""
        if not settings.outreach_ai_enabled or self.llm_router is None:
            return
        contact = request.contact
        first_name = (contact.full_name or "").split()[0] if contact.full_name else ""
        summary, signals, pains = self._ai_context(contact.account_id)
        for message in messages:
            written = ai_writer.generate_message(
                self.llm_router,
                channel=message.channel,
                first_name=first_name,
                title=contact.title or "",
                company=request.intelligence.company_name,
                company_summary=summary,
                signals=signals,
                pain_points=pains,
                offer=settings.outreach_offer_summary,
                model_name=settings.outreach_llm_model,
                provider=settings.outreach_llm_provider,
            )
            if not written:
                continue
            original_body, original_subject = message.body, message.subject
            new_body = written["body"]
            # The review gate requires an opt-out line on emails; the model often
            # omits it, so append a compliant one when missing.
            if message.channel == "email" and "unsubscribe" not in new_body.lower():
                new_body = new_body.rstrip() + "\n\nIf you'd prefer not to hear from me, reply 'unsubscribe'."
            message.body = new_body
            if message.channel == "email" and written.get("subject"):
                message.subject = written["subject"]
            # Safety net: keep the AI copy only if it still passes review; else
            # revert to the template (which passed) so a campaign never fails.
            if not self.reviewer.review(message, request.intelligence).passed:
                message.body, message.subject = original_body, original_subject
                logger.info("AI copy failed review for %s; kept template draft.", contact.full_name)

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
            # Stash the contact title so a later "regenerate" can rebuild context.
            for message in messages:
                message.metadata["contact_title"] = request.contact.title or ""
            # Rewrite the template drafts with AI copy from the prospect's data.
            self._ai_rewrite(request, messages)
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

    def send_message(self, campaign_id: str, message_id: str, *, force: bool = True) -> OutreachCampaign:
        """Send a single message (one channel) through its configured provider."""
        campaign = self._require_campaign(campaign_id)
        if campaign.status not in {"approved", "running"}:
            raise ValueError(
                f"Approve the campaign before sending (current status: {campaign.status})."
            )
        message = self._find_message(campaign, message_id)
        if message.status in {"sent", "delivered", "replied", "human_task"}:
            raise ValueError(f"This message was already handled (status: {message.status}).")
        now = datetime.now(timezone.utc)
        campaign.status = "running"
        allowed, reason = self.rate_limiter.acquire(message.recipient)
        if not allowed:
            message.status = "queued"
            message.metadata["rate_limit_reason"] = reason
        else:
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
            m.status in {"sent", "delivered", "replied", "failed", "suppressed", "human_task"}
            for m in campaign.messages
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

    def _find_message(self, campaign: OutreachCampaign, message_id: str):
        message = next((m for m in campaign.messages if m.message_id == message_id), None)
        if message is None:
            raise ValueError("Message not found in campaign.")
        return message

    def regenerate_message(self, campaign_id: str, message_id: str) -> OutreachCampaign:
        """Re-run the AI writer for a single message using the prospect's data."""
        if self.llm_router is None:
            raise ValueError("No LLM is configured for AI regeneration.")
        campaign = self._require_campaign(campaign_id)
        message = self._find_message(campaign, message_id)
        first_name = (campaign.contact_name or "").split()[0] if campaign.contact_name else ""
        title = str(message.metadata.get("contact_title") or "")
        summary, signals, pains = self._ai_context(campaign.account_id)
        written = ai_writer.generate_message(
            self.llm_router,
            channel=message.channel,
            first_name=first_name,
            title=title,
            company=campaign.company_name,
            company_summary=summary,
            signals=signals,
            pain_points=pains,
            offer=settings.outreach_offer_summary,
            model_name=settings.outreach_llm_model,
            provider=settings.outreach_llm_provider,
        )
        if not written or not written.get("body"):
            raise ValueError("The model did not return usable copy; try again.")
        body = written["body"]
        if message.channel == "email" and "unsubscribe" not in body.lower():
            body = body.rstrip() + "\n\nIf you'd prefer not to hear from me, reply 'unsubscribe'."
        message.body = body
        if message.channel == "email" and written.get("subject"):
            message.subject = written["subject"]
        return self.repository.save_campaign(campaign)

    def update_message(
        self, campaign_id: str, message_id: str, subject: str | None = None, body: str | None = None
    ) -> OutreachCampaign:
        """Save user edits to a message's subject/body."""
        campaign = self._require_campaign(campaign_id)
        message = self._find_message(campaign, message_id)
        if subject is not None:
            message.subject = subject
        if body is not None and body.strip():
            message.body = body
        return self.repository.save_campaign(campaign)

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
