# LOCAL SECRETS — never commit this file (it is listed in .gitignore).
# Used by start-sdr-backend.ps1

$ApolloKey = "kXHHUR1lMg00aaV5swKI9g"

# Neon Postgres connection string (Phase 1). Leave blank to use local SQLite.
$NeonDbUrl = "postgresql://neondb_owner:npg_xdj3knQhTWv9@ep-shiny-shape-af26znmu-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Hunter.io API key (Phase 4 — email find/verify). Leave blank to skip Hunter.
$HunterApiKey = "55d7c03ffe82d4badf303af5cd498b87e68c40f2"

# Serper.dev API key (enrichment web search, primary over SearXNG). Leave blank to use SearXNG only.
$SerperApiKey = "19b73d5a61758c9494cd75f37cbcead64a8d30ae"

# ---- Real outreach sending (leave blank = dry-run / no send) ----
# EMAIL via Brevo SMTP relay (using the xsmtpsib- SMTP key).
$OutreachProvider  = "smtp"
$SmtpHost          = "smtp-relay.brevo.com"
$SmtpPort          = "587"
$SmtpUsername      = "corporate@generativeproduct.io"   # your Brevo account login (SMTP Login)
$SmtpPassword      = "xsmtpsib-53117e1774130a61def6756349ad8fbf1e61b332080cfb1ebf2c8c4763dd461d-uOYjLViDpoMCrT5i"
$OutreachFromEmail = "corporate@generativeproduct.io"   # MUST be a verified Brevo sender
$OutreachFromName  = "SDR Team"
$BrevoApiKey       = ""           # (unused with SMTP; only for the REST 'brevo' provider)
# SMS/WhatsApp via Twilio:
$TwilioAccountSid  = ""
$TwilioAuthToken   = ""
$TwilioFromNumber  = ""           # e.g. +15551234567 (your Twilio number)
