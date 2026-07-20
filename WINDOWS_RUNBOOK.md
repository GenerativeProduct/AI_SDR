# AI SDR Platform — Windows / PowerShell Runbook

Adapted from the Mac 9-terminal runbook for this repo at `E:\Gen_Products\Latest_code\AI_SDR`.
Open each **numbered terminal** in VS Code (Terminal → Split Terminal) and keep long-running ones open.

> **What changed vs the Mac runbook**
> - Paths use `E:\Gen_Products\Latest_code\AI_SDR` (not `/Users/sathya/...`).
> - `source .venv/bin/activate` → `.venv\Scripts\Activate.ps1`
> - `export VAR=val` → `$env:VAR="val"`
> - `2>/dev/null` → `2>$null`
> - **Terminal 6 (main backend on :8000) is SKIPPED** — there is no `backend/` folder in this repo. The SDR backend treats it as optional and runs fine without it.
> - **Terminal 9 (Streamlit) has a blocker**: `app.py` imports a `custom_gpt` module that is missing from this folder. See Terminal 9 notes.

---

## Step 0 — One-time prerequisites

Install these first (skip any you already have):

1. **Docker Desktop** for Windows — https://www.docker.com/products/docker-desktop/ . Launch it and wait until it says *Running*.
2. **Ollama** for Windows — https://ollama.com/download . After install it runs as a background service.
3. **Temporal CLI** (only for the *full* flow) — in PowerShell:
   ```powershell
   winget install Temporal.Temporal
   ```
   (or download from https://github.com/temporalio/cli/releases and add to PATH)
4. **Python 3.11+** — https://www.python.org/downloads/ (check "Add to PATH").

### One-time Python environment

```powershell
cd E:\Gen_Products\Latest_code\AI_SDR
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r ai_sdr_platform\requirements.txt
pip install temporalio                       # needed by the follow-up worker
# For the Streamlit UI (Terminal 9) also:
pip install streamlit pandas numpy plotly requests scikit-learn
```

> If PowerShell blocks `Activate.ps1` with an execution-policy error, run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` then answer `Y`.

---

## Short mode vs Full flow

- **Short mode (ICP → Apollo discovery → SearXNG enrichment):** Terminals **1, 2, 3, 7, 9**.
- **Full flow (through follow-up + conversation):** add Terminals **4, 5, 8**.
- Terminal 6 is skipped in both (no backend in this repo).

---

## Terminal 1 — Ollama (local LLMs)

Ollama already runs as a service after install, so you usually only need to pull models:

```powershell
ollama pull llama3.2:3b
ollama pull llama3.1:8b
```

If it complains the server isn't running, open a dedicated terminal and run `ollama serve`, then pull in another.

Health check: `ollama list`

---

## Terminal 2 — OpenSearch (Docker)

```powershell
docker rm -f opensearch-sdr 2>$null
docker run --name opensearch-sdr -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" -e "DISABLE_SECURITY_PLUGIN=true" -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=Sathya@12345Strong" -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" opensearchproject/opensearch:2
```

Health check (new terminal): `curl.exe http://127.0.0.1:9200`

---

## Terminal 3 — SearXNG (Docker)

SearXNG disables its JSON API and enables a bot limiter by default, which makes
the enrichment calls 403. This repo now ships a config at `searxng\settings.yml`
that enables JSON and disables the limiter. Mount that folder when starting it:

```powershell
docker rm -f searxng-sdr 2>$null
docker run --name searxng-sdr -p 8088:8080 -e "BASE_URL=http://127.0.0.1:8088/" -v "E:\Gen_Products\Latest_code\AI_SDR\searxng:/etc/searxng" searxng/searxng:latest
```

Health check: `curl.exe "http://127.0.0.1:8088/search?q=openai&format=json"`
→ should return JSON (results/answers/infoboxes), **not** a `403 Forbidden` HTML page.

> **Notes:**
> - On first boot the container adds a `uwsgi.ini` file next to `settings.yml` in
>   the `searxng\` folder. That's normal — leave it. Your `settings.yml` is kept
>   as-is (JSON stays enabled).
> - If JSON ever 403s again, the container replaced your `settings.yml` with a
>   default. Delete everything in `searxng\` except `settings.yml` and restart.

---

## Terminal 4 — MetaRank (Docker)  *(full flow only)*

```powershell
cd E:\Gen_Products\Latest_code\AI_SDR
.venv\Scripts\Activate.ps1
python ai_sdr_platform\scripts\seed_metarank_sdr_events.py
cd metarank\sdr
docker compose up -d
docker compose ps
```

MetaRank listens on **http://127.0.0.1:8081**.

---

## Terminal 5 — Temporal Server  *(full flow only)*

**Option A — Docker (recommended; no install needed since Docker is already running):**

```powershell
docker run --rm -p 7233:7233 -p 8233:8233 temporalio/temporal server start-dev --ip 0.0.0.0
```

Keep this terminal open. Uses an in-memory DB (state resets on restart — fine for the flow).
The follow-up worker (T8) connects to `localhost:7233`.

**Option B — project-local native CLI** (persistent DB, matches the original runbook).
Downloads `temporal.exe` into a `bin\` folder inside the repo — no system PATH changes,
installed once, reused every run. First-time setup:

```powershell
cd E:\Gen_Products\Latest_code\AI_SDR
mkdir bin -Force
Invoke-WebRequest -Uri "https://temporal.download/cli/archive/latest?platform=windows&arch=amd64" -OutFile "bin\temporal.tar.gz"
tar -xzf bin\temporal.tar.gz -C bin
.\bin\temporal.exe --version   # confirm install
```

Then start the server (this and every later run):

```powershell
cd E:\Gen_Products\Latest_code\AI_SDR
mkdir ai_sdr_platform\data\temporal -Force
.\bin\temporal.exe server start-dev --db-filename ai_sdr_platform\data\temporal\temporal.db --ui-port 8233
```

Temporal UI (either option): http://127.0.0.1:8233

---

## Terminal 6 — SKIPPED

There is no `backend/` folder (port 8000) in this repo. The SDR backend auto-detects its absence and continues. Nothing to run.

---

## Terminal 7 — SDR Backend (the core — port 8011)

**Easiest: use the launcher script `start-sdr-backend.ps1` (in the repo root).**
Edit it once, run it every time:

```powershell
.\start-sdr-backend.ps1
```

Inside the script, edit only this one line:

```powershell
$ApolloKey = ""        # paste your Apollo key here, or leave "" for public/mock mode
```

- Key present → uses the **apollo** discovery provider (prints green).
- Empty (`""`) → uses the built-in **public/mock** provider (prints yellow). The full
  flow still runs; only the initial company list is mock data instead of live Apollo.

The script sets every env var, activates the venv, and starts uvicorn — so you never
retype the settings. The key lives in the file, not the terminal.

Health check: open **http://127.0.0.1:8011/docs** (Swagger UI). Login for protected routes: `admin@sdr.local` / `admin123`.

<details>
<summary>Manual alternative (set env vars by hand each session)</summary>

```powershell
cd E:\Gen_Products\Latest_code\AI_SDR
.venv\Scripts\Activate.ps1

$env:SDR_API_BASE_URL="http://127.0.0.1:8011"
$env:SDR_DISCOVERY_PROVIDER="apollo"          # or "public" if you have no key
$env:APOLLO_API_KEY="YOUR_APOLLO_API_KEY"     # omit these two lines in public mode
$env:SDR_DISCOVERY_APOLLO_API_KEY="YOUR_APOLLO_API_KEY"
$env:WEB_SEARCH_PROVIDER="searxng"
$env:SEARXNG_BASE_URL="http://127.0.0.1:8088"
$env:SDR_ENRICHMENT_SEARCH_PROVIDER="searxng"
$env:SDR_ENRICHMENT_SEARXNG_URL="http://127.0.0.1:8088"
$env:SDR_ENRICHMENT_COLLECTION="sdr_enrichment"
$env:SDR_ENRICHMENT_TOP_K="8"
$env:SDR_ENRICHMENT_LLM_PROVIDER="ollama_local"
$env:SDR_ENRICHMENT_LLM_MODEL="llama3.2:3b"
$env:SDR_INTELLIGENCE_METARANK_URL="http://127.0.0.1:8081"
$env:SDR_INTELLIGENCE_METARANK_MODEL="sdr-prospect-ranker"
$env:SDR_OUTREACH_PROVIDER="dry_run"

uvicorn ai_sdr_platform.src.api.app:app --host 127.0.0.1 --port 8011 --reload
```
</details>

---

## Terminal 8 — Follow-Up Worker  *(full flow only)*

**What it does:** a long-running Temporal worker that executes durable follow-up
sequences. It connects to the Temporal server (T5), then runs `SDRFollowUpWorkflow`,
which loops over a plan's scheduled "touches": it **sleeps until each touch's scheduled
time** (durably — survives restarts), then calls the backend to fire it
(`POST /follow-up/scheduler/run-plan/{id}`). It stops when the plan is
completed / stopped / paused. Without this worker, follow-up plans get created but
their timed touches never execute.

**Requires:** Terminal 5 (Temporal) and Terminal 7 (backend) already running, plus the
`temporalio` package installed (from Step 0). If it errors about Temporal support, run
`pip install temporalio`.

```powershell
cd E:\Gen_Products\Latest_code\AI_SDR
.venv\Scripts\Activate.ps1
$env:SDR_API_BASE_URL="http://127.0.0.1:8011"
python -m ai_sdr_platform.src.agents.follow_up.temporal_worker
```

It prints nothing dramatic when healthy — it just polls the task queue and waits.
Keep the terminal open.

---

## Terminal 9 — React Frontend (Vite dev server, port 5173)

This is the current UI — a React SPA in `ai-sdr-frontend/` that talks to the SDR
backend on `:8011` (Vite proxies `/api` → `http://127.0.0.1:8011`).

**Prerequisite:** Node.js 20+ (includes `npm`). Install from https://nodejs.org if
`node --version` fails.

```powershell
cd E:\Gen_Products\Latest_code\AI_SDR\ai-sdr-frontend
npm install        # first time only (installs node_modules)
npm run dev
```

Then open **http://localhost:5173**. Login: `admin@sdr.local` / `admin123`.
No `.env` is needed — the proxy default handles the API. (Terminal 7 backend must be
running on :8011 first, or the UI can't log in.)

Optional — seed a sample ICP so the dashboard isn't empty (run from the repo root
with the venv active):

```powershell
cd E:\Gen_Products\Latest_code\AI_SDR
python ai_sdr_platform\scripts\seed_demo_icp.py
```

Routes: `/` dashboard · `/pipeline` NL ICP chat + async pipeline · `/icp` editor ·
`/outreach` · `/conversations` · `/meetings` · `/analytics`.

> **Legacy alternative — Streamlit (port 8501):** the old `app.py` UI still exists.
> It originally crashed on a missing `custom_gpt` module; that import has been removed
> from `app.py`, so `streamlit run app.py --server.port 8501` now works too if you
> prefer it. The React app is the primary UI going forward.

---

## End-to-end test prompt (paste into the SDR chat)

> Target mid-market B2B SaaS companies in the United States with 100 to 1500 employees. Find companies that sell to revenue, sales, RevOps, or customer-facing teams and are likely dealing with poor pipeline visibility, low outbound reply rates, manual lead qualification, slow follow-up, or inefficient SDR workflows. Use Apollo for prospect discovery, enrich the discovered accounts using SearXNG public web search, index and retrieve evidence using OpenSearch, identify buying signals and intent, prioritize prospects, qualify sales readiness, and prepare approval-ready outreach and follow-up plans. Show completed results stage by stage and clearly explain where the flow stops if required data is missing.

---

## Quick start order

**Short mode:** 1 → 2 → 3 → 7 → 9 (React frontend)
**Full flow:** 1 → 2 → 3 → 4 → 5 → 7 → 8 → 9

Start Docker services (2, 3, and 4) first, give OpenSearch ~30s to come up, then start the backend (7).

> **Restarting after a reboot?** Don't re-run the `docker run` commands (they'll error
> "name already in use"). See `RESTART_SERVICES.md` for the restart-only commands.
