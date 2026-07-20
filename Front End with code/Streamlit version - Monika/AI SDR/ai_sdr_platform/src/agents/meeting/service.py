from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from ai_sdr_platform.src.agents.crm.models import CRMSyncRequest
from ai_sdr_platform.src.agents.crm.service import CRMService
from ai_sdr_platform.src.agents.meeting.models import (
    MeetingBooking,
    MeetingProviderStatus,
    MeetingScheduleRequest,
)
from ai_sdr_platform.src.agents.meeting.providers import MeetingProvider
from ai_sdr_platform.src.agents.meeting.repository import SQLAlchemyMeetingRepository
from ai_sdr_platform.src.agents.meeting.temporal_workflow import (
    TemporalMeetingScheduler,
)
from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectOutcome
from ai_sdr_platform.src.shared.config import settings


@dataclass
class MeetingService:
    repository: SQLAlchemyMeetingRepository
    provider: MeetingProvider
    conversation_service: object
    outreach_service: object
    crm_service: CRMService
    intelligence_service: object | None = None
    temporal_enabled: bool = True

    def ensure_from_conversation(self, conversation_id: str) -> MeetingBooking:
        existing = self.repository.get_by_conversation(conversation_id)
        if existing:
            return existing
        thread = self._conversation(conversation_id)
        classification = thread.latest_classification
        if not classification or classification.intent != "meeting_request":
            raise ValueError("Conversation is not classified as a meeting request.")
        campaign = self.outreach_service.get_campaign(thread.campaign_id)
        if campaign is None:
            raise LookupError("Outreach campaign not found.")
        attendee_email = next(
            (
                message.recipient
                for message in campaign.messages
                if message.channel == "email" and "@" in message.recipient
            ),
            None,
        )
        if not attendee_email:
            raise ValueError("A real prospect email is required before booking.")
        meeting = MeetingBooking(
            conversation_id=thread.conversation_id,
            campaign_id=thread.campaign_id,
            intelligence_id=thread.intelligence_id,
            account_id=thread.account_id,
            contact_id=thread.contact_id,
            company_name=thread.company_name,
            contact_name=thread.contact_name,
            attendee_email=attendee_email,
            title=f"{thread.company_name} and SDR discovery meeting",
            description=(
                "Meeting requested during the SDR conversation. "
                f"Conversation ID: {thread.conversation_id}"
            ),
            timezone=settings.meeting_default_timezone,
            duration_minutes=settings.meeting_default_duration_minutes,
            provider=self.provider.name,
        )
        return self.repository.save(meeting)

    def approve_and_book(
        self, meeting_id: str, request: MeetingScheduleRequest
    ) -> MeetingBooking:
        meeting = self._require(meeting_id)
        if meeting.status == "booked":
            return meeting
        if meeting.status not in {"awaiting_approval", "failed", "approved"}:
            raise ValueError(f"Meeting cannot be booked from status {meeting.status}.")
        meeting.start_at = request.start_at
        meeting.end_at = request.start_at + timedelta(
            minutes=request.duration_minutes
        )
        meeting.timezone = request.timezone
        meeting.duration_minutes = request.duration_minutes
        meeting.title = request.title or meeting.title
        if request.notes:
            meeting.description = request.notes
        meeting.approved_by = request.approved_by
        meeting.approved_at = datetime.now(timezone.utc)
        meeting.status = "booking"
        meeting.error = None
        meeting.updated_at = datetime.now(timezone.utc)
        self.repository.save(meeting)
        try:
            result = self.provider.book(meeting)
            meeting.provider_event_id = result.get("provider_event_id")
            meeting.meeting_url = result.get("meeting_url")
            meeting.calendar_url = result.get("calendar_url")
            meeting.provider_payload = result
            if not meeting.provider_event_id or not meeting.meeting_url:
                raise RuntimeError(
                    "Provider did not return an event ID and meeting URL."
                )
            meeting.status = "booked"
            meeting.error = None
        except Exception as exc:
            meeting.status = "failed"
            meeting.error = str(exc)
            meeting.updated_at = datetime.now(timezone.utc)
            return self.repository.save(meeting)

        meeting.updated_at = datetime.now(timezone.utc)
        meeting = self.repository.save(meeting)
        meeting = self._sync_crm(meeting)
        meeting = self._start_temporal_reminders(meeting)
        self._record_booking_outcome(meeting)
        return self.repository.save(meeting)

    def cancel(self, meeting_id: str, reason: str) -> MeetingBooking:
        meeting = self._require(meeting_id)
        if meeting.status == "cancelled":
            return meeting
        if meeting.status != "booked":
            raise ValueError("Only booked meetings can be cancelled.")
        self.provider.cancel(meeting, reason)
        meeting.status = "cancelled"
        meeting.error = None
        meeting.provider_payload["cancellation_reason"] = reason
        meeting.updated_at = datetime.now(timezone.utc)
        return self.repository.save(meeting)

    def send_reminder(self, meeting_id: str, reminder_type: str) -> MeetingBooking:
        meeting = self._require(meeting_id)
        if meeting.status != "booked":
            return meeting
        self.outreach_service.send_follow_up(
            campaign_id=meeting.campaign_id,
            channel="email",
            subject=f"Reminder: {meeting.title}",
            body=(
                f"Hi {meeting.contact_name.split()[0]}, this is a {reminder_type} "
                f"reminder for our meeting. Join here: {meeting.meeting_url}"
            ),
            sequence_order=2000 if reminder_type == "24h" else 2001,
        )
        return meeting

    def retry_crm(self, meeting_id: str) -> MeetingBooking:
        meeting = self._require(meeting_id)
        if meeting.status != "booked":
            raise ValueError("CRM synchronization requires a booked meeting.")
        return self._sync_crm(meeting)

    def ingest_provider_event(self, payload: dict[str, Any]) -> MeetingBooking:
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        event_id = str(
            data.get("uid")
            or data.get("id")
            or data.get("bookingUid")
            or payload.get("provider_event_id")
            or ""
        )
        if not event_id:
            raise ValueError("Provider webhook did not include a booking/event ID.")
        meeting = self.repository.get_by_provider_event_id(event_id)
        if meeting is None:
            raise LookupError("Provider event does not match a stored meeting.")
        event_type = str(
            payload.get("triggerEvent")
            or payload.get("event")
            or payload.get("type")
            or data.get("status")
            or ""
        ).lower()
        if "cancel" in event_type:
            meeting.status = "cancelled"
        if "reschedul" in event_type:
            start_raw = data.get("startTime") or data.get("start")
            end_raw = data.get("endTime") or data.get("end")
            if start_raw:
                meeting.start_at = datetime.fromisoformat(
                    str(start_raw).replace("Z", "+00:00")
                )
            if end_raw:
                meeting.end_at = datetime.fromisoformat(
                    str(end_raw).replace("Z", "+00:00")
                )
            meeting.status = "booked"
        meeting_url = data.get("meetingUrl") or data.get("location")
        if meeting_url:
            meeting.meeting_url = str(meeting_url)
        meeting.provider_payload["latest_webhook"] = payload
        meeting.updated_at = datetime.now(timezone.utc)
        return self.repository.save(meeting)

    def list(self, status: str | None = None) -> list[MeetingBooking]:
        return self.repository.list(status)

    def get(self, meeting_id: str) -> MeetingBooking | None:
        return self.repository.get(meeting_id)

    def status(self) -> MeetingProviderStatus:
        crm_status = self.crm_service.status()
        return MeetingProviderStatus(
            provider=self.provider.name,
            configured=self.provider.configured(),
            calendar_id=(
                settings.meeting_google_calendar_id
                if self.provider.name == "google_calendar"
                else None
            ),
            crm_provider=crm_status.provider,
            crm_configured=crm_status.configured,
            detail=(
                "A booking is marked booked only after the provider returns a real "
                "event ID and meeting URL."
            ),
        )

    def _sync_crm(self, meeting: MeetingBooking) -> MeetingBooking:
        sync = self.crm_service.sync(
            CRMSyncRequest(
                meeting_id=meeting.meeting_id,
                account_id=meeting.account_id,
                contact_id=meeting.contact_id,
                company_name=meeting.company_name,
                contact_name=meeting.contact_name,
                contact_email=str(meeting.attendee_email),
                meeting_start=meeting.start_at,
                meeting_url=meeting.meeting_url,
                qualification_status="meeting_booked",
            )
        )
        meeting.crm_sync_id = sync.sync_id
        meeting.crm_sync_status = "synced" if sync.status == "synced" else "failed"
        if sync.error:
            meeting.provider_payload["crm_error"] = sync.error
        meeting.updated_at = datetime.now(timezone.utc)
        return self.repository.save(meeting)

    def _start_temporal_reminders(self, meeting: MeetingBooking) -> MeetingBooking:
        if not meeting.start_at or not self.temporal_enabled:
            return meeting
        scheduler = TemporalMeetingScheduler(
            target_host=settings.outreach_temporal_host,
            namespace=settings.outreach_temporal_namespace,
            task_queue=settings.meeting_temporal_task_queue,
        )
        try:
            meeting.temporal_workflow_id = asyncio.run(
                scheduler.start(meeting.meeting_id, meeting.start_at)
            )
            meeting.temporal_status = "started"
        except Exception as exc:
            meeting.temporal_status = "failed"
            meeting.provider_payload["temporal_error"] = str(exc)
        meeting.updated_at = datetime.now(timezone.utc)
        return self.repository.save(meeting)

    def _record_booking_outcome(self, meeting: MeetingBooking) -> None:
        if self.intelligence_service is None:
            return
        self.intelligence_service.record_outcome(
            ProspectOutcome(
                intelligence_id=meeting.intelligence_id,
                account_id=meeting.account_id,
                contact_id=meeting.contact_id,
                replied=True,
                positive_reply=True,
                meeting_booked=True,
                opportunity_created=meeting.crm_sync_status == "synced",
                source=self.provider.name,
                metadata={
                    "meeting_id": meeting.meeting_id,
                    "provider_event_id": meeting.provider_event_id,
                    "meeting_url": meeting.meeting_url,
                },
            )
        )
        snapshot = self.intelligence_service.get_latest(meeting.contact_id)
        self.intelligence_service.send_ranking_feedback(
            {
                "event": "interaction",
                "id": f"meeting-booked-{meeting.meeting_id}",
                "ranking": (
                    snapshot.ranking.ranking_event_id
                    if snapshot and snapshot.ranking.ranking_event_id
                    else meeting.intelligence_id
                ),
                "user": "meeting-agent",
                "item": meeting.contact_id,
                "type": "meeting_booked",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _conversation(self, conversation_id: str):
        thread = self.conversation_service.get(conversation_id)
        if thread is None:
            raise LookupError("Conversation not found.")
        return thread

    def _require(self, meeting_id: str) -> MeetingBooking:
        meeting = self.repository.get(meeting_id)
        if meeting is None:
            raise LookupError("Meeting request not found.")
        return meeting
