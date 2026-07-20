from __future__ import annotations

from datetime import datetime, timedelta, timezone


class TemporalMeetingScheduler:
    def __init__(self, target_host: str, namespace: str, task_queue: str) -> None:
        self.target_host = target_host
        self.namespace = namespace
        self.task_queue = task_queue

    async def start(self, meeting_id: str, start_at: datetime) -> str:
        from temporalio.client import Client

        from ai_sdr_platform.src.agents.meeting.temporal_worker import (
            SDRMeetingReminderWorkflow,
        )

        client = await Client.connect(self.target_host, namespace=self.namespace)
        workflow_id = f"sdr-meeting-{meeting_id}"
        await client.start_workflow(
            SDRMeetingReminderWorkflow.run,
            args=[meeting_id, start_at.astimezone(timezone.utc).isoformat()],
            id=workflow_id,
            task_queue=self.task_queue,
        )
        return workflow_id
