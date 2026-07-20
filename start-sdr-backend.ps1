# ============================================================
#  AI SDR Backend launcher (Terminal 7)
#  Edit the two settings below ONCE, then just run:
#      .\start-sdr-backend.ps1
# ============================================================

# ------------------------------------------------------------
#  SECRETS: the Apollo API key is NOT stored in this file, so
#  this script is safe to commit to GitLab.
#
#  Put your key in a file named  secrets.local.ps1  next to this
#  script (it is gitignored), containing exactly one line:
#
#      $ApolloKey = "your-apollo-key-here"
#
#  No secrets.local.ps1  ->  runs in public/mock mode.
# ------------------------------------------------------------

$ErrorActionPreference = "Stop"
Set-Location "E:\Gen_Products\Latest_code\AI_SDR"

$ApolloKey = ""
if (Test-Path ".\secrets.local.ps1") {
    . ".\secrets.local.ps1"
}
# You can also override with an environment variable instead of the file:
if ($env:APOLLO_API_KEY_OVERRIDE) { $ApolloKey = $env:APOLLO_API_KEY_OVERRIDE }

# Activate the virtual environment (harmless if already active)
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

# --- Discovery provider: apollo if a key is set, else public ---
if ($ApolloKey -ne "") {
    $env:SDR_DISCOVERY_PROVIDER      = "apollo"
    $env:APOLLO_API_KEY              = $ApolloKey
    $env:SDR_DISCOVERY_APOLLO_API_KEY = $ApolloKey
    Write-Host "Discovery provider: APOLLO" -ForegroundColor Green
} else {
    $env:SDR_DISCOVERY_PROVIDER = "public"
    Write-Host "Discovery provider: PUBLIC (no Apollo key set)" -ForegroundColor Yellow
}

# --- Core settings (same every run) ---
$env:SDR_API_BASE_URL                 = "http://127.0.0.1:8011"
$env:WEB_SEARCH_PROVIDER              = "searxng"
$env:SEARXNG_BASE_URL                 = "http://127.0.0.1:8088"
$env:SDR_ENRICHMENT_SEARCH_PROVIDER   = "searxng"
$env:SDR_ENRICHMENT_SEARXNG_URL       = "http://127.0.0.1:8088"
$env:SDR_ENRICHMENT_COLLECTION        = "sdr_enrichment"
$env:SDR_ENRICHMENT_TOP_K             = "8"
$env:SDR_ENRICHMENT_LLM_PROVIDER      = "ollama_local"
$env:SDR_ENRICHMENT_LLM_MODEL         = "llama3.2:3b"
$env:SDR_INTELLIGENCE_METARANK_URL    = "http://127.0.0.1:8081"
$env:SDR_INTELLIGENCE_METARANK_MODEL  = "sdr-prospect-ranker"
$env:SDR_OUTREACH_PROVIDER            = "dry_run"

Write-Host "Starting SDR backend on http://127.0.0.1:8011 ..." -ForegroundColor Cyan
uvicorn ai_sdr_platform.src.api.app:app --host 127.0.0.1 --port 8011 --reload
