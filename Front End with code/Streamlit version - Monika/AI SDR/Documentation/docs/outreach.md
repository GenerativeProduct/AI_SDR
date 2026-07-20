# Outreach Agent

Active flow:

`ICP -> Discovery -> Enrichment -> Intent/Propensity -> Queue Ranking -> Personalization -> Outreach Draft`

Pipeline runs create reviewed campaign drafts in `pending_approval`. They never
send automatically.

## Runtime endpoints

- `POST /outreach/campaigns`
- `POST /outreach/campaigns/{id}/approve`
- `POST /outreach/campaigns/{id}/send`
- `POST /outreach/campaigns/{id}/pause`
- `POST /outreach/campaigns/{id}/resume`
- `POST /outreach/campaigns/{id}/cancel`
- `POST /outreach/events`
- `POST /outreach/scheduler/run-due`
- `GET /outreach/performance`
- `POST /outreach/operator/command`

## Safety defaults

- Provider defaults to `dry_run`.
- Approval is required.
- LinkedIn and phone become human tasks.
- Provider credentials remain in backend environment variables.
- Webhook events stop future touches after replies or unsubscribe.
- Duplicate intelligence snapshots do not create duplicate active campaigns.

## Brevo email

```bash
export SDR_OUTREACH_PROVIDER=brevo
export SDR_OUTREACH_BREVO_API_KEY=replace-with-a-new-secret
export SDR_OUTREACH_FROM_EMAIL=verified-sender@your-domain.com
export SDR_OUTREACH_SENDER_NAME="Your SDR Team"
export SDR_OUTREACH_REPLY_TO_EMAIL=replies@your-domain.com
export SDR_OUTREACH_BREVO_WEBHOOK_SECRET=replace-with-a-webhook-secret
```

Configure Brevo transactional webhooks to call
`POST /outreach/events/brevo` and include the webhook secret as
`X-Brevo-Webhook-Secret`. Brevo acceptance means the provider queued the email;
delivery is confirmed later by the `delivered` webhook.

## MetaRank

Set `SDR_INTELLIGENCE_METARANK_URL` and configure
`SDR_INTELLIGENCE_METARANK_MODEL` with a trained SDR ranking model. Until the
service is reachable, queue ranking reports `local` fallback. Product
recommendation models under the repository's existing `metarank/config.yml` are
not valid SDR prospect-ranking models.
