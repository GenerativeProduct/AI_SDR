from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote
from uuid import uuid4

import httpx

from ai_sdr_platform.src.agents.meeting.models import MeetingBooking


class MeetingProvider(Protocol):
    name: str

    def configured(self) -> bool: ...
    def book(self, meeting: MeetingBooking) -> dict[str, Any]: ...
    def cancel(self, meeting: MeetingBooking, reason: str) -> dict[str, Any]: ...


@dataclass
class DryRunMeetingProvider:
    name: str = "dry_run"

    def configured(self) -> bool:
        return True

    def book(self, meeting: MeetingBooking) -> dict[str, Any]:
        event_id = f"dry-{uuid4()}"
        return {
            "provider_event_id": event_id,
            "meeting_url": f"https://meet.invalid/{event_id}",
            "calendar_url": None,
            "status": "confirmed",
            "mode": "dry_run",
        }

    def cancel(self, meeting: MeetingBooking, reason: str) -> dict[str, Any]:
        return {"cancelled": True, "reason": reason, "mode": "dry_run"}


@dataclass
class GoogleCalendarProvider:
    calendar_id: str
    client_id: str
    client_secret: str
    refresh_token: str
    token_uri: str = "https://oauth2.googleapis.com/token"
    timeout_seconds: float = 30.0
    name: str = "google_calendar"

    def configured(self) -> bool:
        return bool(
            self.calendar_id
            and self.client_id
            and self.client_secret
            and self.refresh_token
        )

    def book(self, meeting: MeetingBooking) -> dict[str, Any]:
        if not meeting.start_at or not meeting.end_at:
            raise ValueError("Meeting start and end are required.")
        token = self._access_token()
        if not self._available(meeting, token):
            raise RuntimeError("The configured calendar is busy during this time.")
        event_id = hashlib.sha256(meeting.meeting_id.encode()).hexdigest()[:32]
        body = {
            "id": event_id,
            "summary": meeting.title,
            "description": meeting.description,
            "start": {
                "dateTime": meeting.start_at.isoformat(),
                "timeZone": meeting.timezone,
            },
            "end": {
                "dateTime": meeting.end_at.isoformat(),
                "timeZone": meeting.timezone,
            },
            "attendees": [
                {
                    "email": str(meeting.attendee_email),
                    "displayName": meeting.contact_name,
                }
            ],
            "conferenceData": {
                "createRequest": {
                    "requestId": meeting.meeting_id,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "extendedProperties": {
                "private": {
                    "sdrMeetingId": meeting.meeting_id,
                    "conversationId": meeting.conversation_id,
                    "campaignId": meeting.campaign_id,
                }
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 60},
                ],
            },
        }
        response = httpx.post(
            (
                "https://www.googleapis.com/calendar/v3/calendars/"
                f"{quote(self.calendar_id, safe='')}/events"
            ),
            params={"conferenceDataVersion": 1, "sendUpdates": "all"},
            headers={"Authorization": f"Bearer {token}"},
            json=body,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        meeting_url = payload.get("hangoutLink") or self._conference_url(payload)
        if not payload.get("id") or not meeting_url:
            raise RuntimeError(
                "Google Calendar did not return both an event ID and Meet URL."
            )
        return {
            "provider_event_id": str(payload["id"]),
            "meeting_url": str(meeting_url),
            "calendar_url": payload.get("htmlLink"),
            "status": payload.get("status"),
            "raw": payload,
        }

    def cancel(self, meeting: MeetingBooking, reason: str) -> dict[str, Any]:
        if not meeting.provider_event_id:
            raise ValueError("Provider event ID is required for cancellation.")
        response = httpx.delete(
            (
                "https://www.googleapis.com/calendar/v3/calendars/"
                f"{quote(self.calendar_id, safe='')}/events/{meeting.provider_event_id}"
            ),
            params={"sendUpdates": "all"},
            headers={"Authorization": f"Bearer {self._access_token()}"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return {"cancelled": True, "reason": reason}

    def _access_token(self) -> str:
        if not self.configured():
            raise RuntimeError("Google Calendar OAuth credentials are incomplete.")
        response = httpx.post(
            self.token_uri,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise RuntimeError("Google OAuth token response had no access_token.")
        return str(token)

    def _available(self, meeting: MeetingBooking, token: str) -> bool:
        response = httpx.post(
            "https://www.googleapis.com/calendar/v3/freeBusy",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "timeMin": meeting.start_at.isoformat(),
                "timeMax": meeting.end_at.isoformat(),
                "timeZone": meeting.timezone,
                "items": [{"id": self.calendar_id}],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        busy = (
            response.json()
            .get("calendars", {})
            .get(self.calendar_id, {})
            .get("busy", [])
        )
        return not busy

    @staticmethod
    def _conference_url(payload: dict[str, Any]) -> str | None:
        for point in payload.get("conferenceData", {}).get("entryPoints", []) or []:
            if point.get("entryPointType") == "video" and point.get("uri"):
                return str(point["uri"])
        return None


@dataclass
class CalComMeetingProvider:
    base_url: str
    api_key: str
    api_version: str
    event_type_id: int
    event_type_slug: str = ""
    username: str = ""
    team_slug: str = ""
    organization_slug: str = ""
    timeout_seconds: float = 30.0
    name: str = "calcom"

    def configured(self) -> bool:
        return bool(
            self.base_url
            and self.api_key
            and (
                self.event_type_id
                or (
                    self.event_type_slug
                    and (self.username or self.team_slug)
                )
            )
        )

    def book(self, meeting: MeetingBooking) -> dict[str, Any]:
        if not self.configured() or not meeting.start_at:
            raise RuntimeError(
                "Cal.com credentials, event type, and start time are required."
            )
        body = {
            "start": meeting.start_at.astimezone().isoformat().replace("+00:00", "Z"),
            "attendee": {
                "name": meeting.contact_name,
                "email": str(meeting.attendee_email),
                "timeZone": meeting.timezone,
                "language": "en",
            },
            "lengthInMinutes": meeting.duration_minutes,
            "metadata": {
                "sdrMeetingId": meeting.meeting_id,
                "conversationId": meeting.conversation_id,
            },
        }
        if self.event_type_id:
            body["eventTypeId"] = self.event_type_id
        else:
            body["eventTypeSlug"] = self.event_type_slug
            if self.username:
                body["username"] = self.username
            if self.team_slug:
                body["teamSlug"] = self.team_slug
            if self.organization_slug:
                body["organizationSlug"] = self.organization_slug
        response = httpx.post(
            f"{self.base_url.rstrip('/')}/v2/bookings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "cal-api-version": self.api_version,
                "Content-Type": "application/json",
            },
            json=body,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", {})
        event_id = data.get("uid") or data.get("id")
        meeting_url = data.get("meetingUrl") or data.get("location")
        if not event_id or not meeting_url:
            raise RuntimeError("Cal.com did not return a booking ID and meeting URL.")
        return {
            "provider_event_id": str(event_id),
            "meeting_url": str(meeting_url),
            "calendar_url": None,
            "status": data.get("status"),
            "raw": payload,
        }

    def cancel(self, meeting: MeetingBooking, reason: str) -> dict[str, Any]:
        if not meeting.provider_event_id:
            raise ValueError("Cal.com booking UID is required for cancellation.")
        response = httpx.post(
            f"{self.base_url.rstrip('/')}/v2/bookings/{meeting.provider_event_id}/cancel",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "cal-api-version": self.api_version,
                "Content-Type": "application/json",
            },
            json={"cancellationReason": reason},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
