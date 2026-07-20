from pathlib import Path

from fastapi.testclient import TestClient

from ai_sdr_platform.src.agents.prospect_intelligence.repository import (
    SQLAlchemyProspectIntelligenceRepository,
)
from ai_sdr_platform.src.agents.prospect_intelligence.service import ProspectIntelligenceService
from ai_sdr_platform.src.api.app import create_app
from ai_sdr_platform.src.api.routes import routes_prospect_intelligence


def test_analyze_get_and_list_prospect_intelligence(tmp_path: Path) -> None:
    repo = SQLAlchemyProspectIntelligenceRepository(
        db_url=f"sqlite:///{(tmp_path / 'api.db').resolve()}"
    )
    routes_prospect_intelligence._repository = repo
    routes_prospect_intelligence._service = ProspectIntelligenceService(repository=repo)
    client = TestClient(create_app())

    response = client.post(
        "/prospect-intelligence/analyze",
        json={
            "account": {
                "account_id": "acc_api",
                "icp_id": "icp_api",
                "company_name": "Example Corp",
                "industry": "Software",
                "location": "Europe",
                "employee_count": 700,
                "fit_score": 90,
            },
            "contact": {
                "contact_id": "con_api",
                "account_id": "acc_api",
                "full_name": "Alex Lee",
                "title": "VP Revenue Operations",
                "department": "Revenue Operations",
                "seniority": "VP",
                "email": "alex@example.com",
                "confidence": 90,
                "persona_match_score": 95,
            },
            "enrichment": {
                "account_id": "acc_api",
                "company_name": "Example Corp",
                "company_summary": "Example Corp builds revenue workflow software.",
                "signals": [
                    {
                        "type": "intent",
                        "detail": "Multiple pricing-page visits were observed",
                        "confidence": 0.9,
                        "source_url": "https://example.com/evidence",
                    }
                ],
                "pain_point_hypotheses": ["manual revenue workflows"],
                "personalization_angles": ["Reference pricing research"],
                "recommended_next_action": "Contact Revenue Operations",
                "confidence_score": 0.8,
                "citations": [
                    {
                        "title": "Evidence",
                        "url": "https://example.com/evidence",
                    }
                ],
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["contact_id"] == "con_api"
    assert body["signals"][0]["signal_type"] == "web_intent"
    assert body["propensity"]["reply_probability"]["mode"] == "heuristic"

    fetched = client.get("/prospect-intelligence/con_api")
    assert fetched.status_code == 200
    listed = client.get("/prospect-intelligence", params={"account_id": "acc_api"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    outcome = client.post(
        "/prospect-intelligence/outcomes",
        json={
            "intelligence_id": body["intelligence_id"],
            "account_id": "acc_api",
            "contact_id": "con_api",
            "replied": True,
            "positive_reply": True,
        },
    )
    assert outcome.status_code == 200

    training = client.post(
        "/prospect-intelligence/models/train",
        json={"targets": ["reply"], "minimum_samples": 10, "artifact_dir": str(tmp_path / "models")},
    )
    assert training.status_code == 200
    assert training.json()["models"][0]["trained"] is False
    assert training.json()["models"][0]["sample_count"] == 1
