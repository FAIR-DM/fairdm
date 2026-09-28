"""The Celery application for the project."""

from celery import Celery

app = Celery("fairdm")

# A settings path string spares the worker from serializing the configuration object.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
