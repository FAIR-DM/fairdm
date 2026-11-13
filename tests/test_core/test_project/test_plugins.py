"""Tests for the project's own registered pages: menu, permissions, visibility and links."""

import codecs
import json
import re
from datetime import UTC, date, datetime, timedelta

import latexcodec  # noqa: F401  (registers the "ulatex" codec)
import pytest
import rispy
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point
from django.contrib.sites.models import Site
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.formats import date_format
from partial_dates import PartialDate
from pybtex.database import parse_string
from pytest_django.asserts import assertContains, assertNotContains

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.contrib.plugins.access import can_open
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import Overview
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES, DATE_TYPES, IDENTIFIER_TYPES
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
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
class TestTheProjectMenuEntries:
    def test_the_project_menu_carries_exactly_one_entry_for_the_collection(self):
        view_names = _entry_view_names(Project)
        assert view_names.count("project:overview") == 1
        assert "project:configure" not in view_names


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
        ContributionFactory(
            content_object=private_project,
            contributor=user_with_no_permission,
            level=ContributionLevel.VIEW,
        )
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
            "project:edit",
            "project:descriptions",
            "project:delete",
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
class TestAPrivateProjectsOtherTabs:
    @pytest.fixture
    def address(self, private_project):
        return reverse("project:dataset-list", kwargs={"uuid": private_project.uuid})

    def test_an_anonymous_visitor_is_answered_as_for_a_missing_project(
        self, client, address
    ):
        assert client.get(address).status_code == 404

    def test_a_signed_in_person_with_no_credit_is_answered_as_for_a_missing_project(
        self, client, address, user_with_no_permission
    ):
        client.force_login(user_with_no_permission)

        assert client.get(address).status_code == 404

    def test_a_person_at_view_reaches_the_tab(self, client, address, private_project):
        viewer = PersonFactory(is_active=True, is_claimed=True)
        ContributionFactory(
            content_object=private_project,
            contributor=viewer,
            level=ContributionLevel.VIEW,
        )
        client.force_login(viewer)

        assert client.get(address).status_code == 200


@pytest.mark.django_db
class TestEditPageForAModelLevelChangePermission:
    def test_a_user_holding_only_model_level_change_permission_is_refused(self, client):
        from django.contrib.auth.models import Permission

        from fairdm.factories import (
            ProjectFactory,
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

        url = reverse("project:edit", kwargs={"uuid": project.uuid})
        response = client.get(url)

        assert response.status_code == 404

    def test_a_model_level_grant_adds_nothing_to_a_view_level(self, client):
        from django.contrib.auth.models import Permission

        from fairdm.factories import (
            ProjectFactory,
            UserFactory,
        )

        project = ProjectFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="project", codename="change_project"
            )
        )
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.VIEW
        )
        client.force_login(user)

        url = reverse("project:edit", kwargs={"uuid": project.uuid})
        response = client.get(url)

        assert response.status_code == 403


@pytest.mark.django_db
class TestDescriptionsPageOffersOneAreaPerVocabularyType:
    def test_the_field_set_matches_the_vocabulary_exactly(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert list(form.fields) == [
            concept.uri for concept in ProjectDescription.get_type_concepts()
        ]

    def test_every_area_starts_empty_for_a_project_with_no_descriptions(
        self, client, user_with_change_permission
    ):
        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
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
        concept = ProjectDescription.get_type_concepts()[0]
        first_type = concept.uri

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].label == concept.display_label()
        assert form.fields[first_type].help_text == concept.first_value(
            "skos:definition"
        )


@pytest.mark.django_db
class TestSavingTextIntoOneAreaRecordsOnlyThatType:
    def test_saving_one_area_creates_exactly_one_description_of_that_type(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = next(
            concept.uri for concept in ProjectDescription.get_type_concepts()
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "Some abstract text."})

        assert ProjectDescription.objects.filter(related=project).count() == 1
        row = ProjectDescription.objects.get(related=project)
        assert row.type_id == first_type
        assert row.value == "Some abstract text."


