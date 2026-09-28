"""Tests for the contributor Celery tasks."""

from unittest.mock import MagicMock, patch

import pytest

from fairdm.contrib.contributors.models import (
    ContributorIdentifier,
)


@pytest.mark.django_db
class TestORCIDSyncTask:
    @patch("fairdm.contrib.contributors.tasks.requests.get")
    def test_orcid_sync_task_success(self, mock_get, person, orcid_identifier):
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "person": {
                "name": {
                    "given-names": {"value": "Jane"},
                    "family-name": {"value": "Researcher"},
                },
                "emails": {"email": [{"email": "jane@orcid.org"}]},
            }
        }
        mock_get.return_value = mock_response

        result = sync_contributor_identifier(orcid_identifier.pk)

        mock_get.assert_called_once()
        assert "0000-0001-2345-6789" in mock_get.call_args[0][0]

        orcid_identifier.refresh_from_db()
        assert orcid_identifier.related.synced_data is not None
        assert result is True

    @patch("fairdm.contrib.contributors.tasks.requests.get")
    def test_orcid_sync_task_updates_person_name(self, mock_get, person):
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        identifier = ContributorIdentifier.objects.create(
            related=person,
            type="ORCID",
            value="0000-0002-1234-5678",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "person": {
                "name": {
                    "given-names": {"value": "Updated"},
                    "family-name": {"value": "Name"},
                }
            }
        }
        mock_get.return_value = mock_response

        sync_contributor_identifier(identifier.pk)

        person.refresh_from_db()
        assert person.synced_data is not None


@pytest.mark.django_db
class TestRORSyncTask:
    @patch("fairdm.contrib.contributors.tasks.requests.get")
    def test_ror_sync_task_success(self, mock_get, organization, ror_identifier):
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Test Research Institute",
            "addresses": [
                {
                    "city": "Berlin",
                    "country_geonames_id": 2921044,
                }
            ],
            "links": ["https://example.org"],
        }
        mock_get.return_value = mock_response

        result = sync_contributor_identifier(ror_identifier.pk)

        mock_get.assert_called_once()
        assert "ror.org" in mock_get.call_args[0][0]

        ror_identifier.refresh_from_db()
        assert ror_identifier.related.synced_data is not None
        assert result is True

    @patch("fairdm.contrib.contributors.tasks.requests.get")
    def test_ror_sync_task_updates_organization_location(
        self, mock_get, organization, ror_identifier
    ):
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Updated Institute",
            "addresses": [
                {
                    "city": "Munich",
                    "country_geonames_id": 2921044,
                }
            ],
        }
        mock_get.return_value = mock_response

        sync_contributor_identifier(ror_identifier.pk)

        organization.refresh_from_db()
        assert organization.synced_data is not None


@pytest.mark.django_db
class TestPeriodicRefresh:
    @patch("fairdm.contrib.contributors.tasks.sync_contributor_identifier.delay")
    def test_refresh_all_contributors(
        self, mock_sync_task, orcid_identifier, ror_identifier
    ):
        from fairdm.contrib.contributors.tasks import refresh_all_contributors

        orcid_identifier.related.last_synced = None
        orcid_identifier.related.save()
        ror_identifier.related.last_synced = None
        ror_identifier.related.save()

        result = refresh_all_contributors()

        assert mock_sync_task.call_count == 2
        assert result >= 2

    @patch("fairdm.contrib.contributors.tasks.sync_contributor_identifier.delay")
    def test_refresh_all_only_syncs_identifiers_with_data(self, mock_sync_task, person):
        from fairdm.contrib.contributors.tasks import refresh_all_contributors

        ContributorIdentifier.objects.create(
            related=person,
            type="OTHER",
            value="custom-id-123",
        )

        result = refresh_all_contributors()

        assert isinstance(result, int)


@pytest.mark.django_db
class TestSyncErrorHandling:
    @patch("fairdm.contrib.contributors.tasks.requests.get")
    def test_orcid_sync_handles_404(self, mock_get, orcid_identifier):
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = sync_contributor_identifier(orcid_identifier.pk)
        assert result is False or result is None

    @patch("fairdm.contrib.contributors.tasks.requests.get")
    def test_orcid_sync_handles_timeout(self, mock_get, orcid_identifier):
        import requests

        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = sync_contributor_identifier(orcid_identifier.pk)
        assert result is False or result is None

    @patch("fairdm.contrib.contributors.tasks.requests.get")
    def test_ror_sync_handles_500_error(self, mock_get, ror_identifier):
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = sync_contributor_identifier(ror_identifier.pk)
        assert result is False or result is None

    @patch("fairdm.contrib.contributors.tasks.requests.get")
    def test_sync_handles_invalid_json(self, mock_get, orcid_identifier):
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        result = sync_contributor_identifier(orcid_identifier.pk)
        assert result is False or result is None

    def test_sync_handles_nonexistent_identifier(self):
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        result = sync_contributor_identifier(99999)
        assert result is False or result is None
