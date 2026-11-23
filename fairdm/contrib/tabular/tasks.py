"""The check and the import run in the background, so a large file never holds a request."""

import logging

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task
def check_job(job_id):
    from . import engine
    from .models import ImportJob

    job = ImportJob.objects.get(pk=job_id)
    engine.check(job)


@shared_task
def import_job(job_id, user_id):
    from django.contrib.auth import get_user_model

    from . import engine
    from .models import ImportJob

    job = ImportJob.objects.get(pk=job_id)
    user = get_user_model().objects.filter(pk=user_id).first()
    try:
        engine.perform(job, user)
    except Exception as e:
        logger.exception("Import %s failed", job_id)
        job.status = ImportJob.Status.PROBLEMS
        job.error = f"The import stopped and nothing was written: {e}"
        job.save()
        raise


def start(task, *args):
    """Queue a task once the request's changes are saved, or run it here when no worker answers.

    Requests run in a transaction, so a task queued at once can start before the job it reads
    is saved.
    """

    def queue():
        try:
            task.delay(*args)
        except Exception:  # noqa: BLE001
            logger.warning("No Celery broker; running %s in the request", task.name)
            task(*args)

    transaction.on_commit(queue)
