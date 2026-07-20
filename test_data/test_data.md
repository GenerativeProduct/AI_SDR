# AI SDR — Test Data Inventory

**Purpose:** This document summarizes the contents of the 10 SQLite databases that back the AI SDR application, and maps each one to the SDR workflow module it supports.

**Headline finding:** All 10 databases contain fully defined table structures, but **every table across every database currently holds 0 records.** No sample data has been generated or loaded yet — the storage layer is initialized and ready, but empty. This is consistent with the app's current state as a frontend prototype with placeholder backend integrations.

---

## Database Summary

| Database | Table(s) | Records | Represents | SDR Module |
|---|---|---|---|---|
| `icp.db` | `icp_versions` | 0 | Saved Ideal Customer Profile definitions and their version history (name, status, criteria) | **ICP Setup** |
| `prospects.db` | `discovered_accounts` | 0 | Companies found during prospecting — industry, size, revenue, tech stack, fit score against the ICP | **Prospect Discovery** |
| `prospects.db` | `discovered_contacts` | 0 | Individual people at discovered companies — title, seniority, contact details, verification status | **Prospect Discovery** |
| `enrichment.db` | `enrichment_results` | 0 | Additional company data pulled in to enrich a discovered account (e.g., firmographic details) | **Prospect Discovery** (enrichment step) |
| `prospect_intelligence.db` | `prospect_intelligence_results` | 0 | Research/insights compiled on a specific account or contact ahead of outreach | **Prospect Intelligence** |
| `prospect_intelligence.db` | `prospect_intelligence_outcomes` | 0 | Tracks whether that intelligence led to a reply, positive reply, meeting, qualification, or opportunity | **Prospect Intelligence** (outcome tracking) |
| `outreach.db` | `outreach_campaigns` | 0 | Outreach campaigns tied to a specific account/contact — status and timestamps | **Outreach Orchestration** |
| `outreach.db` | `outreach_events` | 0 | Individual outreach events (e.g., email opens, clicks, sends) linked to a message | **Outreach Orchestration** |
| `conversations.db` | `sdr_conversations` | 0 | Ongoing conversation threads tied to a campaign, with status tracking | **Outreach Orchestration** (conversation tracking) |
| `qualification.db` | `qualification_results` | 0 | Lead qualification outcomes derived from prospect intelligence for a given account/contact | **Qualification Hub** |
| `meetings.db` | `sdr_meetings` | 0 | Meetings booked from a qualified conversation | **Meeting & CRM** |
| `crm.db` | `sdr_crm_syncs` | 0 | Sync records tracking when/how a meeting was pushed into the CRM | **Meeting & CRM** |
| `follow_up.db` | `sdr_follow_up_plans` | 0 | Planned follow-up actions tied to a campaign | **Meeting & CRM / SDR Analytics** (follow-up workflow) |

---

## What Each Module's Data Represents

**ICP Setup** — Stores the target-customer criteria the SDR system prospects against. Currently no ICP has been saved.

**Prospect Discovery** — Captures companies and people found via prospecting sources, plus any enrichment data added afterward. This is the intended entry point of the pipeline; no accounts or contacts have been discovered yet.

**Prospect Intelligence** — Holds research compiled on a prospect before outreach, and separately tracks whether that research translated into engagement (reply, meeting, qualified lead, opportunity). Both the research and outcome tables are empty.

**Outreach Orchestration** — Manages the campaigns, individual send/engagement events, and conversation threads generated once outreach begins. No campaigns have been launched.

**Qualification Hub** — Stores the qualification verdict once a conversation has progressed far enough to assess fit. No qualification decisions exist yet.

**Meeting & CRM** — Covers meetings booked from qualified conversations and the record of syncing those meetings to an external CRM. No meetings or CRM syncs have occurred.

**SDR Analytics** (implied, not a dedicated database) — Would be expected to aggregate data from the modules above (outcomes, qualification, meetings) rather than owning its own database; `follow_up.db` supports the downstream follow-up planning that analytics would report on.

---

## Interpretation

The data layer is structurally complete — every table needed to run the full SDR workflow (ICP → Discovery → Intelligence → Outreach → Qualification → Meeting/CRM → Follow-up) exists with an appropriate schema (IDs, foreign-key-style linkages, status fields, timestamps, and JSON payload columns for flexible detail storage). However, **no test or production data has been generated in any of the 10 databases**, so end-to-end workflow testing or demoing with realistic records is not yet possible using this snapshot. Populating even a small seed dataset per table (e.g., 1 ICP, a handful of accounts/contacts, one campaign) would be the natural next step to validate the pipeline.
