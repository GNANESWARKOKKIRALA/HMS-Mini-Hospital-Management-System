"""
Serverless Email Function — handler.py
Triggered via HTTP POST. Supports:
  - SIGNUP_WELCOME
  - BOOKING_CONFIRMATION
"""

import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ─── SMTP Config (set via environment variables) ───────────────────────────────
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.environ.get("FROM_NAME", "HMS Hospital System")


# ─── Email Templates ───────────────────────────────────────────────────────────

def build_welcome_email(payload: dict) -> tuple[str, str, str]:
    """Returns (to_email, subject, html_body)."""
    name = payload.get("name", "User")
    role = payload.get("role", "user")
    email = payload["email"]

    subject = "Welcome to HMS — Your Account is Ready"
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:auto;padding:32px;background:#f9fafb;border-radius:12px;">
        <h2 style="color:#1a56db;">Welcome to HMS, {name}! 🏥</h2>
        <p>Your <strong>{role}</strong> account has been created successfully.</p>
        <p>You can now log in at <a href="http://localhost:8000">localhost:8000</a>.</p>
        <hr style="margin:24px 0;border:none;border-top:1px solid #e2e8f0;">
        <p style="color:#718096;font-size:0.85rem;">Hospital Management System — automated email</p>
    </div>
    """
    return email, subject, html


def build_booking_email(payload: dict) -> list[tuple[str, str, str]]:
    """Returns list of (to_email, subject, html_body) — one per recipient."""
    patient_email = payload["patient_email"]
    patient_name = payload["patient_name"]
    doctor_email = payload["doctor_email"]
    doctor_name = payload["doctor_name"]
    date = payload["date"]
    start_time = payload["start_time"]
    end_time = payload["end_time"]

    results = []

    # Patient email
    patient_subject = f"Appointment Confirmed — {doctor_name} on {date}"
    patient_html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:auto;padding:32px;background:#f9fafb;border-radius:12px;">
        <h2 style="color:#38a169;">✅ Appointment Confirmed</h2>
        <p>Hi {patient_name},</p>
        <p>Your appointment with <strong>{doctor_name}</strong> has been confirmed.</p>
        <table style="margin:20px 0;background:white;border-radius:8px;padding:16px;width:100%;">
            <tr><td style="color:#718096;">Date</td><td><strong>{date}</strong></td></tr>
            <tr><td style="color:#718096;">Time</td><td><strong>{start_time} – {end_time}</strong></td></tr>
            <tr><td style="color:#718096;">Doctor</td><td><strong>{doctor_name}</strong></td></tr>
        </table>
        <p style="color:#718096;font-size:0.85rem;">Hospital Management System — automated email</p>
    </div>
    """
    results.append((patient_email, patient_subject, patient_html))

    # Doctor email
    doctor_subject = f"New Appointment — {patient_name} on {date}"
    doctor_html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:auto;padding:32px;background:#f9fafb;border-radius:12px;">
        <h2 style="color:#1a56db;">📅 New Appointment Booked</h2>
        <p>Hi {doctor_name},</p>
        <p>A new appointment has been booked by <strong>{patient_name}</strong>.</p>
        <table style="margin:20px 0;background:white;border-radius:8px;padding:16px;width:100%;">
            <tr><td style="color:#718096;">Date</td><td><strong>{date}</strong></td></tr>
            <tr><td style="color:#718096;">Time</td><td><strong>{start_time} – {end_time}</strong></td></tr>
            <tr><td style="color:#718096;">Patient</td><td><strong>{patient_name}</strong></td></tr>
        </table>
        <p style="color:#718096;font-size:0.85rem;">Hospital Management System — automated email</p>
    </div>
    """
    results.append((doctor_email, doctor_subject, doctor_html))
    return results


# ─── SMTP Sender ───────────────────────────────────────────────────────────────

def send_email(to_email: str, subject: str, html_body: str):
    """Send a single HTML email via SMTP."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[EMAIL-SERVICE] SMTP not configured — would have sent to {to_email}: {subject}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.sendmail(FROM_EMAIL, to_email, msg.as_string())

    print(f"[EMAIL-SERVICE] Email sent to {to_email}: {subject}")


# ─── Lambda Handler ────────────────────────────────────────────────────────────

def send(event, context):
    """
    HTTP POST /email/send
    Body: { "trigger": "SIGNUP_WELCOME" | "BOOKING_CONFIRMATION", "payload": { ... } }
    """
    try:
        body = json.loads(event.get("body") or "{}")
        trigger = body.get("trigger")
        payload = body.get("payload", {})

        if not trigger or not payload:
            return _response(400, {"error": "Missing trigger or payload"})

        if trigger == "SIGNUP_WELCOME":
            to_email, subject, html = build_welcome_email(payload)
            send_email(to_email, subject, html)
            return _response(200, {"status": "sent", "trigger": trigger, "to": to_email})

        elif trigger == "BOOKING_CONFIRMATION":
            emails = build_booking_email(payload)
            sent_to = []
            for to_email, subject, html in emails:
                send_email(to_email, subject, html)
                sent_to.append(to_email)
            return _response(200, {"status": "sent", "trigger": trigger, "to": sent_to})

        else:
            return _response(400, {"error": f"Unknown trigger: {trigger}"})

    except Exception as exc:
        print(f"[EMAIL-SERVICE] Error: {exc}")
        return _response(500, {"error": str(exc)})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
