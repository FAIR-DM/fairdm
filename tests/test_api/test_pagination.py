"""Tests for FairDM API pagination (Feature 011 — US1).

Covers:
- Default page_size=25
- Custom ?page_size=N is respected
- ?page_size above max (100) is capped at 100
- Response includes next/previous navigation links when applicable
- count reflects total accessible records
"""

import pytest
from django.urls import reverse

from fairdm.factories import ProjectFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def many_public_projects(db):
    """Create 30 public projects to test pagination (default page_size=25)."""
    return ProjectFactory.create_batch(30, visibility=Visibility.PUBLIC)


@pytest.mark.django_db
class TestPagination:
    """Pagination behaviour for list endpoints."""

    def test_default_page_size_is_25(self, api_client, many_public_projects):
        response = api_client.get(reverse("project-list"))
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 25

    def test_custom_page_size_respected(self, api_client, many_public_projects):
        response = api_client.get(reverse("project-list"), {"page_size": 10})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10

    def test_page_size_capped_at_100(self, api_client, db):
        """Requesting page_size=200 must be silently capped at max_page_size=100."""
        ProjectFactory.create_batch(110, visibility=Visibility.PUBLIC)
        response = api_client.get(reverse("project-list"), {"page_size": 200})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 100

    def test_next_link_present_on_first_page(self, api_client, many_public_projects):
        response = api_client.get(reverse("project-list"))
        data = response.json()
        assert data["count"] == 30
        assert data["next"] is not None

    def test_previous_link_none_on_first_page(self, api_client, many_public_projects):
        response = api_client.get(reverse("project-list"))
        data = response.json()
        assert data["previous"] is None

    def test_second_page_has_previous_link(self, api_client, many_public_projects):
        response = api_client.get(reverse("project-list"), {"page": 2})
        data = response.json()
        assert data["previous"] is not None

    def test_last_page_has_no_next_link(self, api_client, many_public_projects):
        response = api_client.get(reverse("project-list"), {"page": 2, "page_size": 25})
        data = response.json()
        # Page 2 with page_size=25 should be the last page (5 items)
        assert data["next"] is None

    def test_count_reflects_accessible_records(self, api_client, db):
        """count must reflect only publicly accessible records for anonymous users."""
        public_count = 5
        ProjectFactory.create_batch(public_count, visibility=Visibility.PUBLIC)
        ProjectFactory.create_batch(3, visibility=Visibility.PRIVATE)
        response = api_client.get(reverse("project-list"))
        data = response.json()
        assert data["count"] == public_count

    def test_count_increases_for_authenticated_user_with_permissions(self, authenticated_client, user, db):
        """Authenticated user with guardian view permission sees private records."""
        from guardian.shortcuts import assign_perm

        public = ProjectFactory.create_batch(3, visibility=Visibility.PUBLIC)
        private = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, private)

        response = authenticated_client.get(reverse("project-list"))
        data = response.json()
        # Should see 3 public + 1 private = 4
        assert data["count"] == 4
