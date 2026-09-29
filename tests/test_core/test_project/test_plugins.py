"""Tests for the project's own registered pages: menu, permissions, visibility and links."""

import json
import re
from datetime import UTC, date, datetime, timedelta
from urllib.parse import quote

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.formats import date_format
from partial_date import PartialDate
from pytest_django.asserts import assertContains, assertNotContains

from fairdm import plugins
from fairdm.contrib.plugins.access import can_open
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import Delete, Descriptions, Overview, Update
from fairdm.core.utils import assign_perm
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectDateFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility

# `ProjectFactory()` produces private projects unless told otherwise.


def _hrefs(content: str) -> list[str]:
    """Return every ``href`` attribute value in rendered HTML, in document order."""
    return re.findall(r'href="([^"]*)"', content)


def _request_for(user, path="/"):
    request = RequestFactory().get(path)
    request.user = user
    return request


def _entry_view_names(model):
    """Return the view name of each entry in the model's plugin menu."""
    # Rebuild the menu rather than rely on the root urlconf having built it, as
    # tests/test_contrib/test_plugins/test_menus.py does.
    plugins.registry.get_urls_for_model(model)
    menu = plugins.registry.get_plugin_menu_for_model(model)
    return [item.view_name for item in menu.children]


@pytest.mark.django_db
class TestOverviewIsTheProjectsOwnRegistration:
    def test_the_project_menu_carries_an_overview_entry(self):
        assert "project:overview" in _entry_view_names(Project)

    def test_the_overview_entry_is_selected_while_on_the_projects_page(
        self, public_project
    ):
        menu = plugins.registry.get_plugin_menu_for_model(Project)
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        request = _request_for(AnonymousUser(), path=url)
        processed = menu.process(
            request, object=public_project, uuid=public_project.uuid
        )
        overview_item = next(
            child
            for child in processed.children
            if child.view_name == "project:overview"
        )
        assert overview_item.selected is True

    def test_the_overview_declares_no_path_segment_of_its_own(self, public_project):
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        assert url.split(str(public_project.uuid))[-1] == "/"


@pytest.mark.django_db
class TestUpdateDescriptionsAndDeletionAreExtraViewsNotEntries:
    def test_the_update_page_resolves_as_an_extra_view_of_the_overview(
        self, public_project
    ):
        url = reverse("project:overview-update", kwargs={"uuid": public_project.uuid})
        assert url.endswith(f"{public_project.uuid}/update/")

    def test_the_descriptions_page_resolves_as_an_extra_view_of_the_overview(
        self, public_project
    ):
        url = reverse(
            "project:overview-descriptions", kwargs={"uuid": public_project.uuid}
        )
        assert url.endswith(f"{public_project.uuid}/descriptions/")

    def test_the_deletion_page_resolves_as_an_extra_view_of_the_overview(
        self, public_project
    ):
        url = reverse("project:overview-delete", kwargs={"uuid": public_project.uuid})
        assert url.endswith(f"{public_project.uuid}/delete/")

    def test_the_project_menu_carries_no_entry_for_update_descriptions_or_deletion(
        self,
    ):
        view_names = _entry_view_names(Project)
        assert "project:overview-update" not in view_names
        assert "project:overview-descriptions" not in view_names
        assert "project:overview-delete" not in view_names

    def test_the_project_menu_carries_exactly_one_entry_for_the_collection(self):
        view_names = _entry_view_names(Project)
        assert view_names.count("project:overview") == 1
        assert "project:configure" not in view_names


@pytest.mark.django_db
class TestEachExtraViewStatesItsOwnPermission:
    # An additional view inherits its owner's `check` but never its `permission` (#279).
    def test_update_refuses_a_signed_in_user_without_change_permission(
        self, public_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Update, request, public_project) is False

    def test_update_admits_a_user_holding_change_permission(
        self, user_with_change_permission
    ):
        request = _request_for(user_with_change_permission)
        assert can_open(Update, request, user_with_change_permission.project) is True

    def test_update_refuses_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Update, request, public_project) is False

    def test_deletion_refuses_a_signed_in_user_without_delete_permission(
        self, public_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Delete, request, public_project) is False

    def test_deletion_admits_a_user_holding_delete_permission(
        self, user_with_delete_permission
    ):
        request = _request_for(user_with_delete_permission)
        assert can_open(Delete, request, user_with_delete_permission.project) is True

    def test_deletion_refuses_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Delete, request, public_project) is False


@pytest.mark.django_db
class TestTheOverviewGuardsAPrivateProjectsVisibility:
    def test_a_private_project_refuses_a_user_who_may_not_view_it(
        self, private_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Overview, request, private_project) is False

    def test_a_private_project_refuses_an_anonymous_request(self, private_project):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, private_project) is False

    def test_a_private_project_admits_a_user_holding_view_permission(
        self, private_project, user_with_no_permission
    ):
        assign_perm("view_project", user_with_no_permission, private_project)
        request = _request_for(user_with_no_permission)
        assert can_open(Overview, request, private_project) is True

    def test_a_public_project_admits_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, public_project) is True

    def test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record(
        self, client, private_project
    ):
        from django.contrib.auth.models import Permission

        # Real requests: `can_open()` alone does not show that each additional view
        # refuses.
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="project", codename="change_project"
            )
        )
        client.force_login(user)

        for name in (
            "project:overview",
            "project:overview-update",
            "project:overview-descriptions",
            "project:overview-delete",
        ):
            url = reverse(name, kwargs={"uuid": private_project.uuid})
            response = client.get(url)
            assert response.status_code in (403, 404), name


