from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from jinja2 import Environment, StrictUndefined

from ai_sdr_platform.src.agents.outreach.models import (
    Channel,
    OutreachCampaignRequest,
    OutreachMessage,
)


EMAIL_TEMPLATE = """Hi {{ first_name }},

{{ opening }}

{{ value_proposition }}

{{ call_to_action }}

Best,
{{ sender_name }}

If you would prefer not to hear from us, reply unsubscribe."""

SHORT_TEMPLATE = """Hi {{ first_name }} - {{ opening }} {{ value_proposition }} {{ call_to_action }}"""


@dataclass
class MessageComposer:
    sender_name: str = "SDR Team"

    def __post_init__(self) -> None:
        self.environment = Environment(undefined=StrictUndefined, autoescape=False)

    def compose(
        self,
        campaign_id: str,
        request: OutreachCampaignRequest,
        channels: list[Channel],
    ) -> list[OutreachMessage]:
        package = request.intelligence.personalization
        first_name = request.contact.full_name.split()[0]
        cadence = request.cadence
        messages: list[OutreachMessage] = []
        for index, channel in enumerate(channels):
            configured = cadence[index] if index < len(cadence) else None
            delay_hours = configured.delay_hours if configured else index * 72
            recipient = self._recipient(channel, request)
            template = EMAIL_TEMPLATE if channel == "email" else SHORT_TEMPLATE
            body = self.environment.from_string(template).render(
                first_name=first_name,
                opening=package.email_opening,
                value_proposition=package.value_proposition,
                call_to_action=package.call_to_action,
                sender_name=self.sender_name,
            ).strip()
            digest = sha256(
                f"{campaign_id}:{request.contact.contact_id}:{channel}:{index}".encode()
            ).hexdigest()
            messages.append(
                OutreachMessage(
                    campaign_id=campaign_id,
                    intelligence_id=request.intelligence.intelligence_id,
                    contact_id=request.contact.contact_id,
                    channel=channel,
                    recipient=recipient,
                    subject=(
                        package.email_subjects[0]
                        if channel == "email" and package.email_subjects
                        else None
                    ),
                    body=body,
                    sequence_order=index,
                    scheduled_at=datetime.now(timezone.utc) + timedelta(hours=delay_hours),
                    idempotency_key=digest,
                    metadata={
                        "evidence_signal_ids": package.evidence_signal_ids,
                        "primary_angle": package.primary_angle,
                    },
                )
            )
        return messages

    @staticmethod
    def _recipient(channel: Channel, request: OutreachCampaignRequest) -> str:
        if channel == "email":
            return request.contact.email or ""
        if channel in {"sms", "whatsapp", "phone"}:
            return request.contact.phone or ""
        return request.contact.linkedin_url or ""
