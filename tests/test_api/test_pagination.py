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
    def test_default_page_size_is_25(self, api_client, many_public_projects):
        response = api_client.get(reverse("api:project-list"))
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 25

    def test_custom_page_size_respected(self, api_client, many_public_projects):
        response = api_client.get(reverse("api:project-list"), {"page_size": 10})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10

    def test_page_size_capped_at_100(self, api_client, db):
        ProjectFactory.create_batch(110, visibility=Visibility.PUBLIC)
        response = api_client.get(reverse("api:project-list"), {"page_size": 200})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 100

    def test_next_link_present_on_first_page(self, api_client, many_public_projects):
        response = api_client.get(reverse("api:project-list"))
        data = response.json()
        assert data["count"] == 30
        assert data["next"] is not None

    def test_previous_link_none_on_first_page(self, api_client, many_public_projects):
        response = api_client.get(reverse("api:project-list"))
        data = response.json()
        assert data["previous"] is None

    def test_second_page_has_previous_link(self, api_client, many_public_projects):
        response = api_client.get(reverse("api:project-list"), {"page": 2})
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
