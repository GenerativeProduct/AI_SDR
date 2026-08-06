from dataclasses import dataclass
import os


# A single connection string can point every agent's store at the same database
# (e.g. a hosted Neon/Postgres). Each per-agent SDR_*_DATABASE_URL still overrides
# this when set, so nothing changes for anyone who leaves SDR_DATABASE_URL unset.
_DEFAULT_DATABASE_URL = os.getenv("SDR_DATABASE_URL", "")


@dataclass(frozen=True)
class SDRSettings:
    app_name: str = os.getenv("SDR_APP_NAME", "ai-sdr-platform")
    environment: str = os.getenv("SDR_ENVIRONMENT", "local")
    icp_database_url: str = os.getenv("SDR_ICP_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    discovery_database_url: str = os.getenv("SDR_DISCOVERY_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    discovery_provider: str = os.getenv("SDR_DISCOVERY_PROVIDER", "public")
    discovery_sec_user_agent: str = os.getenv("SDR_DISCOVERY_SEC_USER_AGENT", "")
    discovery_companies_house_api_key: str = os.getenv(
        "SDR_DISCOVERY_COMPANIES_HOUSE_API_KEY", ""
    )
    discovery_opencorporates_api_token: str = os.getenv(
        "SDR_DISCOVERY_OPENCORPORATES_API_TOKEN", ""
    )
    discovery_enable_web_search: bool = (
        os.getenv("SDR_DISCOVERY_ENABLE_WEB_SEARCH", "true").lower() == "true"
    )
    discovery_synthetic_contacts: bool = (
        os.getenv("SDR_DISCOVERY_SYNTHETIC_CONTACTS", "true").lower() == "true"
    )
    # Apollo contact discovery. When a key is present the Apollo provider takes
    # priority over web-search and synthetic contacts.
    discovery_apollo_api_key: str = os.getenv(
        "SDR_DISCOVERY_APOLLO_API_KEY", os.getenv("APOLLO_API_KEY", "")
    )
    discovery_apollo_contacts_per_account: int = int(
        os.getenv("SDR_DISCOVERY_APOLLO_CONTACTS_PER_ACCOUNT", "5")
    )
    # Revealing emails calls Apollo's enrichment endpoint and consumes credits.
    discovery_apollo_reveal_emails: bool = (
        os.getenv("SDR_DISCOVERY_APOLLO_REVEAL_EMAILS", "true").lower() == "true"
    )
    discovery_timeout_seconds: float = float(
        os.getenv("SDR_DISCOVERY_TIMEOUT_SECONDS", "15")
    )
    # Optional email-enrichment providers (waterfall). Absent key => provider is
    # not built and is skipped. Hunter finds/verifies emails; ZoomInfo is a stub
    # for a future enterprise integration.
    hunter_api_key: str = os.getenv("HUNTER_API_KEY", "")
    zoominfo_api_key: str = os.getenv("ZOOMINFO_API_KEY", "")
    # Cache-first discovery: reuse DB records younger than the TTL before calling
    # external APIs. Set SDR_DISCOVERY_CACHE_ENABLED=false to always hit the API.
    discovery_cache_enabled: bool = (
        os.getenv("SDR_DISCOVERY_CACHE_ENABLED", "true").lower() == "true"
    )
    cache_ttl_days: int = int(os.getenv("SDR_CACHE_TTL_DAYS", "30"))
    enrichment_database_url: str = os.getenv("SDR_ENRICHMENT_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    intelligence_database_url: str = os.getenv("SDR_INTELLIGENCE_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    intelligence_metarank_url: str = os.getenv("SDR_INTELLIGENCE_METARANK_URL", "")
    intelligence_metarank_model: str = os.getenv(
        "SDR_INTELLIGENCE_METARANK_MODEL", "sdr-prospect-ranker"
    )
    intelligence_metarank_event_path: str = os.getenv(
        "SDR_INTELLIGENCE_METARANK_EVENT_PATH",
        "metarank/sdr/events.jsonl",
    )
    intelligence_monitor_path: str = os.getenv("SDR_INTELLIGENCE_MONITOR_PATH", "")
    intelligence_mlflow_tracking_uri: str = os.getenv(
        "SDR_INTELLIGENCE_MLFLOW_TRACKING_URI", ""
    )
    intelligence_intent_model_path: str = os.getenv("SDR_INTELLIGENCE_INTENT_MODEL_PATH", "")
    intelligence_intent_model_version: str = os.getenv(
        "SDR_INTELLIGENCE_INTENT_MODEL_VERSION", "unconfigured"
    )
    intelligence_reply_model_path: str = os.getenv("SDR_INTELLIGENCE_REPLY_MODEL_PATH", "")
    intelligence_reply_model_version: str = os.getenv(
        "SDR_INTELLIGENCE_REPLY_MODEL_VERSION", "unconfigured"
    )
    intelligence_meeting_model_path: str = os.getenv(
        "SDR_INTELLIGENCE_MEETING_MODEL_PATH", ""
    )
    intelligence_meeting_model_version: str = os.getenv(
        "SDR_INTELLIGENCE_MEETING_MODEL_VERSION", "unconfigured"
    )
    intelligence_qualification_model_path: str = os.getenv(
        "SDR_INTELLIGENCE_QUALIFICATION_MODEL_PATH", ""
    )
    intelligence_qualification_model_version: str = os.getenv(
        "SDR_INTELLIGENCE_QUALIFICATION_MODEL_VERSION", "unconfigured"
    )
    qualification_database_url: str = os.getenv("SDR_QUALIFICATION_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    outreach_database_url: str = os.getenv("SDR_OUTREACH_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    outreach_provider: str = os.getenv("SDR_OUTREACH_PROVIDER", "dry_run")
    outreach_sender_name: str = os.getenv("SDR_OUTREACH_SENDER_NAME", "SDR Team")
    outreach_from_email: str = os.getenv("SDR_OUTREACH_FROM_EMAIL", "")
    outreach_smtp_host: str = os.getenv("SDR_OUTREACH_SMTP_HOST", "")
    outreach_smtp_port: int = int(os.getenv("SDR_OUTREACH_SMTP_PORT", "587"))
    outreach_smtp_username: str = os.getenv("SDR_OUTREACH_SMTP_USERNAME", "")
    outreach_smtp_password: str = os.getenv("SDR_OUTREACH_SMTP_PASSWORD", "")
    outreach_aws_region: str = os.getenv("SDR_OUTREACH_AWS_REGION", "us-east-1")
    outreach_brevo_api_key: str = os.getenv("SDR_OUTREACH_BREVO_API_KEY", "")
    outreach_reply_to_email: str = os.getenv("SDR_OUTREACH_REPLY_TO_EMAIL", "")
    outreach_twilio_account_sid: str = os.getenv("SDR_OUTREACH_TWILIO_ACCOUNT_SID", "")
    outreach_twilio_auth_token: str = os.getenv("SDR_OUTREACH_TWILIO_AUTH_TOKEN", "")
    outreach_twilio_from_number: str = os.getenv("SDR_OUTREACH_TWILIO_FROM_NUMBER", "")
    outreach_max_per_minute: int = int(os.getenv("SDR_OUTREACH_MAX_PER_MINUTE", "30"))
    outreach_max_per_recipient_per_day: int = int(
        os.getenv("SDR_OUTREACH_MAX_PER_RECIPIENT_PER_DAY", "3")
    )
    outreach_openclaw_api_key: str = os.getenv("SDR_OUTREACH_OPENCLAW_API_KEY", "")
    outreach_webhook_secret: str = os.getenv("SDR_OUTREACH_WEBHOOK_SECRET", "")
    outreach_brevo_webhook_secret: str = os.getenv(
        "SDR_OUTREACH_BREVO_WEBHOOK_SECRET", ""
    )
    outreach_brevo_inbound_secret: str = os.getenv(
        "SDR_OUTREACH_BREVO_INBOUND_SECRET", ""
    )
    outreach_temporal_host: str = os.getenv("SDR_OUTREACH_TEMPORAL_HOST", "localhost:7233")
    outreach_temporal_namespace: str = os.getenv("SDR_OUTREACH_TEMPORAL_NAMESPACE", "default")
    outreach_temporal_task_queue: str = os.getenv(
        "SDR_OUTREACH_TEMPORAL_TASK_QUEUE", "sdr-outreach"
    )
    conversation_database_url: str = os.getenv("SDR_CONVERSATION_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    conversation_llm_base_url: str = os.getenv(
        "SDR_CONVERSATION_LLM_BASE_URL", "http://127.0.0.1:11434"
    )
    conversation_llm_model: str = os.getenv(
        "SDR_CONVERSATION_LLM_MODEL", "llama3.1:8b"
    )
    conversation_llm_timeout_seconds: float = float(
        os.getenv("SDR_CONVERSATION_LLM_TIMEOUT_SECONDS", "90")
    )
    follow_up_database_url: str = os.getenv("SDR_FOLLOW_UP_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    meeting_database_url: str = os.getenv("SDR_MEETING_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    meeting_provider: str = os.getenv("SDR_MEETING_PROVIDER", "dry_run")
    meeting_google_calendar_id: str = os.getenv(
        "SDR_MEETING_GOOGLE_CALENDAR_ID", "primary"
    )
    meeting_google_client_id: str = os.getenv("SDR_MEETING_GOOGLE_CLIENT_ID", "")
    meeting_google_client_secret: str = os.getenv(
        "SDR_MEETING_GOOGLE_CLIENT_SECRET", ""
    )
    meeting_google_refresh_token: str = os.getenv(
        "SDR_MEETING_GOOGLE_REFRESH_TOKEN", ""
    )
    meeting_google_token_uri: str = os.getenv(
        "SDR_MEETING_GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"
    )
    meeting_calcom_base_url: str = os.getenv(
        "SDR_MEETING_CALCOM_BASE_URL", "https://api.cal.com"
    )
    meeting_calcom_api_key: str = os.getenv("SDR_MEETING_CALCOM_API_KEY", "")
    meeting_calcom_api_version: str = os.getenv(
        "SDR_MEETING_CALCOM_API_VERSION", "2026-02-25"
    )
    meeting_calcom_event_type_id: int = int(
        os.getenv("SDR_MEETING_CALCOM_EVENT_TYPE_ID", "0")
    )
    meeting_calcom_event_type_slug: str = os.getenv(
        "SDR_MEETING_CALCOM_EVENT_TYPE_SLUG", ""
    )
    meeting_calcom_username: str = os.getenv("SDR_MEETING_CALCOM_USERNAME", "")
    meeting_calcom_team_slug: str = os.getenv("SDR_MEETING_CALCOM_TEAM_SLUG", "")
    meeting_calcom_organization_slug: str = os.getenv(
        "SDR_MEETING_CALCOM_ORGANIZATION_SLUG", ""
    )
    meeting_default_timezone: str = os.getenv(
        "SDR_MEETING_DEFAULT_TIMEZONE", "UTC"
    )
    meeting_default_duration_minutes: int = int(
        os.getenv("SDR_MEETING_DEFAULT_DURATION_MINUTES", "30")
    )
    meeting_webhook_secret: str = os.getenv("SDR_MEETING_WEBHOOK_SECRET", "")
    meeting_temporal_task_queue: str = os.getenv(
        "SDR_MEETING_TEMPORAL_TASK_QUEUE", "sdr-meetings"
    )
    crm_database_url: str = os.getenv("SDR_CRM_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    crm_provider: str = os.getenv("SDR_CRM_PROVIDER", "dry_run")
    crm_twenty_base_url: str = os.getenv(
        "SDR_CRM_TWENTY_BASE_URL", "https://api.twenty.com"
    )
    crm_twenty_api_key: str = os.getenv("SDR_CRM_TWENTY_API_KEY", "")
    crm_twenty_people_object: str = os.getenv(
        "SDR_CRM_TWENTY_PEOPLE_OBJECT", "people"
    )
    crm_twenty_companies_object: str = os.getenv(
        "SDR_CRM_TWENTY_COMPANIES_OBJECT", "companies"
    )
    crm_twenty_opportunities_object: str = os.getenv(
        "SDR_CRM_TWENTY_OPPORTUNITIES_OBJECT", "opportunities"
    )
    enrichment_collection: str = os.getenv("SDR_ENRICHMENT_COLLECTION", "sdr_enrichment")
    enrichment_top_k: int = int(os.getenv("SDR_ENRICHMENT_TOP_K", "8"))
    enrichment_search_provider: str = os.getenv("SDR_ENRICHMENT_SEARCH_PROVIDER", "")
    # Cache-first enrichment: reuse a fresh, complete enrichment for a company
    # instead of re-running SearXNG + LLM every time (avoids search-engine throttling).
    enrichment_cache_enabled: bool = (
        os.getenv("SDR_ENRICHMENT_CACHE_ENABLED", "true").lower() == "true"
    )
    enrichment_searxng_url: str = os.getenv(
        "SDR_ENRICHMENT_SEARXNG_URL", os.getenv("SEARXNG_BASE_URL", "")
    )
    # Serper.dev (Google results API) for enrichment web search. When set it is
    # the primary provider, with SearXNG kept as a free fallback.
    serper_api_key: str = os.getenv("SERPER_API_KEY", "")
    enrichment_llm_provider: str = os.getenv("SDR_ENRICHMENT_LLM_PROVIDER", "ollama_local")
    enrichment_llm_model: str = os.getenv("SDR_ENRICHMENT_LLM_MODEL", "llama3.2:3b")
    default_weight_industry_fit: float = float(os.getenv("SDR_WEIGHT_INDUSTRY_FIT", "0.30"))
    default_weight_company_size_fit: float = float(os.getenv("SDR_WEIGHT_COMPANY_SIZE_FIT", "0.20"))
    default_weight_persona_fit: float = float(os.getenv("SDR_WEIGHT_PERSONA_FIT", "0.25"))
    default_weight_geo_fit: float = float(os.getenv("SDR_WEIGHT_GEO_FIT", "0.10"))
    default_weight_pain_point_fit: float = float(os.getenv("SDR_WEIGHT_PAIN_POINT_FIT", "0.15"))
    auth_enabled: bool = os.getenv("SDR_AUTH_ENABLED", "false").lower() == "true"
    auth_database_url: str = os.getenv("SDR_AUTH_DATABASE_URL", "") or _DEFAULT_DATABASE_URL
    auth_jwt_secret: str = os.getenv(
        "SDR_JWT_SECRET", "dev-change-me-in-production-use-32-chars-min"
    )
    auth_jwt_expire_minutes: int = int(os.getenv("SDR_JWT_EXPIRE_MINUTES", "60"))
    auth_refresh_expire_days: int = int(os.getenv("SDR_REFRESH_EXPIRE_DAYS", "7"))
    auth_default_admin_email: str = os.getenv("SDR_DEFAULT_ADMIN_EMAIL", "admin@sdr.local")
    auth_default_admin_password: str = os.getenv("SDR_DEFAULT_ADMIN_PASSWORD", "admin123")
    cors_origins: str = os.getenv(
        "SDR_CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:5180"
    )
    jobs_database_url: str = os.getenv("SDR_JOBS_DATABASE_URL", "") or _DEFAULT_DATABASE_URL


settings = SDRSettings()

