from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ai_sdr_platform.src.agents.prospect_discovery.models import AccountDiscoveryResult, DiscoveryRequest
from ai_sdr_platform.src.agents.prospect_discovery.service import ProspectDiscoveryService
from ai_sdr_platform.src.workflows.sdr_state import SDRWorkflowState

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    StateGraph = None
    END = "END"


@dataclass
class ProspectDiscoveryNode:
    service: ProspectDiscoveryService

    def execute(self, state: SDRWorkflowState) -> SDRWorkflowState:
        if not state.icp_definition:
            state.warnings.append("No ICP definition found in state; skipping discovery")
            state.discovery_status = "failed"
            return state

        state.discovery_status = "in_progress"
        state.updated_at = datetime.now(timezone.utc)
        request = DiscoveryRequest(icp_definition=state.icp_definition, limit=state.metadata.get("discovery_limit", 10))
        result: AccountDiscoveryResult = self.service.discover_accounts(request)
        state.discovered_accounts = result.accounts
        contact_result = self.service.discover_contacts(
            account_ids=[account.account_id for account in result.accounts],
            target_titles=state.icp_definition.persona_criteria.titles,
            target_seniorities=state.icp_definition.persona_criteria.seniorities,
        )
        state.discovered_contacts = contact_result.contacts
        state.discovery_status = "completed"
        state.current_stage = "discovery_completed"
        state.updated_at = datetime.now(timezone.utc)
        state.metadata["discovered_accounts_count"] = result.total
        state.metadata["discovered_contacts_count"] = contact_result.total
        return state


def run_discovery_node(state: SDRWorkflowState, service: ProspectDiscoveryService) -> SDRWorkflowState:
    return ProspectDiscoveryNode(service=service).execute(state)


def build_discovery_state_graph(service: ProspectDiscoveryService):
    if StateGraph is None:
        return None
    graph = StateGraph(SDRWorkflowState)
    graph.add_node("discovery_agent", lambda state: ProspectDiscoveryNode(service=service).execute(state))
    graph.set_entry_point("discovery_agent")
    graph.add_edge("discovery_agent", END)
    return graph.compile()
