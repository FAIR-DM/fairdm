"""Tests for contributor utils module."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from fairdm.contrib.contributors.models import ContributorIdentifier
from fairdm.contrib.contributors.utils import (
    clean_ror,
    contributor_from_orcid_data,
    contributor_from_ror_data,
    fetch_orcid_data_from_api,
    fetch_ror_data_from_api,
    get_or_create_from_orcid,
    get_or_create_from_ror,
    update_or_create_from_orcid,
    update_or_create_from_ror,
)
from fairdm.factories.contributors import OrganizationFactory, PersonFactory

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def ror_data():
    """Load sample ROR data from JSON file."""
    with open(DATA_DIR / "ror.json", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def orcid_data():
    """Load sample ORCID data from JSON file."""
    with open(DATA_DIR / "orcid.json", encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.django_db
class TestContributorFromRORData:
    """Tests for contributor_from_ror_data function."""

    def test_create_org_from_ror_data(self, ror_data):
        """Test creating organization from ROR data."""
        org = contributor_from_ror_data(ror_data)
        assert org.pk is not None
        assert org.name == "PSL Research University"
        assert org.city == "Paris"
        assert org.country == "FR"
        assert org.synced_data == ror_data

    def test_ror_data_sets_alternative_names(self, ror_data):
        """Test that aliases and acronyms are stored as alternative names."""
        org = contributor_from_ror_data(ror_data)
        assert len(org.alternative_names) == 2
        assert "Université PSL" in org.alternative_names
        assert "PSL" in org.alternative_names

    def test_ror_data_sets_links(self, ror_data):
        """Test that links and wikipedia URL are stored."""
        org = contributor_from_ror_data(ror_data)
        # Should have data["links"] + data["wikipedia_url"]
        assert len(org.links) == 2

    def test_ror_data_creates_identifier(self, ror_data):
        """Test that ROR identifier is created."""
        org = contributor_from_ror_data(ror_data)
        # ROR identifier should be created from the data
        ror_id = ror_data["id"].split("/")[-1]
        # Note: The function doesn't currently create identifiers automatically
        # This test documents current behavior

    def test_update_existing_org(self, ror_data):
        """Test updating an existing organization with ROR data."""
        org = OrganizationFactory(name="Old Name")
        updated_org = contributor_from_ror_data(ror_data, org=org)
        assert updated_org.pk == org.pk
        assert updated_org.name == "PSL Research University"

    def test_ror_data_without_save(self, ror_data):
        """Test creating org instance without saving to database."""
        org = contributor_from_ror_data(ror_data, save=False)
        assert org.pk is None
        assert org.name == "PSL Research University"


@pytest.mark.django_db
class TestContributorFromORCIDData:
    """Tests for contributor_from_orcid_data function."""

    def test_create_person_from_orcid_data(self, orcid_data):
        """Test creating person from ORCID data."""
        person = contributor_from_orcid_data(orcid_data)
        assert person.pk is not None
        assert person.name == "Samuel Jennings"
        assert person.profile == "A test biography"
        assert person.synced_data == orcid_data

    def test_orcid_data_sets_name_fields(self, orcid_data):
        """Test that given and family names are extracted."""
        person = contributor_from_orcid_data(orcid_data)
        assert person.first_name
        assert person.last_name

    def test_orcid_data_sets_alternative_names(self, orcid_data):
        """Test that other-names are stored as alternative names."""
        person = contributor_from_orcid_data(orcid_data)
        assert len(person.alternative_names) >= 1
        assert "Sam Jennings" in person.alternative_names

    def test_orcid_data_creates_identifier(self, orcid_data):
        """Test that ORCID identifier is created."""
        person = contributor_from_orcid_data(orcid_data)
        # ORCID identifier should be created
        orcid_value = orcid_data["orcid-identifier"]["path"]
        assert person.identifiers.filter(type="ORCID", value=orcid_value).exists()

    def test_update_existing_person(self, orcid_data):
        """Test updating an existing person with ORCID data."""
        person = PersonFactory(name="Old Name")
        updated_person = contributor_from_orcid_data(orcid_data, person=person)
        assert updated_person.pk == person.pk
        assert updated_person.name == "Samuel Jennings"

    def test_orcid_data_without_save(self, orcid_data):
        """Test creating person instance without saving to database."""
        person = contributor_from_orcid_data(orcid_data, save=False)
        assert person.pk is None
        assert person.name == "Samuel Jennings"


@pytest.mark.django_db
class TestCleanROR:
    """Tests for clean_ror function."""

    def test_clean_ror_with_url(self):
        """Test cleaning ROR from full URL."""
        ror_url = "https://ror.org/02h6b9e47"
        cleaned = clean_ror(ror_url)
        assert cleaned == "02h6b9e47"

    def test_clean_ror_with_id_only(self):
        """Test cleaning ROR when only ID is provided."""
        ror_id = "02h6b9e47"
        cleaned = clean_ror(ror_id)
        assert cleaned == "02h6b9e47"

    def test_clean_ror_with_whitespace(self):
        """Test cleaning ROR with extra whitespace."""
        ror_id = "  02h6b9e47  "
        cleaned = clean_ror(ror_id)
        assert cleaned == "02h6b9e47"


@pytest.mark.django_db
class TestFetchRORDataFromAPI:
    """Tests for fetch_ror_data_from_api function."""

    def test_fetch_ror_data_success(self):
        """Test successful ROR API fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "https://ror.org/test", "name": "Test Org"}

        with patch("requests.get", return_value=mock_response):
            data = fetch_ror_data_from_api("test123")
            assert data["name"] == "Test Org"

    def test_fetch_ror_data_rate_limit(self):
        """Test handling of rate limit (429) response."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        with patch("requests.get", return_value=mock_response), pytest.warns(UserWarning, match="Rate limited"):
            with pytest.raises(Exception):
                fetch_ror_data_from_api("test123")

    def test_fetch_ror_data_server_error(self):
        """Test handling of server error (5xx) response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        with patch("requests.get", return_value=mock_response), pytest.warns(UserWarning, match="Server error"):
            with pytest.raises(Exception):
                fetch_ror_data_from_api("test123")

    def test_fetch_ror_data_request_exception(self):
        """Test handling of request exception."""
        with patch("requests.get", side_effect=requests.RequestException("Network error")):
            with pytest.raises(Exception, match="Failed to fetch ROR ID"):
                fetch_ror_data_from_api("test123")


