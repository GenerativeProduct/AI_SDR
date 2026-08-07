from __future__ import annotations

import re
from dataclasses import dataclass

from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredContact
from ai_sdr_platform.src.agents.qualification.models import QualificationResult


@dataclass(frozen=True)
class OutreachDraftEligibility:
    """Outreach-owned policy for drafts that require an operator's approval."""

    email_pattern: re.Pattern[str] = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    def eligible_nurture_email(
        self,
        qualification: QualificationResult,
        contact: DiscoveredContact,
    ) -> bool:
        """A Nurture prospect may receive a reviewed discovery-email draft only."""
        return bool(
            qualification.qualification_status == "Nurture"
            and contact.contact_status == "active"
            and not contact.is_former_employee
            and contact.email
            and self.email_pattern.fullmatch(contact.email.strip())
        )
