from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ai_sdr_platform.src.agents.outreach.models import OutreachCampaignRequest
from ai_sdr_platform.src.agents.outreach.service import OutreachService
from ai_sdr_platform.src.workflows.sdr_state import SDRWorkflowState


@dataclass
class OutreachNode:
    service: OutreachService

    def execute(self, state: SDRWorkflowState) -> SDRWorkflowState:
        contacts = {item.contact_id: item for item in state.discovered_contacts}
        campaigns = []
        for intelligence in state.prospect_intelligence_results:
            contact = contacts.get(intelligence.contact_id)
            if contact is None:
                state.warnings.append(
                    f"Outreach skipped for {intelligence.contact_name}: contact handoff is missing."
                )
                continue
            try:
                campaigns.append(
                    self.service.create_campaign(
                        OutreachCampaignRequest(
                            intelligence=intelligence,
                            contact=contact,
                            require_approval=True,
                            created_by=state.initiated_by,
                        )
                    )
                )
            except ValueError as exc:
                state.warnings.append(
                    f"Outreach skipped for {intelligence.contact_name}: {exc}"
                )
        state.outreach_campaigns = campaigns
        state.current_stage = "outreach_drafts_completed"
        state.updated_at = datetime.now(timezone.utc)
        return state
