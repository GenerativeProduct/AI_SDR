from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResearchRequest
from ai_sdr_platform.src.agents.enrichment.service import EnrichmentService
from ai_sdr_platform.src.workflows.sdr_state import EnrichmentNodeResult, SDRWorkflowState

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    StateGraph = None
    END = "END"


@dataclass
class EnrichmentNode:
    service: EnrichmentService

    def execute(self, state: SDRWorkflowState, payload: EnrichmentResearchRequest) -> EnrichmentNodeResult:
        result = self.service.research(payload)
        state.enrichment_result = result
        state.current_stage = "enrichment_completed"
        state.updated_at = datetime.now(timezone.utc)
        state.metadata["enrichment_id"] = result.enrichment_id
        state.metadata["enriched_account_id"] = result.account_id
        return EnrichmentNodeResult(next_stage="lead_scoring", state=state)


def run_enrichment_node(
    state: SDRWorkflowState,
    payload: EnrichmentResearchRequest,
    service: EnrichmentService,
) -> SDRWorkflowState:
    return EnrichmentNode(service=service).execute(state, payload).state


def build_enrichment_state_graph(service: EnrichmentService):
    if StateGraph is None:
        return None

    graph = StateGraph(SDRWorkflowState)

    def _runner(state: SDRWorkflowState) -> SDRWorkflowState:
        payload_data: dict[str, Any] = state.metadata.get("enrichment_payload", {})
        payload = EnrichmentResearchRequest.model_validate(payload_data)
        return EnrichmentNode(service=service).execute(state, payload).state

    graph.add_node("enrichment_agent", _runner)
    graph.set_entry_point("enrichment_agent")
    graph.add_edge("enrichment_agent", END)
    return graph.compile()
