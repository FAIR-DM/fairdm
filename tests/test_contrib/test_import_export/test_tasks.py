"""Tests for fairdm/contrib/import_export/tasks.py."""

from datetime import timedelta
from unittest import mock

import pytest
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from demo.models import RockSample
from fairdm.contrib.import_export import tasks
from fairdm.contrib.import_export.apps import DISCARD_TASK, seed_discard_task
from fairdm.contrib.import_export.models import ImportJob
from fairdm.contrib.import_export.runner import ImportRun
from fairdm.contrib.import_export.undo import ImportUndo
from tests.factories import ImportJobFactory, ImportRowFactory

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

    def test_an_unexpected_error_ends_the_check_as_failed(self, make_job):
        job = make_job([rock("A")])
        with mock.patch.object(ImportRun, "run", side_effect=RuntimeError("boom")):
            tasks.check_job(job.pk)
        job.refresh_from_db()
        assert job.status == Status.FAILED
        assert job.error
        assert "boom" not in job.error

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

    def test_an_unexpected_error_returns_the_job_to_checked(self, make_job):
        job = make_job([rock("A")])
        tasks.check_job(job.pk)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        with mock.patch.object(ImportRun, "run", side_effect=RuntimeError("boom")):
            tasks.import_job(job.pk, None)
        job.refresh_from_db()
        assert job.status == Status.CHECKED
        assert job.error
        assert "boom" not in job.error
        assert job.file
        assert not RockSample.objects.filter(name="A").exists()

    def test_the_person_is_looked_up(self, make_job):
        from fairdm.factories import UserFactory

        user = UserFactory()
        job = make_job([rock("A")])
        tasks.check_job(job.pk)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        tasks.import_job(job.pk, user.pk)
        job.refresh_from_db()
        assert job.imported_by == user


class TestUndoJob:
    """The undo task undoes an import the request has claimed."""

    @pytest.fixture
    def undoing(self, make_job):
        """A job of two new rocks, imported, and then claimed for the undo."""
        job = make_job([rock("A"), rock("B")])
        tasks.check_job(job.pk)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        tasks.import_job(job.pk, None)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.UNDOING)
        job.refresh_from_db()
        return job

    def test_undoes_the_job_and_records_who(self, undoing):
        from fairdm.factories import UserFactory

        user = UserFactory()
        tasks.undo_job(undoing.pk, user.pk)
        undoing.refresh_from_db()
        assert undoing.status == Status.UNDONE
        assert undoing.undone_by == user
        assert not RockSample.objects.filter(dataset=undoing.dataset).exists()

    def test_a_refusal_returns_the_job_to_imported_naming_the_records(self, undoing):
        RockSample.objects.filter(dataset=undoing.dataset).update(rock_type="gabbro")
        tasks.undo_job(undoing.pk, None)
        undoing.refresh_from_db()
        assert undoing.status == Status.IMPORTED
        assert undoing.error
        assert RockSample.objects.filter(dataset=undoing.dataset).count() == 2

    def test_an_unexpected_error_returns_the_job_to_imported_and_is_logged(
        self, undoing
    ):
        with (
            mock.patch.object(ImportUndo, "delete_created", side_effect=ValueError),
            mock.patch.object(tasks.logger, "exception") as logged,
        ):
            tasks.undo_job(undoing.pk, None)
        undoing.refresh_from_db()
        assert undoing.status == Status.IMPORTED
        assert undoing.error
        assert RockSample.objects.filter(dataset=undoing.dataset).count() == 2
        logged.assert_called_once()

    def test_a_time_limit_returns_the_job_to_imported_with_nothing_changed(
        self, undoing
    ):
        from celery.exceptions import SoftTimeLimitExceeded

        with mock.patch.object(
            ImportUndo, "delete_created", side_effect=SoftTimeLimitExceeded
        ):
            tasks.undo_job(undoing.pk, None)
        undoing.refresh_from_db()
        assert undoing.status == Status.IMPORTED
        assert undoing.error
        assert RockSample.objects.filter(dataset=undoing.dataset).count() == 2

    @pytest.mark.parametrize("status", [Status.IMPORTED, Status.UNDONE])
    def test_a_job_that_is_not_undoing_is_left_alone(self, undoing, status):
        ImportJob.objects.filter(pk=undoing.pk).update(status=status)
        tasks.undo_job(undoing.pk, None)
        undoing.refresh_from_db()
        assert undoing.status == status
        assert RockSample.objects.filter(dataset=undoing.dataset).count() == 2

    def test_a_job_that_is_gone_is_ignored(self):
        assert tasks.undo_job(0, None) is None

    def test_the_limits_match_the_other_tasks(self):
        assert tasks.undo_job.soft_time_limit == tasks.IMPORT_LIMITS["soft_time_limit"]
        assert tasks.undo_job.time_limit == tasks.IMPORT_LIMITS["time_limit"]


