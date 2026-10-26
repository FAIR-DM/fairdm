"""Tests for ``fairdm/backups/signals.py``: the default backup tasks."""

import pytest
from django.conf import settings
from django.urls import reverse
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from fairdm.backups.signals import seed_default_tasks
from fairdm.factories import UserFactory

DATABASE_TASK = "fairdm.backups.tasks.backup_database"
MEDIA_TASK = "fairdm.backups.tasks.backup_media"


@pytest.fixture
def superuser_client(client):
    administrator = UserFactory(is_staff=True, is_superuser=True)
    client.force_login(administrator)
    return client


@pytest.mark.django_db
class TestSeedDefaultTasks:
    @pytest.mark.parametrize("task", [DATABASE_TASK, MEDIA_TASK])
    def test_each_task_exists_once_and_is_enabled(self, task):
        periodic_tasks = PeriodicTask.objects.filter(task=task)

        assert periodic_tasks.count() == 1
        assert periodic_tasks.get().enabled is True

    @pytest.mark.parametrize("task", [DATABASE_TASK, MEDIA_TASK])
    def test_each_task_runs_on_sunday_at_three_in_the_portal_time_zone(self, task):
        crontab = PeriodicTask.objects.get(task=task).crontab

        assert (crontab.minute, crontab.hour, crontab.day_of_week) == ("0", "3", "0")
        assert crontab.day_of_month == "*"
        assert crontab.month_of_year == "*"
        assert str(crontab.timezone) == settings.TIME_ZONE

    def test_running_again_leaves_a_changed_task_unchanged(self):
        periodic_task = PeriodicTask.objects.get(task=DATABASE_TASK)
        monthly = CrontabSchedule.objects.create(
            minute="30", hour="1", day_of_month="1", timezone=settings.TIME_ZONE
        )
        PeriodicTask.objects.filter(pk=periodic_task.pk).update(
            crontab=monthly, enabled=False
        )

        seed_default_tasks()

        periodic_task.refresh_from_db()
        assert periodic_task.enabled is False
        assert periodic_task.crontab == monthly

    def test_a_deleted_task_is_created_again_with_the_default_schedule(self):
        PeriodicTask.objects.filter(task=MEDIA_TASK).delete()

        seed_default_tasks()

        crontab = PeriodicTask.objects.get(task=MEDIA_TASK).crontab
        assert (crontab.minute, crontab.hour, crontab.day_of_week) == ("0", "3", "0")

    def test_running_again_adds_no_second_task_or_schedule(self):
        tasks = PeriodicTask.objects.filter(task__in=[DATABASE_TASK, MEDIA_TASK])
        schedules = CrontabSchedule.objects.count()
        count = tasks.count()

        seed_default_tasks()

        assert tasks.count() == count
        assert CrontabSchedule.objects.count() == schedules


@pytest.mark.django_db
class TestPeriodicTaskAdmin:
    def test_run_selected_tasks_sends_the_database_task(self, superuser_client, mocker):
        sent = mocker.patch("fairdm.backups.tasks.backup_database.apply_async")
        periodic_task = PeriodicTask.objects.get(task=DATABASE_TASK)

        response = superuser_client.post(
            reverse("admin:django_celery_beat_periodictask_changelist"),
            {"action": "run_tasks", "_selected_action": [periodic_task.pk]},
        )

        assert response.status_code == 302
        sent.assert_called_once()

    def test_the_changelist_answers_a_superuser(self, superuser_client):
        response = superuser_client.get(
            reverse("admin:django_celery_beat_periodictask_changelist")
        )

        assert response.status_code == 200
