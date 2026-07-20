from pathlib import Path

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResearchRequest
from ai_sdr_platform.src.agents.enrichment.node import EnrichmentNode
from ai_sdr_platform.src.agents.enrichment.repository import SQLAlchemyEnrichmentRepository
from ai_sdr_platform.src.agents.enrichment.service import EnrichmentService
from ai_sdr_platform.src.workflows.sdr_state import SDRWorkflowState


def test_enrichment_node_updates_sdr_state(tmp_path: Path) -> None:
    repo = SQLAlchemyEnrichmentRepository(db_url=f"sqlite:///{(tmp_path / 'node.db').resolve()}")
    node = EnrichmentNode(service=EnrichmentService(repository=repo))
    state = SDRWorkflowState(request_id="req_1", current_stage="enrichment")
    result = node.execute(
        state,
        EnrichmentResearchRequest(account={"account_id": "acc_1", "company_name": "Example Corp"}),
    )
    assert result.next_stage == "lead_scoring"
    assert result.state.current_stage == "enrichment_completed"
    assert result.state.enrichment_result.account_id == "acc_1"
