#!/usr/bin/env bash
# Run backend + frontend quality gates (requires backend on :8011 for live E2E).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== Backend pytest =="
python3 -m pytest ai_sdr_platform/tests/ -q

echo "== Frontend lint / build / unit =="
cd ai-sdr-frontend
npm run lint
npm run build
npm run test:unit

echo "== E2E smoke =="
npm run test:e2e:smoke

if curl -sf http://127.0.0.1:8011/health > /dev/null 2>&1; then
  echo "== E2E live (backend detected) =="
  npm run test:e2e:live
else
  echo "== Skipping live E2E (start backend on :8011 to include) =="
fi

echo "All verification passed."
