from __future__ import annotations

from dataclasses import dataclass, field

from ai_sdr_platform.src.agents.outreach.models import (
    Channel,
    OutreachCampaignRequest,
    PolicyDecision,
)


@dataclass
class CampaignPolicyAgent:
    blocked_domains: set[str] = field(default_factory=set)
    allow_unknown_email_consent: bool = True

    def evaluate(self, request: OutreachCampaignRequest) -> PolicyDecision:
        reasons: list[str] = []
        eligible: list[Channel] = []
        contact = request.contact

        if request.consent_status == "opted_out":
            return PolicyDecision(
                allowed=False,
                reasons=["Recipient has opted out of outreach."],
                eligible_channels=[],
            )
        if contact.contact_status != "active" or contact.is_former_employee:
            return PolicyDecision(
                allowed=False,
                reasons=["Contact is not an active employee."],
                eligible_channels=[],
            )

        email_domain = (contact.email or "").rsplit("@", 1)[-1].lower()
        if contact.email and email_domain not in self.blocked_domains:
            if request.consent_status != "unknown" or self.allow_unknown_email_consent:
                eligible.append("email")
        if contact.linkedin_url:
            eligible.append("linkedin")
        if contact.phone:
            eligible.extend(["phone", "sms", "whatsapp"])

        if not eligible:
            reasons.append("No eligible, reachable channel is available for this contact.")
        if request.consent_status == "unknown":
            reasons.append("Consent is unknown; approval and applicable-law review are required.")
        if "linkedin" in eligible:
            reasons.append("LinkedIn outreach is emitted as a human task, not browser automation.")

        return PolicyDecision(
            allowed=bool(eligible),
            reasons=reasons,
            eligible_channels=list(dict.fromkeys(eligible)),
            requires_human_approval=True,
        )
