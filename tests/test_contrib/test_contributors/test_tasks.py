"""Tests for the contributor Celery tasks."""

from datetime import date, timedelta
from email.utils import format_datetime
from unittest.mock import patch

import pytest
import requests
from celery.exceptions import Retry
from django.conf import settings
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from fairdm.contrib.contributors.choices import SyncStatus
from fairdm.contrib.contributors.models import ContributorIdentifier
from fairdm.contrib.contributors.receivers import REFRESH_TASK, seed_refresh_task
from fairdm.contrib.contributors.services.registries import seconds_to_wait
from fairdm.contrib.contributors.tasks import (
    refresh_all_contributors,
    sync_contributor_identifier,
)
from fairdm.core.vocabularies import IDENTIFIER_TYPES

ORCID_ADDRESS = "https://pub.orcid.org/v3.0/0000-0001-2345-6789"
ROR_ADDRESS = "https://api.ror.org/v2/organizations/02nr0ka47"


@pytest.mark.django_db
class TestORCIDSyncTask:
    def test_orcid_sync_task_success(
        self, registry_network, recorded, person, orcid_identifier
    ):
        registry_network.answer(ORCID_ADDRESS, recorded("orcid-record"))

        result = sync_contributor_identifier(orcid_identifier.pk)

        assert result is True
        assert [call.url for call in registry_network.calls] == [ORCID_ADDRESS]
        person.refresh_from_db()
        assert person.synced_data == recorded("orcid-record")
        assert person.last_synced == timezone.now().date()
        assert person.sync_status == SyncStatus.SUCCEEDED
        assert person.sync_error == ""


@pytest.mark.django_db
class TestRORSyncTask:
    def test_ror_sync_task_success(
        self, registry_network, recorded, organization, ror_identifier
    ):
        registry_network.answer(ROR_ADDRESS, recorded("ror-record"))

        result = sync_contributor_identifier(ror_identifier.pk)

        assert result is True
        assert [call.url for call in registry_network.calls] == [ROR_ADDRESS]
        organization.refresh_from_db()
        assert organization.synced_data == recorded("ror-record")
        assert organization.sync_status == SyncStatus.SUCCEEDED

    def test_ror_sync_task_updates_organization_location(
        self, registry_network, recorded, organization, ror_identifier
    ):
        registry_network.answer(ROR_ADDRESS, recorded("ror-record"))

        sync_contributor_identifier(ror_identifier.pk)

        organization.refresh_from_db()
        assert organization.city == "Potsdam"
        assert organization.country.code == "DE"
        assert organization.location.y == pytest.approx(52.39886)
        assert organization.location.x == pytest.approx(13.06566)

    def test_ror_sync_task_keeps_the_portal_name(
        self, registry_network, recorded, organization, ror_identifier
    ):
        registry_network.answer(ROR_ADDRESS, recorded("ror-record"))

        sync_contributor_identifier(ror_identifier.pk)

        organization.refresh_from_db()
        assert organization.name == "Test University"

    def test_ror_sync_task_names_an_organization_that_has_no_name(
        self, registry_network, recorded, organization, ror_identifier
    ):
        organization.name = ""
        organization.save()
        registry_network.answer(ROR_ADDRESS, recorded("ror-record"))

        sync_contributor_identifier(ror_identifier.pk)

        organization.refresh_from_db()
        assert organization.name == "GFZ Helmholtz Centre for Geosciences"


@pytest.mark.django_db
class TestSyncOutcome:
    def test_a_missing_record_is_recorded_as_a_failure(
        self, registry_network, person, orcid_identifier
    ):
        registry_network.answer(ORCID_ADDRESS, {}, status=404)

        result = sync_contributor_identifier(orcid_identifier.pk)

        assert result is False
        person.refresh_from_db()
        assert person.sync_status == SyncStatus.FAILED
        assert person.sync_error
        assert person.last_synced is None

    def test_a_failure_keeps_the_record_and_date_of_the_last_success(
        self, registry_network, person, orcid_identifier
    ):
        person.record_fetch({"person": {}})
        person.last_synced = date(2026, 1, 5)
        person.save()
        registry_network.answer(ORCID_ADDRESS, {}, status=404)

        sync_contributor_identifier(orcid_identifier.pk)

        person.refresh_from_db()
        assert person.sync_status == SyncStatus.FAILED
        assert person.synced_data == {"person": {}}
        assert person.last_synced == date(2026, 1, 5)

    def test_a_success_clears_the_last_failure(
        self, registry_network, recorded, person, orcid_identifier
    ):
        person.record_failed_fetch("ORCID could not be reached.")
        registry_network.answer(ORCID_ADDRESS, recorded("orcid-record"))

        sync_contributor_identifier(orcid_identifier.pk)

        person.refresh_from_db()
        assert person.sync_status == SyncStatus.SUCCEEDED
        assert person.sync_error == ""

    def test_an_unreadable_answer_is_recorded_as_a_failure(
        self, registry_network, person, orcid_identifier
    ):
        registry_network.answer(ORCID_ADDRESS, ValueError("Invalid JSON"))

        result = sync_contributor_identifier(orcid_identifier.pk)

        assert result is False
        person.refresh_from_db()
        assert person.sync_status == SyncStatus.FAILED

    def test_sync_handles_nonexistent_identifier(self):
        assert sync_contributor_identifier(99999) is False


