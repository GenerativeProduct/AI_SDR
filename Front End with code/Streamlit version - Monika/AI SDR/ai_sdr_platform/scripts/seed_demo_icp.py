#!/usr/bin/env python3
"""Seed a demo ICP for local development."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_sdr_platform.src.agents.icp.models import ICPCreateRequest
from ai_sdr_platform.src.agents.icp.repository import SQLAlchemyICPRepository
from ai_sdr_platform.src.agents.icp.service import ICPService


def main() -> None:
    repo = SQLAlchemyICPRepository()
    service = ICPService(repository=repo)
    result = service.create_icp(
        ICPCreateRequest(
            icp_name="Demo Mid-Market SaaS",
            industries=["SaaS", "software"],
            geographies=["US", "Europe"],
            target_personas=["Director of Revenue Operations", "VP Sales"],
            pain_points=["low outbound reply rate", "pipeline visibility"],
            employee_band="mid-market",
            revenue_band="mid-market",
            created_by="seed-script",
        )
    )
    icp = result.normalized_definition
    print(f"Seeded ICP {icp.icp_id} v{icp.version}: {icp.icp_name}")


if __name__ == "__main__":
    main()
