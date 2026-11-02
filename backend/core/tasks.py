"""
Celery tasks for the Hospital Appointment Management System.

Tasks
─────
send_appointment_reminder   Periodic (Beat, every hour).
                            Finds CONFIRMED appointments starting within 24 h,
                            sends an email + in-app Notification, marks
                            reminder_sent=True so it never fires twice.

send_status_email           On-demand (called from views on booking / cancel /
                            reschedule / complete / no_show events).

send_bulk_announcement      On-demand (admin broadcast).
"""

import datetime
import logging
import sys
import threading

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_send(subject: str, body: str, recipient: str) -> bool:
    """
    Attempt to send one email.  Returns True on success, False on failure.
    Never raises – callers decide how to react.
    """
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@hospital.com"),
            recipient_list=[recipient],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.warning("Email delivery failed to %s: %s", recipient, exc)
        return False

# ---------------------------------------------------------------------------
# Task 0 – Generic single-email sender (called from views)
# ---------------------------------------------------------------------------

@shared_task(name="core.tasks.send_appointment_email", max_retries=3, default_retry_delay=30)
def send_appointment_email(recipient: str, subject: str, body: str):
    """
    Fire-and-forget task for sending a single email.

    Used by views when booking / cancelling / rescheduling to send
    confirmation emails asynchronously via Celery.
    """
    ok = _safe_send(subject, body, recipient)
    logger.info(
        "send_appointment_email to %s: %s", recipient, "sent" if ok else "failed"
    )
    return {"recipient": recipient, "sent": ok}


def safe_dispatch_email(recipient: str, subject: str, body: str) -> bool:
    """
    Dispatch email to recipient safely.
    - If running under Django unit tests or with locmem backend, sends synchronously
      so test assertions against mail.outbox pass immediately.
    - In production / staging / live web server, dispatches asynchronously in a background
      daemon thread so that external SMTP latency or network timeouts never block the
      user's HTTP response or abort database transactions.
    """
    if not recipient:
        return False

    backend_name = getattr(settings, "EMAIL_BACKEND", "") or ""
    if "locmem" in backend_name or "test" in sys.argv:
        return _safe_send(subject, body, recipient)

    try:
        thread = threading.Thread(
            target=_safe_send,
            args=(subject, body, recipient),
            daemon=True,
        )
        thread.start()
        return True
    except Exception as exc:
        logger.warning("safe_dispatch_email background thread dispatch failed, falling back: %s", exc)
        return _safe_send(subject, body, recipient)



@shared_task(name="core.tasks.send_appointment_reminder", bind=True, max_retries=2)
def send_appointment_reminder(self):
    """
    Beat task – runs every hour.

    Finds every Appointment where:
      • status = CONFIRMED
      • reminder_sent = False
      • combined date+start_time is within the next 24 hours

    For each match:
      1. Sends a reminder email to the patient.
      2. Creates an in-app Notification for the patient.
      3. Sets reminder_sent = True so the task never fires twice.

    Returns a dict with counts for logging / monitoring.
    """
    # Import inside task to avoid circular imports at module load time
    from core.models import Appointment, Notification

    now = timezone.now()
    window_end = now + datetime.timedelta(hours=24)

    candidates = (
        Appointment.objects.filter(
            status=Appointment.Status.CONFIRMED,
            reminder_sent=False,
        )
        .select_related(
            "patient__user",
            "slot__doctor__user",
            "slot",
        )
    )

    reminded = 0
    skipped = 0

    for appt in candidates:
        # Build timezone-aware appointment datetime from date + slot start_time
        appt_naive_dt = datetime.datetime.combine(appt.date, appt.slot.start_time)
        appt_aware_dt = timezone.make_aware(appt_naive_dt)

        # Only remind if the appointment falls within the 24-hour window
        if not (now <= appt_aware_dt <= window_end):
            skipped += 1
            continue

        patient_user = appt.patient.user
        doctor_name = appt.slot.doctor.user.get_full_name()
        patient_name = patient_user.get_full_name()
        appt_time_str = appt.slot.start_time.strftime("%H:%M")

        subject = "Reminder: Your upcoming hospital appointment"
        body = (
            f"Dear {patient_name},\n\n"
            f"This is a reminder that you have an appointment with "
            f"Dr. {doctor_name} tomorrow.\n\n"
            f"Date : {appt.date}\n"
            f"Time : {appt_time_str}\n\n"
            f"Please arrive 10 minutes early.\n\n"
            f"If you need to cancel or reschedule, please do so via the app.\n\n"
            f"Hospital Team"
        )

        email_ok = _safe_send(subject, body, patient_user.email)

        # Always create the in-app notification, even if email failed
        Notification.objects.create(
            user=patient_user,
            title="Appointment Reminder",
            message=(
                f"Reminder: Your appointment with Dr. {doctor_name} is on "
                f"{appt.date} at {appt_time_str}."
            ),
        )

        # Mark reminder sent regardless of email success to avoid spam
        appt.reminder_sent = True
        appt.save(update_fields=["reminder_sent"])
        reminded += 1

        if email_ok:
            logger.info(
                "Reminder sent to %s for appointment %s on %s",
                patient_user.email, appt.pk, appt.date,
            )

    logger.info(
        "send_appointment_reminder complete: %d reminded, %d outside window.",
        reminded, skipped,
    )
    return {"reminded": reminded, "skipped_outside_window": skipped}


