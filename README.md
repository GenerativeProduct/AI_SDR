# AI SDR Platform

An AI-powered Sales Development Representative (SDR) platform that runs the full
outbound workflow from a single ICP prompt: **ICP → Prospect Discovery →
Enrichment → Prospect Intelligence → Qualification → Outreach → Follow-Up →
Conversation → Meeting → CRM.**

---

## 🚀 First-time run — start here

If you are setting this up for the **first time on a new machine**, follow the
runbook for your OS end-to-end. It walks through every prerequisite and service
in order:

- **Windows:** [`WINDOWS_RUNBOOK.md`](WINDOWS_RUNBOOK.md)
- **Mac:** [`MAC_RUNBOOK.md`](MAC_RUNBOOK.md)

Once everything is installed, to **restart all services after a reboot** use:

- [`RESTART_SERVICES.md`](RESTART_SERVICES.md)

The Quick Setup below is a summary of those runbooks.

---

## What it does

- **ICP Agent** — turns plain-English targeting (or manual filters) into a structured Ideal Customer Profile.
- **Prospect Discovery** — finds matching companies and contacts via **Apollo** (with public-source fallbacks: GLEIF, OpenCorporates, SEC, web search).
- **Enrichment** — gathers web evidence per company via SearXNG/OpenSearch.
- **Prospect Intelligence** — intent, reply/meeting/qualification propensity, queue ranking, and personalization.
- **Qualification** — BANT / MEDDIC scoring with an ML probability gate.
- **Outreach & Follow-Up** — approval-ready drafts and durable follow-up sequences (Temporal).
- **Meetings & CRM** — booking and sync.

## Architecture highlights

- **Cache-first + TTL** — discovery and enrichment check the database before calling external APIs, so repeat searches are fast and cheap.
- **Identity resolution** — one clean record per company/person (deduplicated across sources by domain / email / LinkedIn).
- **Multi-provider waterfall** — optional providers (Apollo, Hunter, …) light up automatically when their API keys are present; missing keys are skipped.
- **Storage** — Neon/Postgres (or local SQLite fallback).

See [`ARCHITECTURE_MULTI_SOURCE_ENRICHMENT.md`](ARCHITECTURE_MULTI_SOURCE_ENRICHMENT.md) for the full design.

## Tech stack

FastAPI · SQLAlchemy · Pydantic · React (Vite) · Streamlit · Docker (OpenSearch, SearXNG, MetaRank) · Ollama (local LLMs) · Temporal.

## Prerequisites

- Python 3.11+
- Node.js 20+ (for the React frontend)
- Docker Desktop (OpenSearch, SearXNG, MetaRank)
- Ollama (local LLMs)
- Optional: Apollo API key, Hunter API key, a Neon/Postgres URL

## Quick Setup

1. **Secrets** — copy the template and add your own keys. **This is the file you must create before the first run:**
   ```powershell
   copy secrets.local.ps1.example secrets.local.ps1
   ```
   Then edit **`secrets.local.ps1`** and set:
   - `$ApolloKey` — your Apollo API key (leave `""` for public/mock discovery)
   - `$HunterApiKey` — your Hunter key (optional; leave `""` to skip email enrichment)
   - `$NeonDbUrl` — your Neon/Postgres connection string (leave `""` to use local SQLite)

   > `secrets.local.ps1` is gitignored — it is never committed. Each person creates their own.

2. **Python environment:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r ai_sdr_platform\requirements.txt
   ```

3. **Frontend (optional, React UI):**
   ```powershell
   cd ai-sdr-frontend
   npm install
   ```

## Running

Start infrastructure and services in order (full details in the runbooks):

```powershell
# Docker services
docker start opensearch-sdr searxng-sdr

# Backend (port 8011) — reads your keys from secrets.local.ps1
.\start-sdr-backend.ps1

# Pick ONE UI:
cd ai-sdr-frontend; npm run dev            # React     -> http://localhost:5173
streamlit run app.py --server.port 8501    # Streamlit -> http://localhost:8501
```

Login: `admin@sdr.local` / `admin123`

## Configuration reference

| Env var | Purpose |
|---|---|
| `SDR_DATABASE_URL` | Neon/Postgres connection string (else local SQLite) |
| `APOLLO_API_KEY` | Apollo discovery provider |
| `HUNTER_API_KEY` | Hunter email find/verify (optional) |
| `SDR_CACHE_TTL_DAYS` | Freshness window for cached records (default 30) |
| `SDR_DISCOVERY_CACHE_ENABLED` | Toggle cache-first discovery (default true) |
| `SDR_ENRICHMENT_CACHE_ENABLED` | Toggle cache-first enrichment (default true) |

## Run tests

```bash
pytest ai_sdr_platform/tests/unit ai_sdr_platform/tests/integration -q
```

## Documentation

- [`WINDOWS_RUNBOOK.md`](WINDOWS_RUNBOOK.md) / [`MAC_RUNBOOK.md`](MAC_RUNBOOK.md) — full first-time setup, all services.
- [`RESTART_SERVICES.md`](RESTART_SERVICES.md) — restart everything after a reboot.
- [`ARCHITECTURE_MULTI_SOURCE_ENRICHMENT.md`](ARCHITECTURE_MULTI_SOURCE_ENRICHMENT.md) — caching / multi-provider design.
