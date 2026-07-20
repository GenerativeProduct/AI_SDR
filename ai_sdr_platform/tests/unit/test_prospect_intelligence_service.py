import json
from pathlib import Path

from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectIntelligenceRequest
from ai_sdr_platform.src.agents.prospect_intelligence.personalization import PersonalizationAgent
from ai_sdr_platform.src.agents.prospect_intelligence.repository import (
    SQLAlchemyProspectIntelligenceRepository,
)
from ai_sdr_platform.src.agents.prospect_intelligence.service import ProspectIntelligenceService


class FakeLLMRouter:
    def complete(self, **kwargs):
        return json.dumps(
            {
                "primary_angle": "Recent sales hiring",
                "value_proposition": "Improve pipeline execution as the sales team expands.",
                "email_subjects": ["Scaling the new sales team"],
                "email_opening": "Hi Sarah, I noticed Acme is expanding its sales team.",
                "linkedin_message": "Hi Sarah, congratulations on the recent sales hiring.",
                "call_opener": "I noticed the sales team expansion and wanted to compare pipeline workflows.",
                "recommended_channel": "multi_channel",
                "call_to_action": "Open to a 15-minute conversation?",
                "evidence_signal_ids": [],
                "guardrail_notes": ["Verify the hiring evidence before sending."],
            }
        )


def _request() -> ProspectIntelligenceRequest:
    return ProspectIntelligenceRequest(
        account={
            "account_id": "acc_1",
            "icp_id": "icp_1",
            "company_name": "Acme",
            "industry": "SaaS",
            "location": "US",
            "employee_count": 500,
            "fit_score": 84,
        },
        contact={
            "contact_id": "con_1",
            "account_id": "acc_1",
            "full_name": "Sarah Chen",
            "title": "VP Sales",
            "department": "Sales",
            "seniority": "VP",
            "email": "sarah@example.com",
            "confidence": 92,
            "persona_match_score": 88,
        },
        enrichment={
            "account_id": "acc_1",
            "company_name": "Acme",
            "company_summary": "Acme provides sales workflow software.",
            "products_services": ["Sales workflow software"],
            "target_customers": ["Revenue teams"],
            "signals": [
                {
                    "type": "hiring",
                    "detail": "Acme is hiring account executives",
                    "confidence": 0.9,
                    "source_url": "https://example.com/jobs",
                },
                {
                    "type": "risk",
                    "detail": "Budget pressure was mentioned in recent reporting",
                    "confidence": 0.6,
                    "source_url": "https://example.com/report",
                },
            ],
            "pain_point_hypotheses": ["pipeline visibility gaps"],
            "personalization_angles": ["Reference sales-team expansion"],
            "contact_briefs": [{"contact_id": "con_1"}],
            "recommended_next_action": "Contact VP Sales",
            "confidence_score": 0.82,
            "citations": [
                {"title": "Acme jobs", "url": "https://example.com/jobs"},
                {"title": "Acme report", "url": "https://example.com/report"},
            ],
        },
    )


def test_analyze_normalizes_scores_personalizes_and_persists(tmp_path: Path) -> None:
    repo = SQLAlchemyProspectIntelligenceRepository(
        db_url=f"sqlite:///{(tmp_path / 'intelligence.db').resolve()}"
    )
    service = ProspectIntelligenceService(
        repository=repo,
        personalization_agent=PersonalizationAgent(llm_router=FakeLLMRouter()),
    )

    result = service.analyze(_request())

    assert {signal.signal_type for signal in result.signals} == {"hiring", "risk"}
    assert result.features.account_fit_score == 0.84
    assert result.features.persona_match_score == 0.88
    assert result.intent.probability.mode == "heuristic"
    assert result.propensity.reply_probability.calibrated is False
    assert result.personalization.source == "llm"
    assert "heuristic fallback" in result.warnings[0]
    assert service.get_latest("con_1").intelligence_id == result.intelligence_id


def test_request_rejects_cross_account_handoff() -> None:
    payload = _request().model_dump()
    payload["contact"]["account_id"] = "another-account"
    try:
        ProspectIntelligenceRequest.model_validate(payload)
        assert False, "expected account handoff validation error"
    except Exception as exc:
        assert "contact.account_id must match" in str(exc)
