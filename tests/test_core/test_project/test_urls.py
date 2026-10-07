"""Tests that every project page sits under the plural ``projects/`` prefix."""

import pytest
from django.urls import NoReverseMatch, Resolver404, resolve, reverse


@pytest.mark.django_db
class TestTheProjectsPagesSitUnderThePluralPrefix:
    def test_the_overview_resolves_under_the_plural_prefix(self, public_project):
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        assert url == f"/projects/{public_project.uuid}/"

    def test_the_edit_page_resolves_under_the_plural_prefix(self, public_project):
        url = reverse("project:edit", kwargs={"uuid": public_project.uuid})
        assert url == f"/projects/{public_project.uuid}/edit/"

    def test_the_deletion_page_resolves_under_the_plural_prefix(self, public_project):
        url = reverse("project:overview-delete", kwargs={"uuid": public_project.uuid})
        assert url == f"/projects/{public_project.uuid}/delete/"

    def test_nothing_answers_under_the_singular_form(self, public_project):
        with pytest.raises(Resolver404):
            resolve(f"/project/{public_project.uuid}/")

    def test_the_retired_standalone_names_no_longer_reverse(self, public_project):
        for name in ("project-detail", "project-update", "project-delete"):
            with pytest.raises(NoReverseMatch):
                reverse(name, kwargs={"uuid": public_project.uuid})


class TestCreationIsDeclaredAheadOfTheRecordInclude:
    def test_the_creation_page_resolves_to_the_create_view_not_a_record_lookup(self):
        match = resolve("/projects/create/")
        assert match.url_name == "project-create"

    def test_the_creation_url_reverses_to_the_create_route(self):
        assert reverse("project-create") == "/projects/create/"
