from unittest.mock import Mock, patch

from ai_sdr_platform.src.agents.icp.models import (
    AccountCriteria,
    ICPDefinition,
    PersonaCriteria,
    ScoringWeights,
)
from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredAccount
from ai_sdr_platform.src.agents.prospect_discovery.providers import (
    CompaniesHouseAccountProvider,
    GLEIFAccountProvider,
    OpenCorporatesAccountProvider,
    SECAccountProvider,
    WebSearchAccountProvider,
    WebSearchContactProvider,
)


def icp_definition() -> ICPDefinition:
    return ICPDefinition(
        icp_name="Software ICP",
        account_criteria=AccountCriteria(
            industries=["software"],
            geographies=["United States"],
        ),
        persona_criteria=PersonaCriteria(titles=["VP Sales"]),
        scoring_weights=ScoringWeights(
            industry_fit=0.30,
            company_size_fit=0.20,
            persona_fit=0.25,
            geo_fit=0.10,
            pain_point_fit=0.15,
        ),
    )


@patch("ai_sdr_platform.src.agents.prospect_discovery.providers.requests.get")
def test_gleif_provider_maps_real_legal_entity(mock_get: Mock) -> None:
    response = Mock()
    response.json.return_value = {
        "data": [
            {
                "id": "LEI123",
                "attributes": {
                    "entity": {
                        "legalName": {"name": "Example Software Incorporated"},
                        "legalAddress": {"country": "US"},
                        "legalForm": {"other": "Corporation"},
                    }
                },
            }
        ]
    }
    response.raise_for_status.return_value = None
    mock_get.return_value = response

    accounts = GLEIFAccountProvider().search_accounts(icp_definition(), 5)

    assert len(accounts) == 1
    assert accounts[0].company_name == "Example Software Incorporated"
    assert accounts[0].source == "gleif"
    assert accounts[0].location == "US"


@patch("ai_sdr_platform.src.agents.prospect_discovery.providers.requests.get")
def test_sec_provider_maps_registrant_and_uses_user_agent(mock_get: Mock) -> None:
    tickers = Mock()
    tickers.json.return_value = {
        "0": {
            "cik_str": 1234,
            "ticker": "EXM",
            "title": "Example Software Corp",
        }
    }
    tickers.raise_for_status.return_value = None
    submission = Mock()
    submission.json.return_value = {
        "name": "Example Software Corp",
        "sicDescription": "Prepackaged Software",
        "website": "https://example.com",
        "addresses": {
            "business": {
                "stateOrCountryDescription": "California",
                "country": "US",
            }
        },
    }
    submission.raise_for_status.return_value = None
    mock_get.side_effect = [tickers, submission]

    accounts = SECAccountProvider(
        user_agent="AI SDR contact@example.com"
    ).search_accounts(icp_definition(), 5)

    assert len(accounts) == 1
    assert accounts[0].source == "sec_edgar"
    assert accounts[0].industry == "Prepackaged Software"
    assert mock_get.call_args_list[0].kwargs["headers"]["User-Agent"] == (
        "AI SDR contact@example.com"
    )


@patch("ai_sdr_platform.src.agents.prospect_discovery.providers.requests.get")
def test_opencorporates_provider_maps_company(mock_get: Mock) -> None:
    response = Mock()
    response.json.return_value = {
        "results": {
            "companies": [
                {
                    "company": {
                        "name": "Washington SaaS Inc",
                        "company_number": "123",
                        "jurisdiction_code": "us_wa",
                        "company_type": "Corporation",
                        "opencorporates_url": "https://opencorporates.com/companies/us_wa/123",
                    }
                }
            ]
        }
    }
    response.raise_for_status.return_value = None
    mock_get.return_value = response

    accounts = OpenCorporatesAccountProvider().search_accounts(icp_definition(), 5)

    assert len(accounts) == 1
    assert accounts[0].source == "opencorporates"
    assert accounts[0].location == "US_WA"


