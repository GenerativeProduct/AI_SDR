#!/usr/bin/env bash
# Start AI SDR backend + frontend dev servers (Ctrl+C stops both).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export SDR_AUTH_ENABLED="${SDR_AUTH_ENABLED:-true}"
export SDR_CORS_ORIGINS="${SDR_CORS_ORIGINS:-http://localhost:5173,http://localhost:5174,http://localhost:5180}"

python3 -m uvicorn ai_sdr_platform.src.api.app:app --reload --port 8011 &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 2
curl -sf "http://127.0.0.1:8011/health" > /dev/null && echo "Backend ready on :8011"

cd ai-sdr-frontend
npm run dev
