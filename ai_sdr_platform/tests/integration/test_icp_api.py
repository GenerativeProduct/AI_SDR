from pathlib import Path

from fastapi.testclient import TestClient

from ai_sdr_platform.src.agents.icp.models import ICPSuggestionResponse
from ai_sdr_platform.src.agents.icp.repository import SQLAlchemyICPRepository
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.api.app import create_app
from ai_sdr_platform.src.api.routes import routes_icp


class StubSuggestionProvider:
    def suggest(self, request):
        return ICPSuggestionResponse(
            personas=["Director of Revenue Operations"],
            pain_points=["forecasting inconsistency"],
            exclusions={"industries": [], "customer_statuses": ["existing_customer"], "company_names": [], "employee_max_below": None, "geographies": []},
            reasoning="stubbed",
            source="llm",
        )


def build_client(tmp_path: Path) -> TestClient:
    repo = SQLAlchemyICPRepository(db_url=f"sqlite:///{(tmp_path / 'icp_api.db').resolve()}")
    routes_icp._repository = repo
    routes_icp._service = ICPService(repository=repo, suggestion_provider=StubSuggestionProvider())
    return TestClient(create_app())


def test_create_icp_endpoint(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/icp",
        json={
            "industries": ["SaaS"],
            "geographies": ["US"],
            "target_personas": ["RevOps"],
            "pain_points": ["manual lead routing"],
            "created_by": "integration-test",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["normalized_definition"]["account_criteria"]["industries"] == ["software"]
    assert body["normalized_definition"]["audit"]["created_by"] == "integration-test"


def test_validate_icp_endpoint_rejects_empty_payload(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post("/icp/validate", json={})
    assert response.status_code == 400


def test_suggest_icp_endpoint(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/icp/suggest",
        json={"industries": ["SaaS"], "target_personas": ["RevOps"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "llm"
    assert body["personas"] == ["Director of Revenue Operations"]


def test_create_icp_from_structured_filters(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/icp",
        json={
            "filters": {
                "target_industries": ["SaaS"],
                "revenue_ranges": ["$10M-$50M"],
                "company_size_ranges": ["200-1000"],
                "funding_stages": ["Series B"],
                "geographies": ["US"],
                "tech_stack_signals": ["Salesforce"],
                "target_job_titles": ["VP Sales"],
                "seniority_levels": ["VP"],
                "pain_points": ["low outbound reply rate"],
                "buying_signals": ["sales hiring"],
            },
            "created_by": "filter-test",
        },
    )

    assert response.status_code == 200
    definition = response.json()["normalized_definition"]
    assert definition["account_criteria"]["industries"] == ["software"]
    assert definition["account_criteria"]["funding_stages"] == ["Series B"]
    assert definition["account_criteria"]["tech_stack_signals"] == ["Salesforce"]
    assert definition["persona_criteria"]["seniority_levels"] == ["VP"]
    assert definition["persona_criteria"]["buying_signals"] == ["sales hiring"]
    assert definition["pain_points"] == ["low outbound reply rate"]
    assert definition["audit_metadata"]["has_structured_filters"] is True


def test_suggest_icp_accepts_filters_without_legacy_fields(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/icp/suggest",
        json={
            "filters": {
                "target_industries": ["FinTech"],
                "geographies": ["Europe"],
                "target_job_titles": ["CRO"],
                "pain_points": ["manual qualification"],
            }
        },
    )
    assert response.status_code == 200
    assert response.json()["source"] == "llm"


def test_update_icp_endpoint_creates_new_version(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    created = client.post(
        "/icp",
        json={
            "industries": ["SaaS"],
            "geographies": ["US"],
            "target_personas": ["RevOps"],
            "pain_points": ["manual lead routing"],
            "created_by": "integration-test",
        },
    ).json()["normalized_definition"]
    icp_id = created["icp_id"]
    response = client.put(
        f"/icp/{icp_id}",
        json={
            "pain_points": ["manual lead routing", "forecasting inconsistency"],
            "updated_by": "integration-updater",
            "change_reason": "expanded scope",
        },
    )
    assert response.status_code == 200
    body = response.json()["normalized_definition"]
    assert body["version"] == 2
