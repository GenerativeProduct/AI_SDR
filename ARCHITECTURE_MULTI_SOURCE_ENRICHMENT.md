# Multi-Source Discovery, Enrichment & Caching — Architecture

Design for turning the current single-source (Apollo) discovery flow into a cached,
multi-provider system: a local database is the source of truth, external APIs
(Apollo, Hunter, ZoomInfo, …) fill gaps in a **waterfall**, every new record is
saved back, and **no duplicates** are ever stored.

Providers are **optional**: if an API key is present the provider is used; if not,
it is silently skipped and the next available method is used. So this works today
with only Apollo + SearXNG, and gains Hunter/ZoomInfo the moment keys are added —
no code changes required at the call sites.

---

## 1. Principles

1. **The local DB is the source of truth.** Every search checks the DB first.
2. **Cache-first with freshness.** A DB record is trusted only if it is younger
   than a TTL (default 30 days). Stale records are re-fetched.
3. **Waterfall, not parallel.** Providers are tried in priority order; we stop
   paying for the next one once we have a confident result.
4. **Optional providers degrade gracefully.** No key → provider is not built →
   the waterfall skips it. Never a crash, never a hard dependency.
5. **One record per real-world entity.** Identity resolution + DB unique
   constraints make duplicates impossible.
6. **Save everything new.** Any record fetched from an API is written back so the
   next search is cheaper.

---

## 2. Current state (what exists today)

- **Discovery providers** implement two protocols in
  `prospect_discovery/providers.py`: `AccountDiscoveryProvider.search_accounts()`
  and `ContactDiscoveryProvider.search_contacts()`. Apollo, GLEIF, SEC,
  OpenCorporates, WebSearch are implementations; `CompositeAccountProvider`
  already chains them.
- **Persistence** uses SQLAlchemy repositories (`repository.py` in each agent),
  defaulting to a local SQLite file `ai_sdr_platform/data/prospects.db`. Saves are
  upserts keyed by the source-specific id (`account_id` / `contact_id`).
- **Config** already exposes per-agent DB URLs via env
  (`SDR_DISCOVERY_DATABASE_URL`, `SDR_ENRICHMENT_DATABASE_URL`, …), so the DB
  backend is swappable without code changes.
- **Gap:** discovery **always** calls the provider; the DB is written but never
  read as a cache. Dedup is by source id only (cross-source duplicates possible).
  Enrichment runs only on the top-N accounts.

---

## 3. Target architecture (overview)

```
                         ┌─────────────────────────────────────────┐
   ICP  ─────────────▶   │            Discovery Service             │
                         │  (cache-first orchestrator)              │
                         └───────────────┬─────────────────────────┘
                                         │ 1. read
                          ┌──────────────▼───────────────┐
                          │   Local DB (Neon / Postgres)  │  ◀── source of truth
                          │   accounts · contacts ·        │
                          │   enrichment  (+ last_verified)│
                          └──────────────┬───────────────┘
                          2. gaps / stale │
                          ┌──────────────▼───────────────┐
                          │      Provider Waterfall       │
                          │  (only providers with creds)  │
                          │  Apollo → Hunter → ZoomInfo →  │
                          │  SearXNG/public fallback       │
                          └──────────────┬───────────────┘
                          3. merge + save │  (identity resolution, no dupes)
                                         ▼
                                   back to Local DB
```

The **Discovery Service** becomes a thin orchestrator:
`resolve(request) = cache_lookup() → identify_gaps() → waterfall_fetch(gaps) →
merge_and_save() → return(cache ∪ fresh)`.

---

## 4. Provider abstraction (optional + waterfall)

### 4.1 One interface per capability

Providers declare a **capability** and whether they are **available** (have creds):

```python
class AccountProvider(Protocol):
    name: str
    def is_available(self) -> bool: ...
    def search_accounts(self, icp, limit) -> list[DiscoveredAccount]: ...

class ContactProvider(Protocol):
    name: str
    def is_available(self) -> bool: ...
    def search_contacts(self, accounts, titles, seniorities) -> list[DiscoveredContact]: ...

class EmailProvider(Protocol):          # NEW capability (Hunter, etc.)
    name: str
    def is_available(self) -> bool: ...
    def find_email(self, full_name, domain) -> EmailResult | None: ...
    def verify_email(self, email) -> EmailVerification: ...
```

### 4.2 The registry only builds providers that have credentials

