"""
Config package initializer – exposes the Celery app so Django picks it up.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
