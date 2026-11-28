"""Tests that every project page sits under the plural ``projects/`` prefix."""

import pytest
from django.urls import resolve, reverse


@pytest.mark.django_db
class TestTheProjectsPagesSitUnderThePluralPrefix:
    def test_the_overview_resolves_under_the_plural_prefix(self, public_project):
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        assert url == f"/projects/{public_project.uuid}/"


class TestCreationIsDeclaredAheadOfTheRecordInclude:
    def test_the_creation_page_resolves_to_the_create_view_not_a_record_lookup(self):
        match = resolve("/projects/create/")
        assert match.url_name == "project-create"
