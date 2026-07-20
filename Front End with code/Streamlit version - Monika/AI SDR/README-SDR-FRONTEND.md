# AI SDR Platform

Production-shaped AI SDR backend with FastAPI agents and React frontend.

## Quick start

```bash
# Backend
pip install -r ai_sdr_platform/requirements.txt temporalio
export SDR_AUTH_ENABLED=true
uvicorn ai_sdr_platform.src.api.app:app --reload --port 8011

# Frontend
cd ai-sdr-frontend && npm install && npm run dev
```

## New in this milestone

- JWT auth (`/auth/login`, `/auth/refresh`, `/auth/me`)
- CORS for React dev server
- Async pipeline jobs (`POST /sdr/pipeline/run` → `GET /sdr/jobs/{id}`)
- Dashboard aggregation (`GET /sdr/dashboard`)
- React SPA in `ai-sdr-frontend/`

## Testing

```bash
cd ai-sdr-frontend
npm run test              # Vitest unit tests
npm run test:e2e:smoke    # Login page (port 5180, no backend)
npm run test:e2e:live     # Auth + dashboard + pipeline (backend on :8011)
```

E2E uses port **5180** by default to avoid colliding with other Vite apps on 5173.

## One-command dev stack

```bash
bash scripts/dev-stack.sh
```

## Full verification

```bash
bash scripts/verify-all.sh
```

Runs backend pytest, frontend lint/build/unit, smoke E2E, and live E2E when backend is on `:8011`.

Login: `admin@sdr.local` / `admin123`

See `ai_sdr_platform/.env.example` and `ai-sdr-frontend/.env.example` for configuration.

## Docker (production-shaped)

```bash
docker compose up --build
```

- SPA: http://localhost:8080
- API (direct): http://localhost:8011
- Login: `admin@sdr.local` / `admin123`

Set `SDR_JWT_SECRET` in your environment before deploying.

