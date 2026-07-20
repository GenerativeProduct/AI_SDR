# AI SDR Platform

Implemented agents:

- ICP Agent
- Enrichment Agent
- Prospect Intelligence: intent, propensity, ranking, and personalization

The Enrichment Agent reuses the existing OpenSearch/SearchXNG/LLM research pipeline, persists structured results in SQLite or Postgres, and exposes a LangGraph workflow node.

Production-shaped AI SDR agent system scaffold inspired by production-grade agentic system layouts.

## Current scope
- Folder structure for a scalable SDR platform
- Only the first agent is implemented: `ICP Agent`
- Deterministic ICP normalization and validation
- FastAPI route scaffold for ICP operations
- LangGraph-ready node wrapper
- Unit and integration tests for the ICP slice

## Why ICP first
ICP is the control layer for the entire SDR workflow. Discovery, enrichment, intent, scoring, and outreach all depend on a clean, validated target definition.

## Initial module layout
- `src/agents/icp/`: ICP agent implementation
- `src/api/routes/`: API routes
- `src/shared/`: shared config, logging, exceptions, types
- `src/workflows/`: workflow state models
- `tests/`: unit and integration tests
- `evals/`, `prometheus/`, `grafana/`: production scaffolding for later phases

## Planned next agents
- Account Discovery
- Contact Discovery
- Enrichment
- Intent
- Lead Scoring
- Personalization
- Outreach
- Follow-Up
- Conversation
- Qualification
- Meeting
- CRM
- Analytics
