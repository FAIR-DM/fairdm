"""Tests for the ``safe_markdown`` filter in ``fairdm/templatetags/fairdm.py`` (#266)."""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.urls import resolve, reverse
from django.utils import translation

from fairdm.factories import DatasetFactory, PersonFactory, ProjectFactory
from fairdm.templatetags.fairdm import (
    has_permission,
    on_menu_page,
    on_own_profile,
    safe_markdown,
)
from fairdm.utils.choices import Visibility
from fairdm.utils.markdown import markdownify


class TestSafeMarkdown:
    def test_renders_through_markdownify(self):
        content = "**bold** and <script>alert(1)</script>"

        assert safe_markdown(content) == markdownify(content)

    def test_template_engine_does_not_double_escape_the_output(self):
        template = Template("{% load fairdm %}{{ content|safe_markdown }}")
        rendered = template.render(Context({"content": "**bold**"}))

        assert "<strong>bold</strong>" in rendered
        assert "&lt;strong&gt;" not in rendered


@pytest.mark.django_db
class TestHasPermissionTag:
    def test_a_permission_named_in_the_context_list_is_admitted(self):
        assert has_permission(
            {"user_permissions": ["dataset.change_dataset"]}, "dataset.change_dataset"
        )

    def test_no_user_in_context_is_refused(self):
        assert not has_permission({}, "dataset.change_dataset")

    def test_belonging_to_a_group_named_data_administrators_grants_nothing_on_its_own(
        self,
    ):
        from django.contrib.auth.models import Group

        legacy_named_group = Group.objects.create(name="Data Administrators")
        member = PersonFactory()
        member.groups.add(legacy_named_group)

        assert not has_permission({"user": member}, "dataset.change_dataset")

    def test_a_person_actually_holding_the_permission_is_admitted(self):
        from django.contrib.auth.models import Permission

        person = PersonFactory()
        person.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )

        assert has_permission({"user": person}, "dataset.change_dataset")


@pytest.mark.django_db
class TestPermalinkTag:
    def test_it_gives_the_records_absolute_permalink_for_the_request(self, rf):
        project = ProjectFactory()
        template = Template("{% load fairdm %}{% permalink record as link %}{{ link }}")

        html = template.render(Context({"record": project, "request": rf.get("/")}))

        assert html == f"http://testserver/{project.uuid}/"


@pytest.mark.django_db
class TestDockTags:
    """The dock's Profile and Menu items are current on the pages they hold."""

    PROJECTS = "project-list project-create project"

    def current(self, client, path, person=None):
        """Return the labels of the dock items drawn as current on a page."""
        if person is not None:
            client.force_login(person)
        response = client.get(path)
        dock = BeautifulSoup(response.content, "html.parser").select_one(".dock")
        return [item.get_text(strip=True) for item in dock.select(".dock-active")]

    @pytest.fixture(autouse=True)
    def english(self):
        """Pin the language the labels are compared in, as another test may leave one active."""
        with translation.override("en"):
            yield

    def test_a_visitor_is_offered_log_in_in_place_of_profile(self, client):
        response = client.get(reverse("project-list"))
        dock = BeautifulSoup(response.content, "html.parser").select_one(".dock")
        links = [a["href"] for a in dock.find_all("a", href=True)]

        assert any(link.startswith(reverse("account_login")) for link in links)

    def test_the_project_list_makes_projects_current(self, client):
        assert self.current(client, reverse("project-list")) == ["Projects"]

    def test_a_datasets_own_page_keeps_datasets_current(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        assert self.current(client, dataset.get_absolute_url()) == ["Datasets"]

    def test_a_person_sees_profile_current_on_their_own_profile(self, client):
        person = PersonFactory()

        assert self.current(client, person.get_absolute_url(), person) == ["Profile"]

    def test_someone_elses_profile_is_a_menu_page(self, client):
        person, other = PersonFactory(), PersonFactory()

        assert self.current(client, other.get_absolute_url(), person) == ["Menu"]

    def test_the_search_results_are_a_menu_page(self, client):
        assert self.current(client, reverse("mvp-search")) == ["Menu"]

    def test_menu_is_not_current_on_a_section_the_dock_holds(self, rf):
        request = rf.get("/")
        request.resolver_match = resolve(reverse("project-list"))
        request.user = AnonymousUser()

        assert not on_menu_page({"request": request}, "home", self.PROJECTS)

    def test_a_page_without_a_resolved_view_is_a_menu_page(self, rf):
        request = rf.get("/")
        request.resolver_match = None
        request.user = AnonymousUser()

        assert on_menu_page({"request": request}, "home", self.PROJECTS)
        assert not on_own_profile({"request": request})
