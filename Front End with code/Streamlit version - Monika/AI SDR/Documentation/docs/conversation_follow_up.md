# Conversation and Follow-Up Agents

Active lifecycle:

`Outreach Send -> Provider Events -> Inbound Reply -> Conversation Classification -> Sequence Stop -> Reply Draft -> Human Approval -> Provider Send`

## Conversation Agent

- Persists one thread per outreach campaign.
- Classifies interested, meeting request, pricing request, objection, not now,
  unsubscribe, wrong person, out of office, and ambiguous replies.
- Stops follow-up before drafting a response.
- Produces a reviewable response draft.
- Requires explicit approval before provider delivery.
- Records reply and meeting outcomes for propensity training and MetaRank.

Endpoints:

- `POST /conversations/inbound`
- `POST /conversations/inbound/brevo`
- `GET /conversations`
- `GET /conversations/{id}`
- `POST /conversations/{id}/approve-reply`
- `POST /conversations/{id}/send-reply`

## Follow-Up Agent

- Creates approval-ready future touches after the initial campaign draft.
- Stores due times and lifecycle state in SQL.
- Uses the existing Outreach provider, rate limit, and idempotency controls.
- Stops and suppresses pending touches after reply, unsubscribe, meeting,
  qualification, or operator cancellation.
- Includes an optional Temporal workflow adapter for durable production timers.

Endpoints:

- `POST /follow-up/plans`
- `GET /follow-up/plans`
- `GET /follow-up/plans/{id}`
- `POST /follow-up/plans/{id}/approve`
- `POST /follow-up/scheduler/run-due`

## Brevo

Transactional status webhooks use `/outreach/events/brevo`. Parsed inbound reply
emails use `/conversations/inbound/brevo`. Configure a public HTTPS endpoint and
shared secret:

```bash
export SDR_OUTREACH_BREVO_INBOUND_SECRET=replace-with-a-random-secret
```

## Production scheduling

The local scheduler endpoint makes the complete flow testable without external
services. Install `requirements-outreach.txt` and run Temporal workers for
durable timers, retry policies, cancellation, and crash recovery.
