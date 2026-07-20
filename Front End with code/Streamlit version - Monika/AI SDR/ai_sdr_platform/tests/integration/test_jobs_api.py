from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_sdr_platform.src.api.app import create_app
from ai_sdr_platform.src.shared import config
from ai_sdr_platform.src.shared.jobs import JobStatus, JobStore


@pytest.fixture
def jobs_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(
        config,
        "settings",
        replace(config.settings, auth_enabled=False),
    )
    jobs_db = f"sqlite:///{(tmp_path / 'jobs_test.db').resolve()}"
    store = JobStore(db_url=jobs_db)
    import ai_sdr_platform.src.api.routes.routes_sdr_pipeline as pipeline_routes
    import ai_sdr_platform.src.shared.jobs as jobs_module

    monkeypatch.setattr(jobs_module, "job_store", store)
    monkeypatch.setattr(pipeline_routes, "job_store", store)

    def fake_execute(payload, *args, **kwargs):
        from ai_sdr_platform.src.agents.icp.models import (
            AccountCriteria,
            ICPDefinition,
            PersonaCriteria,
            ScoringWeights,
        )

        return pipeline_routes.SDRPipelineResponse(
            icp_definition=ICPDefinition(
                icp_name="Test ICP",
                account_criteria=AccountCriteria(industries=["software"]),
                persona_criteria=PersonaCriteria(titles=["RevOps"]),
                scoring_weights=ScoringWeights(
                    industry_fit=0.3,
                    company_size_fit=0.2,
                    persona_fit=0.25,
                    geo_fit=0.1,
                    pain_point_fit=0.15,
                ),
            ),
            summary={"accounts_discovered": 1},
        )

    monkeypatch.setattr(pipeline_routes, "_execute_pipeline", fake_execute)
    return TestClient(create_app())


def test_pipeline_async_job(jobs_client: TestClient) -> None:
    create = jobs_client.post(
        "/sdr/pipeline/run",
        json={
            "icp_payload": {
                "industries": ["SaaS"],
                "geographies": ["US"],
                "target_personas": ["RevOps"],
            }
        },
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]
    final = None
    for _ in range(30):
        status = jobs_client.get(f"/sdr/jobs/{job_id}")
        final = status.json()
        if final["status"] in {JobStatus.COMPLETED.value, JobStatus.FAILED.value}:
            break
        time.sleep(0.05)
    assert final is not None
    assert final["status"] == JobStatus.COMPLETED.value, final.get("error")
    assert final["result"]["summary"]["accounts_discovered"] == 1