@pytest.mark.django_db
class TestAPrivateProjectsPageThroughARealRequest:
    # A sign-in redirect or a 403 would confirm the project exists, so the refusal is a
    # 404.
    def test_an_anonymous_visitor_is_refused_a_private_project(
        self, client, private_project
    ):
        response = client.get(
            reverse("project:overview", kwargs={"uuid": private_project.uuid})
        )
        assert response.status_code == 404

    def test_a_signed_in_visitor_without_view_rights_is_refused(
        self, client, private_project, user_with_no_permission
    ):
        client.force_login(user_with_no_permission)
        response = client.get(
            reverse("project:overview", kwargs={"uuid": private_project.uuid})
        )
        assert response.status_code == 404

    def test_an_anonymous_visitor_reaches_a_public_project(
        self, client, public_project
    ):
        response = client.get(
            reverse("project:overview", kwargs={"uuid": public_project.uuid})
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestUpdatePageOverHTTP:
    def test_the_update_page_is_keyed_by_the_projects_identifier_not_its_own_address(
        self, public_project
    ):
        url = reverse("project:overview-update", kwargs={"uuid": public_project.uuid})
        assert url == f"/projects/{public_project.uuid}/update/"

    def test_an_anonymous_visitor_opening_the_update_page_is_redirected_to_sign_in(
        self, client, public_project
    ):
        url = reverse("project:overview-update", kwargs={"uuid": public_project.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("account_login") in response.url

    def test_a_user_holding_only_model_level_change_permission_is_refused(self, client):
        from django.contrib.auth.models import Permission

        from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectDateFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)

        project = ProjectFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="project", codename="change_project"
            )
        )
        client.force_login(user)

        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        assert response.status_code == 404

    def test_a_user_holding_change_permission_at_the_model_level_is_admitted_once_visible(
        self, client
    ):
        from django.contrib.auth.models import Permission

        from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectDateFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)

        project = ProjectFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="project", codename="change_project"
            )
        )
        assign_perm("view_project", user, project)
        client.force_login(user)

        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestExactlyOnePageOffersTheProjectsOwnAttributes:
    ATTRIBUTES_FIELDS = {"image", "name", "status", "visibility", "owner"}

    def _all_pages(self):
        """Return every registered page for `Project`, extra views included."""
        pages = []
        for plugin_cls, _kwargs in plugins.registry.get_plugins_for_model(Project):
            pages.append(plugin_cls)
            pages.extend(plugin_cls.get_extra_views())
        return pages

    def test_exactly_one_page_offers_the_attributes_field_set(self):
        offering_pages = []
        for page in self._all_pages():
            form_class = getattr(page, "form_class", None)
            fields = getattr(getattr(form_class, "Meta", None), "fields", None)
            if fields and self.ATTRIBUTES_FIELDS & set(fields):
                offering_pages.append(page)

        assert offering_pages == [Update]


@pytest.mark.django_db
class TestDescriptionsIsAnExtraViewNotARegistrationOfItsOwn:
    def test_reversed_by_name_it_resolves_at_an_address_keyed_by_the_projects_identifier(
        self, public_project
    ):
        url = reverse(
            "project:overview-descriptions", kwargs={"uuid": public_project.uuid}
        )
        assert url == f"/projects/{public_project.uuid}/descriptions/"

    def test_an_anonymous_visitor_is_redirected_to_sign_in(
        self, client, public_project
    ):
        url = reverse(
            "project:overview-descriptions", kwargs={"uuid": public_project.uuid}
        )
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("account_login") in response.url


@pytest.mark.django_db
class TestDescriptionsPageStatesItsOwnPermission:
    def test_refuses_a_signed_in_user_without_change_permission(
        self, public_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Descriptions, request, public_project) is False

    def test_admits_a_user_holding_change_permission(self, user_with_change_permission):
        request = _request_for(user_with_change_permission)
        assert (
            can_open(Descriptions, request, user_with_change_permission.project) is True
        )

    def test_refuses_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Descriptions, request, public_project) is False


@pytest.mark.django_db
class TestDescriptionsPageOffersOneAreaPerVocabularyType:
    def test_the_field_set_matches_the_vocabulary_exactly(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert list(form.fields) == list(ProjectDescription.VOCABULARY.values)

    def test_every_area_starts_empty_for_a_project_with_no_descriptions(
        self, client, user_with_change_permission
    ):
        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert all(field.initial in (None, "") for field in form)


@pytest.mark.django_db
class TestDescriptionsPageAreasAreLabelledFromTheVocabulary:
    def test_the_first_areas_label_and_help_text_match_its_concept(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]
        concept = ProjectDescription.VOCABULARY.get_concept(first_type)

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].label == concept.label()
        assert form.fields[first_type].help_text == concept.definition()


