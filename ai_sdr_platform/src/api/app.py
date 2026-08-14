from pathlib import Path
import logging
import os
import sys

# Surface our own "sdr.*" loggers on the console. Uvicorn only configures its
# own loggers, so application INFO logs (e.g. how many companies Apollo returned)
# would otherwise be hidden. This makes discovery diagnostics visible in the
# backend terminal.
_sdr_logger = logging.getLogger("sdr")
if not _sdr_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s: [%(name)s] %(message)s"))
    _sdr_logger.addHandler(_handler)
    _sdr_logger.setLevel(logging.INFO)
    _sdr_logger.propagate = False

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from ai_sdr_platform.src.api.routes.routes_auth import router as auth_router
from ai_sdr_platform.src.api.routes.routes_dashboard import router as dashboard_router
from ai_sdr_platform.src.api.routes.routes_enrichment import (
    configure_enrichment_service,
    router as enrichment_router,
)
from ai_sdr_platform.src.api.routes.routes_icp import configure_icp_service, router as icp_router
from ai_sdr_platform.src.api.routes.routes_prospect_discovery import (
    configure_prospect_discovery_service,
    router as prospect_discovery_router,
)
from ai_sdr_platform.src.api.routes.routes_sdr_pipeline import router as sdr_pipeline_router
from ai_sdr_platform.src.api.routes.routes_prospect_intelligence import (
    configure_prospect_intelligence_service,
    router as prospect_intelligence_router,
)
from ai_sdr_platform.src.api.routes.routes_outreach import (
    configure_outreach_service,
    router as outreach_router,
)
from ai_sdr_platform.src.api.routes.routes_follow_up import (
    configure_follow_up_service,
    router as follow_up_router,
)
from ai_sdr_platform.src.api.routes.routes_conversation import (
    configure_conversation_service,
    router as conversation_router,
)
from ai_sdr_platform.src.api.routes.routes_qualification import (
    configure_qualification_service,
    router as qualification_router,
)
from ai_sdr_platform.src.api.routes.routes_crm import (
    configure_crm_service,
    router as crm_router,
)
from ai_sdr_platform.src.api.routes.routes_meeting import (
    configure_meeting_service,
    router as meeting_router,
)
from ai_sdr_platform.src.api.routes import routes_enrichment, routes_icp, routes_prospect_intelligence
from ai_sdr_platform.src.auth.dependencies import auth_middleware
from ai_sdr_platform.src.auth.service import AuthService
from ai_sdr_platform.src.shared.config import settings


def _optional_backend_services() -> tuple[object | None, object | None]:
    try:
        backend_dir = Path(__file__).resolve().parents[3] / "backend"
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from app.core.llm_clients import LLMRouter
        from app.services.opensearch_web import OpenSearchWebService

        return LLMRouter(), OpenSearchWebService()
    except Exception:
        return None, None


def create_app(llm_router: object | None = None, opensearch_web: object | None = None) -> FastAPI:
    app = FastAPI(title="AI SDR Platform", version="1.0.0")
    if llm_router is None or opensearch_web is None:
        auto_llm_router, auto_opensearch_web = _optional_backend_services()
        llm_router = llm_router or auto_llm_router
        opensearch_web = opensearch_web or auto_opensearch_web
    # No backend LLM router present -> use the local Ollama router so enrichment,
    # personalization, ICP suggestions and outreach copy actually use the model.
    if llm_router is None:
        from ai_sdr_platform.src.shared.llm_router import OllamaLLMRouter
        llm_router = OllamaLLMRouter()
        import logging
        logging.getLogger("sdr.llm").info(
            "Using local Ollama LLM router at %s", getattr(llm_router, "base_url", "?")
        )
    configure_prospect_discovery_service(opensearch_web=opensearch_web)
    configure_outreach_service(llm_router=llm_router)
    configure_follow_up_service()
    configure_qualification_service()
    configure_crm_service()
    if (
        llm_router is not None
        and getattr(routes_icp._service, "suggestion_provider", None) is None
    ):
        configure_icp_service(llm_router=llm_router)
    if (
        llm_router is not None
        and getattr(routes_prospect_intelligence._service, "llm_router", None) is None
    ):
        configure_prospect_intelligence_service(llm_router=llm_router)
    if (
        getattr(routes_enrichment._service, "search_provider", None) is None
        and getattr(routes_enrichment._service, "llm_router", None) is None
    ):
        configure_enrichment_service(llm_router=llm_router, opensearch_web=opensearch_web)
    configure_conversation_service()
    configure_meeting_service()

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(auth_middleware)

    app.include_router(auth_router)
    app.include_router(icp_router)
    app.include_router(prospect_discovery_router)
    app.include_router(enrichment_router)
    app.include_router(sdr_pipeline_router)
    app.include_router(dashboard_router)
    app.include_router(prospect_intelligence_router)
    app.include_router(qualification_router)
    app.include_router(outreach_router)
    app.include_router(conversation_router)
    app.include_router(follow_up_router)
    app.include_router(meeting_router)
    app.include_router(crm_router)

    if settings.auth_enabled:
        AuthService().ensure_default_admin()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "ai-sdr-platform"}

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        schema["security"] = [{"BearerAuth": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi

    return app


app = create_app()
