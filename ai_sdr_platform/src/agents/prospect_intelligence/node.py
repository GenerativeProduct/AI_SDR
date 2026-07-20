from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectIntelligenceRequest
from ai_sdr_platform.src.agents.prospect_intelligence.service import ProspectIntelligenceService
from ai_sdr_platform.src.workflows.sdr_state import SDRWorkflowState


@dataclass
class ProspectIntelligenceNode:
    service: ProspectIntelligenceService

    def execute(self, state: SDRWorkflowState) -> SDRWorkflowState:
        if not state.enrichment_result or not state.discovered_accounts:
            state.warnings.append("Enrichment output is required before prospect intelligence")
            return state
        account_id = state.enrichment_result.account_id
        account = next(
            (item for item in state.discovered_accounts if item.account_id == account_id),
            None,
        )
        contacts = [item for item in state.discovered_contacts if item.account_id == account_id]
        if not account or not contacts:
            state.warnings.append("No account/contact handoff was available for prospect intelligence")
            return state

        state.prospect_intelligence_results = [
            self.service.analyze(
                ProspectIntelligenceRequest(
                    account=account,
                    contact=contact,
                    enrichment=state.enrichment_result,
                    icp_definition=state.icp_definition,
                    llm_provider=str(state.metadata.get("llm_provider", "ollama_local")),
                    llm_model=str(state.metadata.get("llm_model", "llama3.2:3b")),
                    created_by=state.initiated_by,
                )
            )
            for contact in contacts
        ]
        state.current_stage = "prospect_intelligence_completed"
        state.updated_at = datetime.now(timezone.utc)
        return state
