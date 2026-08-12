from __future__ import annotations

import re
from dataclasses import dataclass

from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredContact
from ai_sdr_platform.src.agents.outreach.models import (
    Channel,
    OutreachCampaignRequest,
)
from ai_sdr_platform.src.agents.outreach.policy import CampaignPolicyAgent
from ai_sdr_platform.src.agents.qualification.models import QualificationResult


@dataclass(frozen=True)
class OutreachDraftEligibility:
    """Outreach-owned policy for drafts that require an operator's approval."""

    email_pattern: re.Pattern[str] = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    phone_pattern: re.Pattern[str] = re.compile(r"^\+?[1-9]\d{6,14}$")

    def requested_channels(
        self,
        request: OutreachCampaignRequest,
        policy_agent: CampaignPolicyAgent,
    ) -> list[Channel]:
        """Return reachable draft channels that are allowed by Outreach policy."""
        candidates: list[Channel] = []
        if self._valid_email(request.contact.email):
            candidates.append("email")
        if self._valid_phone(request.contact.phone):
            candidates.append("sms")

        decision = policy_agent.evaluate(request)
        return [
            channel
            for channel in candidates
            if channel in decision.eligible_channels
        ]

    def eligible_nurture_draft(
        self,
        qualification: QualificationResult,
        contact: DiscoveredContact,
        channels: list[Channel],
    ) -> bool:
        """A Nurture prospect may receive reviewed outreach drafts only."""
        return bool(
            qualification.qualification_status == "Nurture"
            and contact.contact_status == "active"
            and not contact.is_former_employee
            and channels
        )

    def _valid_email(self, value: str | None) -> bool:
        return bool(value and self.email_pattern.fullmatch(value.strip()))

    def _valid_phone(self, value: str | None) -> bool:
        normalized = re.sub(r"[\s().-]", "", value or "")
        return bool(self.phone_pattern.fullmatch(normalized))
