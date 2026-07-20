from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    IntelligenceSignal,
    PersonalizationPackage,
    ProspectIntelligenceRequest,
    PropensityAssessment,
)


@dataclass
class PersonalizationAgent:
    llm_router: object | None = None

    def generate(
        self,
        request: ProspectIntelligenceRequest,
        signals: list[IntelligenceSignal],
        propensity: PropensityAssessment,
    ) -> PersonalizationPackage:
        if self.llm_router is not None:
            raw = self.llm_router.complete(
                prompt=self._prompt(request, signals, propensity),
                provider=request.llm_provider,
                max_tokens=900,
                model_name=request.llm_model,
            )
            parsed = self._extract_json(raw)
            if parsed:
                try:
                    parsed["source"] = "llm"
                    parsed["evidence_signal_ids"] = self._valid_evidence_ids(
                        parsed.get("evidence_signal_ids", []), signals
                    )
                    return PersonalizationPackage.model_validate(parsed)
                except Exception:
                    pass
        return self._fallback(request, signals)

    def _prompt(
        self,
        request: ProspectIntelligenceRequest,
        signals: list[IntelligenceSignal],
        propensity: PropensityAssessment,
    ) -> str:
        evidence = [
            {
                "signal_id": signal.signal_id,
                "type": signal.signal_type,
                "detail": signal.detail,
                "verified": signal.verified,
                "source_url": signal.source_url,
            }
            for signal in signals
        ]
        payload = {
            "account": request.account.model_dump(mode="json"),
            "contact": request.contact.model_dump(mode="json"),
            "enrichment": request.enrichment.model_dump(mode="json"),
            "propensity": propensity.model_dump(mode="json"),
            "evidence": evidence,
        }
        return (
            "You are a B2B SDR personalization agent. Produce grounded channel-ready messaging. "
            "Use only supplied evidence. Treat pain points as hypotheses, never facts. "
            "Return JSON only with keys: primary_angle, value_proposition, email_subjects, "
            "email_opening, linkedin_message, call_opener, recommended_channel, call_to_action, "
            "evidence_signal_ids, guardrail_notes. recommended_channel must be email, linkedin, "
            "phone, or multi_channel. Keep messages concise and do not invent metrics.\n\n"
            f"Input:\n{json.dumps(payload, indent=2)}"
        )

    @staticmethod
    def _fallback(
        request: ProspectIntelligenceRequest,
        signals: list[IntelligenceSignal],
    ) -> PersonalizationPackage:
        account = request.account
        contact = request.contact
        evidence = next((signal for signal in signals if signal.polarity == "positive"), None)
        pain_point = (
            request.enrichment.pain_point_hypotheses[0]
            if request.enrichment.pain_point_hypotheses
            else "prospect research and pipeline execution"
        )
        angle = evidence.detail if evidence else f"{account.company_name}'s {account.industry} operating context"
        return PersonalizationPackage(
            primary_angle=angle,
            value_proposition=f"Connect the offer to {pain_point} without presenting the hypothesis as a confirmed fact.",
            email_subjects=[
                f"Idea for {account.company_name}",
                f"{contact.full_name}, a thought on {pain_point}",
            ],
            email_opening=(
                f"Hi {contact.full_name}, I noticed {angle}. "
                f"Teams in your position often review how they handle {pain_point}."
            ),
            linkedin_message=(
                f"Hi {contact.full_name}, I came across {angle}. "
                f"I have a concise idea related to {pain_point} that may be relevant to your role."
            ),
            call_opener=(
                f"I am calling because of {angle}; I wanted to test whether {pain_point} "
                "is currently a priority for your team."
            ),
            recommended_channel="email" if contact.email else "linkedin",
            call_to_action="Would a short 15-minute conversation be useful?",
            evidence_signal_ids=[evidence.signal_id] if evidence else [],
            guardrail_notes=[
                "Verify the selected evidence before sending.",
                "Present inferred pain points as hypotheses.",
            ],
            source="deterministic",
        )

    @staticmethod
    def _valid_evidence_ids(values: Any, signals: list[IntelligenceSignal]) -> list[str]:
        allowed = {signal.signal_id for signal in signals}
        return [str(value) for value in values if str(value) in allowed]

    @staticmethod
    def _extract_json(raw: str) -> dict[str, Any]:
        raw = str(raw or "")
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end <= start:
            return {}
        try:
            data = json.loads(raw[start : end + 1])
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
