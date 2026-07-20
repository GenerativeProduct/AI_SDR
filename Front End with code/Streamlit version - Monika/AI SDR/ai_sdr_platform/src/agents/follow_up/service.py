from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ai_sdr_platform.src.agents.follow_up.models import (
    FollowUpPlan,
    FollowUpPlanRequest,
    FollowUpTouch,
)
from ai_sdr_platform.src.agents.follow_up.repository import SQLAlchemyFollowUpRepository
from ai_sdr_platform.src.agents.follow_up.temporal_workflow import (
    TemporalFollowUpScheduler,
)
from ai_sdr_platform.src.agents.outreach.service import OutreachService
from ai_sdr_platform.src.shared.config import settings


@dataclass
class FollowUpService:
    repository: SQLAlchemyFollowUpRepository
    outreach_service: OutreachService
    scheduler_backend: str = "temporal"

    def create_plan(self, request: FollowUpPlanRequest) -> FollowUpPlan:
        existing = self.repository.get_by_campaign(request.campaign_id)
        if existing:
            return existing
        campaign = self.outreach_service.get_campaign(request.campaign_id)
        if campaign is None:
            raise LookupError("Campaign not found.")
        initial = next(
            (message for message in campaign.messages if message.channel == "email"),
            campaign.messages[0] if campaign.messages else None,
        )
        if initial is None:
            raise ValueError("Campaign has no source message for follow-up generation.")
        now = datetime.now(timezone.utc)
        bodies = [
            (
                f"Hi {campaign.contact_name.split()[0]}, following up in case my earlier note "
                "was relevant. Is improving this area a priority this quarter?"
            ),
            (
                f"Hi {campaign.contact_name.split()[0]}, I will close the loop after this note. "
                "Would it be useful to share a short example tailored to your team?"
            ),
        ]
        touches = [
            FollowUpTouch(
                sequence_order=index + 1,
                delay_hours=delay,
                channel=initial.channel,
                subject=(
                    f"Re: {initial.subject}" if initial.subject
                    else "Following up"
                ),
                body=bodies[min(index, len(bodies) - 1)],
                scheduled_at=now + timedelta(hours=delay),
                status="pending_approval" if request.require_approval else "approved",
            )
            for index, delay in enumerate(request.delays_hours)
        ]
        plan = FollowUpPlan(
            campaign_id=campaign.campaign_id,
            contact_id=campaign.contact_id,
            status="pending_approval" if request.require_approval else "active",
            touches=touches,
        )
        return self.repository.save(plan)

    def approve(self, plan_id: str, approved_by: str) -> FollowUpPlan:
        plan = self._require(plan_id)
        if plan.status != "pending_approval":
            raise ValueError("Only pending follow-up plans can be approved.")
        plan.status = "active"
        plan.approved_by = approved_by
        plan.updated_at = datetime.now(timezone.utc)
        for touch in plan.touches:
            if touch.status == "pending_approval":
                touch.status = "approved"
        plan = self.repository.save(plan)
        return self._start_temporal_schedule(plan)

    def scheduler_status(self):
        from ai_sdr_platform.src.agents.follow_up.models import FollowUpSchedulerStatus

        temporal_enabled = self.scheduler_backend == "temporal"
        return FollowUpSchedulerStatus(
            configured_backend="temporal" if temporal_enabled else "local",
            temporal_enabled=temporal_enabled,
            temporal_host=settings.outreach_temporal_host,
            temporal_namespace=settings.outreach_temporal_namespace,
            temporal_task_queue=settings.outreach_temporal_task_queue,
            detail=(
                "Follow-up approval starts a Temporal workflow. The workflow uses "
                "durable timers and calls the backend when each touch becomes due."
                if temporal_enabled
                else "Follow-up uses the local SQL scheduler endpoint."
            ),
        )

    def process_due(self, *, force: bool = False) -> list[FollowUpPlan]:
        processed = []
        now = datetime.now(timezone.utc)
        for plan in self.repository.list(status="active"):
            processed.append(self._process_plan(plan, force=force, now=now))
        return processed

    def process_plan(self, plan_id: str, *, force: bool = False) -> FollowUpPlan:
        return self._process_plan(self._require(plan_id), force=force)

    def stop_for_campaign(self, campaign_id: str, reason: str) -> FollowUpPlan | None:
        plan = self.repository.get_by_campaign(campaign_id)
        if plan is None or plan.status in {"stopped", "completed"}:
            return plan
        plan.status = "stopped"
        plan.stop_reason = reason
        plan.updated_at = datetime.now(timezone.utc)
        for touch in plan.touches:
            if touch.status in {"pending_approval", "approved", "queued"}:
                touch.status = "suppressed"
        return self.repository.save(plan)

    def list(self, status: str | None = None) -> list[FollowUpPlan]:
        return self.repository.list(status)

    def get(self, plan_id: str) -> FollowUpPlan | None:
        return self.repository.get(plan_id)

    def _require(self, plan_id: str) -> FollowUpPlan:
        plan = self.repository.get(plan_id)
        if plan is None:
            raise LookupError("Follow-up plan not found.")
        return plan

    def _process_plan(
        self,
        plan: FollowUpPlan,
        *,
        force: bool = False,
        now: datetime | None = None,
    ) -> FollowUpPlan:
        now = now or datetime.now(timezone.utc)
        if plan.status != "active":
            return plan
        for touch in plan.touches:
            if touch.status not in {"approved", "queued"}:
                continue
            if not force and touch.scheduled_at > now:
                touch.status = "queued"
                continue
            result = self.outreach_service.send_follow_up(
                campaign_id=plan.campaign_id,
                channel=touch.channel,
                subject=touch.subject,
                body=touch.body,
                sequence_order=touch.sequence_order,
            )
            touch.status = result.status
            touch.provider_message_id = result.provider_message_id
            touch.sent_at = now
        if all(
            touch.status in {"sent", "human_task", "failed", "suppressed"}
            for touch in plan.touches
        ):
            plan.status = "completed"
        plan.updated_at = now
        return self.repository.save(plan)

    def _start_temporal_schedule(self, plan: FollowUpPlan) -> FollowUpPlan:
        if self.scheduler_backend != "temporal":
            plan.scheduler_backend = "local"
            plan.temporal_schedule_status = "not_started"
            return self.repository.save(plan)
        scheduler = TemporalFollowUpScheduler(
            target_host=settings.outreach_temporal_host,
            namespace=settings.outreach_temporal_namespace,
            task_queue=settings.outreach_temporal_task_queue,
        )
        try:
            workflow_id = asyncio.run(scheduler.start(plan.plan_id))
            plan.scheduler_backend = "temporal"
            plan.temporal_workflow_id = workflow_id
            plan.temporal_schedule_status = "started"
            plan.temporal_error = None
        except Exception as exc:
            plan.scheduler_backend = "temporal"
            plan.temporal_schedule_status = "failed"
            plan.temporal_error = str(exc)
        plan.updated_at = datetime.now(timezone.utc)
        return self.repository.save(plan)
