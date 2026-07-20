from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ai_sdr_platform.src.agents.icp.models import ICPCreateRequest, ICPValidationResult
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.workflows.sdr_state import ICPNodeResult, SDRWorkflowState

try:
    from langgraph.graph import StateGraph, END
except Exception:  # pragma: no cover
    StateGraph = None
    END = "END"


@dataclass
class ICPNode:
    service: ICPService

    def execute(self, state: SDRWorkflowState, payload: ICPCreateRequest) -> ICPNodeResult:
        result: ICPValidationResult = self.service.create_icp(payload)
        state.icp_definition = result.normalized_definition
        state.warnings = result.warnings
        state.current_stage = "icp_completed"
        state.updated_at = datetime.now(timezone.utc)
        state.metadata["icp_version"] = result.normalized_definition.version
        state.metadata["icp_id"] = result.normalized_definition.icp_id
        return ICPNodeResult(next_stage="icp_completed", state=state)


def run_icp_node(state: SDRWorkflowState, payload: ICPCreateRequest, service: ICPService) -> SDRWorkflowState:
    return ICPNode(service=service).execute(state, payload).state


def build_icp_state_graph(service: ICPService):
    if StateGraph is None:
        return None

    graph = StateGraph(SDRWorkflowState)

    def _runner(state: SDRWorkflowState) -> SDRWorkflowState:
        payload_data: dict[str, Any] = state.metadata.get("icp_payload", {})
        payload = ICPCreateRequest.model_validate(payload_data)
        return ICPNode(service=service).execute(state, payload).state

    graph.add_node("icp_agent", _runner)
    graph.set_entry_point("icp_agent")
    graph.add_edge("icp_agent", END)
    return graph.compile()
