# Meeting and CRM Agents

Flow:

`Conversation meeting_request -> Follow-Up stop -> Meeting approval -> Free/Busy check -> Calendar booking -> Meet URL -> CRM sync -> Temporal reminders -> Analytics/MetaRank`

## Guarantees

- A reply asking for a meeting is not recorded as `meeting_booked`.
- `booked` requires a provider event ID and meeting URL.
- Google Calendar is checked with Free/Busy before event creation.
- Calendar creation uses an idempotent event ID and sends attendee updates.
- CRM synchronization is idempotent per local meeting record and can be retried.
- MetaRank receives `meeting_booked` only after provider confirmation.
- Temporal schedules 24-hour and 1-hour reminders.

## Google Calendar and Meet

Create a Google Cloud OAuth desktop client, enable Google Calendar API, download
the client JSON, then run:

```bash
source .venv/bin/activate
pip install -r ai_sdr_platform/requirements-outreach.txt
python ai_sdr_platform/scripts/google_calendar_oauth.py \
  --client-secrets /absolute/path/to/client_secret.json
```

Store the returned secrets in `ai_sdr_platform/.env.sdr`:

```text
SDR_MEETING_PROVIDER=google_calendar
SDR_MEETING_GOOGLE_CALENDAR_ID=primary
SDR_MEETING_GOOGLE_CLIENT_ID=...
SDR_MEETING_GOOGLE_CLIENT_SECRET=...
SDR_MEETING_GOOGLE_REFRESH_TOKEN=...
SDR_MEETING_DEFAULT_TIMEZONE=Asia/Kolkata
SDR_MEETING_DEFAULT_DURATION_MINUTES=30
SDR_MEETING_TEMPORAL_TASK_QUEUE=sdr-meetings
SDR_MEETING_WEBHOOK_SECRET=generate-a-long-random-secret
```

## Twenty CRM

Create a Twenty API key and configure:

```text
SDR_CRM_PROVIDER=twenty
SDR_CRM_TWENTY_BASE_URL=https://your-twenty-host
SDR_CRM_TWENTY_API_KEY=...
SDR_CRM_TWENTY_PEOPLE_OBJECT=people
SDR_CRM_TWENTY_COMPANIES_OBJECT=companies
SDR_CRM_TWENTY_OPPORTUNITIES_OBJECT=opportunities
```

The agent creates a company, person, and opportunity only after the calendar
booking succeeds. Workspace-specific required fields must be added to the
Twenty adapter if the workspace schema makes them mandatory.

## Cal.com alternative

Cal.com can be the booking provider instead of Google:

```text
SDR_MEETING_PROVIDER=calcom
SDR_MEETING_CALCOM_BASE_URL=https://api.cal.com
SDR_MEETING_CALCOM_API_KEY=...
SDR_MEETING_CALCOM_EVENT_TYPE_ID=12345
SDR_MEETING_CALCOM_API_VERSION=2026-02-25
```

If the numeric event type ID is hard to obtain, configure by public booking URL
instead. For a URL like `https://cal.com/sathya/30min`:

```text
SDR_MEETING_CALCOM_EVENT_TYPE_ID=0
SDR_MEETING_CALCOM_USERNAME=sathya
SDR_MEETING_CALCOM_EVENT_TYPE_SLUG=30min
```

Use Google Calendar mode when the platform should directly create a Google Meet
event. Use Cal.com mode when the selected Cal.com event type owns calendar and
video-conference creation.

## Runtime

Start the additional Temporal worker:

```bash
source .venv/bin/activate
set -a
source ai_sdr_platform/.env.sdr
set +a
export SDR_API_BASE_URL=http://127.0.0.1:8011
python -m ai_sdr_platform.src.agents.meeting.temporal_worker
```

Status endpoints:

```text
GET /meetings/status
GET /meetings
GET /crm/status
GET /crm/syncs
POST /meetings/webhooks/provider
```

Configure Cal.com to send booking cancellation and rescheduling webhooks to:

```text
https://your-public-api/meetings/webhooks/provider
```

Include `X-SDR-Webhook-Secret` with the configured shared secret. Google
Calendar attendee updates remain authoritative in Google; direct bookings and
cancellations initiated by this platform are synchronized immediately.
