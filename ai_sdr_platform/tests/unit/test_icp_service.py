from pathlib import Path

from ai_sdr_platform.src.agents.icp.models import ICPCreateRequest, ICPSuggestionRequest, ICPUpdateRequest
from ai_sdr_platform.src.agents.icp.repository import SQLAlchemyICPRepository
from ai_sdr_platform.src.agents.icp.service import ICPService
from ai_sdr_platform.src.shared.exceptions import ICPValidationError


def _service(tmp_path: Path) -> ICPService:
    repo = SQLAlchemyICPRepository(db_url=f"sqlite:///{(tmp_path / 'icp_test.db').resolve()}")
    return ICPService(repository=repo)


def test_icp_service_normalizes_and_expands_persona_aliases(tmp_path: Path) -> None:
    service = _service(tmp_path)
    result = service.create_icp(
        ICPCreateRequest(
            industries=["SaaS"],
            geographies=["United States"],
            employee_band="mid-market",
            target_personas=["RevOps"],
            pain_points=["forecasting inconsistency"],
            created_by="tester",
        )
    )
    definition = result.normalized_definition
    assert definition.account_criteria.industries == ["software"]
    assert definition.account_criteria.geographies == ["US"]
    assert definition.account_criteria.employee_range.min == 200
    assert "VP Revenue Operations" in definition.persona_criteria.titles


def test_icp_service_requires_some_target_signal(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        service.create_icp(ICPCreateRequest())
        assert False, "expected validation error"
    except ICPValidationError as exc:
        assert "at least one account-level or persona-level targeting signal" in str(exc)


def test_icp_update_creates_new_version(tmp_path: Path) -> None:
    service = _service(tmp_path)
    created = service.create_icp(
        ICPCreateRequest(
            industries=["SaaS"],
            geographies=["US"],
            target_personas=["RevOps"],
            pain_points=["manual lead routing"],
            created_by="owner-1",
        )
    ).normalized_definition
    updated = service.update_icp(
        created.icp_id,
        ICPUpdateRequest(
            pain_points=["manual lead routing", "forecasting inconsistency"],
            updated_by="owner-2",
            change_reason="Expanded for forecasting use case",
        ),
    ).normalized_definition
    assert updated.version == 2
    assert updated.audit.updated_by == "owner-2"
    assert updated.audit.change_reason == "Expanded for forecasting use case"
    versions = service.list_versions(created.icp_id)
    assert len(versions) == 2


def test_deterministic_suggestion_fallback(tmp_path: Path) -> None:
    service = _service(tmp_path)
    suggestion = service.suggest(
        ICPSuggestionRequest(
            industries=["SaaS"],
            target_personas=["RevOps"],
            offer_summary="Pipeline analytics for revenue teams",
            notes="Forecast visibility is weak",
        )
    )
    assert suggestion.source == "deterministic"
    assert "VP Revenue Operations" in suggestion.personas
    assert "poor pipeline visibility" in suggestion.pain_points


def test_repository_prefers_env_config_for_database_url() -> None:
    from ai_sdr_platform.src.shared.config import settings

    assert hasattr(settings, "icp_database_url")
