from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone

from temporalio import activity, workflow


@activity.defn(name="send_meeting_reminder")
async def send_meeting_reminder(meeting_id: str, reminder_type: str) -> None:
    import httpx

    base_url = os.getenv("SDR_API_BASE_URL", "http://127.0.0.1:8011")
    response = httpx.post(
        f"{base_url.rstrip('/')}/meetings/{meeting_id}/reminders/{reminder_type}",
        timeout=30,
    )
    response.raise_for_status()


@workflow.defn(name="SDRMeetingReminderWorkflow")
class SDRMeetingReminderWorkflow:
    @workflow.run
    async def run(self, meeting_id: str, start_at_iso: str) -> None:
        start_at = datetime.fromisoformat(start_at_iso)
        now = workflow.now()
        for reminder_type, before in (
            ("24h", timedelta(hours=24)),
            ("1h", timedelta(hours=1)),
        ):
            due = start_at - before
            if due > now:
                await workflow.sleep(due - now)
            await workflow.execute_activity(
                send_meeting_reminder,
                args=[meeting_id, reminder_type],
                start_to_close_timeout=timedelta(minutes=2),
            )


async def run_worker() -> None:
    from temporalio.client import Client
    from temporalio.worker import Worker

    from ai_sdr_platform.src.shared.config import settings

    client = await Client.connect(
        settings.outreach_temporal_host,
        namespace=settings.outreach_temporal_namespace,
    )
    worker = Worker(
        client,
        task_queue=settings.meeting_temporal_task_queue,
        workflows=[SDRMeetingReminderWorkflow],
        activities=[send_meeting_reminder],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
