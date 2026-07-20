from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TemporalOutreachScheduler:
    target_host: str
    namespace: str
    task_queue: str

    async def start_campaign(self, campaign_id: str) -> str:
        try:
            from temporalio.client import Client
        except ImportError as exc:
            raise RuntimeError(
                "Temporal support requires the optional temporalio dependency."
            ) from exc
        client = await Client.connect(self.target_host, namespace=self.namespace)
        handle = await client.start_workflow(
            "OutreachSequenceWorkflow",
            campaign_id,
            id=f"outreach-{campaign_id}",
            task_queue=self.task_queue,
        )
        return handle.id
