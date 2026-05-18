import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _call_email_service(trigger: str, payload: dict):
    """POST to the serverless email function running via serverless-offline."""
    url = f"{settings.EMAIL_SERVICE_URL}/email/send"
    try:
        resp = requests.post(url, json={"trigger": trigger, "payload": payload}, timeout=10)
        resp.raise_for_status()
        logger.info("Email service responded: %s", resp.json())
    except requests.RequestException as exc:
        # Log but don't crash — email failure must not break the main flow
        logger.error("Email service call failed: %s", exc)


def send_welcome_email(user):
    _call_email_service("SIGNUP_WELCOME", {
        "email": user.email,
        "name": user.get_full_name() or user.username,
        "role": user.role,
    })


def send_booking_confirmation(appointment):
    patient = appointment.patient.user
    doctor = appointment.slot.doctor.user
    slot = appointment.slot

    _call_email_service("BOOKING_CONFIRMATION", {
        "patient_email": patient.email,
        "patient_name": patient.get_full_name() or patient.username,
        "doctor_email": doctor.email,
        "doctor_name": f"Dr. {doctor.get_full_name()}",
        "date": slot.date.strftime("%Y-%m-%d"),
        "start_time": slot.start_time.strftime("%H:%M"),
        "end_time": slot.end_time.strftime("%H:%M"),
    })
