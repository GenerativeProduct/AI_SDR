# Qualification Agent

The Qualification Agent runs after Prospect Intelligence and before Outreach:

```text
Enrichment
-> Prospect Intelligence ML probabilities
-> BANT and MEDDIC evidence assessment
-> Hybrid qualification decision
-> Outreach
```

## Purpose

Qualification does not recalculate ICP fit. It determines whether an already
matched prospect has enough commercial evidence to be treated as SQL, MQL,
Nurture, or Disqualified.

The agent adapts the BANT/MEDDIC implementation from Monika's `SALES_AGENT`
branch to the current platform contracts.

## Decision design

- The calibrated LightGBM qualification probability remains the learned signal.
- BANT evaluates budget, authority, need, and timeline evidence.
- MEDDIC evaluates metrics, economic buyer, decision criteria, decision process,
  identified pain, and champion evidence.
- The final score combines the ML probability with framework evidence coverage.
- Missing information is returned explicitly for SDR validation.
- SQL and MQL prospects proceed to Outreach.
- Nurture and Disqualified prospects stop before campaign creation and retain
  an explicit warning and next action in the pipeline response.

## API

```text
POST /qualification/evaluate
GET  /qualification
GET  /qualification/{contact_id}
```

## Pipeline response

`POST /sdr/pipeline/run` now returns `qualification_results` and reports
`summary.prospects_qualified`.

## Storage

Results are persisted with SQLAlchemy. Configure a database with:

```text
SDR_QUALIFICATION_DATABASE_URL
```

SQLite is used by default.