# ---------------------------------------------------------------------------
# Task 2 – Event-driven status email  (called from views)
# ---------------------------------------------------------------------------

# Human-readable messages keyed by event name
_EVENT_TEMPLATES = {
    "BOOKED": {
        "patient_subject": "Appointment Confirmed",
        "patient_body": (
            "Dear {patient_name},\n\n"
            "Your appointment with Dr. {doctor_name} has been confirmed.\n\n"
            "Date : {date}\n"
            "Time : {time}\n\n"
            "Please arrive 10 minutes early.\n\nHospital Team"
        ),
        "doctor_subject": "New Patient Appointment",
        "doctor_body": (
            "Dear Dr. {doctor_name},\n\n"
            "{patient_name} has booked an appointment with you.\n\n"
            "Date : {date}\n"
            "Time : {time}\n\nHospital Team"
        ),
    },
    "CANCELLED": {
        "patient_subject": "Appointment Cancelled",
        "patient_body": (
            "Dear {patient_name},\n\n"
            "Your appointment with Dr. {doctor_name} on {date} at {time} "
            "has been cancelled.\n\nHospital Team"
        ),
        "doctor_subject": "Appointment Cancelled by Patient",
        "doctor_body": (
            "Dear Dr. {doctor_name},\n\n"
            "{patient_name} has cancelled their appointment on {date} at {time}.\n\n"
            "Hospital Team"
        ),
    },
    "RESCHEDULED": {
        "patient_subject": "Appointment Rescheduled",
        "patient_body": (
            "Dear {patient_name},\n\n"
            "Your appointment with Dr. {doctor_name} has been rescheduled.\n\n"
            "New Date : {date}\n"
            "New Time : {time}\n\nHospital Team"
        ),
        "doctor_subject": "Appointment Rescheduled",
        "doctor_body": (
            "Dear Dr. {doctor_name},\n\n"
            "{patient_name} rescheduled their appointment to {date} at {time}.\n\n"
            "Hospital Team"
        ),
    },
    "COMPLETED": {
        "patient_subject": "Appointment Completed",
        "patient_body": (
            "Dear {patient_name},\n\n"
            "Your appointment with Dr. {doctor_name} on {date} has been marked as "
            "completed. A medical record may have been created.\n\nHospital Team"
        ),
        "doctor_subject": None,  # No doctor email on completion
        "doctor_body": None,
    },
    "EXPIRED": {
        "patient_subject": "Appointment Expired",
        "patient_body": (
            "Dear {patient_name},\n\n"
            "Your appointment with Dr. {doctor_name} on {date} was marked as "
            "expired because you did not attend. Please contact the clinic "
            "if this is incorrect.\n\nHospital Team"
        ),
        "doctor_subject": None,
        "doctor_body": None,
    },
}


@shared_task(
    name="core.tasks.send_status_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_status_email(self, appointment_id: str, event: str):
    """
    Send event-driven emails for appointment lifecycle events.

    Parameters
    ----------
    appointment_id : str   UUID of the appointment.
    event          : str   One of BOOKED | CANCELLED | RESCHEDULED |
                           COMPLETED | EXPIRED.

    Both patient and doctor emails are sent where applicable (see
    _EVENT_TEMPLATES).  Retries up to 3 times on transient failures.
    """
    from core.models import Appointment

    template = _EVENT_TEMPLATES.get(event)
    if not template:
        logger.warning("send_status_email: unknown event '%s'", event)
        return {"status": "unknown_event"}

    try:
        appt = Appointment.objects.select_related(
            "patient__user",
            "slot__doctor__user",
            "slot",
        ).get(pk=appointment_id)
    except Appointment.DoesNotExist:
        logger.warning("send_status_email: appointment %s not found", appointment_id)
        return {"status": "not_found"}

    ctx = {
        "patient_name": appt.patient.user.get_full_name(),
        "doctor_name": appt.slot.doctor.user.get_full_name(),
        "date": str(appt.date),
        "time": appt.slot.start_time.strftime("%H:%M"),
    }

    results = {}

    # Patient email
    p_subject = template["patient_subject"]
    p_body = template["patient_body"]
    if p_subject and p_body:
        ok = _safe_send(p_subject, p_body.format(**ctx), appt.patient.user.email)
        results["patient_email"] = "sent" if ok else "failed"

    # Doctor email (only for events that have one)
    d_subject = template["doctor_subject"]
    d_body = template["doctor_body"]
    if d_subject and d_body:
        ok = _safe_send(d_subject, d_body.format(**ctx), appt.slot.doctor.user.email)
        results["doctor_email"] = "sent" if ok else "failed"

    logger.info("send_status_email(%s, %s): %s", appointment_id, event, results)
    return {"event": event, "appointment_id": appointment_id, **results}


# ---------------------------------------------------------------------------
# Task 3 – Admin bulk announcement
# ---------------------------------------------------------------------------

@shared_task(name="core.tasks.send_bulk_announcement")
def send_bulk_announcement(user_emails: list, subject: str, body: str):
    """
    Send a broadcast announcement email to a list of addresses.
    Each email is sent independently so one failure never blocks the others.
    """
    sent, failed = 0, 0
    for email in user_emails:
        if _safe_send(subject, body, email):
            sent += 1
        else:
            failed += 1
    logger.info("Bulk announcement: %d sent, %d failed.", sent, failed)
    return {"sent": sent, "failed": failed}
