from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResult
from ai_sdr_platform.src.agents.icp.models import ICPDefinition
from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredAccount, DiscoveredContact
from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectIntelligenceResult
from ai_sdr_platform.src.agents.outreach.models import OutreachCampaign


class SDRWorkflowState(BaseModel):
    request_id: str
    tenant_id: str = "default"
    initiated_by: str = "system"
    current_stage: str = "icp"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    icp_definition: Optional[ICPDefinition] = None
    discovered_accounts: list[DiscoveredAccount] = Field(default_factory=list)
    discovered_contacts: list[DiscoveredContact] = Field(default_factory=list)
    discovery_status: str = "idle"
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    enrichment_result: Optional[EnrichmentResult] = None
    prospect_intelligence_results: list[ProspectIntelligenceResult] = Field(default_factory=list)
    outreach_campaigns: list[OutreachCampaign] = Field(default_factory=list)


class ICPNodeResult(BaseModel):
    next_stage: str
    state: SDRWorkflowState


class EnrichmentNodeResult(BaseModel):
    next_stage: str
    state: SDRWorkflowState


class WorkflowNodeResult(BaseModel):
    next_stage: str
    state: SDRWorkflowState