@pytest.mark.django_db
class TestExistingDescriptionsShowInTheirOwnArea:
    def test_the_existing_description_appears_in_its_own_area_and_others_stay_empty(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type, second_type = [
            concept.uri for concept in ProjectDescription.get_type_concepts()
        ][:2]
        ProjectDescription.objects.create(
            related=project, type_id=first_type, value="Existing abstract."
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
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
        first_type = next(
            concept.uri for concept in ProjectDescription.get_type_concepts()
        )
        row = ProjectDescription.objects.create(
            related=project, type_id=first_type, value="Original text."
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
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
        first_type = next(
            concept.uri for concept in ProjectDescription.get_type_concepts()
        )
        ProjectDescription.objects.create(
            related=project, type_id=first_type, value="Existing text."
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
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
        first_type = next(
            concept.uri for concept in ProjectDescription.get_type_concepts()
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
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

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={})

        assert not ProjectDescription.objects.filter(related=project).exists()

    def test_whitespace_only_is_treated_as_empty_and_removes_a_stored_row(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = next(
            concept.uri for concept in ProjectDescription.get_type_concepts()
        )
        ProjectDescription.objects.create(
            related=project, type_id=first_type, value="Existing text."
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
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
        first_type = next(
            concept.uri for concept in ProjectDescription.get_type_concepts()
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.post(url, data={first_type: "Some text."})

        assert response.status_code == 302
        assert response.url == reverse(
            "project:overview", kwargs={"uuid": project.uuid}
        )


@pytest.mark.django_db
class TestProjectsOwnPageOffersTheDeletionLink:
    def test_a_signed_in_user_who_may_not_delete_it_is_not_offered_the_link(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        delete_url = reverse("project:delete", kwargs={"uuid": project.uuid})
        assertNotContains(response, f'href="{delete_url}"')


@pytest.mark.django_db
class TestUpdateDescriptionsAndDeletionEachLinkBackToTheProject:
    def test_the_update_page_links_back_to_the_project(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        url = reverse("project:edit", kwargs={"uuid": project.uuid})
        response = client.get(url)

        project_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assertContains(response, f'href="{project_url}"')

    def test_the_descriptions_page_links_back_to_the_project(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        project_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assertContains(response, f'href="{project_url}"')


@pytest.mark.django_db
class TestEveryLinkEachPageDrawsResolvesToARealAddress:
    def _permitted_user(self, project):
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
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

        response = client.get(reverse("project:edit", kwargs={"uuid": project.uuid}))

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)

    def test_the_descriptions_page_draws_no_empty_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(project))

        response = client.get(
            reverse("project:descriptions", kwargs={"uuid": project.uuid})
        )

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)

    def test_the_deletion_page_draws_no_empty_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(project))

        response = client.get(reverse("project:delete", kwargs={"uuid": project.uuid}))

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)


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
            reverse("project:descriptions", kwargs={"uuid": private_project.uuid})
        )

        assert response.status_code in (403, 404)

    def test_the_same_visitor_cannot_write_a_description_either(
        self, client, private_project, user_with_no_permission
    ):
        user = self._model_wide_changer(user_with_no_permission)
        client.force_login(user)

        response = client.post(
            reverse("project:descriptions", kwargs={"uuid": private_project.uuid}),
            data={"Abstract": "written by someone who may not see this project"},
        )

        assert response.status_code in (403, 404)
        assert private_project.descriptions.count() == 0

    def test_a_visitor_holding_view_rights_still_reaches_it(
        self, client, private_project, user_with_no_permission
    ):
        ContributionFactory(
            content_object=private_project,
            contributor=user_with_no_permission,
            level=ContributionLevel.EDIT,
        )
        client.force_login(user_with_no_permission)

        response = client.get(
            reverse("project:descriptions", kwargs={"uuid": private_project.uuid})
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
        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 404

    def test_an_anonymous_requester_gets_404(self, client):
        project = ProjectFactory()
        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 404

    def test_a_user_with_no_rights_on_a_public_project_still_gets_the_plain_refusal(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)
        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 403


def _overview_url(project):
    return reverse("project:overview", kwargs={"uuid": project.uuid})


def _page(client, project, language=None):
    """Open the project's page and return the response with its parsed HTML."""
    headers = {"Accept-Language": language} if language else {}
    # The locale middleware leaves the request's language active on the thread.
    with translation.override(language):
        response = client.get(_overview_url(project), headers=headers)
    assert response.status_code == 200
    response.page = BeautifulSoup(response.content, "html.parser")
    return response


def _figures(page):
    """The values of the four figures, in the order they are drawn."""
    return [figure.get_text(strip=True) for figure in page.select(".ov-figure__value")]


def _json_ld(page):
    return json.loads(page.head.find("script", type="application/ld+json").string)


@pytest.mark.django_db
class TestOverviewFiguresAndChartsCountWhatTheViewerMaySee:
    """US-1 scenarios 1 and 2: a visitor's counts follow the datasets they may see."""

    def test_a_visitor_counts_the_public_datasets_only(self, client, overview_showcase):
        response = _page(client, overview_showcase.project)

        assert _figures(response.page)[:3] == ["2", "2", "2"]

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

    def test_a_visitors_records_by_type_leave_out_the_types_only_private_datasets_hold(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        bars = response.page.select_one(".ov-mix").get_text()
        assert "Rock" in bars
        assert "Soil" not in bars
        assert "ICP" not in bars

    def test_the_teams_records_by_type_include_them(
        self, client, overview_showcase, project_team_member
    ):
        client.force_login(project_team_member)

        response = _page(client, overview_showcase.project)

        bars = response.page.select_one(".ov-mix").get_text()
        assert "Soil" in bars
        assert "ICP" in bars

    def test_a_visitors_growth_chart_counts_the_visible_records_only(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        description = response.page.find(id="project-growth-description")
        assert "2 samples" in description.get_text()
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

        rows = {
            row.pk: row.data_is_public
            for row in response.context["datasets_preview"]["rows"]
        }
        assert rows == {
            overview_showcase.published.pk: True,
            overview_showcase.unpublished.pk: False,
        }


@pytest.mark.django_db
class TestOverviewReadinessChecklistIsForTheTeam:
    def test_a_visitor_is_shown_no_checklist(self, client, overview_showcase):
        response = _page(client, overview_showcase.project)

        assert "readiness" not in response.context
        assert response.page.select_one('[data-card="readiness"]') is None

    def test_the_team_sees_every_item_and_a_link_to_each_fix_that_has_a_page(
        self, client, overview_showcase, project_team_member
    ):
        project = overview_showcase.project
        client.force_login(project_team_member)

        response = _page(client, project)

        readiness = response.context["readiness"]
        assert (readiness["done"], readiness["total"]) == (5, 10)
        card = response.page.select_one('[data-card="readiness"]')
        assert len(card.select("ul > li")) == 10
        links = {a["href"] for a in card.select("ul a")}
        assert links == {
            reverse("project:descriptions", kwargs={"uuid": project.uuid}),
            reverse("project:keywords", kwargs={"uuid": project.uuid}),
            reverse("project:key-dates", kwargs={"uuid": project.uuid}),
            reverse("project:identifiers", kwargs={"uuid": project.uuid}),
            reverse("project:contribution-list", kwargs={"uuid": project.uuid}),
        }

    def test_a_completed_item_stops_being_listed_as_missing(
        self, client, overview_showcase, project_team_member
    ):
        ProjectIdentifierFactory(
            related=overview_showcase.project,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.5555/ready",
        )
        client.force_login(project_team_member)

        response = _page(client, overview_showcase.project)

        assert response.context["readiness"]["done"] == 6


@pytest.mark.django_db
class TestOverviewNotices:
    def test_the_team_of_a_private_project_is_told_it_is_private(self, client):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        response = _page(client, project)

        update_url = reverse("project:edit", kwargs={"uuid": project.uuid})
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
        project.add_contributor(
            contact, with_roles=[f"{CONTRIBUTOR_ROLES}/contact-person"]
        )

        response = _page(client, project)

        alerts = response.page.select('[role="alert"]')
        assert any(alert.find("a", href=contact.get_absolute_url()) for alert in alerts)

    def test_without_a_contact_person_the_notice_names_the_first_leader(self, client):
        project = ProjectFactory(
            visibility=Visibility.PUBLIC,
            status=Project.STATUS_CHOICES.SEARCHING_FOR_COLLABORATORS,
        )
        leader = PersonFactory(name="Lead Person", is_active=True)
        project.add_contributor(
            leader, with_roles=[f"{CONTRIBUTOR_ROLES}/project-leader"]
        )

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

        header = response.page.find("h1").find_parent("header")
        for leader in overview_showcase.leaders:
            assert header.find("a", href=leader.get_absolute_url()) is not None

    def test_a_leader_is_named_before_a_manager_however_they_were_credited(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        manager = PersonFactory(name="Manager Person", is_active=True)
        leader = PersonFactory(name="Leader Person", is_active=True)
        project.add_contributor(
            manager, with_roles=[f"{CONTRIBUTOR_ROLES}/project-manager"]
        )
        project.add_contributor(
            leader, with_roles=[f"{CONTRIBUTOR_ROLES}/project-leader"]
        )

        response = _page(client, project)

        assert response.context["header_people"] == [leader, manager]

    def test_the_people_card_shows_everyone_credited_the_leaders_included(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        people = response.context["people"]
        shown = {row["contributor"].pk for row in people["named"]}
        shown |= {c.pk for c in people["faces"]}
        assert shown & {p.pk for p in overview_showcase.leaders} == {
            p.pk for p in overview_showcase.leaders
        }
        assert response.context["people"]["total"] == len(
            overview_showcase.leaders
        ) + len(overview_showcase.others)

    def test_the_panel_names_six_then_draws_ten_faces_and_counts_the_rest(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        panel = response.page.select_one('[data-card="people"]')
        assert len(panel.select(".ov-people > li")) == 6
        assert len(panel.select(".ov-faces a[aria-label]")) == 10
        assert (
            response.context["people"]["more"],
            response.context["people"]["total"],
        ) == (6, 22)

    def test_the_count_links_to_the_full_list_of_contributors(
        self, client, overview_showcase
    ):
        project = overview_showcase.project
        contributors_url = reverse(
            "project:contribution-list", kwargs={"uuid": project.uuid}
        )

        response = _page(client, project)

        counted = [
            a
            for a in response.page.find_all("a", href=contributors_url)
            if "6" in a.get_text()
        ]
        assert counted

    def test_each_face_is_named_for_assistive_technology(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        faces = response.page.select(".ov-faces a[title]")
        assert faces
        for face in faces:
            assert face["aria-label"] == face["title"]

    def test_a_leader_is_listed_in_the_people_card(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        leader = PersonFactory(is_active=True)
        project.add_contributor(
            leader, with_roles=[f"{CONTRIBUTOR_ROLES}/project-leader"]
        )

        response = _page(client, project)

        named = response.context["people"]["named"]
        assert [row["contributor"].pk for row in named] == [leader.pk]
        panel = response.page.select_one('[data-card="people"]')
        assert panel.find("a", href=leader.get_absolute_url()) is not None

    def test_with_nobody_credited_the_people_card_still_shows(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        assert response.context["people"]["total"] == 0
        assert response.page.select_one('[data-card="people"]') is not None

    def test_an_organisation_credited_on_the_project_is_listed_like_a_person(
        self, client
    ):
        from fairdm.factories import OrganizationFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        organisation = OrganizationFactory(name="Institute")
        project.add_contributor(organisation, with_roles=[f"{CONTRIBUTOR_ROLES}/other"])

        response = _page(client, project)

        panel = response.page.select_one('[data-card="people"]')
        assert panel.find("a", string="Institute") is not None


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
                with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
            )
        return project

    def test_one_creator_is_written_surname_and_initial(self, client):
        project = self._project_with_creators(("Anna", "Keller"))

        assert self._citation(client, project).startswith("Keller, A. (")

    def test_two_creators_are_joined_by_an_ampersand(self, client):
        project = self._project_with_creators(("Anna", "Keller"), ("Tomas", "Oliveira"))

        assert self._citation(client, project).startswith("Keller, A. & Oliveira, T. (")

    def test_several_creators_are_comma_separated_with_an_ampersand_before_the_last(
        self, client
    ):
        project = self._project_with_creators(
            ("Anna", "Keller"), ("Tomas", "Oliveira"), ("Lena", "Brandt")
        )

        assert self._citation(client, project).startswith(
            "Keller, A., Oliveira, T. & Brandt, L. ("
        )

    def test_creators_are_named_in_the_order_credited_people_before_organizations(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        partner = OrganizationFactory(name="Acme Lab")
        project.add_contributor(partner, with_roles=[f"{CONTRIBUTOR_ROLES}/creator"])
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            moving = project.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
            )
        Crediting(project).move(moving, "up")

        assert self._citation(client, project).startswith(
            "Oliveira, T., Keller, A. & Acme Lab ("
        )

    def test_a_project_with_a_doi_is_cited_by_it(self, client):
        project = self._project_with_creators(("Anna", "Keller"))
        ProjectIdentifierFactory(
            related=project, type_id=f"{IDENTIFIER_TYPES}/doi", value="10.5555/cited"
        )

        assert self._citation(client, project).endswith("https://doi.org/10.5555/cited")

    def test_a_project_without_a_doi_is_cited_by_its_permalink_and_the_card_says_so(
        self, client
    ):
        project = self._project_with_creators(("Anna", "Keller"))

        response = _page(client, project)

        assert (
            response.page.find(id="citation-text")
            .get_text()
            .endswith(f"http://testserver/{project.uuid}/")
        )
        assert response.context["citation"]["note"]

    def test_the_year_is_the_projects_start_year(self, client):
        project = self._project_with_creators(("Anna", "Keller"))
        ProjectDateFactory(
            related=project,
            type_id=f"{DATE_TYPES}/start",
            value=PartialDate.fromisoformat("2019-05"),
        )

        assert "(2019)" in self._citation(client, project)


@pytest.mark.django_db
class TestOverviewTimeline:
    def _progress(self, client, project, start, end):
        for type_, day in ((f"{DATE_TYPES}/start", start), (f"{DATE_TYPES}/end", end)):
            ProjectDateFactory(
                related=project,
                type_id=type_,
                value=PartialDate.fromisoformat(day.isoformat()),
            )
        response = _page(client, project)
        return response, response.page.find(role="progressbar")

    def test_before_the_start_it_has_not_begun(self, client):
        today = timezone.localdate()
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response, bar = self._progress(
            client, project, today + timedelta(days=30), today + timedelta(days=400)
        )

        assert bar["aria-valuenow"] == "0"
        assert response.context["timeline"]["not_started"] is True

    def test_during_the_project_it_says_how_far_through_it_is(self, client):
        today = timezone.localdate()
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response, bar = self._progress(
            client, project, today - timedelta(days=100), today + timedelta(days=100)
        )

        assert bar["aria-valuenow"] == "50"
        timeline = response.context["timeline"]
        assert not timeline["finished"]
        assert not timeline["not_started"]

    def test_after_the_end_it_is_finished(self, client):
        today = timezone.localdate()
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response, bar = self._progress(
            client, project, today - timedelta(days=800), today - timedelta(days=100)
        )

        assert bar["aria-valuenow"] == "100"
        assert response.context["timeline"]["finished"] is True

    def test_a_project_with_no_start_date_draws_no_timeline(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        assert response.page.find(role="progressbar") is None

    def test_a_project_with_a_start_and_no_end_is_shown_as_ongoing_with_no_bar(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        ProjectDateFactory(
            related=project,
            type_id=f"{DATE_TYPES}/start",
            value=PartialDate.fromisoformat("2020-01"),
        )

        response = _page(client, project)

        assert response.page.find(role="progressbar") is None
        assert response.context["timeline"]["end"] is None

    def test_the_start_and_end_are_shown_as_precisely_as_they_were_recorded(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        ProjectDateFactory(
            related=project,
            type_id=f"{DATE_TYPES}/start",
            value=PartialDate.fromisoformat("2020"),
        )
        ProjectDateFactory(
            related=project,
            type_id=f"{DATE_TYPES}/end",
            value=PartialDate.fromisoformat("2022-03"),
        )

        response = _page(client, project)

        shown = f"2020 \u2013 {date_format(date(2022, 3, 1), 'YEAR_MONTH_FORMAT')}"
        assert response.page.find("span", string=shown) is not None

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

    def _links(self, client, **award):
        project = ProjectFactory(
            visibility=Visibility.PUBLIC, funding=[{**self.AWARD, **award}]
        )
        response = _page(client, project)
        section = response.page.select_one('[data-card="funding"]')
        return response, section.find_all("a")

    @pytest.mark.parametrize(
        "identifier", ["javascript:alert(1)", "10.13039/501100001659"]
    )
    def test_a_funder_identifier_that_is_not_a_web_address_is_not_a_link(
        self, client, identifier
    ):
        _, links = self._links(client, funderIdentifier=identifier)

        assert links == []

    @pytest.mark.parametrize("uri", ["javascript:alert(1)", "AWARD/42"])
    def test_an_award_uri_that_is_not_a_web_address_is_not_a_link(self, client, uri):
        response, links = self._links(client, awardURI=uri)

        assert links == []
        assert "AWARD-42" in response.page.get_text()

    def test_web_addresses_stay_links(self, client):
        _, links = self._links(
            client,
            funderIdentifier="https://doi.org/10.13039/501100001659",
            awardURI="https://example.org/awards/42",
        )

        assert [a["href"] for a in links] == [
            "https://doi.org/10.13039/501100001659",
            "https://example.org/awards/42",
        ]

    def test_a_project_without_funding_still_shows_a_visitor_the_funding_card(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC, funding=[])

        response = _page(client, project)

        assert response.page.select_one('[data-card="funding"]') is not None
        assert response.page.select_one('[data-card="funding"] li') is None


@pytest.mark.django_db
class TestOverviewCardsAlwaysShown:
    """FR-003 and the Edge Cases: a card the page has is shown even with nothing to put in it."""

    SIDE_CARDS = ["details", "people", "identifiers", "funding", "citation"]

    def test_a_bare_project_shows_every_side_card_to_a_visitor(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC, funding=[])

        response = _page(client, project)

        for card in self.SIDE_CARDS:
            assert response.page.select_one(f'[data-card="{card}"]') is not None, card

    def test_a_project_with_no_dates_shows_the_progress_entry_in_details(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        assert response.page.select_one('[data-card="details"] [data-card="progress"]')

    def test_the_readiness_checklist_stays_out_of_a_visitors_page(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        assert response.page.select_one('[data-card="readiness"]') is None


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
        project.add_contributor(person, with_roles=[f"{CONTRIBUTOR_ROLES}/creator"])

        response = _page(client, project)

        assert person.email not in response.content.decode()

    def test_it_names_no_dataset_the_viewer_may_not_see(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        assert overview_showcase.private.name not in json.dumps(_json_ld(response.page))


@pytest.mark.django_db
class TestOverviewFirstRun:
    def test_a_project_with_no_datasets_offers_its_team_a_way_to_add_one_and_draws_no_chart(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        response = _page(client, project)

        add_url = f"{reverse('dataset-create')}?project={project.uuid}"
        assert response.page.find("a", href=add_url) is not None
        assert response.page.find(attrs={"data-mvp-chart": True}) is None
        assert response.context["mix"] is None
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
    """SC-006: each chart states in text what it shows, and records by type are counted."""

    def test_each_chart_is_named_and_points_at_its_text_alternative(
        self, client, overview_showcase
    ):
        response = _page(client, overview_showcase.project)

        for chart_id in ("project-growth",):
            surface = response.page.find(id=chart_id).find(attrs={"role": "img"})
            assert surface["aria-label"]
            described_by = surface["aria-describedby"].split()
            assert f"{chart_id}-description" in described_by
            assert response.page.find(id=f"{chart_id}-description").get_text(strip=True)

    def test_the_records_by_type_list_every_type_with_its_count(
        self, client, overview_showcase, project_team_member
    ):
        client.force_login(project_team_member)

        response = _page(client, overview_showcase.project)

        rows = {
            row.select_one(".ov-mix__label").get_text(strip=True): row.select_one(
                ".ov-mix__n"
            ).get_text(strip=True)
            for row in response.page.select(".ov-mix li:has(.ov-mix__n)")
        }
        assert rows["Rock Samples"] == "2"
        assert rows["Water Samples"] == "1"
        assert rows["XRF Measurements"] == "2"

    def test_a_type_the_registry_no_longer_holds_is_left_out_of_the_records_by_type(
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

        text = response.page.select_one(".ov-mix").get_text()
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

        text = response.page.select_one(".ov-mix").get_text()
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
        self, client, overview_showcase, project_team_member
    ):
        client.force_login(project_team_member)
        months = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]
        with translation.override("de"):
            expected = [date_format(month, "YEAR_MONTH_FORMAT") for month in months]

        response = _page(client, overview_showcase.project, language="de")

        assert self._growth_labels(response.page) == expected
        assert expected != self._growth_labels(
            _page(client, overview_showcase.project, language="en").page
        )

    def test_the_growth_charts_description_names_its_months_in_the_language(
        self, client, overview_showcase, project_team_member
    ):
        client.force_login(project_team_member)
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
        level = ContributionLevel.VIEW
        if "change" in rights:
            level = ContributionLevel.EDIT
        if "delete" in rights:
            level = ContributionLevel.MANAGE
        ContributionFactory(content_object=project, contributor=user, level=level)
        return user

    def test_a_visitor_is_offered_no_manage_links(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        for name in ("edit", "delete", "descriptions"):
            url = reverse(f"project:{name}", kwargs={"uuid": project.uuid})
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
    """SC-005: what is not available yet is announced and does nothing."""

    def test_every_disabled_button_says_why(self, client, overview_showcase):
        response = _page(client, overview_showcase.project)

        disabled = response.page.find_all("button", disabled=True)
        assert disabled
        for button in disabled:
            assert button["title"]


@pytest.mark.django_db
class TestDatasetsTabListsWhatTheViewerMaySee:
    """The tab agrees with the Overview's link and with the main dataset list."""

    def _listed(self, client, project):
        address = reverse("project:dataset-list", kwargs={"uuid": project.uuid})
        return list(client.get(address).context["object_list"])

    def test_a_visitor_sees_the_public_datasets_only(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        public = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PRIVATE)

        assert self._listed(client, project) == [public]

    def test_someone_holding_a_level_on_the_project_sees_a_private_dataset(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        private = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        member = PersonFactory(is_active=True, is_claimed=True)
        ContributionFactory(
            content_object=project, contributor=member, level=ContributionLevel.VIEW
        )
        client.force_login(member)

        assert self._listed(client, project) == [private]

    def test_someone_holding_a_level_on_one_dataset_sees_that_one_and_not_its_sibling(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        held = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        member = PersonFactory(is_active=True, is_claimed=True)
        ContributionFactory(
            content_object=held, contributor=member, level=ContributionLevel.VIEW
        )
        client.force_login(member)

        assert self._listed(client, project) == [held]

    def test_a_superuser_sees_a_private_dataset(self, client):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        private = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        client.force_login(UserFactory(is_superuser=True, is_staff=True))

        assert self._listed(client, project) == [private]

    def test_a_dataset_of_another_project_is_left_out(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(
            project=ProjectFactory(visibility=Visibility.PUBLIC),
            visibility=Visibility.PUBLIC,
        )

        assert self._listed(client, project) == []

    def test_each_card_carries_the_counts_of_the_main_list(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        sample = RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=dataset, sample=sample)

        listed = self._listed(client, project)[0]

        assert (listed.sample_count, listed.measurement_count) == (1, 1)


@pytest.fixture
def mapped():
    """A public project with samples in a published, unpublished and private dataset.

    The published dataset holds two located samples and one without a location. The
    unpublished dataset holds one located sample and the private dataset two.
    """
    from types import SimpleNamespace

    from demo.factories import RockSampleFactory, SoilSampleFactory

    project = ProjectFactory(visibility=Visibility.PUBLIC)
    published = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=True
    )
    unpublished = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=False
    )
    private = DatasetFactory(
        project=project, visibility=Visibility.PRIVATE, published=False
    )
    RockSampleFactory(dataset=published, location=Point(7.9, 48.9, srid=4326))
    RockSampleFactory(dataset=published, location=Point(8.1, 49.0, srid=4326))
    RockSampleFactory(dataset=published, location=None)
    RockSampleFactory(dataset=unpublished, location=Point(20.0, 10.0, srid=4326))
    SoilSampleFactory(dataset=private, location=Point(-70.0, -33.0, srid=4326))
    SoilSampleFactory(dataset=private, location=Point(-70.5, -33.5, srid=4326))
    return SimpleNamespace(
        project=project, published=published, unpublished=unpublished, private=private
    )


def loads_map_script(response):
    """Say whether the page asked for MapLibre: ``has_map`` is set only when it does."""
    return "has_map" in response.context and bool(response.context["has_map"])


def _member(record, level):
    """Return a signed-in-ready user credited on the record at the given level."""
    user = UserFactory()
    ContributionFactory(content_object=record, contributor=user, level=level)
    return user


@pytest.mark.django_db
class TestOverviewSampleMap:
    def test_a_visitors_map_counts_only_the_published_datasets_samples(
        self, client, mapped
    ):
        response = _page(client, mapped.project)

        sample_map = response.context["sample_map"]
        assert sample_map["located"] == 2
        assert sample_map["missing"] == 1
        assert sample_map["bounds"] == [7.9, 48.9, 8.1, 49.0]

    def test_a_private_datasets_samples_add_to_neither_count_nor_bounds_for_a_visitor(
        self, client, mapped
    ):
        sample_map = _page(client, mapped.project).context["sample_map"]

        assert sample_map["located"] + sample_map["missing"] == 3
        assert sample_map["bounds"][0] > 0
        assert sample_map["bounds"][1] > 0

    def test_a_member_of_the_private_dataset_gets_its_samples_too(self, client, mapped):
        client.force_login(_member(mapped.private, ContributionLevel.VIEW))

        sample_map = _page(client, mapped.project).context["sample_map"]

        assert sample_map["located"] == 4
        assert sample_map["missing"] == 1
        assert sample_map["bounds"] == [-70.5, -33.5, 8.1, 49.0]

    def test_the_projects_team_gets_every_sample(self, client, mapped):
        client.force_login(_member(mapped.project, ContributionLevel.EDIT))

        sample_map = _page(client, mapped.project).context["sample_map"]

        assert sample_map["located"] == 5
        assert sample_map["missing"] == 1

    @pytest.mark.parametrize(
        ("viewer", "seeded"), [("visitor", 3), ("dataset member", 5), ("team", 6)]
    )
    def test_located_and_missing_add_up_to_the_samples_figure_the_page_shows(
        self, client, mapped, viewer, seeded
    ):
        if viewer == "dataset member":
            client.force_login(_member(mapped.private, ContributionLevel.VIEW))
        elif viewer == "team":
            client.force_login(_member(mapped.project, ContributionLevel.EDIT))

        response = _page(client, mapped.project)

        sample_map = response.context["sample_map"]
        assert response.context["counts"]["samples"] == seeded
        assert sample_map["located"] + sample_map["missing"] == seeded

    def test_datasets_counts_the_datasets_the_mapped_samples_come_from(
        self, client, mapped
    ):
        visitor = _page(client, mapped.project).context["sample_map"]
        client.force_login(_member(mapped.project, ContributionLevel.EDIT))
        team = _page(client, mapped.project).context["sample_map"]

        assert visitor["datasets"] == 1
        assert team["datasets"] == 3

    def test_the_points_address_is_the_projects_own(self, client, mapped):
        sample_map = _page(client, mapped.project).context["sample_map"]

        assert sample_map["points_url"] == reverse(
            "project:overview-sample-points", kwargs={"uuid": mapped.project.uuid}
        )

    def test_a_project_with_no_samples_has_no_map(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = _page(client, project)

        assert response.context["sample_map"] is None
        assert not loads_map_script(response)

    def test_samples_none_of_which_is_located_give_a_map_of_none_and_no_map_script(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        RockSampleFactory.create_batch(2, dataset=dataset, location=None)

        response = _page(client, project)

        assert response.context["sample_map"]["located"] == 0
        assert response.context["sample_map"]["missing"] == 2
        assert not loads_map_script(response)

    def test_has_map_is_true_once_a_sample_is_located(self, client, mapped):
        response = _page(client, mapped.project)

        assert loads_map_script(response)


def portal_name(db):
    """Name the site, which a citation gives as its publisher."""
    Site.objects.filter(pk=Site.objects.get_current().pk).update(
        name="Acme Data Portal"
    )
    Site.objects.clear_cache()
    yield "Acme Data Portal"
    Site.objects.clear_cache()


@pytest.mark.django_db
class TestOverviewCitationFormats:
    """The project's citation as BibTeX and RIS, as the Cite panel offers it."""

    def make_project(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC, name="Seismic survey")
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            project.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
            )
        ProjectDateFactory(
            related=project,
            type_id=f"{DATE_TYPES}/start",
            value=PartialDate.fromisoformat("2021-03-02"),
        )
        return project

    def formats_of(self, client, project):
        citation = _page(client, project).context["citation"]
        return {entry["key"]: entry["value"] for entry in citation["formats"]}

    def entry_of(self, formats):
        data = parse_string(formats["bibtex"], "bibtex")
        assert len(data.entries) == 1
        key, entry = next(iter(data.entries.items()))
        return key, entry, rispy.loads(formats["ris"])[0]

    def test_the_text_and_both_files_give_the_same_people_year_title_and_publisher(
        self, client, portal_name
    ):
        project = self.make_project()

        formats = self.formats_of(client, project)
        key, entry, ris = self.entry_of(formats)

        assert formats["text"].startswith("Keller, A. & Oliveira, T. (2021). ")
        assert "Seismic survey. Acme Data Portal." in formats["text"]
        assert [(p.last_names, p.first_names) for p in entry.persons["author"]] == [
            (["Keller"], ["Anna"]),
            (["Oliveira"], ["Tomas"]),
        ]
        assert entry.fields["year"] == "2021"
        assert codecs.decode(entry.fields["title"], "ulatex") == "Seismic survey"
        assert codecs.decode(entry.fields["publisher"], "ulatex") == portal_name
        assert key == str(project.uuid)
        assert ris["authors"] == ["Keller, Anna", "Oliveira, Tomas"]
        assert (ris["year"], ris["title"], ris["publisher"]) == (
            "2021",
            "Seismic survey",
            portal_name,
        )

    def test_without_a_doi_the_files_give_the_permalink_and_no_doi(self, client):
        project = self.make_project()
        permalink = f"http://testserver/{project.uuid}/"

        formats = self.formats_of(client, project)
        entry, ris = self.entry_of(formats)[1:]

        assert formats["text"].endswith(permalink)
        assert entry.fields["url"] == permalink
        assert "doi" not in entry.fields
        assert ris["urls"] == [permalink]
        assert "doi" not in ris

    def test_with_a_doi_the_files_give_the_doi_and_its_link(self, client):
        project = self.make_project()
        ProjectIdentifierFactory(
            related=project, type_id=f"{IDENTIFIER_TYPES}/doi", value="10.5555/cited_1"
        )

        formats = self.formats_of(client, project)
        entry, ris = self.entry_of(formats)[1:]

        assert formats["text"].endswith("https://doi.org/10.5555/cited_1")
        assert entry.fields["doi"] == "10.5555/cited_1"
        assert entry.fields["url"] == "https://doi.org/10.5555/cited_1"
        assert ris["doi"] == "10.5555/cited_1"
        assert ris["urls"] == ["https://doi.org/10.5555/cited_1"]

    def test_a_project_is_a_misc_entry_and_a_general_reference(self, client):
        formats = self.formats_of(client, self.make_project())
        entry, ris = self.entry_of(formats)[1:]

        assert entry.type == "misc"
        assert ris["type_of_reference"] == "GEN"

    def test_with_nobody_credited_no_author_is_given(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        formats = self.formats_of(client, project)
        entry, ris = self.entry_of(formats)[1:]

        assert "author" not in entry.persons
        assert "authors" not in ris
        assert formats["text"].startswith("(")

    def test_each_format_has_an_address_beside_the_page(self, client):
        project = self.make_project()

        citation = _page(client, project).context["citation"]

        assert {e["key"]: e["download"] for e in citation["formats"]} == {
            "text": False,
            "bibtex": True,
            "ris": True,
        }
        assert [e["url"] for e in citation["formats"]] == [
            reverse(
                "project:overview-citation",
                kwargs={"uuid": project.uuid, "format": key},
            )
            for key in ("text", "bibtex", "ris")
        ]
