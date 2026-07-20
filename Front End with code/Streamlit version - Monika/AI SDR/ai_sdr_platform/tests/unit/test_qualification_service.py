from pathlib import Path

from ai_sdr_platform.src.agents.prospect_intelligence.service import (
    ProspectIntelligenceService,
)
from ai_sdr_platform.src.agents.prospect_intelligence.repository import (
    SQLAlchemyProspectIntelligenceRepository,
)
from ai_sdr_platform.src.agents.qualification.models import QualificationRequest
from ai_sdr_platform.src.agents.qualification.repository import (
    SQLAlchemyQualificationRepository,
)
from ai_sdr_platform.src.agents.qualification.service import QualificationService

from ai_sdr_platform.tests.unit.test_prospect_intelligence_service import _request


def test_qualification_combines_ml_probability_with_bant_and_meddic(
    tmp_path: Path,
) -> None:
    intelligence_service = ProspectIntelligenceService(
        repository=SQLAlchemyProspectIntelligenceRepository(
            db_url=f"sqlite:///{(tmp_path / 'intelligence.db').resolve()}"
        )
    )
    intelligence_request = _request()
    intelligence = intelligence_service.analyze(intelligence_request)
    repository = SQLAlchemyQualificationRepository(
        db_url=f"sqlite:///{(tmp_path / 'qualification.db').resolve()}"
    )
    service = QualificationService(repository=repository)

    result = service.qualify(
        QualificationRequest(
            intelligence=intelligence,
            contact=intelligence_request.contact,
            enrichment=intelligence_request.enrichment,
            created_by="test",
        )
    )

    assert result.bant is not None
    assert result.meddic is not None
    assert result.decision_source == "hybrid_ml_framework"
    assert result.ml_qualification_probability == (
        intelligence.propensity.qualification_probability.value
    )
    assert 0 <= result.qualification_score <= 100
    assert result.model_version == (
        intelligence.propensity.qualification_probability.model_version
    )
    assert service.get_latest("con_1").qualification_id == result.qualification_id
