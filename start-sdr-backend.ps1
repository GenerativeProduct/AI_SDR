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
Set-Location "C:\Users\sachi\Desktop\Desktop\Gen_Products\Latest_code\AI_SDR"

$ApolloKey = ""
$NeonDbUrl = ""
$HunterApiKey = ""
$SerperApiKey = ""
$OutreachProvider = "dry_run"
$BrevoApiKey = ""
$OutreachFromEmail = ""
$OutreachFromName = "SDR Team"
$TwilioAccountSid = ""
$TwilioAuthToken = ""
$TwilioFromNumber = ""
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

# --- Database: Neon Postgres if a connection string is set, else local SQLite ---
if ($NeonDbUrl) {
    $env:SDR_DATABASE_URL = $NeonDbUrl
    Write-Host "Database: NEON POSTGRES" -ForegroundColor Green
} else {
    Write-Host "Database: local SQLite (no Neon URL set)" -ForegroundColor Yellow
}

# --- Email enrichment: Hunter.io if a key is set (optional waterfall provider) ---
if ($HunterApiKey) {
    $env:HUNTER_API_KEY = $HunterApiKey
    Write-Host "Email provider: HUNTER" -ForegroundColor Green
} else {
    Write-Host "Email provider: none (no Hunter key set)" -ForegroundColor Yellow
}

# --- Enrichment web search: Serper (Google) primary, SearXNG fallback ---
if ($SerperApiKey) {
    $env:SERPER_API_KEY = $SerperApiKey
    Write-Host "Enrichment search: SERPER (primary) + SearXNG (fallback)" -ForegroundColor Green
} else {
    Write-Host "Enrichment search: SearXNG only (no Serper key set)" -ForegroundColor Yellow
}

# --- Real outreach sending providers (blank = dry-run) ---
$env:SDR_OUTREACH_PROVIDER = $OutreachProvider
if ($BrevoApiKey)       { $env:SDR_OUTREACH_BREVO_API_KEY = $BrevoApiKey }
if ($OutreachFromEmail) { $env:SDR_OUTREACH_FROM_EMAIL    = $OutreachFromEmail }
if ($OutreachFromName)  { $env:SDR_OUTREACH_SENDER_NAME   = $OutreachFromName }
if ($TwilioAccountSid)  { $env:SDR_OUTREACH_TWILIO_ACCOUNT_SID = $TwilioAccountSid }
if ($TwilioAuthToken)   { $env:SDR_OUTREACH_TWILIO_AUTH_TOKEN  = $TwilioAuthToken }
if ($TwilioFromNumber)  { $env:SDR_OUTREACH_TWILIO_FROM_NUMBER = $TwilioFromNumber }
$_emailReal = if ($OutreachProvider -ne "dry_run") { "REAL ($OutreachProvider)" } else { "dry-run" }
$_smsReal   = if ($TwilioAccountSid) { "REAL (twilio)" } else { "dry-run" }
Write-Host "Outreach sending: email=$_emailReal | sms=$_smsReal" -ForegroundColor Green

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
