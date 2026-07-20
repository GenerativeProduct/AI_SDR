from __future__ import annotations

from typing import Any

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResearchRequest
from ai_sdr_platform.src.agents.enrichment.node import EnrichmentNode
from ai_sdr_platform.src.agents.enrichment.service import EnrichmentService
from ai_sdr_platform.src.agents.icp.models import ICPCreateRequest
from ai_sdr_platform.src.agents.icp.node import ICPNode
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.agents.prospect_discovery.node import ProspectDiscoveryNode
from ai_sdr_platform.src.agents.prospect_discovery.service import ProspectDiscoveryService
from ai_sdr_platform.src.agents.prospect_intelligence.node import ProspectIntelligenceNode
from ai_sdr_platform.src.agents.prospect_intelligence.service import ProspectIntelligenceService
from ai_sdr_platform.src.agents.outreach.node import OutreachNode
from ai_sdr_platform.src.agents.outreach.service import OutreachService
from ai_sdr_platform.src.workflows.sdr_state import SDRWorkflowState

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    StateGraph = None
    END = "END"


def build_sdr_workflow(
    icp_service: ICPService,
    discovery_service: ProspectDiscoveryService,
    enrichment_service: EnrichmentService,
    intelligence_service: ProspectIntelligenceService | None = None,
    outreach_service: OutreachService | None = None,
):
    if StateGraph is None:
        return None

    workflow = StateGraph(SDRWorkflowState)

    def icp_node_runner(state: SDRWorkflowState) -> SDRWorkflowState:
        payload_data: dict[str, Any] = state.metadata.get("icp_payload", {})
        payload = ICPCreateRequest.model_validate(payload_data)
        return ICPNode(service=icp_service).execute(state, payload).state

    def discovery_node_runner(state: SDRWorkflowState) -> SDRWorkflowState:
        return ProspectDiscoveryNode(service=discovery_service).execute(state)

    def enrichment_node_runner(state: SDRWorkflowState) -> SDRWorkflowState:
        if not state.discovered_accounts:
            state.warnings.append("No discovered accounts available for enrichment")
            return state
        top_account = state.discovered_accounts[0]
        contacts = [contact for contact in state.discovered_contacts if contact.account_id == top_account.account_id]
        payload = EnrichmentResearchRequest(
            account=top_account.model_dump(),
            contacts=[contact.model_dump() for contact in contacts],
            icp_context=state.icp_definition.model_dump(mode="json") if state.icp_definition else {},
            collection=str(state.metadata.get("enrichment_collection", "")) or None,
            search_provider=str(state.metadata.get("search_provider", "")) or None,
            top_k=int(state.metadata.get("enrichment_top_k", 8)),
            auto_fetch_and_index=bool(state.metadata.get("auto_fetch_and_index", True)),
            llm_provider=str(state.metadata.get("llm_provider", "ollama_local")),
            llm_model=str(state.metadata.get("llm_model", "llama3.2:3b")),
            created_by=str(state.initiated_by),
        )
        return EnrichmentNode(service=enrichment_service).execute(state, payload).state

    workflow.add_node("icp_agent", icp_node_runner)
    workflow.add_node("discovery_agent", discovery_node_runner)
    workflow.add_node("enrichment_agent", enrichment_node_runner)
    if intelligence_service is not None:
        workflow.add_node(
            "prospect_intelligence_agent",
            lambda state: ProspectIntelligenceNode(service=intelligence_service).execute(state),
        )
    if intelligence_service is not None and outreach_service is not None:
        workflow.add_node(
            "outreach_agent",
            lambda state: OutreachNode(service=outreach_service).execute(state),
        )
    workflow.set_entry_point("icp_agent")
    workflow.add_edge("icp_agent", "discovery_agent")
    workflow.add_edge("discovery_agent", "enrichment_agent")
    if intelligence_service is not None:
        workflow.add_edge("enrichment_agent", "prospect_intelligence_agent")
        if outreach_service is not None:
            workflow.add_edge("prospect_intelligence_agent", "outreach_agent")
            workflow.add_edge("outreach_agent", END)
        else:
            workflow.add_edge("prospect_intelligence_agent", END)
    else:
        workflow.add_edge("enrichment_agent", END)
    return workflow.compile()
