# Enrichment Agent

The Enrichment Agent converts discovered accounts and contacts into reusable, cited sales intelligence.

## Responsibilities

- Build deterministic company and contact research queries.
- Reuse the existing OpenSearch web service and configured SearchXNG/provider chain.
- Auto-fetch and index relevant pages when enabled.
- Retrieve and deduplicate evidence.
- Use the configured LLM to synthesize a structured SDR brief.
- Fall back to deterministic output when search or LLM evidence is unavailable.
- Persist validated results using SQLAlchemy with SQLite by default and Postgres via configuration.
- Expose a LangGraph-compatible workflow node.

## API

```text
POST /enrichment/research
GET  /enrichment
GET  /enrichment/{account_id}
```

## Storage

- OpenSearch stores fetched pages, snippets, citations, and search memory.
- SQLite/Postgres stores final structured enrichment results.
- Neo4j can be added later for account-contact-signal relationships.

## Configuration

```text
SDR_ENRICHMENT_DATABASE_URL
SDR_ENRICHMENT_COLLECTION
SDR_ENRICHMENT_TOP_K
SDR_ENRICHMENT_SEARCH_PROVIDER
SDR_ENRICHMENT_LLM_PROVIDER
SDR_ENRICHMENT_LLM_MODEL
```

## Streamlit

The `Enrichment Agent` tab contains:

- A user-facing account research flow.
- An internal testing console for OpenSearch collection, search provider, top-k, indexing, and LLM settings.
