# Prospect Intelligence

Prospect Intelligence is the production handoff between Enrichment and Outreach:

```text
Enrichment evidence
-> normalized signals
-> intent probability
-> reply, meeting, and qualification propensity
-> prospect ranking
-> grounded multi-channel personalization
-> BANT/MEDDIC qualification
-> Outreach
```

## What it consumes

- Account Discovery `fit_score`
- Contact Discovery `persona_match_score` and identity confidence
- Enrichment signals, confidence, citations, pain-point hypotheses, and contact briefs
- Optional ICP definition for audit context

It does not recalculate account or persona fit.

## Runtime behavior

- Enrichment signals are normalized to a canonical taxonomy.
- Signal strength includes confidence, source reliability, verification, and recency.
- Trained calibrated model artifacts are used when configured.
- Otherwise, estimates are explicitly returned as `mode=heuristic` and `calibrated=false`.
- Personalization uses the configured LLM router with deterministic fallback.
- MetaRank is optional and falls back to local ordering if unavailable.
- Complete intelligence snapshots and outcome labels are persisted.

## API

```text
POST /prospect-intelligence/analyze
GET  /prospect-intelligence
GET  /prospect-intelligence/{contact_id}
POST /prospect-intelligence/outcomes
POST /prospect-intelligence/models/train
```

## Model configuration

```text
SDR_INTELLIGENCE_DATABASE_URL
SDR_INTELLIGENCE_REPLY_MODEL_PATH
SDR_INTELLIGENCE_REPLY_MODEL_VERSION
SDR_INTELLIGENCE_MEETING_MODEL_PATH
SDR_INTELLIGENCE_MEETING_MODEL_VERSION
SDR_INTELLIGENCE_QUALIFICATION_MODEL_PATH
SDR_INTELLIGENCE_QUALIFICATION_MODEL_VERSION
SDR_INTELLIGENCE_METARANK_URL
SDR_INTELLIGENCE_METARANK_MODEL
SDR_INTELLIGENCE_MLFLOW_TRACKING_URI
SDR_INTELLIGENCE_MONITOR_PATH
```

Install optional ML dependencies from `ai_sdr_platform/requirements-ml.txt`.

## Production promotion

1. Capture outreach outcomes using `/prospect-intelligence/outcomes`.
2. Collect both positive and negative reply, meeting, and qualification labels.
3. Train models through `/prospect-intelligence/models/train`.
4. Review Brier score, ROC AUC, calibration by segment, and temporal holdout results.
5. Configure approved artifact paths and versions.
6. Enable MetaRank only after ranking and interaction feedback exists.
7. Feed monitoring events into Evidently for feature, prediction, and calibration drift.
8. Introduce Feast when online scoring and historical training require point-in-time feature consistency.
