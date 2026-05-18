import datetime
import logging
from django.conf import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def _get_credentials(user):
    """Build and refresh Google credentials for a user."""
    if not user.google_access_token:
        return None
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.GOOGLE_SCOPES,
    )
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            user.google_access_token = creds.token
            user.google_token_expiry = creds.expiry
            user.save(update_fields=['google_access_token', 'google_token_expiry'])
        except Exception as exc:
            logger.error("Failed to refresh Google token for %s: %s", user.email, exc)
            return None
    return creds


def create_calendar_event(user, title: str, date, start_time, end_time, description: str = '') -> str | None:
    """Create a Google Calendar event. Returns the event ID or None on failure."""
    creds = _get_credentials(user)
    if not creds:
        logger.warning("No Google credentials for user %s — skipping calendar event", user.email)
        return None

    try:
        service = build('calendar', 'v3', credentials=creds)

        start_dt = datetime.datetime.combine(date, start_time).isoformat()
        end_dt = datetime.datetime.combine(date, end_time).isoformat()

        event = {
            'summary': title,
            'description': description,
            'start': {'dateTime': start_dt, 'timeZone': 'UTC'},
            'end': {'dateTime': end_dt, 'timeZone': 'UTC'},
        }
        created = service.events().insert(calendarId='primary', body=event).execute()
        return created.get('id')
    except Exception as exc:
        logger.error("Failed to create calendar event for %s: %s", user.email, exc)
        return None


def create_appointment_calendar_events(appointment):
    """Create calendar events for both doctor and patient."""
    slot = appointment.slot
    doctor_user = slot.doctor.user
    patient_user = appointment.patient.user

    doctor_name = f"Dr. {doctor_user.get_full_name()}"
    patient_name = patient_user.get_full_name() or patient_user.username

    # Patient calendar
    patient_event_id = create_calendar_event(
        user=patient_user,
        title=f"Appointment with {doctor_name}",
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        description=f"Medical appointment with {doctor_name}"
    )

    # Doctor calendar
    doctor_event_id = create_calendar_event(
        user=doctor_user,
        title=f"Appointment with {patient_name}",
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        description=f"Patient appointment with {patient_name}"
    )

    if patient_event_id:
        appointment.patient_calendar_event_id = patient_event_id
    if doctor_event_id:
        appointment.doctor_calendar_event_id = doctor_event_id
    if patient_event_id or doctor_event_id:
        appointment.save(update_fields=['patient_calendar_event_id', 'doctor_calendar_event_id'])
