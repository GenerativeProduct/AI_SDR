#!/bin/bash
# ============================================================
#  AI SDR Backend launcher (Terminal 7) — macOS / Linux
#  Run it with:   ./start-sdr-backend.sh
#  First time only:  chmod +x start-sdr-backend.sh
# ============================================================
#
#  SECRETS: the Apollo API key is NOT stored in this file, so
#  this script is safe to commit.
#
#  Put your key in a file named  secrets.local.sh  next to this
#  script (it is gitignored), containing exactly one line:
#
#      ApolloKey="your-apollo-key-here"
#
#  No secrets.local.sh  ->  runs in public/mock mode.
# ------------------------------------------------------------

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# Activate the virtual environment (harmless if already active)
if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

ApolloKey=""
if [ -f "./secrets.local.sh" ]; then
    # shellcheck disable=SC1091
    source ./secrets.local.sh
fi
# Environment variable overrides the file, if set.
if [ -n "$APOLLO_API_KEY_OVERRIDE" ]; then
    ApolloKey="$APOLLO_API_KEY_OVERRIDE"
fi

# --- Discovery provider: apollo if a key is set, else public ---
if [ -n "$ApolloKey" ]; then
    export SDR_DISCOVERY_PROVIDER="apollo"
    export APOLLO_API_KEY="$ApolloKey"
    export SDR_DISCOVERY_APOLLO_API_KEY="$ApolloKey"
    echo -e "${GREEN}Discovery provider: APOLLO${NC}"
else
    export SDR_DISCOVERY_PROVIDER="public"
    echo -e "${YELLOW}Discovery provider: PUBLIC (no Apollo key set)${NC}"
fi

# --- Core settings (same every run) ---
export SDR_API_BASE_URL="http://127.0.0.1:8011"
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
export SDR_OUTREACH_PROVIDER="${SDR_OUTREACH_PROVIDER:-dry_run}"

echo -e "${CYAN}Starting SDR backend on http://127.0.0.1:8011 ...${NC}"
uvicorn ai_sdr_platform.src.api.app:app --host 127.0.0.1 --port 8011 --reload
