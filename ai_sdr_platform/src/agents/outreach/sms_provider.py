from __future__ import annotations

from dataclasses import dataclass

from ai_sdr_platform.src.agents.outreach.models import (
    OutreachMessage,
    ProviderSendResult,
)


@dataclass
class TwilioMessagingProvider:
    account_sid: str
    auth_token: str
    from_number: str
    channel: str = "sms"
    name: str = "twilio"

    def send(self, message: OutreachMessage) -> ProviderSendResult:
        from twilio.rest import Client

        recipient = message.recipient
        sender = self.from_number
        if self.channel == "whatsapp":
            recipient = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"
            sender = sender if sender.startswith("whatsapp:") else f"whatsapp:{sender}"
        result = Client(self.account_sid, self.auth_token).messages.create(
            body=message.body,
            from_=sender,
            to=recipient,
        )
        return ProviderSendResult(
            accepted=True,
            provider=self.name,
            provider_message_id=result.sid,
            status="sent",
        )
