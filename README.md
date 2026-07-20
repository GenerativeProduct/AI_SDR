# SALES_AGENT

Production-shaped AI SDR platform work. Current implemented module: **ICP Agent**,Prospect Discovery Agent(account discovery agent+ contact discovery agent)

## ICP Agent

The ICP Agent converts rough sales-manager targeting input into a structured, validated Ideal Customer Profile.

Features included:

- Deterministic normalization for industries, geographies, employee/revenue bands, personas, pain points, exclusions, and scoring weights.
- Optional LLM enrichment through Ollama via the backend LLM router.
- Guardrailed LLM suggestion parsing so malformed local-model JSON does not crash the agent.
- Versioned SQLAlchemy repository with SQLite default and Postgres-compatible database URL support.
- LangGraph node wrapper for SDR workflow orchestration.
- FastAPI routes for validate, suggest, create, update, list, get, and versions.
- Unit and integration tests.

## Run Tests

```bash
pytest ai_sdr_platform/tests/unit ai_sdr_platform/tests/integration -q
```

## API Routes

```text
POST /icp/validate
POST /icp/suggest
POST /icp
PUT /icp/{icp_id}
GET /icp
GET /icp/{icp_id}
GET /icp/{icp_id}/versions
```

## Recommended Ollama Model

## Prospect Discovery Agent (Step 6)

The Prospect Discovery Agent identifies high-fit target accounts and decision-makers based on the configured ICP.

### Features Included

#### Account Discovery Agent
- Matches companies against ICP filters:
  - Industry
  - Geography
  - Employee size
  - Revenue fit
  - Exclusion rules
- Deterministic fit scoring with ranking logic
- Fit reasoning generation for explainability
- Saves discovered accounts into database
- Mock provider support for development/testing

#### Contact Discovery Agent
- Finds relevant contacts inside discovered accounts
- Persona/title matching
- Seniority normalization (C-Level, VP, Director, Manager)
- Contact confidence scoring
- Persona match scoring
- Email + LinkedIn enrichment (mock stage)
- Saves discovered contacts into database

### Discovery Flow

```text
ICP → Account Discovery → High-Fit Accounts
                       ↓
                Contact Discovery
                       ↓
             Ranked Prospect List
```

### API Routes

```text
POST /prospects/discover/accounts
POST /prospects/discover/contacts
```

### Database Tables

```text
discovered_accounts
discovered_contacts
```

### Current Status

- Deterministic matching logic implemented
- Mock discovery providers enabled
- Backend APIs integrated
- Streamlit UI connected
- Ready for enrichment integration

### Future Integrations

- LinkedIn Sales Navigator
- Apollo.io
- CRM enrichment
- OpenSearch indexing
- Real-time provider APIs

```text
llama3.2:3b
```

Use stronger local models like `llama3.1:8b` or `mistral:7b` if you want better reasoning and can tolerate slower responses.
