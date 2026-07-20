# ICP Agent

The ICP Agent accepts either natural-language targeting, structured filters, or
both. Structured filters are treated as hard constraints and include:

- Target industries and geographies
- Revenue and company-size ranges
- Funding stages and technology-stack signals
- Target job titles and seniority levels
- Pain points and buying signals

The normalized ICP definition carries these filters into Prospect Discovery
while retaining backward compatibility with the original ICP fields.

## Purpose
The ICP Agent is the first SDR agent. It turns rough business targeting input into a normalized, validated Ideal Customer Profile that downstream agents can trust.

## Current V1.5 responsibilities
- Normalize industries and geographies
- Expand persona aliases such as `RevOps`
- Convert employee and revenue bands into structured numeric ranges
- Validate scoring weights and minimum targeting requirements
- Persist ICP definitions with version history
- Support deterministic suggestions and optional LLM-assisted suggestions
- Produce a deterministic ICP definition for later agents

## API
- `POST /icp/validate`
- `POST /icp/suggest`
- `POST /icp`
- `PUT /icp/{icp_id}`
- `GET /icp`
- `GET /icp/{icp_id}`
- `GET /icp/{icp_id}/versions`

## Deterministic + LLM design
The control path remains deterministic:
- validation is strict
- normalization is rule-based
- persisted output is consistent

The LLM path is optional and assistive:
- persona suggestions
- pain point suggestions
- exclusion suggestions
- reasoning text for SDR operators

## Persistence model
- SQLite-backed SQLAlchemy repository for local production-ready persistence
- versioned ICP records
- audit fields for create/update timestamps and actors
- update operations create a new version instead of mutating history
