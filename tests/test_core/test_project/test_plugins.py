"""Tests for the project's own registered pages: menu, permissions, visibility and links."""

import re
from urllib.parse import quote

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from fairdm import plugins
from fairdm.contrib.plugins.access import can_open
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import Delete, Descriptions, Overview, Update
from fairdm.core.utils import assign_perm
from fairdm.factories import ProjectFactory, UserFactory
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

        from fairdm.factories import ProjectFactory, UserFactory

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

        from fairdm.factories import ProjectFactory, UserFactory

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
