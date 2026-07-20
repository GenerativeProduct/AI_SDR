---
name: sdr-outreach
description: Safely operate the AI SDR outreach service through its restricted API.
---

# SDR Outreach Operator

Use only the controlled AI SDR operator endpoint:

- Base URL: `SDR_API_BASE_URL`
- API key: `SDR_OUTREACH_OPENCLAW_API_KEY`
- Endpoint: `POST /outreach/operator/command`
- Header: `X-OpenClaw-Key`

Supported actions:

- `run_sdr_pipeline`
- `list_priority_prospects`
- `draft_outreach`
- `approve_campaign`
- `send_campaign`
- `pause_campaign`
- `show_attention_replies`
- `performance_summary`
- `list_conversations`
- `approve_conversation_reply`
- `send_conversation_reply`
- `list_follow_up_plans`
- `approve_follow_up_plan`
- `run_due_follow_ups`

Rules:

1. Never send a campaign before the user explicitly approves it.
2. Never browse or automate LinkedIn. LinkedIn work is returned as a human task.
3. Never expose provider credentials or the OpenClaw API key.
4. Never execute arbitrary shell commands for outreach.
5. Confirm campaign ID, recipient, channel, subject, and body before approval.
6. Use `send_campaign` only after the campaign status is `approved`.
7. Respect pause, unsubscribe, suppression, rate-limit, and compliance results.
8. Show the classified intent and drafted reply before approving a conversation response.
9. Never resume or send follow-ups after an unsubscribe, reply, meeting request, or suppression.
10. Use `run_sdr_pipeline` when the user wants ICP, discovery, enrichment, prospect intelligence, outreach drafts, and follow-up plans generated in one controlled flow.

Example request:

```bash
curl -sS "$SDR_API_BASE_URL/outreach/operator/command" \
  -H "Content-Type: application/json" \
  -H "X-OpenClaw-Key: $SDR_OUTREACH_OPENCLAW_API_KEY" \
  -d '{"action":"performance_summary","actor":"openclaw-operator"}'
```

Full pipeline example:

```bash
curl -sS "$SDR_API_BASE_URL/outreach/operator/command" \
  -H "Content-Type: application/json" \
  -H "X-OpenClaw-Key: $SDR_OUTREACH_OPENCLAW_API_KEY" \
  -d '{
    "action": "run_sdr_pipeline",
    "actor": "openclaw-operator",
    "discovery_limit": 5,
    "enrich_top_accounts": 3,
    "icp_payload": {
      "name": "US mid-market SaaS RevOps ICP",
      "industry": "B2B SaaS",
      "company_size": "50-500 employees",
      "geography": "United States",
      "target_personas": ["VP Sales", "Head of RevOps", "Sales Operations"],
      "pain_points": ["manual prospecting", "low reply rates", "slow SDR research"],
      "value_proposition": "AI SDR platform that finds, enriches, scores, personalizes, and follows up with high-intent prospects",
      "exclusions": ["students", "agencies", "companies under 20 employees"]
    }
  }'
```
