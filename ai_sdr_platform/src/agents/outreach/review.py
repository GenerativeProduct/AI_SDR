from __future__ import annotations

from dataclasses import dataclass, field

from ai_sdr_platform.src.agents.outreach.models import OutreachMessage, ReviewResult
from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectIntelligenceResult


@dataclass
class ReviewApprovalAgent:
    prohibited_phrases: set[str] = field(
        default_factory=lambda: {"guaranteed results", "100% guaranteed", "risk-free"}
    )

    def review(
        self,
        message: OutreachMessage,
        intelligence: ProspectIntelligenceResult,
    ) -> ReviewResult:
        issues: list[str] = []
        body_lower = message.body.lower()
        evidence_ids = message.metadata.get("evidence_signal_ids", [])
        valid_ids = {signal.signal_id for signal in intelligence.signals}

        if not message.recipient:
            issues.append(f"No recipient is available for channel {message.channel}.")
        if any(phrase in body_lower for phrase in self.prohibited_phrases):
            issues.append("Message contains an unsupported or prohibited claim.")
        if evidence_ids and not set(evidence_ids).issubset(valid_ids):
            issues.append("Message references evidence that is absent from the intelligence snapshot.")
        if message.channel == "email" and "unsubscribe" not in body_lower:
            issues.append("Email does not contain an opt-out instruction.")
        if message.channel in {"sms", "whatsapp", "linkedin"} and len(message.body) > 1000:
            issues.append("Message exceeds the channel length guardrail.")

        return ReviewResult(
            passed=not issues,
            issues=issues,
            evidence_signal_ids=list(evidence_ids),
        )
