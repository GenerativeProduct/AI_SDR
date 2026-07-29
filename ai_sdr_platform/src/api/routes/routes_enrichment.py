from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ai_sdr_platform.src.agents.enrichment.models import (
    EnrichmentListResponse,
    EnrichmentResearchRequest,
    EnrichmentResult,
)
from ai_sdr_platform.src.agents.enrichment.repository import SQLAlchemyEnrichmentRepository
from ai_sdr_platform.src.agents.enrichment.service import (
    DirectOpenSearchProvider,
    EnrichmentService,
    SearxngSearchProvider,
)
from ai_sdr_platform.src.shared.config import settings

router = APIRouter(prefix="/enrichment", tags=["enrichment-agent"])
_repository = SQLAlchemyEnrichmentRepository()
_service = EnrichmentService(repository=_repository)


def configure_enrichment_service(
    *,
    llm_router: object | None = None,
    opensearch_web: object | None = None,
    tenant_id: str = "default",
    role: str = "viewer",
) -> EnrichmentService:
    global _service
    # Prefer the optional OpenSearch backend when present; otherwise fall back to
    # a local SearXNG instance so enrichment still does real web research instead
    # of the do-nothing Noop provider.
    if opensearch_web is not None:
        search_provider = DirectOpenSearchProvider(
            opensearch_web, tenant_id=tenant_id, role=role
        )
    elif settings.enrichment_search_provider == "searxng" and settings.enrichment_searxng_url:
        search_provider = SearxngSearchProvider(base_url=settings.enrichment_searxng_url)
    else:
        search_provider = None
    _service = EnrichmentService(
        repository=_repository,
        search_provider=search_provider,
        llm_router=llm_router,
    )
    return _service


def get_enrichment_service() -> EnrichmentService:
    return _service


@router.post("/research", response_model=EnrichmentResult)
def research_account(
    payload: EnrichmentResearchRequest,
    service: EnrichmentService = Depends(get_enrichment_service),
) -> EnrichmentResult:
    try:
        return service.research(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Enrichment research failed: {exc}") from exc


@router.get("", response_model=EnrichmentListResponse)
def list_enrichments(service: EnrichmentService = Depends(get_enrichment_service)) -> EnrichmentListResponse:
    items = service.list_results()
    return EnrichmentListResponse(items=items, total=len(items))


@router.get("/status", response_model=dict)
def enrichment_status(
    service: EnrichmentService = Depends(get_enrichment_service),
) -> dict:
    provider = service.search_provider
    is_searxng = provider is not None and provider.__class__.__name__ == "SearxngSearchProvider"
    opensearch_web = getattr(provider, "opensearch_web", None)
    configured_provider = (
        opensearch_web.configured_provider()
        if opensearch_web is not None and hasattr(opensearch_web, "configured_provider")
        else None
    )
    available_provider_chain = (
        opensearch_web.available_providers_in_chain()
        if opensearch_web is not None and hasattr(opensearch_web, "available_providers_in_chain")
        else []
    )
    opensearch_available = (
        bool(opensearch_web.available())
        if opensearch_web is not None and hasattr(opensearch_web, "available")
        else False
    )
    live_search_configured = bool(
        is_searxng
        or (
            configured_provider
            and configured_provider != "manual_urls"
            and available_provider_chain
        )
    )
    return {
        "search_provider_configured": provider is not None,
        "search_provider": provider.__class__.__name__ if provider is not None else "NoopSearchProvider",
        "configured_web_provider": configured_provider or ("searxng" if is_searxng else None),
        "available_web_provider_chain": available_provider_chain or (["searxng"] if is_searxng else []),
        "live_search_configured": live_search_configured,
        "opensearch_index_available": opensearch_available,
        "llm_configured": service.llm_router is not None,
        "detail": (
            "Enrichment is using live SearXNG web search."
            if is_searxng
            else "Enrichment will use live web retrieval. OpenSearch indexing is also available."
            if live_search_configured and opensearch_available
            else "Enrichment will use live web retrieval directly; OpenSearch indexing is not available."
            if live_search_configured
            else "Enrichment search is wired, but no live web provider is configured; set WEB_SEARCH_PROVIDER and provider credentials/base URL."
            if provider is not None
            else "No enrichment search provider is configured; enrichment will produce limited evidence."
        ),
    }


@router.get("/{account_id}", response_model=EnrichmentResult)
def get_enrichment(
    account_id: str,
    service: EnrichmentService = Depends(get_enrichment_service),
) -> EnrichmentResult:
    result = service.get_latest(account_id)
    if not result:
        raise HTTPException(status_code=404, detail="Enrichment result not found")
    return result
