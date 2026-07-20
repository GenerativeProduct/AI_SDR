import pytest
from pydantic import ValidationError

from ai_sdr_platform.src.agents.icp.models import RangeInt, ScoringWeights


def test_range_rejects_min_greater_than_max() -> None:
    with pytest.raises(ValidationError):
        RangeInt(min=100, max=10)


def test_scoring_weights_must_sum_to_one() -> None:
    with pytest.raises(ValidationError):
        ScoringWeights(
            industry_fit=0.3,
            company_size_fit=0.2,
            persona_fit=0.2,
            geo_fit=0.1,
            pain_point_fit=0.1,
        )
