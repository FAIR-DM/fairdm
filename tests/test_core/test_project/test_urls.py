"""The project's own address: everything about a project sits under the plural prefix.

T092 - `projects/<uuid>/` is the project itself, and every page of it is a segment below —
       nothing answers under the singular `project/<uuid>/` form any longer.
T093 - `projects/create/` still resolves as the creation page and is not read as a record
       lookup, because it stays declared ahead of the `projects/<uuid>/` include.
"""

import pytest
from django.urls import NoReverseMatch, Resolver404, resolve, reverse


@pytest.mark.django_db
class TestTheProjectsPagesSitUnderThePluralPrefix:
    """Registered pages for a project used to mount at `project/<uuid>/` while the project's own
    page stayed at `projects/<uuid>/` — one of them had to move, and the singular form is the one
    that goes (013 plan P5)."""

    def test_the_overview_resolves_under_the_plural_prefix(self, public_project):
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        assert url == f"/projects/{public_project.uuid}/"

    def test_the_attributes_page_resolves_under_the_plural_prefix(self, public_project):
        url = reverse("project:overview-update", kwargs={"uuid": public_project.uuid})
        assert url == f"/projects/{public_project.uuid}/update/"

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
    """A route declared after the record include would have `create` swallowed as an
    identifier, so `projects/create/` resolving to the creation page (not a record lookup)
    pins the declaration order rather than the outcome of one lucky arrangement."""

    def test_the_creation_page_resolves_to_the_create_view_not_a_record_lookup(self):
        match = resolve("/projects/create/")
        assert match.url_name == "project-create"

    def test_the_creation_url_reverses_to_the_create_route(self):
        assert reverse("project-create") == "/projects/create/"