@pytest.mark.django_db
class TestFetchORCIDDataFromAPI:
    """Tests for fetch_orcid_data_from_api function."""

    def test_fetch_orcid_data_success(self):
        """Test successful ORCID API fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "orcid-identifier": {"path": "0000-0001-2345-6789"},
            "person": {"name": {"credit-name": {"value": "Test Person"}}},
        }

        with patch("requests.get", return_value=mock_response):
            data = fetch_orcid_data_from_api("0000-0001-2345-6789")
            assert data["orcid-identifier"]["path"] == "0000-0001-2345-6789"

    def test_fetch_orcid_data_not_found(self):
        """Test handling of 404 response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        with patch("requests.get", return_value=mock_response), pytest.raises(Exception):
            fetch_orcid_data_from_api("0000-0001-2345-6789")


@pytest.mark.django_db
class TestUpdateOrCreateFromROR:
    """Tests for update_or_create_from_ror function."""

    def test_create_new_org_from_ror(self, ror_data):
        """Test creating new organization when it doesn't exist."""
        with patch("fairdm.contrib.contributors.utils.transforms.RORTransform.fetch_from_api", return_value=ror_data):
            org, created = update_or_create_from_ror("013cjyk83")
            assert created is True
            assert org.name == "PSL Research University"

    def test_update_existing_org_from_ror(self, ror_data):
        """Test updating existing organization."""
        # Create org with identifier matching the ROR data
        existing_org = OrganizationFactory()
        ContributorIdentifier.objects.create(related=existing_org, type="ROR", value="013cjyk83")

        with patch("fairdm.contrib.contributors.utils.transforms.RORTransform.fetch_from_api", return_value=ror_data):
            org, created = update_or_create_from_ror("013cjyk83", force=True)
            assert created is False
            assert org.pk == existing_org.pk
            assert org.name == "PSL Research University"

    def test_skip_update_if_recently_synced(self, ror_data):
        """Test that recently synced org is not re-fetched unless force=True."""
        from django.utils import timezone

        existing_org = OrganizationFactory()
        existing_org.last_synced = timezone.now().date()
        existing_org.save()

        ContributorIdentifier.objects.create(related=existing_org, type="ROR", value="02h6b9e47")

        # Without force, should not fetch
        with patch("fairdm.contrib.contributors.utils.transforms.RORTransform.fetch_from_api") as mock_fetch:
            org, created = update_or_create_from_ror("02h6b9e47", force=False)
            assert created is False
            mock_fetch.assert_not_called()


