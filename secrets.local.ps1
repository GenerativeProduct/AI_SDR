# LOCAL SECRETS — never commit this file (it is listed in .gitignore).
# Used by start-sdr-backend.ps1

$ApolloKey = "kXHHUR1lMg00aaV5swKI9g"

# Neon Postgres connection string (Phase 1). Leave blank to use local SQLite.
$NeonDbUrl = "postgresql://neondb_owner:npg_xdj3knQhTWv9@ep-shiny-shape-af26znmu-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Hunter.io API key (Phase 4 — email find/verify). Leave blank to skip Hunter.
$HunterApiKey = "55d7c03ffe82d4badf303af5cd498b87e68c40f2"