@pytest.fixture
def retry():
    """Stand in for the task's ``retry``, which raises ``Retry`` as Celery's does."""
    with patch.object(
        sync_contributor_identifier, "retry", side_effect=Retry()
    ) as stub:
        yield stub


@pytest.mark.django_db
class TestSyncRetries:
    def test_a_server_error_is_retried_and_recorded(
        self, registry_network, retry, organization, ror_identifier
    ):
        registry_network.answer(ROR_ADDRESS, {}, status=500)

        with pytest.raises(Retry):
            sync_contributor_identifier(ror_identifier.pk)

        assert isinstance(retry.call_args.kwargs["exc"], requests.HTTPError)
        organization.refresh_from_db()
        assert organization.sync_status == SyncStatus.FAILED

    def test_a_timeout_is_retried(self, registry_network, retry, orcid_identifier):
        registry_network.fail(ORCID_ADDRESS, requests.Timeout("timed out"))

        with pytest.raises(Retry):
            sync_contributor_identifier(orcid_identifier.pk)

        assert isinstance(retry.call_args.kwargs["exc"], requests.Timeout)

    def test_a_rate_limit_is_retried_after_the_wait_the_registry_asks_for(
        self, registry_network, retry, person, orcid_identifier
    ):
        registry_network.answer(
            ORCID_ADDRESS, {}, status=429, headers={"Retry-After": "120"}
        )

        with pytest.raises(Retry):
            sync_contributor_identifier(orcid_identifier.pk)

        assert retry.call_args.kwargs["countdown"] == 120
        person.refresh_from_db()
        assert person.sync_status == SyncStatus.FAILED

    def test_a_rate_limit_without_a_wait_is_retried_with_a_growing_delay(
        self, registry_network, retry, orcid_identifier
    ):
        registry_network.answer(ORCID_ADDRESS, {}, status=429)

        with pytest.raises(Retry):
            sync_contributor_identifier(orcid_identifier.pk)

        assert "countdown" not in retry.call_args.kwargs


class TestSecondsToWait:
    def test_reads_a_number_of_seconds(self):
        assert seconds_to_wait("120") == 120

    def test_reads_an_http_date(self):
        until = timezone.now() + timedelta(seconds=120)

        assert 118 <= seconds_to_wait(format_datetime(until, usegmt=True)) <= 120

    @pytest.mark.parametrize("value", [None, "", "soon"])
    def test_a_value_that_says_nothing_is_none(self, value):
        assert seconds_to_wait(value) is None


@pytest.mark.django_db
class TestIdentifierChangeSync:
    def test_a_changed_value_queues_a_sync(
        self, orcid_identifier, django_capture_on_commit_callbacks
    ):
        orcid_identifier.value = "0000-0002-1825-0097"

        with (
            patch(
                "fairdm.contrib.contributors.tasks.sync_contributor_identifier.delay"
            ) as delay,
            django_capture_on_commit_callbacks(execute=True),
        ):
            orcid_identifier.save()

        delay.assert_called_once_with(orcid_identifier.pk)

    def test_a_save_that_changes_nothing_queues_no_sync(
        self, orcid_identifier, django_capture_on_commit_callbacks
    ):
        with (
            patch(
                "fairdm.contrib.contributors.tasks.sync_contributor_identifier.delay"
            ) as delay,
            django_capture_on_commit_callbacks(execute=True),
        ):
            orcid_identifier.save()

        delay.assert_not_called()


@pytest.mark.django_db
class TestPeriodicRefresh:
    @patch("fairdm.contrib.contributors.tasks.sync_contributor_identifier.delay")
    def test_refresh_all_contributors(
        self, mock_sync_task, orcid_identifier, ror_identifier
    ):
        result = refresh_all_contributors()

        assert mock_sync_task.call_count == 2
        assert result == 2

    @patch("fairdm.contrib.contributors.tasks.sync_contributor_identifier.delay")
    def test_refresh_all_only_syncs_identifiers_with_data(self, mock_sync_task, person):
        ContributorIdentifier.objects.create(
            related=person,
            type_id=f"{IDENTIFIER_TYPES}/researcher-id",
            value="custom-id-123",
        )

        assert refresh_all_contributors() == 0
        mock_sync_task.assert_not_called()

    def test_the_refresh_exists_once_and_is_enabled(self):
        periodic_tasks = PeriodicTask.objects.filter(task=REFRESH_TASK)

        assert periodic_tasks.count() == 1
        assert periodic_tasks.get().enabled is True

    def test_the_refresh_runs_weekly_on_monday_at_three(self):
        crontab = PeriodicTask.objects.get(task=REFRESH_TASK).crontab

        assert (crontab.minute, crontab.hour, crontab.day_of_week) == ("0", "3", "1")
        assert (crontab.day_of_month, crontab.month_of_year) == ("*", "*")
        assert str(crontab.timezone) == settings.TIME_ZONE

    def test_seeding_again_leaves_a_changed_refresh_unchanged(self):
        periodic_task = PeriodicTask.objects.get(task=REFRESH_TASK)
        monthly = CrontabSchedule.objects.create(
            minute="30", hour="1", day_of_month="1", timezone=settings.TIME_ZONE
        )
        PeriodicTask.objects.filter(pk=periodic_task.pk).update(
            crontab=monthly, enabled=False
        )

        seed_refresh_task()

        periodic_task.refresh_from_db()
        assert periodic_task.crontab == monthly
        assert periodic_task.enabled is False
        assert PeriodicTask.objects.filter(task=REFRESH_TASK).count() == 1
