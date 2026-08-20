from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from ai_sdr_platform.src.agents.outreach.email_provider import (
    BrevoEmailProvider,
    ResendEmailProvider,
    SESEmailProvider,
    SMTPEmailProvider,
)
from ai_sdr_platform.src.agents.outreach.models import (
    OutreachMessage,
    ProviderSendResult,
)
from ai_sdr_platform.src.agents.outreach.sms_provider import TwilioMessagingProvider


class OutreachProvider(Protocol):
    name: str

    def send(self, message: OutreachMessage) -> ProviderSendResult:
        ...


@dataclass
class DryRunProvider:
    name: str = "dry_run"

    def send(self, message: OutreachMessage) -> ProviderSendResult:
        return ProviderSendResult(
            accepted=True,
            provider=self.name,
            provider_message_id=f"dry-{uuid4()}",
            status="sent",
            detail="Accepted by the local dry-run provider; no external message was sent.",
        )


@dataclass
class HumanTaskProvider:
    name: str = "human_task"

    def send(self, message: OutreachMessage) -> ProviderSendResult:
        return ProviderSendResult(
            accepted=True,
            provider=self.name,
            provider_message_id=f"task-{uuid4()}",
            status="human_task",
            detail="Created a human task. No automated action was taken on this channel.",
        )


@dataclass
class ProviderRegistry:
    email: OutreachProvider
    sms: OutreachProvider
    whatsapp: OutreachProvider
    linkedin: OutreachProvider
    phone: OutreachProvider

    def for_message(self, message: OutreachMessage) -> OutreachProvider:
        return getattr(self, message.channel)

    @classmethod
    def dry_run(cls) -> "ProviderRegistry":
        dry = DryRunProvider()
        human = HumanTaskProvider()
        return cls(email=dry, sms=dry, whatsapp=dry, linkedin=human, phone=human)
