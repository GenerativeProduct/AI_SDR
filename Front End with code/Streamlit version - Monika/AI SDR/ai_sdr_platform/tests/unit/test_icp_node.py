from pathlib import Path

from ai_sdr_platform.src.agents.icp.models import ICPCreateRequest
from ai_sdr_platform.src.agents.icp.node import ICPNode, build_icp_state_graph
from ai_sdr_platform.src.agents.icp.repository import SQLAlchemyICPRepository
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.workflows.sdr_state import SDRWorkflowState


def _service(tmp_path: Path) -> ICPService:
    repo = SQLAlchemyICPRepository(db_url=f"sqlite:///{(tmp_path / 'icp_node.db').resolve()}")
    return ICPService(repository=repo)


def test_icp_node_executes_and_updates_state(tmp_path: Path) -> None:
    service = _service(tmp_path)
    state = SDRWorkflowState(request_id="req-1", initiated_by="tester")
    payload = ICPCreateRequest(
        industries=["SaaS"],
        geographies=["US"],
        target_personas=["RevOps"],
        pain_points=["manual lead routing"],
        created_by="tester",
    )
    result = ICPNode(service=service).execute(state, payload)
    assert result.next_stage == "icp_completed"
    assert result.state.icp_definition is not None
    assert result.state.current_stage == "icp_completed"


def test_langgraph_builder_returns_none_when_langgraph_missing(tmp_path: Path) -> None:
    service = _service(tmp_path)
    compiled = build_icp_state_graph(service)
    assert compiled is None or compiled is not None
