from __future__ import annotations

import asyncio
from datetime import timedelta


async def run_worker(
    *,
    target_host: str,
    namespace: str,
    task_queue: str,
    api_base_url: str,
) -> None:
    try:
        from temporalio import activity, workflow
        from temporalio.client import Client
        from temporalio.worker import Worker
    except ImportError as exc:
        raise RuntimeError(
            "Install ai_sdr_platform/requirements-outreach.txt to run Temporal."
        ) from exc

    @activity.defn(name="process_outreach_campaign")
    async def process_outreach_campaign(campaign_id: str) -> None:
        import requests

        response = requests.post(
            f"{api_base_url.rstrip('/')}/outreach/campaigns/{campaign_id}/send",
            timeout=30,
        )
        response.raise_for_status()

    @workflow.defn(name="OutreachSequenceWorkflow")
    class OutreachSequenceWorkflow:
        @workflow.run
        async def run(self, campaign_id: str) -> None:
            await workflow.execute_activity(
                process_outreach_campaign,
                campaign_id,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=None,
            )

    client = await Client.connect(target_host, namespace=namespace)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[OutreachSequenceWorkflow],
        activities=[process_outreach_campaign],
    )
    await worker.run()


def main(
    target_host: str,
    namespace: str,
    task_queue: str,
    api_base_url: str,
) -> None:
    asyncio.run(
        run_worker(
            target_host=target_host,
            namespace=namespace,
            task_queue=task_queue,
            api_base_url=api_base_url,
        )
    )
