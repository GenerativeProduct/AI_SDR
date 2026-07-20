import pytest
from pydantic import ValidationError

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentAccount, EnrichmentResearchRequest


def test_enrichment_request_accepts_account_and_contacts() -> None:
    request = EnrichmentResearchRequest(
        account={
            "account_id": "acc_1",
            "company_name": "Johnson Fitness",
            "website": "https://example.com",
            "industry": "Fitness Equipment",
        },
        contacts=[{"full_name": "Sarah Miller", "title": "VP Sales"}],
    )
    assert request.account.company_name == "Johnson Fitness"
    assert request.contacts[0].title == "VP Sales"


def test_enrichment_account_rejects_empty_company_name() -> None:
    with pytest.raises(ValidationError):
        EnrichmentAccount(company_name=" ")
