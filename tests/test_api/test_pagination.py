"""Tests for FairDM API pagination (Feature 011 â€” US1)."""

import pytest
from django.urls import reverse

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import ContributionFactory, ProjectFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def many_public_projects(db):
    return ProjectFactory.create_batch(30, visibility=Visibility.PUBLIC)


@pytest.mark.django_db
class TestPagination:
    def test_custom_page_size_respected(self, api_client, many_public_projects):
        response = api_client.get(reverse("api:project-list"), {"page_size": 10})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10

    def test_next_link_present_on_first_page(self, api_client, many_public_projects):
        response = api_client.get(reverse("api:project-list"), {"page_size": 25})
        data = response.json()
        assert data["count"] == 30
        assert data["next"] is not None

    def test_previous_link_none_on_first_page(self, api_client, many_public_projects):
        response = api_client.get(reverse("api:project-list"), {"page_size": 25})
        data = response.json()
        assert data["previous"] is None

    def test_second_page_has_previous_link(self, api_client, many_public_projects):
        response = api_client.get(
            reverse("api:project-list"), {"page": 2, "page_size": 25}
        )
        data = response.json()
        assert data["previous"] is not None

    def test_last_page_has_no_next_link(self, api_client, many_public_projects):
        response = api_client.get(
            reverse("api:project-list"), {"page": 2, "page_size": 25}
        )
        data = response.json()
        assert data["next"] is None

    def test_count_reflects_accessible_records(self, api_client, db):
        public_count = 5
        ProjectFactory.create_batch(public_count, visibility=Visibility.PUBLIC)
        ProjectFactory.create_batch(3, visibility=Visibility.PRIVATE)
        response = api_client.get(reverse("api:project-list"))
        data = response.json()
        assert data["count"] == public_count

    def test_count_increases_for_authenticated_user_with_permissions(
        self, authenticated_client, user, db
    ):

        public = ProjectFactory.create_batch(3, visibility=Visibility.PUBLIC)
        private = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=private, contributor=user, level=ContributionLevel.VIEW
        )

        response = authenticated_client.get(reverse("api:project-list"))
        data = response.json()
        assert data["count"] == 4


@pytest.mark.django_db
class TestPageSizes:
    @pytest.fixture
    def projects(self, db):
        return ProjectFactory.create_batch(12, visibility=Visibility.PUBLIC)

    @pytest.fixture
    def set_sizes(self, settings):
        """Return a function that changes the default and the largest page size."""

        def set_sizes(default=None, largest=None):
            if default is not None:
                settings.REST_FRAMEWORK = {
                    **settings.REST_FRAMEWORK,
                    "PAGE_SIZE": default,
                }
            if largest is not None:
                settings.FAIRDM_API_MAX_PAGE_SIZE = largest

        return set_sizes

    @staticmethod
    def listed(client, **query):
        response = client.get(reverse("api:project-list"), query)
        assert response.status_code == 200
        return response.json()

    def test_a_list_holds_the_default_number_of_records(self, api_client, settings, db):
        default = settings.REST_FRAMEWORK["PAGE_SIZE"]
        ProjectFactory.create_batch(default + 5, visibility=Visibility.PUBLIC)

        data = self.listed(api_client)

        assert len(data["results"]) == default
        assert data["count"] == default + 5

    def test_the_largest_page_size_is_a_setting(self, settings):
        assert settings.REST_FRAMEWORK["PAGE_SIZE"] <= settings.FAIRDM_API_MAX_PAGE_SIZE

    def test_a_larger_size_is_honoured_up_to_the_ceiling(
        self, api_client, projects, set_sizes
    ):
        set_sizes(default=3, largest=8)

        assert len(self.listed(api_client, page_size=6)["results"]) == 6
        assert len(self.listed(api_client, page_size=8)["results"]) == 8

    def test_a_size_above_the_ceiling_gives_the_ceiling(
        self, api_client, projects, set_sizes
    ):
        set_sizes(default=3, largest=8)

        data = self.listed(api_client, page_size=50)

        assert len(data["results"]) == 8
        assert data["next"] is not None

    def test_a_changed_default_is_followed(self, api_client, projects, set_sizes):
        set_sizes(default=5, largest=20)

        assert len(self.listed(api_client)["results"]) == 5

        set_sizes(default=9)

        assert len(self.listed(api_client)["results"]) == 9

    def test_a_changed_ceiling_is_followed(self, api_client, projects, set_sizes):
        set_sizes(default=3, largest=4)

        assert len(self.listed(api_client, page_size=10)["results"]) == 4

        set_sizes(largest=9)

        assert len(self.listed(api_client, page_size=10)["results"]) == 9

    def test_a_middle_page_has_a_next_and_a_previous_address(
        self, api_client, projects
    ):
        data = self.listed(api_client, page=2, page_size=4)

        assert data["next"] is not None
        assert data["previous"] is not None
        assert len(data["results"]) == 4

    def test_following_next_walks_every_record_once(
        self, api_client, projects, set_sizes
    ):
        set_sizes(default=5)
        seen = []

        response = api_client.get(reverse("api:project-list"))
        while True:
            data = response.json()
            seen += [record["uuid"] for record in data["results"]]
            if data["next"] is None:
                break
            response = api_client.get(data["next"])

        assert sorted(seen) == sorted(project.uuid for project in projects)
