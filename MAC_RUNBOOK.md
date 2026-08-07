# AI SDR Platform — macOS Runbook

The macOS companion to `WINDOWS_RUNBOOK.md`. Open each **numbered terminal** in
iTerm/Terminal (or VS Code → Terminal → Split Terminal) and keep the long-running
ones open.

> **Set your project path once per terminal.** All commands below assume you are
> in the repo folder. Adjust this to wherever you cloned it:
>
> ```bash
> export AI_SDR=~/Projects/AI_SDR
> cd "$AI_SDR"
> ```

> **What differs from the original Mac runbook**
> - **Terminal 6 (main backend on :8000) is SKIPPED** — there is no `backend/`
>   folder in this repo. The SDR backend detects its absence and runs without it.
> - **Terminal 9 is the React frontend**, not Streamlit. The Streamlit app still
>   works but is legacy.
> - Discovery runs in `public` mode unless you supply an Apollo key.

---

## Step 0 — One-time prerequisites

Homebrew is the easiest route. Install it first if you don't have it
(https://brew.sh), then:

```bash
brew install --cask docker      # Docker Desktop
brew install --cask ollama      # local LLM runtime
brew install python@3.11
brew install node               # Node.js 20+ for the React frontend
brew install temporal           # Temporal CLI (full flow only)
```

Open **Docker Desktop** from Applications and wait until it reports *Running* —
the `docker` command fails until the engine is up.

> **Apple Silicon note:** most images here are multi-architecture and run
> natively. If any container exits immediately with an `exec format error`, add
> `--platform linux/amd64` to that `docker run` command (MetaRank is the most
> likely candidate).

### One-time Python environment

```bash
cd "$AI_SDR"
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r ai_sdr_platform/requirements.txt
```

`requirements.txt` already includes `temporalio`, `requests`, `numpy`,
`scikit-learn`, `joblib` and `jinja2` — all required for the API to start.

### One-time frontend dependencies

```bash
cd "$AI_SDR/ai-sdr-frontend"
npm install
```

---

## Short mode vs Full flow

- **Short mode** (ICP → discovery → enrichment): Terminals **1, 2, 3, 7, 9**
- **Full flow** (through follow-up + conversation): add Terminals **4, 5, 8**
- Terminal 6 is skipped in both.

---

## Terminal 1 — Ollama (local LLMs)

Ollama runs as a background service once installed, so normally you only pull models:

```bash
ollama pull llama3.2:3b
ollama pull llama3.1:8b
```

Health check: `ollama list`

> If you see `Error: listen tcp 127.0.0.1:11434: bind: address already in use`,
> that means Ollama is **already running**. Nothing to fix — skip `ollama serve`.

---

## Terminal 2 — OpenSearch (Docker)

```bash
docker rm -f opensearch-sdr 2>/dev/null || true

docker run --name opensearch-sdr \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" \
  opensearchproject/opensearch:2
```

Health check (new terminal): `curl http://127.0.0.1:9200`

---

## Terminal 3 — SearXNG (Docker)

SearXNG disables its JSON API and enables a bot limiter by default, which makes
programmatic queries return `403`. The repo ships a config at
`searxng/settings.yml` that fixes both — mount that folder when starting it:

```bash
docker rm -f searxng-sdr 2>/dev/null || true

docker run --name searxng-sdr \
  -p 8088:8080 \
  -e "BASE_URL=http://127.0.0.1:8088/" \
  -v "$AI_SDR/searxng:/etc/searxng" \
  searxng/searxng:latest
```

Health check:

```bash
curl "http://127.0.0.1:8088/search?q=openai&format=json"
```

→ should return JSON, **not** a `403 Forbidden` HTML page.

> **Harmless startup noise:** you will see errors registering the `ahmia`,
> `torch` and `wikidata` engines, plus a warning about a missing
> `limiter.toml`. These are individual search engines failing to load (Tor
> engines need a proxy; Wikidata rate-limits) and the missing limiter config is
> expected because we disabled the limiter. The lines that matter are
> `Listening at: http://:::8080` and `Started worker-1`.

---

## Terminal 4 — MetaRank (Docker) *(full flow only)*

```bash
cd "$AI_SDR"
source .venv/bin/activate
python ai_sdr_platform/scripts/seed_metarank_sdr_events.py
cd metarank/sdr
docker compose up -d
docker compose ps
```

MetaRank listens on **http://127.0.0.1:8081**.

---

## Terminal 5 — Temporal Server *(full flow only)*

**Option A — Homebrew CLI (recommended on Mac):**

```bash
cd "$AI_SDR"
mkdir -p ai_sdr_platform/data/temporal
temporal server start-dev \
  --db-filename ai_sdr_platform/data/temporal/temporal.db \
  --ui-port 8233
```

**Option B — Docker (no install needed):**

```bash
docker run --rm -p 7233:7233 -p 8233:8233 \
  temporalio/temporal server start-dev --ip 0.0.0.0
```

Option A persists workflow state between restarts; Option B uses an in-memory
database that resets. Keep the terminal open either way.

Temporal UI: http://127.0.0.1:8233

---

## Terminal 6 — SKIPPED

There is no `backend/` folder (port 8000) in this repo. The SDR backend detects
this at startup and continues without it. Nothing to run.

---

## Terminal 7 — SDR Backend (the core — port 8011)

**Use the launcher script.** First time only, make it executable:

```bash
cd "$AI_SDR"
chmod +x start-sdr-backend.sh
```

Then every run:

```bash
./start-sdr-backend.sh
```

**Apollo & Outreach keys (optional).** Place your API keys in `secrets.local.sh` (gitignored):

```bash
cp secrets.local.sh.example secrets.local.sh
```

Edit `secrets.local.sh` to configure live discovery and outreach providers:

```bash
# Apollo Discovery Key (optional - leave empty for public/mock discovery)
ApolloKey="your-apollo-key-here"

# Resend Email Outreach (optional - set provider to resend to send live emails)
RESEND_API_KEY="re_123456789"
RESEND_FROM_EMAIL="onboarding@resend.dev"
RESEND_SENDER_NAME="SDR Team"
TEST_RECIPIENT="your-personal-email@gmail.com"  # Dev redirect for Resend free tier

# Twilio SMS & WhatsApp Messaging (optional)
SDR_OUTREACH_TWILIO_ACCOUNT_SID="AC123456"
SDR_OUTREACH_TWILIO_AUTH_TOKEN="your-token"
SDR_OUTREACH_TWILIO_FROM_NUMBER="+15550001111"

# LLM Providers (optional - Groq & xAI Grok)
GROQ_API_KEY="gsk_12345"
GROK_API_KEY="xai_12345"
```

- Apollo Key present → **apollo** discovery provider (prints green).
- Resend Key set & `SDR_OUTREACH_PROVIDER=resend` → **resend** email provider.
- Twilio credentials set → **twilio** SMS & WhatsApp messaging enabled.
- Default / Keys empty → **public/mock** discovery & **dry_run** outreach provider (prints yellow). The full pipeline still runs cleanly offline.

The script activates the venv, exports every required variable, and starts uvicorn — so you never retype settings.

Health check: open **http://127.0.0.1:8011/docs**.
Login for protected routes: `admin@sdr.local` / `admin123`.

<details>
<summary>Manual alternative (export variables by hand each session)</summary>

```bash
cd "$AI_SDR"
source .venv/bin/activate

export SDR_API_BASE_URL="http://127.0.0.1:8011"
export SDR_DISCOVERY_PROVIDER="public"        # or "apollo" with a key
# export APOLLO_API_KEY="your-key"
export WEB_SEARCH_PROVIDER="searxng"
export SEARXNG_BASE_URL="http://127.0.0.1:8088"
export SDR_ENRICHMENT_SEARCH_PROVIDER="searxng"
export SDR_ENRICHMENT_SEARXNG_URL="http://127.0.0.1:8088"
export SDR_ENRICHMENT_COLLECTION="sdr_enrichment"
export SDR_ENRICHMENT_TOP_K="8"
export SDR_ENRICHMENT_LLM_PROVIDER="ollama_local"
export SDR_ENRICHMENT_LLM_MODEL="llama3.2:3b"
export SDR_INTELLIGENCE_METARANK_URL="http://127.0.0.1:8081"
export SDR_INTELLIGENCE_METARANK_MODEL="sdr-prospect-ranker"
export SDR_OUTREACH_PROVIDER="resend"         # or "dry_run" / "brevo" / "smtp"
# export RESEND_API_KEY="your-resend-key"
# export TEST_RECIPIENT="your-test-email@gmail.com"

uvicorn ai_sdr_platform.src.api.app:app --host 127.0.0.1 --port 8011 --reload
```
</details>

---

## Terminal 8 — Follow-Up Worker *(full flow only)*

**What it does:** a long-running Temporal worker that executes durable follow-up
sequences. It runs `SDRFollowUpWorkflow`, which sleeps until each scheduled
"touch" is due — durably, surviving restarts — then calls the backend to fire it.
Without this worker, follow-up plans are created but their touches never execute.

**Requires:** Terminals 5 and 7 already running.

```bash
cd "$AI_SDR"
source .venv/bin/activate
export SDR_API_BASE_URL="http://127.0.0.1:8011"
python -m ai_sdr_platform.src.agents.follow_up.temporal_worker
```

It stays silent when healthy — that means it connected and is polling the task
queue. Keep the terminal open.

> If it fails with `ModuleNotFoundError: No module named 'temporalio'`, the venv
> is not active in that terminal. Run `source .venv/bin/activate` first.

---

## Terminal 9 — React Frontend (port 5173)

```bash
cd "$AI_SDR/ai-sdr-frontend"
npm run dev
```

Open **http://localhost:5173** and log in with `admin@sdr.local` / `admin123`.
No `.env` is needed — Vite proxies `/api` → `http://127.0.0.1:8011`. Terminal 7
must be running first, or login will fail.

Optional — seed a sample ICP so the dashboard isn't empty:

```bash
cd "$AI_SDR"
source .venv/bin/activate
python ai_sdr_platform/scripts/seed_demo_icp.py
```

Routes: `/` dashboard · `/pipeline` NL ICP chat · `/icp` editor · `/outreach` ·
`/conversations` · `/meetings` · `/analytics`

> **Legacy alternative — Streamlit (port 8501):**
> `streamlit run app.py --server.port 8501`

---

## Running the pipeline

The stages are sequential — each consumes what the previous produced:

**ICP → Discovery → Enrichment → Intelligence → Qualification → Outreach → Follow-Up**

On a fresh database, start at ICP. Jumping straight to Intelligence fails with
"no records" because Discovery hasn't produced any contacts to score yet. The
**Pipeline Chat** page runs the whole chain from a single prompt.

### End-to-end test prompt

> Target mid-market B2B SaaS companies in the United States with 100 to 1500
> employees. Find companies that sell to revenue, sales, RevOps, or
> customer-facing teams and are likely dealing with poor pipeline visibility, low
> outbound reply rates, manual lead qualification, slow follow-up, or inefficient
> SDR workflows. Identify buying signals and intent, prioritize prospects,
> qualify sales readiness, and prepare approval-ready outreach and follow-up
> plans. Show completed results stage by stage and clearly explain where the flow
> stops if required data is missing.

---

## Quick start order

**Short mode:** 1 → 2 → 3 → 7 → 9
**Full flow:** 1 → 2 → 3 → 4 → 5 → 7 → 8 → 9

Start the Docker services first and give OpenSearch ~30 seconds before starting
the backend.

---

## Restarting later

Containers persist. Do **not** re-run `docker run` — it fails with
"name already in use". Start the existing ones instead:

```bash
docker start opensearch-sdr searxng-sdr
cd "$AI_SDR/metarank/sdr" && docker compose up -d
```

Then Terminals 5, 7, 8, 9 as above.

### Stopping everything

`Ctrl+C` in the Temporal, backend, worker and frontend terminals, then:

```bash
docker stop opensearch-sdr searxng-sdr
cd "$AI_SDR/metarank/sdr" && docker compose down
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'temporalio'` | venv not active in that terminal | `source .venv/bin/activate` |
| `bind: address already in use` on 11434 | Ollama already running | Skip `ollama serve` — it's fine |
| `403 Forbidden` from SearXNG | JSON API disabled | Confirm `searxng/` is mounted (Terminal 3) and recreate the container |
| `permission denied: ./start-sdr-backend.sh` | Script not executable | `chmod +x start-sdr-backend.sh` |
| `docker: name is already in use` | Container exists already | Use `docker start <name>` instead of `docker run` |
| `exec format error` on Apple Silicon | Image is amd64-only | Add `--platform linux/amd64` to that `docker run` |
| Login fails on a fresh database | API crashed before seeding admin | Check the backend terminal for a traceback |
| Intelligence/Qualification return nothing | No upstream data yet | Run ICP → Discovery first |
