# AI SDR Frontend

React SPA for the AI SDR platform — replaces the Streamlit `icp_agent_tab` workflow.

## Stack

- React 19 + Vite + TypeScript + Tailwind CSS 4
- React Router 7, TanStack Query 5, Zustand
- Proxies `/api` → FastAPI backend on `:8011`

## Dev setup

```bash
# Terminal A — backend
cd "../ai_sdr_platform"
pip install -r requirements.txt temporalio
export SDR_AUTH_ENABLED=true
uvicorn ai_sdr_platform.src.api.app:app --reload --port 8011

# Terminal B — frontend
cd ai-sdr-frontend
npm install
npm run dev
```

Default login: `admin@sdr.local` / `admin123` (seeded when `SDR_AUTH_ENABLED=true`).

Optional demo data:

```bash
npm run seed:demo   # from ai-sdr-frontend — creates a sample ICP
```

## Routes

| Route | Purpose |
|-------|---------|
| `/` | Dashboard |
| `/pipeline` | NL ICP chat + async pipeline |
| `/icp` | Advanced ICP editor |
| `/outreach` | Campaign approve/send |
| `/conversations` | Reply approval |
| `/meetings` | Book meetings + CRM sync |
| `/analytics` | Cross-module export |

## Scripts

- `npm run dev` — Vite dev server
- `npm run build` — production build
- `npm run test` — Vitest unit tests
- `npm run codegen` — export OpenAPI from FastAPI
