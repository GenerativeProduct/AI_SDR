from pathlib import Path

from fastapi.testclient import TestClient

from ai_sdr_platform.src.agents.icp.models import ICPCreateRequest
from ai_sdr_platform.src.agents.icp.repository import SQLAlchemyICPRepository
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.agents.prospect_discovery.repository import SQLAlchemyProspectDiscoveryRepository
from ai_sdr_platform.src.agents.prospect_discovery.service import ProspectDiscoveryService
from ai_sdr_platform.src.api.app import create_app
from ai_sdr_platform.src.api.routes import routes_icp, routes_prospect_discovery


def build_client(tmp_path: Path) -> TestClient:
    icp_repo = SQLAlchemyICPRepository(db_url=f"sqlite:///{(tmp_path / 'icp.db').resolve()}")
    discovery_repo = SQLAlchemyProspectDiscoveryRepository(db_url=f"sqlite:///{(tmp_path / 'discovery.db').resolve()}")
    routes_icp._repository = icp_repo
    routes_icp._service = ICPService(repository=icp_repo)
    app = create_app()
    routes_prospect_discovery._repository = discovery_repo
    routes_prospect_discovery._service = ProspectDiscoveryService(repository=discovery_repo)
    return TestClient(app)


def _icp_payload() -> dict:
    icp = ICPService(repository=SQLAlchemyICPRepository(db_url="sqlite:///:memory:")).validate_only(
        ICPCreateRequest(
            industries=["SaaS"],
            geographies=["Europe"],
            target_personas=["RevOps"],
            pain_points=["pipeline visibility"],
            created_by="test",
        )
    ).normalized_definition
    return icp.model_dump(mode="json")


def test_run_prospect_discovery_and_list_results(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post("/prospect-discovery/run", json={"icp_definition": _icp_payload(), "limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["account_total"] >= 1
    assert body["contact_total"] >= 1

    listed_accounts = client.get("/prospect-discovery/accounts")
    assert listed_accounts.status_code == 200
    assert len(listed_accounts.json()) >= 1

    account_id = body["accounts"][0]["account_id"]
    listed_contacts = client.get("/prospect-discovery/contacts", params={"account_id": account_id})
    assert listed_contacts.status_code == 200
    assert all(item["account_id"] == account_id for item in listed_contacts.json())