class TestDiscardStale:
    """An import left unfinished for 30 days is discarded and its file deleted."""

    def old(self, job, days=31):
        """Make the job's upload older by a number of days."""
        ImportJob.objects.filter(pk=job.pk).update(
            created=timezone.now() - timedelta(days=days)
        )
        job.refresh_from_db()
        return job

    @pytest.mark.parametrize(
        "status",
        [
            Status.MATCHING,
            Status.CHECKING,
            Status.CHECKED,
            Status.NOTHING,
            Status.PROBLEMS,
        ],
    )
    def test_an_unfinished_job_is_discarded_and_loses_its_file(self, status):
        job = self.old(ImportJobFactory(with_file=True, status=status))
        stored = job.file.name
        tasks.discard_stale_jobs()
        job.refresh_from_db()
        assert job.status == Status.DISCARDED
        assert not job.file
        assert job.samples == {}
        assert not default_storage.exists(stored)

    def test_the_rows_are_kept(self):
        job = self.old(ImportJobFactory(with_file=True))
        ImportRowFactory(job=job)
        ImportRowFactory(job=job)
        tasks.discard_stale_jobs()
        assert job.rows.count() == 2

    def test_a_younger_job_is_left_alone(self):
        job = self.old(ImportJobFactory(with_file=True), days=29)
        tasks.discard_stale_jobs()
        job.refresh_from_db()
        assert job.status == Status.CHECKED
        assert job.file

    @pytest.mark.parametrize(
        "status",
        [
            Status.IMPORTING,
            Status.UNDOING,
            Status.IMPORTED,
            Status.UNDONE,
            Status.FAILED,
        ],
    )
    def test_a_job_with_a_result_or_at_work_is_left_alone(self, status):
        job = self.old(ImportJobFactory(status=status))
        tasks.discard_stale_jobs()
        job.refresh_from_db()
        assert job.status == status

    def test_it_answers_how_many_it_discarded(self):
        self.old(ImportJobFactory())
        self.old(ImportJobFactory())
        ImportJobFactory()
        assert tasks.discard_stale_jobs() == 2


class TestDiscardSchedule:
    """The daily discard is scheduled once the beat tables exist."""

    def test_the_periodic_task_exists(self):
        assert PeriodicTask.objects.filter(task=DISCARD_TASK, enabled=True).count() == 1

    def test_seeding_again_leaves_a_changed_schedule_unchanged(self):
        scheduled = PeriodicTask.objects.get(task=DISCARD_TASK)
        PeriodicTask.objects.filter(pk=scheduled.pk).update(enabled=False)
        seed_discard_task()
        scheduled.refresh_from_db()
        assert scheduled.enabled is False
        assert PeriodicTask.objects.filter(task=DISCARD_TASK).count() == 1

    def test_seeding_recreates_a_missing_task(self):
        PeriodicTask.objects.filter(task=DISCARD_TASK).delete()
        seed_discard_task()
        assert PeriodicTask.objects.filter(task=DISCARD_TASK).count() == 1