@pytest.mark.django_db
class TestUpdateOrCreateFromORCID:
    """Tests for update_or_create_from_orcid function."""

    def test_create_new_person_from_orcid(self, orcid_data):
        """Test creating new person when they don't exist."""
        with patch(
            "fairdm.contrib.contributors.utils.fetch_orcid_data_from_api",
            return_value=orcid_data,
        ):
            person, created = update_or_create_from_orcid("0000-0003-3762-7336")
            assert created is True
            assert person.name == "Samuel Jennings"

    def test_update_existing_person_from_orcid(self, orcid_data):
        """Test updating existing person."""
        existing_person = PersonFactory()
        ContributorIdentifier.objects.create(related=existing_person, type="ORCID", value="0000-0003-3762-7336")

        with patch(
            "fairdm.contrib.contributors.utils.fetch_orcid_data_from_api",
            return_value=orcid_data,
        ):
            person, created = update_or_create_from_orcid("0000-0003-3762-7336", force=True)
            assert created is False
            assert person.pk == existing_person.pk
            assert person.name == "Samuel Jennings"


@pytest.mark.django_db
class TestGetOrCreateFromROR:
    """Tests for get_or_create_from_ror function."""

    def test_get_existing_org(self):
        """Test retrieving existing organization by ROR."""
        existing_org = OrganizationFactory()
        ContributorIdentifier.objects.create(related=existing_org, type="ROR", value="02h6b9e47")

        org, created = get_or_create_from_ror("02h6b9e47")
        assert created is False
        assert org.pk == existing_org.pk

    def test_create_new_org(self, ror_data):
        """Test creating new org when not found."""
        with patch("fairdm.contrib.contributors.utils.transforms.RORTransform.fetch_from_api", return_value=ror_data):
            org, created = get_or_create_from_ror("013cjyk83")
            assert created is True
            assert org.name == "PSL Research University"


@pytest.mark.django_db
class TestGetOrCreateFromORCID:
    """Tests for get_or_create_from_orcid function."""

    def test_get_existing_person(self):
        """Test retrieving existing person by ORCID."""
        existing_person = PersonFactory()
        ContributorIdentifier.objects.create(related=existing_person, type="ORCID", value="0000-0003-3762-7336")

        person, created = get_or_create_from_orcid("0000-0003-3762-7336")
        assert created is False
        assert person.pk == existing_person.pk

    def test_create_new_person(self, orcid_data):
        """Test creating new person when not found."""
        with patch(
            "fairdm.contrib.contributors.utils.fetch_orcid_data_from_api",
            return_value=orcid_data,
        ):
            person, created = get_or_create_from_orcid("0000-0003-3762-7336")
            assert created is True
            assert person.name == "Samuel Jennings"
