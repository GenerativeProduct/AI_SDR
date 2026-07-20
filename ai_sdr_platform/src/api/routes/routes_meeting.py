import hmac
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from ai_sdr_platform.src.agents.meeting.models import (
    MeetingBooking,
    MeetingCancelRequest,
    MeetingDraftRequest,
    MeetingListResponse,
    MeetingProviderStatus,
    MeetingScheduleRequest,
)
from ai_sdr_platform.src.agents.meeting.providers import (
    CalComMeetingProvider,
    DryRunMeetingProvider,
    GoogleCalendarProvider,
)
from ai_sdr_platform.src.agents.meeting.repository import SQLAlchemyMeetingRepository
from ai_sdr_platform.src.agents.meeting.service import MeetingService
from ai_sdr_platform.src.api.routes.routes_conversation import (
    get_conversation_service,
)
from ai_sdr_platform.src.api.routes.routes_crm import get_crm_service
from ai_sdr_platform.src.api.routes.routes_outreach import get_outreach_service
from ai_sdr_platform.src.api.routes.routes_prospect_intelligence import (
    get_prospect_intelligence_service,
)
from ai_sdr_platform.src.shared.config import settings

router = APIRouter(prefix="/meetings", tags=["meetings"])
_repository = SQLAlchemyMeetingRepository()


def _provider():
    if settings.meeting_provider == "google_calendar":
        return GoogleCalendarProvider(
            calendar_id=settings.meeting_google_calendar_id,
            client_id=settings.meeting_google_client_id,
            client_secret=settings.meeting_google_client_secret,
            refresh_token=settings.meeting_google_refresh_token,
            token_uri=settings.meeting_google_token_uri,
        )
    if settings.meeting_provider == "calcom":
        return CalComMeetingProvider(
            base_url=settings.meeting_calcom_base_url,
            api_key=settings.meeting_calcom_api_key,
            api_version=settings.meeting_calcom_api_version,
            event_type_id=settings.meeting_calcom_event_type_id,
            event_type_slug=settings.meeting_calcom_event_type_slug,
            username=settings.meeting_calcom_username,
            team_slug=settings.meeting_calcom_team_slug,
            organization_slug=settings.meeting_calcom_organization_slug,
        )
    return DryRunMeetingProvider()


_service = MeetingService(
    repository=_repository,
    provider=_provider(),
    conversation_service=get_conversation_service(),
    outreach_service=get_outreach_service(),
    crm_service=get_crm_service(),
    intelligence_service=get_prospect_intelligence_service(),
)


def configure_meeting_service() -> MeetingService:
    global _service
    _service = MeetingService(
        repository=_repository,
        provider=_provider(),
        conversation_service=get_conversation_service(),
        outreach_service=get_outreach_service(),
        crm_service=get_crm_service(),
        intelligence_service=get_prospect_intelligence_service(),
    )
    return _service


def get_meeting_service() -> MeetingService:
    return _service


@router.get("/status", response_model=MeetingProviderStatus)
def provider_status(
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingProviderStatus:
    return service.status()


@router.post("/requests", response_model=MeetingBooking)
def create_request(
    payload: MeetingDraftRequest,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingBooking:
    try:
        return service.ensure_from_conversation(payload.conversation_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=MeetingListResponse)
def list_meetings(
    status: str | None = Query(default=None),
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingListResponse:
    items = service.list(status)
    return MeetingListResponse(items=items, total=len(items))


@router.get("/{meeting_id}", response_model=MeetingBooking)
def get_meeting(
    meeting_id: str,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingBooking:
    meeting = service.get(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return meeting


@router.post("/{meeting_id}/approve-and-book", response_model=MeetingBooking)
def approve_and_book(
    meeting_id: str,
    payload: MeetingScheduleRequest,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingBooking:
    try:
        meeting = service.approve_and_book(meeting_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if meeting.status == "failed":
        raise HTTPException(status_code=502, detail=meeting.error or "Booking failed.")
    return meeting


@router.post("/{meeting_id}/cancel", response_model=MeetingBooking)
def cancel_meeting(
    meeting_id: str,
    payload: MeetingCancelRequest,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingBooking:
    try:
        return service.cancel(meeting_id, payload.reason)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{meeting_id}/reminders/{reminder_type}", response_model=MeetingBooking)
def send_reminder(
    meeting_id: str,
    reminder_type: str,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingBooking:
    if reminder_type not in {"24h", "1h"}:
        raise HTTPException(status_code=400, detail="Unsupported reminder type.")
    try:
        return service.send_reminder(meeting_id, reminder_type)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{meeting_id}/retry-crm", response_model=MeetingBooking)
def retry_crm(
    meeting_id: str,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingBooking:
    try:
        return service.retry_crm(meeting_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/webhooks/provider", response_model=MeetingBooking)
def provider_webhook(
    payload: dict[str, Any],
    x_sdr_webhook_secret: str | None = Header(default=None),
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingBooking:
    expected = settings.meeting_webhook_secret
    if expected and not hmac.compare_digest(
        x_sdr_webhook_secret or "", expected
    ):
        raise HTTPException(status_code=401, detail="Invalid meeting webhook secret.")
    try:
        return service.ingest_provider_event(payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
