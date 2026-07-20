import json
from pathlib import Path

from fastapi.testclient import TestClient

from ai_sdr_platform.src.agents.enrichment.repository import SQLAlchemyEnrichmentRepository
from ai_sdr_platform.src.agents.enrichment.service import EnrichmentService
from ai_sdr_platform.src.api.app import create_app
from ai_sdr_platform.src.api.routes import routes_enrichment


class FakeSearchProvider:
    def search(self, **kwargs):
        return {
            "hits": [
                {
                    "title": "Example Account",
                    "url": "https://example.com",
                    "snippet": "Example provides workflow software for revenue teams.",
                    "score": 0.9,
                }
            ],
            "explanation": "Relevant account evidence.",
        }


class FakeLLMRouter:
    def complete(self, **kwargs):
        return json.dumps(
            {
                "company_summary": "Example provides workflow software for revenue teams.",
                "products_services": ["Workflow software"],
                "target_customers": ["Revenue teams"],
                "signals": [],
                "pain_point_hypotheses": ["Manual workflow coordination"],
                "personalization_angles": ["Reference revenue workflow automation"],
                "recommended_next_action": "Contact the revenue operations leader.",
                "confidence_score": 0.8,
            }
        )


def build_client(tmp_path: Path) -> TestClient:
    repo = SQLAlchemyEnrichmentRepository(db_url=f"sqlite:///{(tmp_path / 'enrichment_api.db').resolve()}")
    routes_enrichment._repository = repo
    routes_enrichment._service = EnrichmentService(
        repository=repo,
        search_provider=FakeSearchProvider(),
        llm_router=FakeLLMRouter(),
    )
    return TestClient(create_app())


def test_research_get_and_list_enrichment(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/enrichment/research",
        json={
            "account": {
                "account_id": "acc_api",
                "company_name": "Example Corp",
                "industry": "Software",
            },
            "contacts": [{"full_name": "Alex Lee", "title": "VP Revenue Operations"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["account_id"] == "acc_api"
    assert response.json()["confidence_score"] == 0.8

    fetched = client.get("/enrichment/acc_api")
    assert fetched.status_code == 200
    assert fetched.json()["company_name"] == "Example Corp"

    listed = client.get("/enrichment")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
