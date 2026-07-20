from __future__ import annotations

import asyncio
import os

from ai_sdr_platform.src.agents.follow_up.temporal_workflow import (
    workflow_definitions,
)
from ai_sdr_platform.src.shared.config import settings


async def run_worker(
    *,
    target_host: str,
    namespace: str,
    task_queue: str,
    api_base_url: str,
) -> None:
    try:
        from temporalio.client import Client
        from temporalio.worker import Worker
    except ImportError as exc:
        raise RuntimeError(
            "Temporal support requires ai_sdr_platform/requirements-outreach.txt."
        ) from exc

    workflow_cls, get_plan_activity, process_plan_activity = workflow_definitions(
        api_base_url
    )
    client = await Client.connect(target_host, namespace=namespace)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[workflow_cls],
        activities=[get_plan_activity, process_plan_activity],
    )
    await worker.run()


def main(
    target_host: str | None = None,
    namespace: str | None = None,
    task_queue: str | None = None,
    api_base_url: str | None = None,
) -> None:
    asyncio.run(
        run_worker(
            target_host=target_host or settings.outreach_temporal_host,
            namespace=namespace or settings.outreach_temporal_namespace,
            task_queue=task_queue or settings.outreach_temporal_task_queue,
            api_base_url=api_base_url
            or os.getenv("SDR_API_BASE_URL")
            or "http://127.0.0.1:8011",
        )
    )


if __name__ == "__main__":
    main()
