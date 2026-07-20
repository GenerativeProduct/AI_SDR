# Prospect Discovery

Production Prospect Discovery uses real public company records:

- SearchXNG plus OpenSearch indexing for web-discovered company candidates
- GLEIF LEI records for global legal entities
- SEC EDGAR registrants for US public companies when a compliant SEC
  `User-Agent` is configured
- OpenCorporates public registry search
- Companies House search when an API key is configured

Configuration:

```text
SDR_DISCOVERY_PROVIDER=public
SDR_DISCOVERY_ENABLE_WEB_SEARCH=true
SDR_DISCOVERY_SEC_USER_AGENT="Your App your-email@example.com"
SDR_DISCOVERY_OPENCORPORATES_API_TOKEN=
SDR_DISCOVERY_COMPANIES_HOUSE_API_KEY=
SDR_DISCOVERY_TIMEOUT_SECONDS=15
WEB_SEARCH_PROVIDER=searxng
SEARXNG_BASE_URL=http://127.0.0.1:8080
OPENSEARCH_URL=http://127.0.0.1:9200
OPENSEARCH_INDEX_PREFIX=kb_chunks
WEB_SEARCH_AUTO_INDEX=true
```

`GET /prospect-discovery/status` reports active providers.
`GET /enrichment/status` reports whether live retrieval and OpenSearch indexing
are active.

## Local OpenSearch indexing

Start the local index used by both the OpenSearch tab and SDR discovery:

```bash
cd ai_sdr_platform/opensearch
docker compose up -d
curl http://127.0.0.1:9200
```

When `OPENSEARCH_URL` is configured, SearchXNG results are fetched, page content
is indexed into OpenSearch, and later discovery/enrichment queries retrieve
indexed evidence before falling back to direct live snippets.

Public registries provide company/account records, not Apollo-style employee
databases. The production service never invents contacts. Until a public
leadership/contact-page extractor is configured, real account discovery can
continue into account enrichment, while Prospect Intelligence and Outreach
wait for a real named contact.

Tests can instantiate `ProspectDiscoveryService` without providers to use the
explicit mock fixture.
