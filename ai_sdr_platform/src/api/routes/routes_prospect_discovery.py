from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ai_sdr_platform.src.agents.prospect_discovery.models import (
    AccountDiscoveryResult,
    ContactDiscoveryRequest,
    ContactDiscoveryResult,
    DiscoveryRequest,
    ProspectDiscoveryRunResult,
)
from ai_sdr_platform.src.agents.prospect_discovery.repository import SQLAlchemyProspectDiscoveryRepository
from ai_sdr_platform.src.agents.prospect_discovery.service import ProspectDiscoveryService
from ai_sdr_platform.src.agents.prospect_discovery.providers import (
    CompaniesHouseAccountProvider,
    CompositeAccountProvider,
    GLEIFAccountProvider,
    NoPublicContactProvider,
    OpenCorporatesAccountProvider,
    SECAccountProvider,
    SyntheticContactProvider,
    WebSearchAccountProvider,
    WebSearchContactProvider,
)
from ai_sdr_platform.src.shared.config import settings

router = APIRouter(prefix="/prospect-discovery", tags=["prospect-discovery"])
_repository = SQLAlchemyProspectDiscoveryRepository()
_service = ProspectDiscoveryService(repository=_repository)


def configure_prospect_discovery_service(
    opensearch_web: object | None = None,
) -> ProspectDiscoveryService:
    global _service
    if settings.discovery_provider == "mock":
        _service = ProspectDiscoveryService(repository=_repository)
        return _service
    account_providers = []
    if settings.discovery_enable_web_search and opensearch_web is not None:
        account_providers.append(
            WebSearchAccountProvider(
                opensearch_web=opensearch_web,
                timeout_seconds=settings.discovery_timeout_seconds,
            )
        )
    account_providers.append(
        GLEIFAccountProvider(timeout_seconds=settings.discovery_timeout_seconds)
    )
    if settings.discovery_sec_user_agent:
        account_providers.append(
            SECAccountProvider(
                user_agent=settings.discovery_sec_user_agent,
                timeout_seconds=settings.discovery_timeout_seconds,
            )
        )
    account_providers.append(
        OpenCorporatesAccountProvider(
            api_token=settings.discovery_opencorporates_api_token,
            timeout_seconds=settings.discovery_timeout_seconds,
        )
    )
    if settings.discovery_companies_house_api_key:
        account_providers.append(
            CompaniesHouseAccountProvider(
                api_key=settings.discovery_companies_house_api_key,
                timeout_seconds=settings.discovery_timeout_seconds,
            )
        )
    if settings.discovery_enable_web_search and opensearch_web is not None:
        contact_provider = WebSearchContactProvider(opensearch_web=opensearch_web)
    elif settings.discovery_synthetic_contacts:
        contact_provider = SyntheticContactProvider()
    else:
        contact_provider = NoPublicContactProvider()
    _service = ProspectDiscoveryService(
        repository=_repository,
        account_provider=CompositeAccountProvider(providers=account_providers),
        contact_provider=contact_provider,
    )
    return _service


def get_prospect_discovery_service() -> ProspectDiscoveryService:
    return _service


@router.get("/status", response_model=dict)
def discovery_status(
    service: ProspectDiscoveryService = Depends(get_prospect_discovery_service),
) -> dict:
    account_provider = service.account_provider
    providers = [
        provider.name
        for provider in getattr(account_provider, "providers", [])
    ]
    return {
        "mode": "mock" if account_provider is None else "public",
        "account_providers": providers or ["mock"],
        "contact_provider": (
            service.contact_provider.name if service.contact_provider else "mock"
        ),
        "synthetic_contacts_enabled": settings.discovery_synthetic_contacts,
        "web_search_configured": "web_search" in providers,
        "sec_configured": bool(settings.discovery_sec_user_agent),
        "companies_house_configured": bool(settings.discovery_companies_house_api_key),
        "opencorporates_configured": True,
        "detail": (
            "Real company accounts come from SearchXNG/OpenSearch discovery plus "
            "public registries. Public registry sources do not provide verified "
            "employee emails or phone numbers. Web contact extraction returns "
            "public unverified persona candidates when names/titles are visible."
            if account_provider is not None
            else "Mock discovery is enabled for local tests."
        ),
        "synthetic_note": (
            "Synthetic persona contacts are generated when no web contact provider "
            "is configured. Verify before outreach."
            if settings.discovery_synthetic_contacts
            and getattr(service.contact_provider, "name", "") == "synthetic_persona"
            else None
        ),
    }


@router.post("/accounts", response_model=AccountDiscoveryResult)
def discover_accounts(
    payload: DiscoveryRequest,
    service: ProspectDiscoveryService = Depends(get_prospect_discovery_service),
) -> AccountDiscoveryResult:
    return service.discover_accounts(payload)


@router.post("/contacts", response_model=ContactDiscoveryResult)
def discover_contacts(
    payload: ContactDiscoveryRequest,
    service: ProspectDiscoveryService = Depends(get_prospect_discovery_service),
) -> ContactDiscoveryResult:
    return service.discover_contacts(
        account_ids=payload.account_ids,
        target_titles=payload.target_titles,
        target_seniorities=payload.target_seniorities,
    )


@router.post("/run", response_model=ProspectDiscoveryRunResult)
def run_discovery(
    payload: DiscoveryRequest,
    service: ProspectDiscoveryService = Depends(get_prospect_discovery_service),
) -> ProspectDiscoveryRunResult:
    return service.run_full_discovery(payload)


@router.get("/accounts", response_model=list[dict])
def list_discovered_accounts(
    icp_id: str | None = Query(default=None),
    service: ProspectDiscoveryService = Depends(get_prospect_discovery_service),
) -> list[dict]:
    return [item.model_dump(mode="json") for item in service.repository.list_accounts(icp_id=icp_id)]


@router.get("/contacts", response_model=list[dict])
def list_discovered_contacts(
    account_id: str | None = Query(default=None),
    service: ProspectDiscoveryService = Depends(get_prospect_discovery_service),
) -> list[dict]:
    return [item.model_dump(mode="json") for item in service.repository.list_contacts(account_id=account_id)]
