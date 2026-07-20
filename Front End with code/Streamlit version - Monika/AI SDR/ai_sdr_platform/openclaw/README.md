# OpenClaw Integration

OpenClaw is an operator interface, not the outreach execution engine. It calls a
restricted API while credentials, policy, approval, sending, audit history, and
provider webhooks remain inside the AI SDR backend.

## Configure

```bash
export SDR_API_BASE_URL=http://127.0.0.1:8000
export SDR_OUTREACH_OPENCLAW_API_KEY=replace-with-a-long-random-secret
```

Install the `skills/sdr-outreach` folder into the OpenClaw skills directory used
by your deployment, then restart its gateway. Do not grant this skill shell,
browser automation, LinkedIn automation, or unrestricted provider credentials.

## Verify

```bash
curl -sS "$SDR_API_BASE_URL/outreach/operator/command" \
  -H "Content-Type: application/json" \
  -H "X-OpenClaw-Key: $SDR_OUTREACH_OPENCLAW_API_KEY" \
  -d '{"action":"list_priority_prospects","limit":5}'
```