```python
def build_provider_registry(settings) -> ProviderRegistry:
    accounts, contacts, emails = [], [], []

    if settings.discovery_apollo_api_key:          # present → build it
        accounts.append(ApolloAccountProvider(...))
        contacts.append(ApolloContactProvider(...))
    if settings.hunter_api_key:                    # absent today → skipped
        emails.append(HunterEmailProvider(...))
    if settings.zoominfo_api_key:                  # absent today → skipped
        accounts.append(ZoomInfoAccountProvider(...))
        contacts.append(ZoomInfoContactProvider(...))

    # Always-available public fallbacks (no key needed)
    accounts += [GLEIFAccountProvider(...), OpenCorporatesAccountProvider(...)]
    emails.append(SearxngEmailGuesser(...))        # pattern-guess + SearXNG verify

    return ProviderRegistry(accounts=accounts, contacts=contacts, emails=emails)
```

Because the registry is built from whatever keys exist, **adding Hunter later is
just setting `HUNTER_API_KEY`** — the waterfall picks it up automatically.

### 4.3 The waterfall

For each unit of work (e.g. "find the email for this person"), iterate available
providers in priority order and stop at the first confident result:

```python
def find_email(person, domain, providers) -> EmailResult | None:
    for p in providers:                 # already filtered to is_available()
        result = p.find_email(person.full_name, domain)
        if result and result.confidence >= THRESHOLD:
            return result               # stop — don't pay the next provider
    return None                         # nobody found it → leave blank / guess
```

Priority (highest data quality first): **ZoomInfo → Apollo → Hunter → public/SearXNG**.
You can reorder via a `SDR_PROVIDER_PRIORITY` env list.

---

## 5. Database design (Neon / Postgres)

### 5.1 Why Postgres/Neon

SQLAlchemy already abstracts the DB, so moving off SQLite is a connection-string
change. Neon gives hosted, free, serverless Postgres that survives machine moves
and supports the **unique constraints** and **`ON CONFLICT` upserts** that make
dedup reliable (SQLite is weaker here). Driver: `psycopg2-binary`.

### 5.2 Canonical identity keys (the anti-duplicate core)

Duplicates happen when two providers return the same entity with different source
ids. We compute a **canonical key** and make it `UNIQUE` in the DB:

| Entity   | Canonical key (first non-null wins)                        |
|----------|------------------------------------------------------------|
| Company  | `domain` (normalized, no `www.`/scheme) → else slug(name)  |
| Contact  | `lower(email)` → else `linkedin_url` → else `lower(full_name)+company_domain` |

```python
def company_key(a: DiscoveredAccount) -> str:
    return normalize_domain(a.website) or slug(a.company_name)

def contact_key(c: DiscoveredContact, company_domain: str) -> str:
    if c.email:        return c.email.strip().lower()
    if c.linkedin_url: return normalize_linkedin(c.linkedin_url)
    return f"{c.full_name.strip().lower()}@@{company_domain}"
```

### 5.3 Schema (adds cache/identity columns to your existing fields)

```sql
CREATE TABLE companies (
    company_key      TEXT PRIMARY KEY,           -- canonical (domain/slug)
    company_name     TEXT NOT NULL,
    domain           TEXT,
    website          TEXT,
    linkedin_url     TEXT,
    industry         TEXT,
    location         TEXT,
    employee_count   INTEGER,
    revenue_range    TEXT,
    sources          TEXT[],                     -- ['apollo','zoominfo']
    first_seen_at    TIMESTAMPTZ DEFAULT now(),
    last_verified_at TIMESTAMPTZ DEFAULT now(),  -- drives TTL
    raw              JSONB                        -- provider payloads, merged
);

CREATE TABLE contacts (
    contact_key      TEXT PRIMARY KEY,           -- canonical (email/linkedin/name)
    company_key      TEXT REFERENCES companies(company_key),
    full_name        TEXT NOT NULL,
    title            TEXT,
    seniority        TEXT,
    department       TEXT,
    email            TEXT,
    email_status     TEXT,                       -- verified/unverified/…
    linkedin_url     TEXT,
    phone            TEXT,
    confidence       INTEGER,
    sources          TEXT[],
    first_seen_at    TIMESTAMPTZ DEFAULT now(),
    last_verified_at TIMESTAMPTZ DEFAULT now(),
    raw              JSONB
);

CREATE TABLE enrichment_cache (
    company_key      TEXT PRIMARY KEY REFERENCES companies(company_key),
    summary          TEXT,
    signals          JSONB,
    citations        JSONB,
    evidence_hash    TEXT,                       -- dedupe identical evidence
    provider         TEXT,                       -- searxng / opensearch
    refreshed_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON contacts (company_key);
CREATE INDEX ON companies (last_verified_at);
CREATE INDEX ON contacts  (last_verified_at);
```

