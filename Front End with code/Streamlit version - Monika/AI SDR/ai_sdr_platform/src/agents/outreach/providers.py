from __future__ import annotations

import smtplib
import html
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol
from uuid import uuid4
import requests

from ai_sdr_platform.src.agents.outreach.models import (
    OutreachMessage,
    ProviderSendResult,
)


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
class SMTPEmailProvider:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    use_tls: bool = True
    name: str = "smtp"

    def send(self, message: OutreachMessage) -> ProviderSendResult:
        email = EmailMessage()
        email["From"] = self.from_email
        email["To"] = message.recipient
        email["Subject"] = message.subject or "A quick question"
        email.set_content(message.body)
        with smtplib.SMTP(self.host, self.port, timeout=20) as client:
            if self.use_tls:
                client.starttls()
            if self.username:
                client.login(self.username, self.password)
            client.send_message(email)
        return ProviderSendResult(
            accepted=True,
            provider=self.name,
            provider_message_id=email["Message-ID"] or f"smtp-{uuid4()}",
            status="sent",
        )


@dataclass
class SESEmailProvider:
    region: str
    from_email: str
    name: str = "ses"

    def send(self, message: OutreachMessage) -> ProviderSendResult:
        import boto3

        response = boto3.client("ses", region_name=self.region).send_email(
            Source=self.from_email,
            Destination={"ToAddresses": [message.recipient]},
            Message={
                "Subject": {"Data": message.subject or "A quick question"},
                "Body": {"Text": {"Data": message.body}},
            },
        )
        return ProviderSendResult(
            accepted=True,
            provider=self.name,
            provider_message_id=response["MessageId"],
            status="sent",
        )


@dataclass
class BrevoEmailProvider:
    api_key: str
    from_email: str
    from_name: str
    reply_to_email: str | None = None
    timeout_seconds: float = 20.0
    name: str = "brevo"

    def send(self, message: OutreachMessage) -> ProviderSendResult:
        payload = {
            "sender": {"email": self.from_email, "name": self.from_name},
            "to": [{"email": message.recipient}],
            "subject": message.subject or "A quick question",
            "textContent": message.body,
            "htmlContent": (
                "<html><body><p>"
                + html.escape(message.body).replace("\n", "<br>")
                + "</p></body></html>"
            ),
            "headers": {
                "Idempotency-Key": message.idempotency_key,
                "X-SDR-Message-Id": message.message_id,
            },
            "tags": ["ai-sdr-outreach"],
        }
        if self.reply_to_email:
            payload["replyTo"] = {
                "email": self.reply_to_email,
                "name": self.from_name,
            }
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": self.api_key,
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = response.text[:500] if response.text else response.reason
            raise ValueError(
                f"Brevo rejected the email send with HTTP {response.status_code}: {detail}"
            ) from exc
        provider_message_id = response.json().get("messageId")
        return ProviderSendResult(
            accepted=True,
            provider=self.name,
            provider_message_id=provider_message_id,
            status="sent",
            detail="Brevo accepted the transactional email.",
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
