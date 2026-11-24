"""Tests for fairdm/contrib/import_export/tasks.py."""

from unittest import mock

import pytest
from django.db import transaction

from fairdm.contrib.import_export import tasks
from fairdm.contrib.import_export.models import ImportJob
from fairdm.contrib.import_export.runner import ImportRun

pytestmark = pytest.mark.django_db

Status = ImportJob.Status


def rock(name):
    """Return the cells of a new rock with every required column filled."""
    return {"name": name, "rock_type": "granite", "collection_date": "2024-06-30"}


class TestStart:
    """A task is queued when the transaction commits, never run in place."""

    def test_queues_on_commit(self, django_capture_on_commit_callbacks):
        task = mock.Mock()
        with django_capture_on_commit_callbacks(execute=False) as callbacks:
            tasks.start(task, 7, "x")
            task.delay.assert_not_called()
        assert len(callbacks) == 1
        callbacks[0]()
        task.delay.assert_called_once_with(7, "x")

    def test_queues_nothing_when_the_transaction_rolls_back(self):
        task = mock.Mock()
        with pytest.raises(RuntimeError), transaction.atomic():
            tasks.start(task, 1)
            raise RuntimeError
        task.delay.assert_not_called()
        task.assert_not_called()

    def test_never_runs_the_task_in_place(self, django_capture_on_commit_callbacks):
        task = mock.Mock()
        with django_capture_on_commit_callbacks(execute=True):
            tasks.start(task, 1)
        task.assert_not_called()
        task.run.assert_not_called()


class TestCheckJob:
    """The check task runs the check and answers a time limit."""

    def test_checks_the_job(self, make_job):
        job = make_job([rock("A")])
        tasks.check_job(job.pk)
        job.refresh_from_db()
        assert job.status == Status.CHECKED

    def test_a_time_limit_ends_the_check_as_failed(self, make_job):
        from celery.exceptions import SoftTimeLimitExceeded

        job = make_job([rock("A")])
        with mock.patch.object(ImportRun, "check", side_effect=SoftTimeLimitExceeded):
            tasks.check_job(job.pk)
        job.refresh_from_db()
        assert job.status == Status.FAILED
        assert job.error
        assert not job.file

    def test_a_job_that_is_gone_is_ignored(self):
        assert tasks.check_job(0) is None


class TestImportJob:
    """The import task runs the import and answers a time limit."""

    def test_imports_the_job(self, make_job):
        job = make_job([rock("A")])
        tasks.check_job(job.pk)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        tasks.import_job(job.pk, None)
        job.refresh_from_db()
        assert job.status == Status.IMPORTED

    def test_a_time_limit_returns_the_job_to_checked(self, make_job):
        from celery.exceptions import SoftTimeLimitExceeded

        job = make_job([rock("A")])
        tasks.check_job(job.pk)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        with mock.patch.object(ImportRun, "perform", side_effect=SoftTimeLimitExceeded):
            tasks.import_job(job.pk, None)
        job.refresh_from_db()
        assert job.status == Status.CHECKED
        assert job.error
        assert job.file

    def test_the_person_is_looked_up(self, make_job):
        from fairdm.factories import UserFactory

        user = UserFactory()
        job = make_job([rock("A")])
        tasks.check_job(job.pk)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        tasks.import_job(job.pk, user.pk)
        job.refresh_from_db()
        assert job.imported_by == user