@pytest.mark.django_db
class TestSavingTextIntoOneAreaRecordsOnlyThatType:
    def test_saving_one_area_creates_exactly_one_description_of_that_type(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "Some abstract text."})

        assert ProjectDescription.objects.filter(related=project).count() == 1
        row = ProjectDescription.objects.get(related=project)
        assert row.type == first_type
        assert row.value == "Some abstract text."


@pytest.mark.django_db
class TestExistingDescriptionsShowInTheirOwnArea:
    def test_the_existing_description_appears_in_its_own_area_and_others_stay_empty(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type, second_type = ProjectDescription.VOCABULARY.values[:2]
        ProjectDescription.objects.create(
            related=project, type=first_type, value="Existing abstract."
        )

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].initial == "Existing abstract."
        assert form.fields[second_type].initial in (None, "")


@pytest.mark.django_db
class TestEditingAnExistingDescriptionPersists:
    def test_the_changed_text_persists(self, client, user_with_change_permission):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]
        row = ProjectDescription.objects.create(
            related=project, type=first_type, value="Original text."
        )

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "Changed text."})

        row.refresh_from_db()
        assert row.value == "Changed text."
        assert ProjectDescription.objects.filter(related=project).count() == 1


@pytest.mark.django_db
class TestClearingAnAreaRemovesTheDescription:
    def test_clearing_the_area_deletes_the_row(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]
        ProjectDescription.objects.create(
            related=project, type=first_type, value="Existing text."
        )

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: ""})

        assert not ProjectDescription.objects.filter(
            related=project, type=first_type
        ).exists()


@pytest.mark.django_db
class TestRepeatSubmissionNeverDuplicatesAType:
    def test_submitting_the_same_area_three_times_leaves_exactly_one_row(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "First."})
        client.post(url, data={first_type: "Second."})
        client.post(url, data={first_type: "Third."})

        assert (
            ProjectDescription.objects.filter(related=project, type=first_type).count()
            == 1
        )
        assert (
            ProjectDescription.objects.get(related=project, type=first_type).value
            == "Third."
        )


@pytest.mark.django_db
class TestEmptyAndWhitespaceOnlyAreasCreateNothing:
    def test_leaving_an_area_empty_creates_no_description(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={})

        assert not ProjectDescription.objects.filter(related=project).exists()

    def test_whitespace_only_is_treated_as_empty_and_removes_a_stored_row(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]
        ProjectDescription.objects.create(
            related=project, type=first_type, value="Existing text."
        )

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "   \n  "})

        assert not ProjectDescription.objects.filter(
            related=project, type=first_type
        ).exists()


@pytest.mark.django_db
class TestASuccessfulSubmissionRedirectsToTheProjectsPage:
    def test_the_redirect_target_is_the_projects_own_overview_url(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        response = client.post(url, data={first_type: "Some text."})

        assert response.status_code == 302
        assert response.url == reverse(
            "project:overview", kwargs={"uuid": project.uuid}
        )


@pytest.mark.django_db
class TestProjectsOwnPageOffersUpdateAndDescriptionsLinks:
    def test_a_user_who_may_change_the_project_is_offered_both_links(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        update_url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        descriptions_url = reverse(
            "project:overview-descriptions", kwargs={"uuid": project.uuid}
        )
        assertContains(response, f'href="{update_url}"')
        assertContains(response, f'href="{descriptions_url}"')

    def test_a_signed_in_user_who_may_not_change_it_is_offered_neither(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        update_url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        descriptions_url = reverse(
            "project:overview-descriptions", kwargs={"uuid": project.uuid}
        )
        assertNotContains(response, f'href="{update_url}"')
        assertNotContains(response, f'href="{descriptions_url}"')


@pytest.mark.django_db
class TestProjectsOwnPageOffersTheDeletionLink:
    def test_a_user_who_may_delete_the_project_is_offered_the_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assertContains(response, f'href="{delete_url}"')

    def test_a_signed_in_user_who_may_not_delete_it_is_not_offered_the_link(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assertNotContains(response, f'href="{delete_url}"')


@pytest.mark.django_db
class TestUpdateDescriptionsAndDeletionEachLinkBackToTheProject:
    def test_the_update_page_links_back_to_the_project(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)

        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        project_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assertContains(response, f'href="{project_url}"')

    def test_the_descriptions_page_links_back_to_the_project(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)

        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        project_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assertContains(response, f'href="{project_url}"')

    def test_the_deletion_page_links_back_to_the_project(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)

        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)

        project_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assertContains(response, f'href="{project_url}"')


@pytest.mark.django_db
class TestEveryLinkEachPageDrawsResolvesToARealAddress:
    def _permitted_user(self, project):
        user = UserFactory()
        assign_perm("change_project", user, project)
        assign_perm("delete_project", user, project)
        return user

    def test_the_listing_draws_no_empty_link(self, client):
        ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(UserFactory())

        response = client.get(reverse("project-list"))

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)

    def test_the_projects_own_page_draws_no_empty_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(project))

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)

    def test_the_update_page_draws_no_empty_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(project))

        response = client.get(
            reverse("project:overview-update", kwargs={"uuid": project.uuid})
        )

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)

    def test_the_descriptions_page_draws_no_empty_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(project))

        response = client.get(
            reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})
        )

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)

    def test_the_deletion_page_draws_no_empty_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(project))

        response = client.get(
            reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        )

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)