### 5.4 Merge-on-conflict (dedupe + field-level merge)

```sql
INSERT INTO contacts (contact_key, company_key, full_name, title, email,
                      email_status, linkedin_url, confidence, sources,
                      last_verified_at, raw)
VALUES (...)
ON CONFLICT (contact_key) DO UPDATE SET
    -- keep the better/non-null value, don't overwrite good data with blanks
    title        = COALESCE(EXCLUDED.title, contacts.title),
    email        = COALESCE(EXCLUDED.email, contacts.email),
    email_status = CASE WHEN EXCLUDED.email_status = 'verified'
                        THEN 'verified' ELSE contacts.email_status END,
    confidence   = GREATEST(EXCLUDED.confidence, contacts.confidence),
    sources      = ARRAY(SELECT DISTINCT unnest(contacts.sources || EXCLUDED.sources)),
    last_verified_at = now(),
    raw          = contacts.raw || EXCLUDED.raw;
```

This is the "one clean record per human, merged across sources" behavior.

---

## 6. Cache-first flow with TTL

```python
TTL = timedelta(days=settings.cache_ttl_days)   # default 30

def resolve_contacts(accounts, titles, seniorities):
    fresh, stale_or_missing = [], []
    for acc in accounts:
        cached = repo.contacts_for_company(acc.company_key)
        cached_fresh = [c for c in cached if now() - c.last_verified_at < TTL]
        if cached_fresh:
            fresh += cached_fresh          # served from DB, no API cost
        else:
            stale_or_missing.append(acc)   # needs a provider call

    # Only the gap goes to the waterfall (your "40 from DB, 10 from API" case)
    newly_fetched = contact_waterfall(stale_or_missing, titles, seniorities)
    repo.upsert_contacts(newly_fetched)    # merge-on-conflict, no dupes

    log.info("contacts: %d from cache, %d from API", len(fresh), len(newly_fetched))
    return fresh + newly_fetched
```

Same shape for accounts and for enrichment (cache keyed by `company_key`, TTL by
`refreshed_at`). Enriching all 50 companies is fine — the first run pays SearXNG/
OpenSearch once, and repeat runs are served from `enrichment_cache`.

---

## 7. Config / env (all optional except the DB URL)

```
# Database (phase 1)
SDR_DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/sdr   # Neon
# (the per-agent SDR_*_DATABASE_URL vars can all point at this one)

# Caching (phase 2)
SDR_CACHE_TTL_DAYS=30

# Providers (phase 4) — absent = skipped, no crash
HUNTER_API_KEY=
ZOOMINFO_API_KEY=
SDR_PROVIDER_PRIORITY=zoominfo,apollo,hunter,public
```

Add the DB URL to `start-sdr-backend.ps1` so it is set every run.

---

## 8. Phased implementation plan

| Phase | Goal | Touches | Risk |
|-------|------|---------|------|
| **1** | **Neon/Postgres migration** — swap connection string, install driver, verify tables create and the existing flow still works end-to-end on Postgres. | `config.py`, `start-sdr-backend.ps1`, repositories (no logic change) | Low |
| **2** | **Cache-first reads + TTL** — add `last_verified_at`, check DB before Apollo/SearXNG, fetch only gaps, log cache vs API. | discovery service, repositories | Medium |
| **3** | **Identity resolution + unique constraints** — canonical keys, merge-on-conflict, kill duplicates. | new `identity.py`, schema, repositories | Medium |
| **4** | **Hunter (+ any future provider) in the waterfall** — email-find/verify step, provider registry filters by available keys. | providers, registry, config | Low (additive) |

Each phase is independently shippable and testable. Nothing in phases 2–4
requires Hunter/ZoomInfo keys to exist; they light up automatically when added.

---

## 9. Phase 1 — concrete steps (what we'll do first)

1. Create a Neon project → copy the `postgresql://…` connection string.
2. `pip install psycopg2-binary` (add to `requirements.txt`).
3. Add a single `SDR_DATABASE_URL` in `config.py`; make each `*_database_url`
   fall back to it, so one env var configures every agent's store.
4. Point `start-sdr-backend.ps1` at the Neon URL.
5. Ensure each repository calls `Base.metadata.create_all(engine)` on init (most
   already do) so tables auto-create on Postgres.
6. Smoke test: run the SDR flow, confirm accounts/contacts/enrichment rows land
   in Neon (check via the Neon SQL console) and the UI still works.

No behavior change in phase 1 — it's a pure storage swap that makes phases 2–4
possible (and gives you a hosted DB that survives laptop moves).
