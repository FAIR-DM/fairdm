"""Demo portal project configuration."""

from fairdm.conf.celery import app as celery_app

# Imported at startup so `shared_task` binds to this app.
__all__ = ("celery_app",)
