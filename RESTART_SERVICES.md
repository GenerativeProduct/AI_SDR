# AI SDR — Restart All Services (after a reboot)

Your Docker containers and Ollama models still exist after a restart — you do **not**
re-download or re-create them. Use `docker start` (not `docker run`) for the containers
you already made. Run each block in its own VS Code terminal, in this order.

> Before you start: open **Docker Desktop** and wait until it says *Running*.
> Ollama starts automatically as a Windows background service.

---

## 1. Docker infra — OpenSearch + SearXNG  (Terminals 2 & 3)

These containers already exist; just start them again:

```powershell
docker start opensearch-sdr searxng-sdr
```

Check they're up:

```powershell
docker ps
curl.exe http://127.0.0.1:9200                                  # OpenSearch
curl.exe "http://127.0.0.1:8088/search?q=test&format=json"      # SearXNG (expect JSON)
```

> If a container is missing from `docker ps -a` (e.g. it was removed), recreate it with
> the original `docker run` command from `WINDOWS_RUNBOOK.md` (Terminals 2 / 3).

---

## 2. MetaRank  (Terminal 4 — full flow only)

Started via docker compose, so bring it back the same way:

```powershell
cd C:\Users\sachi\Desktop\Desktop\Gen_Products\Latest_code\AI_SDR\metarank\sdr
docker compose up -d
docker compose ps
```

---

## 3. Temporal server  (Terminal 5 — full flow only)

Using the project-local binary in `bin\` (persistent DB):

```powershell
cd C:\Users\sachi\Desktop\Desktop\Gen_Products\Latest_code\AI_SDR
.\bin\temporal.exe server start-dev --db-filename ai_sdr_platform\data\temporal\temporal.db --ui-port 8233
```

(Or the Docker option: `docker run --rm -p 7233:7233 -p 8233:8233 temporalio/temporal server start-dev --ip 0.0.0.0`)
Keep this terminal open. UI: http://127.0.0.1:8233

---

## 4. SDR Backend  (Terminal 7 — the core)

```powershell
cd C:\Users\sachi\Desktop\Desktop\Gen_Products\Latest_code\AI_SDR
.\start-sdr-backend.ps1
```

Wait for `Application startup complete`. Verify: http://127.0.0.1:8011/docs
(The venv auto-activates; `temporalio` is already installed.)

---

## 5. Follow-Up Worker  (Terminal 8 — full flow only)

New terminal — **make sure the prompt shows `(.venv)`** before running:

```powershell
cd C:\Users\sachi\Desktop\Desktop\Gen_Products\Latest_code\AI_SDR
$env:SDR_API_BASE_URL="http://127.0.0.1:8011"
python -m ai_sdr_platform.src.agents.follow_up.temporal_worker
```

Goes quiet when healthy (it's polling Temporal). Requires Terminals 5 + 7 running.

---

## 6. React Frontend  (Terminal 9)

`node_modules` persists, so no reinstall needed:

```powershell
cd C:\Users\sachi\Desktop\Desktop\Gen_Products\Latest_code\AI_SDR\ai-sdr-frontend
npm run dev
```

Open **http://localhost:5173** — login `admin@sdr.local` / `admin123`.
(Run `npm install` again only if you deleted `node_modules`.)

---

## 7. Streamlit UI  (Terminal 10 — alternative to the React frontend)

The legacy Streamlit UI (`app.py`). Use this **instead of** the React frontend (Terminal 9) —
pick one, they're two UIs for the same backend on different ports. Needs the venv active:

```powershell
cd C:\Users\sachi\Desktop\Desktop\Gen_Products\Latest_code\AI_SDR
.venv\Scripts\Activate.ps1
streamlit run app.py --server.port 8501
```

Streamlit opens **http://localhost:8501** automatically. The SDR Backend (section 4) must be
running on :8011 first. In the app's sidebar, set **AI SDR Backend URL** to `http://127.0.0.1:8011`.

---

## Order recap

**Short mode:** 1 (docker start) → backend → a UI
`docker start opensearch-sdr searxng-sdr` → `.\start-sdr-backend.ps1` → `npm run dev` (React) **or** `streamlit run app.py --server.port 8501` (Streamlit)

**Full flow:** OpenSearch+SearXNG → MetaRank → Temporal → Backend → Worker → UI
(sections 1 → 2 → 3 → 4 → 5 → 6 or 7 above)

> **UI choice:** run the React frontend (section 6, :5173) **or** Streamlit (section 7, :8501), not both.

## Stopping everything

```powershell
docker stop opensearch-sdr searxng-sdr
cd C:\Users\sachi\Desktop\Desktop\Gen_Products\Latest_code\AI_SDR\metarank\sdr; docker compose down
```
Then Ctrl+C in the Temporal, backend, worker, and UI (React or Streamlit) terminals.
