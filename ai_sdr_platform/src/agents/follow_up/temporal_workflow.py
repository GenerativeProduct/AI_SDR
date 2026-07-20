from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from temporalio import activity, workflow


@dataclass
class TemporalFollowUpScheduler:
    target_host: str
    namespace: str
    task_queue: str

    async def start(self, plan_id: str) -> str:
        try:
            from temporalio.client import Client
        except ImportError as exc:
            raise RuntimeError(
                "Temporal support requires ai_sdr_platform/requirements-outreach.txt."
            ) from exc
        client = await Client.connect(self.target_host, namespace=self.namespace)
        handle = await client.start_workflow(
            SDRFollowUpWorkflow.run,
            plan_id,
            id=f"sdr-follow-up-{plan_id}",
            task_queue=self.task_queue,
        )
        return handle.id


@dataclass
class FollowUpActivities:
    api_base_url: str

    @activity.defn(name="get_sdr_follow_up_plan")
    async def get_sdr_follow_up_plan(self, plan_id: str) -> dict[str, Any]:
        import requests

        response = requests.get(
            f"{self.api_base_url.rstrip('/')}/follow-up/plans/{plan_id}",
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    @activity.defn(name="process_sdr_follow_up_plan")
    async def process_sdr_follow_up_plan(self, plan_id: str) -> None:
        import requests

        response = requests.post(
            f"{self.api_base_url.rstrip('/')}/follow-up/scheduler/run-plan/{plan_id}",
            timeout=30,
        )
        response.raise_for_status()


@workflow.defn(name="SDRFollowUpWorkflow")
class SDRFollowUpWorkflow:
    @workflow.run
    async def run(self, plan_id: str) -> None:
        while True:
            plan = await workflow.execute_activity(
                "get_sdr_follow_up_plan",
                plan_id,
                start_to_close_timeout=timedelta(minutes=2),
            )
            if plan.get("status") in {"stopped", "completed", "paused"}:
                return
            pending_times = [
                touch.get("scheduled_at")
                for touch in plan.get("touches", [])
                if touch.get("status") in {"approved", "queued"}
                and touch.get("scheduled_at")
            ]
            if not pending_times:
                return
            next_at = min(
                datetime.fromisoformat(value.replace("Z", "+00:00"))
                for value in pending_times
            )
            now = workflow.now()
            if next_at > now:
                await workflow.sleep(next_at - now)
            await workflow.execute_activity(
                "process_sdr_follow_up_plan",
                plan_id,
                start_to_close_timeout=timedelta(minutes=2),
            )


def workflow_definitions(api_base_url: str):
    activities = FollowUpActivities(api_base_url=api_base_url)
    return (
        SDRFollowUpWorkflow,
        activities.get_sdr_follow_up_plan,
        activities.process_sdr_follow_up_plan,
    )