@patch("ai_sdr_platform.src.agents.prospect_discovery.providers.requests.get")
def test_companies_house_provider_maps_company(mock_get: Mock) -> None:
    response = Mock()
    response.json.return_value = {
        "items": [
            {
                "title": "Example Software Ltd",
                "company_number": "01234567",
                "company_type": "ltd",
                "address": {"locality": "London", "country": "United Kingdom"},
            }
        ]
    }
    response.raise_for_status.return_value = None
    mock_get.return_value = response

    accounts = CompaniesHouseAccountProvider(
        api_key="test-key"
    ).search_accounts(icp_definition(), 5)

    assert len(accounts) == 1
    assert accounts[0].source == "companies_house"
    assert accounts[0].location == "London, United Kingdom"


def test_web_search_provider_maps_live_hits() -> None:
    opensearch_web = Mock()
    opensearch_web.search.return_value = {
        "hits": [
            {
                "title": "Example Cloud Software - LinkedIn",
                "url": "https://www.linkedin.com/company/example-cloud-software",
                "domain": "linkedin.com",
                "snippet": "B2B cloud software company in Washington.",
            }
        ]
    }

    accounts = WebSearchAccountProvider(opensearch_web).search_accounts(
        icp_definition(), 5
    )

    assert len(accounts) == 1
    assert accounts[0].source == "web_search"
    assert accounts[0].company_name == "Example Cloud Software"


def test_web_search_provider_rejects_listicle_hits() -> None:
    opensearch_web = Mock()
    opensearch_web.search.return_value = {
        "hits": [
            {
                "title": "Companies that use Crunchbase in United States (287)",
                "url": "https://example.com/companies-that-use-crunchbase",
                "domain": "example.com",
                "snippet": "A list of companies.",
            },
            {
                "title": "Crunchbase raises $30M more | TechCrunch",
                "url": "https://techcrunch.com/story",
                "domain": "techcrunch.com",
                "snippet": "News article.",
            },
        ]
    }

    accounts = WebSearchAccountProvider(opensearch_web).search_accounts(
        icp_definition(), 5
    )

    assert accounts == []


def test_web_search_contact_provider_extracts_public_persona() -> None:
    opensearch_web = Mock()
    opensearch_web.search.return_value = {
        "hits": [
            {
                "title": "Jordan Lee - VP Sales - Example Cloud Software | LinkedIn",
                "url": "https://www.linkedin.com/in/jordan-lee",
                "domain": "linkedin.com",
                "snippet": "Jordan Lee is VP Sales at Example Cloud Software.",
            }
        ]
    }
    account = WebSearchAccountProvider(opensearch_web).search_accounts(
        icp_definition(), 1
    )
    if not account:
        from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredAccount

        account = [
            DiscoveredAccount(
                account_id="acc_test",
                icp_id=icp_definition().icp_id,
                company_name="Example Cloud Software",
                industry="software",
                location="United States",
                employee_count=0,
                source="test",
            )
        ]

    contacts = WebSearchContactProvider(opensearch_web).search_contacts(
        account, ["VP Sales"], ["VP"]
    )

    assert len(contacts) == 1
    assert contacts[0].full_name == "Jordan Lee"
    assert contacts[0].source == "web_search_public"
    assert contacts[0].email_verification_status == "missing_public_email"


def test_synthetic_contact_provider_generates_persona_per_account() -> None:
    from ai_sdr_platform.src.agents.prospect_discovery.providers import (
        SyntheticContactProvider,
    )

    accounts = [
        DiscoveredAccount(
            account_id="acc_syn",
            icp_id="icp_1",
            company_name="Example Software Inc",
            website="https://example.com",
            industry="Software",
            location="US",
            employee_count=500,
            source="gleif",
        )
    ]
    contacts = SyntheticContactProvider().search_contacts(
        accounts, ["VP Sales", "Director of Revenue Operations"], []
    )

    assert len(contacts) == 2
    assert contacts[0].source == "synthetic_persona"
    assert contacts[0].email.endswith("@example.com")
    assert contacts[0].email_verification_status == "synthetic_unverified"
