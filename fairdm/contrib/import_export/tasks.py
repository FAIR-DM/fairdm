"""The background tasks that check and import an uploaded file.

The portal runs a worker, so a task is only ever queued and never run in place.
"""

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext as _

from .models import ImportJob
from .runner import ImportRun

# A file of 50,000 rows of the widest demo type took 11 minutes to check and 13 to
# import, so each task may run for 40 minutes before it is asked to stop and five more
# before it is killed. See specs/041-records-import/research.md.
CHECK_LIMITS = {"soft_time_limit": 2400, "time_limit": 2700}
IMPORT_LIMITS = {"soft_time_limit": 2400, "time_limit": 2700}


def start(task, *args):
    """Queue a task once the current transaction has committed.

    Nothing is queued when the transaction rolls back, and nothing runs in place when
    no worker is there: the task waits.

    Args:
        task: The Celery task.
        *args: The arguments to queue it with.
    """
    transaction.on_commit(lambda: task.delay(*args))


@shared_task(**CHECK_LIMITS)
def check_job(job_pk):
    """Check a job's file against its dataset.

    A job that is no longer being checked is left alone. A check that runs out of time
    ends the job as failed.

    Args:
        job_pk: The key of the import job.
    """
    job = ImportJob.objects.filter(pk=job_pk).first()
    if job is None or job.status != ImportJob.Status.CHECKING:
        return
    run = ImportRun(job)
    try:
        run.check()
    except SoftTimeLimitExceeded:
        run.fail(_("The check took too long and was stopped."))


@shared_task(**IMPORT_LIMITS)
def import_job(job_pk, user_pk):
    """Import the rows of a checked job.

    An import that runs out of time has written nothing and returns to the check.

    Args:
        job_pk: The key of the import job.
        user_pk: The key of the person who started the import, or None.
    """
    job = ImportJob.objects.filter(pk=job_pk).first()
    if job is None:
        return
    user = get_user_model().objects.filter(pk=user_pk).first()
    run = ImportRun(job)
    try:
        run.perform(user)
    except SoftTimeLimitExceeded:
        run.stop(_("The import took too long and was stopped. Nothing was written."))
