import json
from pathlib import Path

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResearchRequest
from ai_sdr_platform.src.agents.enrichment.repository import SQLAlchemyEnrichmentRepository
from ai_sdr_platform.src.agents.enrichment.service import EnrichmentService


class FakeSearchProvider:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, **kwargs):
        self.queries.append(kwargs["query"])
        return {
            "hits": [
                {
                    "title": "Johnson Fitness Home Equipment",
                    "url": "https://example.com/products",
                    "snippet": "Treadmills, home gyms, financing, and commercial fitness products.",
                    "score": 0.91,
                }
            ],
            "explanation": "The company focuses on home and commercial fitness equipment.",
            "provider": "searxng",
            "indexed_count": 1,
        }


class FakeLLMRouter:
    def complete(self, **kwargs):
        return json.dumps(
            {
                "company_summary": "Johnson Fitness sells home and commercial fitness equipment.",
                "products_services": ["Treadmills", "Home gyms", "Financing"],
                "target_customers": ["Homeowners", "Commercial gyms"],
                "signals": [
                    {
                        "type": "product",
                        "detail": "Financing is part of the buyer journey.",
                        "confidence": 0.82,
                        "source_url": "https://example.com/products",
                    }
                ],
                "pain_point_hypotheses": ["Quote follow-up friction"],
                "personalization_angles": ["Reference financing and home-gym demand"],
                "recommended_next_action": "Prioritize VP Sales for outreach.",
                "confidence_score": 0.84,
            }
        )


def build_service(tmp_path: Path) -> tuple[EnrichmentService, FakeSearchProvider]:
    repo = SQLAlchemyEnrichmentRepository(db_url=f"sqlite:///{(tmp_path / 'enrichment.db').resolve()}")
    search = FakeSearchProvider()
    return EnrichmentService(repository=repo, search_provider=search, llm_router=FakeLLMRouter()), search


def test_research_builds_queries_synthesizes_and_persists(tmp_path: Path) -> None:
    service, search = build_service(tmp_path)
    result = service.research(
        EnrichmentResearchRequest(
            account={
                "account_id": "acc_123",
                "company_name": "Johnson Fitness",
                "industry": "Fitness Equipment",
                "location": "US",
            },
            contacts=[{"full_name": "Sarah Miller", "title": "VP Sales"}],
            search_provider="searxng",
        )
    )

    assert search.queries
    assert result.account_id == "acc_123"
    assert result.company_summary.startswith("Johnson Fitness")
    assert result.products_services == ["Treadmills", "Home gyms", "Financing"]
    assert result.citations[0].url == "https://example.com/products"
    assert result.signals[0].confidence == 0.82
    assert service.get_latest("acc_123").enrichment_id == result.enrichment_id


def test_research_has_deterministic_fallback_without_llm(tmp_path: Path) -> None:
    repo = SQLAlchemyEnrichmentRepository(db_url=f"sqlite:///{(tmp_path / 'fallback.db').resolve()}")
    service = EnrichmentService(repository=repo)
    result = service.research(
        EnrichmentResearchRequest(
            account={"company_name": "Fallback Fitness", "industry": "Fitness"},
        )
    )
    assert result.status == "limited_evidence"
    assert "lead follow-up friction" in result.pain_point_hypotheses
    assert result.confidence_score == 0.35