@pytest.mark.django_db
class TestUpdatePageOffersTheDeletionLink:
    def test_a_user_who_may_delete_the_project_is_offered_the_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_project", user, project)
        assign_perm("delete_project", user, project)
        client.force_login(user)

        response = client.get(
            reverse("project:overview-update", kwargs={"uuid": project.uuid})
        )

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assert any(
            href.startswith(delete_url) for href in _hrefs(response.content.decode())
        )

    def test_a_user_who_may_change_but_not_delete_is_offered_no_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)

        response = client.get(
            reverse("project:overview-update", kwargs={"uuid": project.uuid})
        )

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assert not any(
            href.startswith(delete_url) for href in _hrefs(response.content.decode())
        )

    def test_the_link_returns_to_the_update_page_when_deletion_is_abandoned(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_project", user, project)
        assign_perm("delete_project", user, project)
        client.force_login(user)

        update_url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(update_url)
        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        link = next(
            href
            for href in _hrefs(response.content.decode())
            if href.startswith(delete_url)
        )

        assert f"back={quote(update_url, safe='')}" in link


@pytest.mark.django_db
class TestTheDescriptionsPageGuardsAPrivateProjectsVisibility:
    def _model_wide_changer(self, user):
        from django.contrib.auth.models import Permission

        user.user_permissions.add(Permission.objects.get(codename="change_project"))
        return type(user).objects.get(pk=user.pk)

    def test_a_private_project_refuses_a_visitor_who_may_not_view_it(
        self, client, private_project, user_with_no_permission
    ):
        user = self._model_wide_changer(user_with_no_permission)
        client.force_login(user)

        response = client.get(
            reverse(
                "project:overview-descriptions", kwargs={"uuid": private_project.uuid}
            )
        )

        assert response.status_code in (403, 404)

    def test_the_same_visitor_cannot_write_a_description_either(
        self, client, private_project, user_with_no_permission
    ):
        user = self._model_wide_changer(user_with_no_permission)
        client.force_login(user)

        response = client.post(
            reverse(
                "project:overview-descriptions", kwargs={"uuid": private_project.uuid}
            ),
            data={"Abstract": "written by someone who may not see this project"},
        )

        assert response.status_code in (403, 404)
        assert private_project.descriptions.count() == 0

    def test_it_agrees_with_the_projects_own_page_on_the_same_project(
        self, client, private_project, user_with_no_permission
    ):
        user = self._model_wide_changer(user_with_no_permission)
        request = _request_for(user)

        assert can_open(Descriptions, request, private_project) == can_open(
            Overview, request, private_project
        )

    def test_a_visitor_holding_view_rights_still_reaches_it(
        self, client, private_project, user_with_no_permission
    ):
        assign_perm("view_project", user_with_no_permission, private_project)
        assign_perm("change_project", user_with_no_permission, private_project)
        client.force_login(user_with_no_permission)

        response = client.get(
            reverse(
                "project:overview-descriptions", kwargs={"uuid": private_project.uuid}
            )
        )

        assert response.status_code == 200


@pytest.mark.django_db
class TestDescriptionsPageAnswersNotFoundForAPrivateProject:
    def test_a_signed_in_user_with_no_rights_on_a_private_project_gets_404(
        self, client
    ):
        project = ProjectFactory()
        user = UserFactory()
        client.force_login(user)
        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 404

    def test_an_anonymous_requester_gets_404(self, client):
        project = ProjectFactory()
        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 404

    def test_a_user_with_no_rights_on_a_public_project_still_gets_the_plain_refusal(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)
        url = reverse("project:overview-descriptions", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 403


def _overview_url(project):
    return reverse("project:overview", kwargs={"uuid": project.uuid})


def _page(client, project, language=None):
    """Open the project's page and return the response with its parsed HTML."""
    headers = {"Accept-Language": language} if language else {}
    response = client.get(_overview_url(project), headers=headers)
    assert response.status_code == 200
    response.page = BeautifulSoup(response.content, "html.parser")
    return response


def _figures(page):
    """The values of the four figures, in the order they are drawn."""
    return [figure.get_text(strip=True) for figure in page.select(".stat-value")]


def _json_ld(page):
    return json.loads(page.head.find("script", type="application/ld+json").string)


def _card_holding(page, tag):
    """The card that holds the first ``tag`` in the page."""
    return page.find(tag).find_parent(class_="card")


@pytest.mark.django_db
class TestOverviewFiguresAndChartsCountWhatTheViewerMaySee:
    """US-1 scenarios 1 and 2: a visitor's counts follow the datasets they may see."""

    def test_a_visitor_counts_the_public_datasets_only(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        assert _figures(response.page)[:3] == ["2", "3", "2"]

    def test_the_team_counts_every_dataset(
        self, client, overview_showcase, project_team_member
    ):
        client.force_login(project_team_member)

        response = _page(client, overview_showcase.project)

        assert _figures(response.page)[:3] == ["3", "6", "3"]

    def test_the_contributors_figure_counts_everyone_credited(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        assert _figures(response.page)[3] == "22"

    def test_a_visitors_composition_chart_leaves_out_the_types_only_private_datasets_hold(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        description = response.page.find(id="project-composition-description")
        assert "Rock" in description.get_text()
        assert "Soil" not in description.get_text()
        assert "ICP" not in description.get_text()

    def test_the_teams_composition_chart_includes_them(
        self, client, overview_showcase, project_team_member
    ):
        client.force_login(project_team_member)

        response = _page(client, overview_showcase.project)

        description = response.page.find(id="project-composition-description")
        assert "Soil" in description.get_text()
        assert "ICP" in description.get_text()

    def test_a_visitors_growth_chart_counts_the_visible_records_only(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        description = response.page.find(id="project-growth-description")
        assert "3 samples" in description.get_text()
        assert "2 measurements" in description.get_text()

    def test_the_teams_growth_chart_counts_every_record(
        self, client, overview_showcase, project_team_member
    ):
        client.force_login(project_team_member)

        response = _page(client, overview_showcase.project)

        description = response.page.find(id="project-growth-description")
        assert "6 samples" in description.get_text()
        assert "3 measurements" in description.get_text()

    def test_a_visitors_licence_summary_leaves_out_licences_only_private_datasets_carry(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        assert "CC0" not in response.page.get_text()

    def test_the_datasets_listed_are_the_ones_the_viewer_may_see(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        listed = {row.name for row in response.context["datasets_preview"]["rows"]}
        assert listed == {
            overview_showcase.published.name,
            overview_showcase.unpublished.name,
        }
        assert overview_showcase.private.name not in response.page.get_text()

    def test_a_private_datasets_metadata_never_reaches_the_pages_head(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        head = str(response.page.head)
        assert overview_showcase.private.name not in head
        assert overview_showcase.private.name not in response.content.decode()

    def test_a_dataset_the_project_lists_says_whether_it_is_published(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        rows = {row.pk: row.data_is_public for row in response.context["datasets_preview"]["rows"]}
        assert rows == {
            overview_showcase.published.pk: True,
            overview_showcase.unpublished.pk: False,
        }


@pytest.mark.django_db
class TestOverviewReadinessChecklistIsForTheTeam:
    def test_a_visitor_is_shown_no_checklist(self, client, overview_showcase):
        response = _page(client, overview_showcase.project)

        assert "readiness" not in response.context
        assert response.page.find("progress", attrs={"max": "10"}) is None

    def test_the_team_sees_every_item_and_a_link_to_each_fix_that_has_a_page(
        self, client, overview_showcase, project_team_member
    ):
        project = overview_showcase.project
        client.force_login(project_team_member)

        response = _page(client, project)

        readiness = response.context["readiness"]
        assert (readiness["done"], readiness["total"]) == (5, 10)
        card = _card_holding(response.page, "progress")
        assert len(card.select("ul > li")) == 10
        links = {a["href"] for a in card.select("ul a")}
        assert links == {
            reverse("project:overview-descriptions", kwargs={"uuid": project.uuid}),
            reverse("project:overview-update", kwargs={"uuid": project.uuid}),
            reverse("project:contribution-list", kwargs={"uuid": project.uuid}),
        }

    def test_a_completed_item_stops_being_listed_as_missing(
        self, client, overview_showcase, project_team_member
    ):
        ProjectIdentifierFactory(
            related=overview_showcase.project, type="DOI", value="10.5555/ready"
        )
        client.force_login(project_team_member)

        response = _page(client, overview_showcase.project)

        assert response.context["readiness"]["done"] == 6


@pytest.mark.django_db
class TestOverviewNotices:
    def test_the_team_of_a_private_project_is_told_it_is_private(self, client):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        user = UserFactory()
        assign_perm("view_project", user, project)
        assign_perm("change_project", user, project)
        client.force_login(user)

        response = _page(client, project)

        update_url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        alerts = response.page.select('[role="alert"]')
        assert any(alert.find("a", href=update_url) for alert in alerts)

    def test_a_public_project_gives_its_team_no_privacy_notice(
        self, client, overview_showcase, project_team_member
    ):
        client.force_login(project_team_member)

        response = _page(client, overview_showcase.project)

        assert response.page.select('[role="alert"]') == []

    def test_a_project_searching_for_collaborators_names_who_to_contact(self, client):
        project = ProjectFactory(
            visibility=Visibility.PUBLIC,
            status=Project.STATUS_CHOICES.SEARCHING_FOR_COLLABORATORS,
        )
        contact = PersonFactory(name="Contact Person", is_active=True)
        project.add_contributor(contact, with_roles=["ContactPerson"])

        response = _page(client, project)

        alerts = response.page.select('[role="alert"]')
        assert any(alert.find("a", href=contact.get_absolute_url()) for alert in alerts)

    def test_without_a_contact_person_the_notice_names_the_first_leader(self, client):
        project = ProjectFactory(
            visibility=Visibility.PUBLIC,
            status=Project.STATUS_CHOICES.SEARCHING_FOR_COLLABORATORS,
        )
        leader = PersonFactory(name="Lead Person", is_active=True)
        project.add_contributor(leader, with_roles=["ProjectLeader"])

        response = _page(client, project)

        alerts = response.page.select('[role="alert"]')
        assert any(alert.find("a", href=leader.get_absolute_url()) for alert in alerts)

    def test_a_project_in_any_other_state_shows_no_collaborators_notice(self, client):
        project = ProjectFactory(
            visibility=Visibility.PUBLIC,
            status=Project.STATUS_CHOICES.IN_PROGRESS,
        )

        response = _page(client, project)

        assert response.page.select('[role="alert"]') == []


@pytest.mark.django_db
class TestOverviewPeople:
    def test_the_header_names_the_leaders_linked_to_their_pages(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        header = response.page.find("h1").find_parent(class_="card")
        for leader in overview_showcase.leaders:
            assert header.find("a", href=leader.get_absolute_url()) is not None

    def test_the_people_card_shows_everyone_else_and_not_the_leaders(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        shown = {c.pk for c in response.context["people"]["shown"]}
        assert shown <= {p.pk for p in overview_showcase.others}
        assert not shown & {p.pk for p in overview_showcase.leaders}

    def test_the_card_draws_eighteen_faces_and_counts_the_rest(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        tiles = response.page.select("li[data-tip]")
        assert len(tiles) == 18
        assert (response.context["people"]["more"], response.context["people"]["total"]) == (2, 20)

    def test_the_count_links_to_the_full_list_of_contributors(
        self, client, overview_showcase
    ):
        project = overview_showcase.project
        contributors_url = reverse("project:contribution-list", kwargs={"uuid": project.uuid})

        response = _page(client, project)

        counted = [
            a
            for a in response.page.find_all("a", href=contributors_url)
            if "2" in a.get_text()
        ]
        assert counted

    def test_each_face_is_named_for_assistive_technology(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        for tile in response.page.select("li[data-tip]"):
            assert tile.find("a")["aria-label"] == tile["data-tip"]

    def test_when_everyone_credited_leads_the_people_card_is_left_out(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        project.add_contributor(PersonFactory(is_active=True), with_roles=["ProjectLeader"])

        response = _page(client, project)

        assert response.page.select("li[data-tip]") == []
        assert response.context["people"]["shown"] == []

    def test_an_organisation_credited_on_the_project_is_listed_like_a_person(
        self, client
    ):
        from fairdm.factories import OrganizationFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        organisation = OrganizationFactory(name="Institute")
        project.add_contributor(organisation, with_roles=["Other"])

        response = _page(client, project)

        assert response.page.find("li", attrs={"data-tip": "Institute"}) is not None


@pytest.mark.django_db
class TestOverviewCitation:
    def _citation(self, client, project):
        response = _page(client, project)
        return response.page.find(id="citation-text").get_text(strip=True)

    def _project_with_creators(self, *names):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        for first, last in names:
            project.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=["Creator"],
            )
        return project

    def test_one_creator_is_written_surname_and_initial(self, client):
        project = self._project_with_creators(("Anna", "Keller"))

        assert self._citation(client, project).startswith("Keller, A. (")

    def test_two_creators_are_joined_by_an_ampersand(self, client):
        project = self._project_with_creators(("Anna", "Keller"), ("Tomas", "Oliveira"))

        assert self._citation(client, project).startswith(
            "Keller, A. & Oliveira, T. ("
        )

    def test_several_creators_are_comma_separated_with_an_ampersand_before_the_last(
        self, client
    ):
        project = self._project_with_creators(
            ("Anna", "Keller"), ("Tomas", "Oliveira"), ("Lena", "Brandt")
        )

        assert self._citation(client, project).startswith(
            "Keller, A., Oliveira, T. & Brandt, L. ("
        )

    def test_a_project_with_a_doi_is_cited_by_it(self, client):
        project = self._project_with_creators(("Anna", "Keller"))
        ProjectIdentifierFactory(related=project, type="DOI", value="10.5555/cited")

        assert self._citation(client, project).endswith("https://doi.org/10.5555/cited")

    def test_a_project_without_a_doi_is_cited_by_its_page_and_the_card_says_so(
        self, client
    ):
        project = self._project_with_creators(("Anna", "Keller"))

        response = _page(client, project)

        assert response.page.find(id="citation-text").get_text().endswith(
            _overview_url(project)
        )
        assert response.context["citation"]["note"]

    def test_the_year_is_the_projects_start_year(self, client):
        project = self._project_with_creators(("Anna", "Keller"))
        ProjectDateFactory(related=project, type="Start", value=PartialDate("2019-05"))

        assert "(2019)" in self._citation(client, project)


@pytest.mark.django_db
class TestOverviewTimeline:
    def _progress(self, client, project, start, end):
        for type_, day in (("Start", start), ("End", end)):
            ProjectDateFactory(
                related=project, type=type_, value=PartialDate(day.isoformat())
            )
        response = _page(client, project)
        return response, response.page.find("progress")

    def test_before_the_start_it_has_not_begun(self, client):
        today = timezone.localdate()
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response, bar = self._progress(
            client, project, today + timedelta(days=30), today + timedelta(days=400)
        )

        assert bar["value"] == "0"
        assert response.context["timeline"]["not_started"] is True

    def test_during_the_project_it_says_how_far_through_it_is(self, client):
        today = timezone.localdate()
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response, bar = self._progress(
            client, project, today - timedelta(days=100), today + timedelta(days=100)
        )

        assert bar["value"] == "50"
        timeline = response.context["timeline"]
        assert not timeline["finished"]
        assert not timeline["not_started"]

    def test_after_the_end_it_is_finished(self, client):
        today = timezone.localdate()
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response, bar = self._progress(
            client, project, today - timedelta(days=800), today - timedelta(days=100)
        )

        assert bar["value"] == "100"
        assert response.context["timeline"]["finished"] is True

    def test_a_project_with_no_start_date_draws_no_timeline(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        assert response.page.find("progress") is None

    def test_a_project_with_a_start_and_no_end_is_shown_as_ongoing_with_no_bar(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        ProjectDateFactory(related=project, type="Start", value=PartialDate("2020-01"))

        response = _page(client, project)

        assert response.page.find("progress") is None
        assert response.context["timeline"]["end"] is None

    def test_the_bar_is_named_for_assistive_technology(self, client):
        today = timezone.localdate()
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        _, bar = self._progress(
            client, project, today - timedelta(days=100), today + timedelta(days=100)
        )

        assert bar["aria-label"]


@pytest.mark.django_db
class TestOverviewFunding:
    AWARD = {
        "funderName": "Funder Example",
        "awardTitle": "Award Example",
        "awardNumber": "AWARD-42",
    }

    def test_a_project_with_funding_shows_it_to_a_visitor(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC, funding=[self.AWARD])

        response = _page(client, project)

        text = response.page.get_text()
        assert "Funder Example" in text
        assert "AWARD-42" in text

    def test_a_project_without_funding_shows_a_visitor_no_funding_card(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC, funding=[])
        with_funding = ProjectFactory(visibility=Visibility.PUBLIC, funding=[self.AWARD])

        without = _page(client, project)
        with_ = _page(client, with_funding)

        assert len(without.page.select("h2.card-title")) == (
            len(with_.page.select("h2.card-title")) - 1
        )

    def test_the_team_of_a_project_without_funding_still_gets_the_card(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC, funding=[])
        user = UserFactory()
        assign_perm("view_project", user, project)
        assign_perm("change_project", user, project)

        visitor_cards = len(_page(client, project).page.select("h2.card-title"))
        client.force_login(user)
        team_cards = len(_page(client, project).page.select("h2.card-title"))

        # The team also gets the checklist and the manage controls, but it is the funding card
        # that this compares: readiness adds one card, funding the other.
        assert team_cards == visitor_cards + 2


@pytest.mark.django_db
class TestOverviewSchemaOrgDescription:
    def test_the_pages_head_carries_the_projects_description(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC, name="Deep heat flow")

        response = _page(client, project)

        data = _json_ld(response.page)
        assert data["@type"] == "ResearchProject"
        assert data["name"] == "Deep heat flow"

    def test_a_name_that_could_end_the_script_element_cannot_break_out_of_it(
        self, client
    ):
        name = "</script><script>alert(1)</script> & <b>"
        project = ProjectFactory(visibility=Visibility.PUBLIC, name=name)

        response = _page(client, project)

        assert _json_ld(response.page)["name"] == name
        assert "<script>alert(1)" not in response.content.decode()

    def test_it_carries_no_contributor_email_address(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        person = PersonFactory(is_active=True)
        project.add_contributor(person, with_roles=["Creator"])

        response = _page(client, project)

        assert person.email not in response.content.decode()

    def test_it_names_no_dataset_the_viewer_may_not_see(self, client, overview_showcase):
        response = _page(client, overview_showcase.project)

        assert overview_showcase.private.name not in json.dumps(
            _json_ld(response.page)
        )


@pytest.mark.django_db
class TestOverviewFirstRun:
    def test_a_project_with_no_datasets_offers_its_team_a_way_to_add_one_and_draws_no_chart(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("view_project", user, project)
        assign_perm("change_project", user, project)
        client.force_login(user)

        response = _page(client, project)

        add_url = f"{reverse('dataset-create')}?project={project.uuid}"
        assert response.page.find("a", href=add_url) is not None
        assert response.page.find(attrs={"data-mvp-chart": True}) is None
        assert response.context["composition_chart"] is None
        assert response.context["growth_chart"] is None

    def test_a_visitor_to_a_project_with_no_datasets_is_offered_no_way_to_add_one(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        assert response.page.find("a", href=reverse("dataset-create")) is None
        assert response.page.find(attrs={"data-mvp-chart": True}) is None

    def test_the_chart_libraries_are_not_loaded_when_there_is_no_chart(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        assert "echarts" not in response.content.decode()


@pytest.mark.django_db
class TestOverviewCharts:
    """SC-006: each chart states in text what it shows."""

    def test_each_chart_is_named_and_points_at_its_text_alternative(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        for chart_id in ("project-composition", "project-growth"):
            surface = response.page.find(id=chart_id).find(attrs={"role": "img"})
            assert surface["aria-label"]
            described_by = surface["aria-describedby"].split()
            assert f"{chart_id}-description" in described_by
            assert response.page.find(id=f"{chart_id}-description").get_text(strip=True)

    def test_the_composition_text_lists_every_type_with_its_count(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        text = response.page.find(id="project-composition-description").get_text()
        assert "Rock Samples: 2" in text
        assert "Water Samples: 1" in text
        assert "XRF Measurements: 2" in text

    def test_a_type_the_registry_no_longer_holds_is_left_out_of_the_composition(
        self, client, overview_showcase, monkeypatch
    ):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory
        from demo.models import ExampleMeasurement
        from fairdm.registry import registry

        published = overview_showcase.published
        ExampleMeasurementFactory(
            dataset=published, sample=RockSampleFactory(dataset=published)
        )
        held = {
            model: config
            for model, config in registry._registry.items()
            if model is not ExampleMeasurement
        }
        monkeypatch.setattr(registry, "_registry", held)

        response = _page(client, overview_showcase.project)

        text = response.page.find(id="project-composition-description").get_text()
        assert "Example" not in text
        assert "Rock Samples" in text

    def test_a_record_whose_type_no_longer_exists_does_not_break_the_page(
        self, client, overview_showcase
    ):
        from django.contrib.contenttypes.models import ContentType

        from fairdm.core.sample.models import Sample

        stale = ContentType.objects.create(app_label="demo", model="removedsample")
        sample = Sample.objects.filter(dataset=overview_showcase.published).first()
        Sample.objects.filter(pk=sample.pk).update(polymorphic_ctype=stale)

        response = _page(client, overview_showcase.project)

        text = response.page.find(id="project-composition-description").get_text()
        assert "Rock Samples" in text


@pytest.mark.django_db
class TestOverviewFollowsTheActiveLanguage:
    """FR-057: dates in chart labels and descriptions use the locale's named formats."""

    def _growth_labels(self, page):
        options = page.find(id="project-growth").find(
            "script", attrs={"data-mvp-chart-options": True}
        )
        return json.loads(options.string)["xAxis"][0]["data"]

    def test_the_growth_charts_month_labels_follow_the_language(
        self, client, overview_showcase
    ):
        months = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]
        with translation.override("de"):
            expected = [date_format(month, "YEAR_MONTH_FORMAT") for month in months]

        response = _page(client, overview_showcase.project, language="de")

        assert self._growth_labels(response.page) == expected
        assert expected != self._growth_labels(
            _page(client, overview_showcase.project, language="en").page
        )

    def test_the_growth_charts_description_names_its_months_in_the_language(
        self, client, overview_showcase
    ):
        with translation.override("de"):
            first = date_format(date(2026, 1, 1), "YEAR_MONTH_FORMAT")
            last = date_format(date(2026, 3, 1), "YEAR_MONTH_FORMAT")

        response = _page(client, overview_showcase.project, language="de")

        text = response.page.find(id="project-growth-description").get_text()
        assert first in text
        assert last in text

    def test_a_datasets_last_updated_date_follows_the_language(
        self, client, overview_showcase
    ):
        updated = datetime(2026, 1, 5, 12, tzinfo=UTC)
        Dataset.all_objects.filter(pk=overview_showcase.published.pk).update(
            modified=updated
        )
        with translation.override("de"):
            expected = date_format(updated, "SHORT_DATE_FORMAT")

        response = _page(client, overview_showcase.project, language="de")

        assert expected in response.page.get_text()


@pytest.mark.django_db
class TestOverviewManageMenu:
    def _team_member(self, project, *rights):
        user = UserFactory()
        assign_perm("view_project", user, project)
        for right in rights:
            assign_perm(f"{right}_project", user, project)
        return user

    def test_a_user_who_may_change_and_delete_is_offered_delete_in_the_manage_menu(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._team_member(project, "change", "delete"))

        response = _page(client, project)

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assert response.page.find("a", href=delete_url) is not None

    def test_a_user_who_may_change_but_not_delete_is_not_offered_it(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._team_member(project, "change"))

        response = _page(client, project)

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assert response.page.find("a", href=delete_url) is None

    def test_a_user_who_may_delete_but_not_change_is_still_offered_delete(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._team_member(project, "delete"))

        response = _page(client, project)

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assert response.page.find("a", href=delete_url) is not None

    def test_a_visitor_is_offered_no_manage_links(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        for name in ("update", "delete", "descriptions"):
            url = reverse(f"project:overview-{name}", kwargs={"uuid": project.uuid})
            assert response.page.find("a", href=url) is None

    def test_the_add_dataset_action_is_offered_to_the_team_only(
        self, client, overview_showcase, project_team_member
    ):
        project = overview_showcase.project
        add_url = f"{reverse('dataset-create')}?project={project.uuid}"

        visitor = _page(client, project)
        client.force_login(project_team_member)
        team = _page(client, project)

        assert visitor.page.find("a", href=add_url) is None
        assert team.page.find("a", href=add_url) is not None


@pytest.mark.django_db
class TestOverviewNotAvailableYet:
    """FR-016, FR-017 and SC-005: what is not available yet is announced and does nothing."""

    def test_every_disabled_button_says_why(self, client, overview_showcase):
        response = _page(client, overview_showcase.project)

        disabled = response.page.find_all("button", disabled=True)
        assert disabled
        for button in disabled:
            assert button["title"]

    def test_a_card_standing_in_for_a_missing_capability_carries_no_link_or_button(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        placeholders = [
            card
            for card in response.page.select(".card")
            if card.select_one(".card.bg-base-200")
            and card.select_one(".card.bg-base-200") is not card
        ]
        assert len(placeholders) == 2
        for card in placeholders:
            assert card.find("a") is None
            assert card.find("button") is None
