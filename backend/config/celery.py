"""
Celery application for the Hospital Appointment Management System.

Beat schedule:
  send-appointment-reminders  – every hour, on the hour
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# ---------------------------------------------------------------------------
# Celery Beat periodic schedule
# ---------------------------------------------------------------------------

app.conf.beat_schedule = {
    # Runs every hour at minute 0 (e.g. 09:00, 10:00, …)
    "send-appointment-reminders-hourly": {
        "task": "core.tasks.send_appointment_reminder",
        "schedule": crontab(minute=0),
    },
}

app.conf.timezone = "UTC"
