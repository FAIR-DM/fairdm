"""Integration tests for the project list, create, update and delete views."""

import re
from datetime import timedelta

import pytest
from bs4 import BeautifulSoup
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Organization
from fairdm.core.choices import ProjectStatus
from fairdm.core.project.models import Project
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES, DESCRIPTION_TYPES
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectCreateView:
    def test_authenticated_user_can_access_create_view(self, authenticated_client):
        url = reverse("project-create")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

        # Set equality, not presence: the full ProjectForm has more fields than creation
        # offers.
        form = response.context["form"]
        assert set(form.fields.keys()) == {"name", "status", "visibility"}

    def test_create_project_records_creator(self, authenticated_client, user):
        url = reverse("project-create")
        form_data = {
            "name": "Creator Recorded Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
        }
        response = authenticated_client.post(url, data=form_data)

        assert response.status_code == 302

        project = Project.objects.get(name="Creator Recorded Project")
        assert project.created_by == user


@pytest.mark.django_db
class TestProjectListing:
    def test_listing_returns_200_for_anonymous_visitor(self, client):
        response = client.get(reverse("project-list"))
        assert response.status_code == 200

    def test_listing_shows_only_the_public_project_to_an_anonymous_visitor(
        self, client, public_project, private_project
    ):
        response = client.get(reverse("project-list"))
        entries = list(response.context["object_list"])
        assert public_project in entries
        assert private_project not in entries

    def test_listing_excludes_the_signed_in_owners_own_private_project(
        self, client, user_with_change_permission
    ):
        client.force_login(user_with_change_permission)
        response = client.get(reverse("project-list"))
        entries = list(response.context["object_list"])
        assert user_with_change_permission.project not in entries

    def test_listing_search_by_name_returns_the_matching_project_only(self, client):
        target = ProjectFactory(
            name="Zircon Thermochronology Survey", visibility=Visibility.PUBLIC
        )
        other = ProjectFactory(
            name="Basalt Petrology Atlas", visibility=Visibility.PUBLIC
        )
        response = client.get(reverse("project-list"), {"q": "Thermochronology"})
        entries = list(response.context["object_list"])
        assert target in entries
        assert other not in entries

    def test_listing_search_by_identifier_value_returns_the_project(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        identifier = ProjectIdentifierFactory(related=project)
        response = client.get(reverse("project-list"), {"q": identifier.value})
        entries = list(response.context["object_list"])
        assert project in entries

    def test_listing_ordered_by_name_sorts_both_ways_whatever_the_default_order(
        self, client
    ):
        # The default order is newest-modified first (bravo, charlie, alpha), which
        # neither name order matches, so an ignored sort fails here.
        alpha, bravo, charlie = (
            ProjectFactory(name=f"{name} Project", visibility=Visibility.PUBLIC)
            for name in ("Alpha", "Bravo", "Charlie")
        )
        now = timezone.now()
        for project, age in ((bravo, 1), (charlie, 2), (alpha, 3)):
            Project.objects.filter(pk=project.pk).update(
                modified=now - timedelta(days=age)
            )

        ascending = client.get(reverse("project-list"), {"o": "name"})
        descending = client.get(reverse("project-list"), {"o": "-name"})

        assert list(ascending.context["object_list"]) == [alpha, bravo, charlie]
        assert list(descending.context["object_list"]) == [charlie, bravo, alpha]

    def test_listing_ordered_by_date_added_sorts_both_ways_whatever_the_default_order(
        self, client
    ):
        # Modified order (second, third, first) matches neither direction of `added`.
        first, second, third = (
            ProjectFactory(visibility=Visibility.PUBLIC) for _ in range(3)
        )
        now = timezone.now()
        for project, age in ((first, 3), (second, 2), (third, 1)):
            Project.objects.filter(pk=project.pk).update(
                added=now - timedelta(days=age)
            )
        for project, age in ((second, 1), (third, 2), (first, 3)):
            Project.objects.filter(pk=project.pk).update(
                modified=now - timedelta(days=age)
            )

        oldest_first = client.get(reverse("project-list"), {"o": "added"})
        newest_first = client.get(reverse("project-list"), {"o": "-added"})

        assert list(oldest_first.context["object_list"]) == [first, second, third]
        assert list(newest_first.context["object_list"]) == [third, second, first]

    def test_listing_status_filter_takes_several_statuses_at_once(self, client):
        concept = ProjectFactory(
            status=ProjectStatus.CONCEPT, visibility=Visibility.PUBLIC
        )
        complete = ProjectFactory(
            status=ProjectStatus.COMPLETE, visibility=Visibility.PUBLIC
        )
        in_progress = ProjectFactory(
            status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC
        )
        response = client.get(
            reverse("project-list"),
            {"status": [ProjectStatus.CONCEPT, ProjectStatus.COMPLETE]},
        )
        entries = list(response.context["object_list"])
        assert concept in entries
        assert complete in entries
        assert in_progress not in entries

    def test_listing_tag_filter_narrows_to_the_matching_tag(self, client):
        matching = ProjectFactory(visibility=Visibility.PUBLIC)
        matching.tags.add("geothermal")
        other = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"tags": "geothermal"})
        entries = list(response.context["object_list"])
        assert matching in entries
        assert other not in entries

    def test_listing_shows_empty_state_when_a_search_matches_nothing(
        self, client, public_project
    ):
        response = client.get(
            reverse("project-list"), {"q": "no-project-should-match-this-term"}
        )
        assert response.status_code == 200
        assert list(response.context["object_list"]) == []

    def test_listing_entry_links_to_its_projects_page(self, client, public_project):
        response = client.get(reverse("project-list"))
        expected_url = public_project.get_absolute_url()
        assertContains(response, f'href="{expected_url}"')


@pytest.mark.django_db
class TestListingOffersTheCreationLink:
    def test_a_signed_in_user_is_offered_the_link(self, client):
        # Within <main>: the navbar's own "Create new" widget carries the same href on
        # every page.
        ProjectFactory(visibility=Visibility.PUBLIC)
        client.force_login(UserFactory())

        response = client.get(reverse("project-list"))

        create_url = reverse("project-create")
        main = BeautifulSoup(response.content, "html.parser").find("main")
        assert main.find("a", href=create_url) is not None

    def test_an_anonymous_visitor_is_not_offered_the_link(self, client):
        ProjectFactory(visibility=Visibility.PUBLIC)

        response = client.get(reverse("project-list"))

        create_url = reverse("project-create")
        assertNotContains(response, f'href="{create_url}"')


@pytest.mark.django_db
class TestProjectCreateViewExtended:
    def test_project_create_anonymous_redirects_to_login(self, client):
        url = reverse("project-create")
        response = client.get(url)
        assert response.status_code == 302
        expected_url = f"{reverse('account_login')}?next={url}"
        assert response.url == expected_url

    def test_project_create_redirects_to_detail(self, authenticated_client):
        url = reverse("project-create")
        response = authenticated_client.post(
            url,
            data={
                "name": "Redirect Test Project",
                "status": "1",
                "visibility": str(Visibility.PRIVATE),
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="Redirect Test Project")
        expected_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assert response.url == expected_url

    def test_creator_holds_all_project_permissions(self, client, user):
        client.force_login(user)
        url = reverse("project-create")
        response = client.post(
            url,
            data={
                "name": "Permission Test Project",
                "status": "1",
                "visibility": str(Visibility.PRIVATE),
            },
        )
        assert response.status_code == 302

        project = Project.objects.get(name="Permission Test Project")

        expected_perms = [
            "view_project",
            "change_project",
            "delete_project",
            "change_project_metadata",
            "change_project_settings",
        ]
        for perm in expected_perms:
            assert user.has_perm(perm, project), f"Missing permission: {perm}"

    def test_creator_is_listed_at_the_manage_level_with_no_stored_row(
        self, client, user
    ):
        from guardian.models import UserObjectPermission

        from fairdm.contrib.contributors.access import RecordAccess

        client.force_login(user)
        response = client.post(
            reverse("project-create"),
            data={
                "name": "Manager Project",
                "status": "1",
                "visibility": str(Visibility.PRIVATE),
            },
        )
        assert response.status_code == 302

        project = Project.objects.get(name="Manager Project")
        assert RecordAccess(project).own_level(user) == ContributionLevel.MANAGE
        assert not UserObjectPermission.objects.exists()

    def test_a_superuser_creates_a_project_without_being_credited(self, client):
        from fairdm.factories import UserFactory

        admin = UserFactory(is_superuser=True, is_staff=True)
        client.force_login(admin)
        response = client.post(
            reverse("project-create"),
            data={
                "name": "Admin Project",
                "status": "1",
                "visibility": str(Visibility.PRIVATE),
            },
        )
        assert response.status_code == 302

        project = Project.objects.get(name="Admin Project")
        assert project.contributors.count() == 0

    def test_creator_added_as_contributor_with_roles(self, client, user):
        client.force_login(user)
        url = reverse("project-create")
        response = client.post(
            url,
            data={
                "name": "Contributor Role Test Project",
                "status": "1",
                "visibility": str(Visibility.PRIVATE),
            },
        )
        assert response.status_code == 302

        project = Project.objects.get(name="Contributor Role Test Project")

        contributor = project.contributors.filter(contributor=user).first()
        assert contributor is not None, "User should be a contributor"
        role_names = list(contributor.roles.values_list("uri", flat=True))
        for role in [
            f"{CONTRIBUTOR_ROLES}/creator",
            f"{CONTRIBUTOR_ROLES}/project-member",
            f"{CONTRIBUTOR_ROLES}/contact-person",
        ]:
            assert role in role_names, f"Missing contributor role: {role}"


def _identifier_management_data(total=0, initial=0):
    """Return management-form data for the identifiers row set."""
    return {
        "identifiers-TOTAL_FORMS": str(total),
        "identifiers-INITIAL_FORMS": str(initial),
        "identifiers-MIN_NUM_FORMS": "0",
        "identifiers-MAX_NUM_FORMS": "1000",
    }


def _date_management_data(total=0, initial=0):
    """Return management-form data for the dates row set."""
    return {
        "dates-TOTAL_FORMS": str(total),
        "dates-INITIAL_FORMS": str(initial),
        "dates-MIN_NUM_FORMS": "0",
        "dates-MAX_NUM_FORMS": "1000",
    }


@pytest.mark.django_db
class TestProjectUpdateView:
    def _post_changes(self, client, user, project, owner):
        client.force_login(user)
        url = reverse("project:edit", kwargs={"uuid": project.uuid})
        return client.post(
            url,
            data={
                "name": "Renamed",
                "status": project.status,
                "visibility": Visibility.PUBLIC,
                "owner": owner.pk,
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )

    def test_an_editor_changes_the_project_but_not_its_visibility_or_owner(
        self, client
    ):
        org = Organization.objects.create(name="Original Org")
        other_org = Organization.objects.create(name="Other Org")
        project = ProjectFactory(
            name="Original", visibility=Visibility.PRIVATE, owner=org
        )
        editor = UserFactory()
        ContributionFactory(
            content_object=project, contributor=editor, level=ContributionLevel.EDIT
        )

        response = self._post_changes(client, editor, project, other_org)

        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "Renamed"
        assert project.visibility == Visibility.PRIVATE
        assert project.owner_id == org.pk

    def test_a_manager_changes_visibility_and_owner(self, client):
        org = Organization.objects.create(name="Original Org")
        other_org = Organization.objects.create(name="Other Org")
        project = ProjectFactory(visibility=Visibility.PRIVATE, owner=org)
        manager = UserFactory()
        ContributionFactory(
            content_object=project, contributor=manager, level=ContributionLevel.MANAGE
        )

        response = self._post_changes(client, manager, project, other_org)

        assert response.status_code == 302
        project.refresh_from_db()
        assert project.visibility == Visibility.PUBLIC
        assert project.owner_id == other_org.pk

    def test_a_data_curator_changes_visibility_and_owner_without_being_listed(
        self, client
    ):
        from django.contrib.auth.models import Group

        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        org = Organization.objects.create(name="Original Org")
        other_org = Organization.objects.create(name="Other Org")
        project = ProjectFactory(visibility=Visibility.PRIVATE, owner=org)
        curator = UserFactory()
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))

        response = self._post_changes(client, curator, project, other_org)

        assert response.status_code == 302
        project.refresh_from_db()
        assert project.visibility == Visibility.PUBLIC
        assert project.owner_id == other_org.pk
        assert not project.contributors.filter(contributor=curator).exists()

    def test_uploading_an_image_persists_it_and_clearing_it_removes_it(self, client):
        import io

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Image", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:edit", kwargs={"uuid": project.uuid})
        base_data = {
            "name": project.name,
            "status": project.status,
            "visibility": project.visibility,
            "owner": org.pk,
            **_identifier_management_data(),
            **_date_management_data(),
        }

        buffer = io.BytesIO()
        Image.new("RGB", (10, 10), color="red").save(buffer, format="PNG")
        buffer.seek(0)
        upload = SimpleUploadedFile("test.png", buffer.read(), content_type="image/png")

        response = client.post(url, data={**base_data, "image": upload})
        assert response.status_code == 302, response.context["form"].errors
        project.refresh_from_db()
        assert project.image

        response = client.post(url, data={**base_data, "image-clear": "on"})
        assert response.status_code == 302, response.context["form"].errors
        project.refresh_from_db()
        assert not project.image


def _project_field_data(project):
    """Return the attributes form's field values, unchanged from `project`."""
    return {
        "name": project.name,
        "status": project.status,
        "visibility": project.visibility,
        "owner": project.owner_id,
    }


@pytest.mark.django_db
class TestProjectDeleteView:
    def test_project_delete_page_refuses_rather_than_raises_on_a_restricted_sample(
        self, client
    ):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        project = ProjectFactory(name="Holds The Samples")
        dataset = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        sample = RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=DatasetFactory(), sample=sample)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:delete", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert Project.objects.filter(pk=project.pk).exists()

    def test_project_delete_confirmation_ignores_surrounding_whitespace(self, client):
        project = ProjectFactory(name="Spaced Project")
        pk = project.pk
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "  Spaced Project  "})
        assert response.status_code == 302
        assert response.url == reverse("project-list")
        assert not Project.objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestProjectCardRendering:
    def _card_html(self, client):
        response = client.get(reverse("project-list"))
        assert response.status_code == 200
        return response, response.content.decode()

    def test_card_reports_the_public_dataset_count(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        response, _ = self._card_html(client)
        assertContains(response, "2 datasets")

    def test_card_says_so_rather_than_showing_a_zero(self, client):
        ProjectFactory(visibility=Visibility.PUBLIC)
        response, html = self._card_html(client)
        assertContains(response, "No datasets")
        assert "0 datasets" not in html

    def test_private_datasets_are_not_counted_on_the_card(self, client):
        # The count must not be a number only a private dataset explains (#330).
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        response, html = self._card_html(client)
        assertContains(response, "1 dataset")
        assert "3 datasets" not in html

    def test_card_renders_the_abstract_as_plain_text(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        ProjectDescriptionFactory(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="## Objectives\n\nWe measure **heat flow** across the rift.",
        )
        response, html = self._card_html(client)
        assertContains(response, "Objectives")
        assertContains(response, "heat flow")
        assert "## Objectives" not in html
        assert "**heat flow**" not in html

    def test_card_shows_contributor_names_and_the_owning_organization(self, client):
        person = PersonFactory(name="Ada Lovelace")
        organization = OrganizationFactory(name="Institute of Deep Time")
        project = ProjectFactory(owner=organization, visibility=Visibility.PUBLIC)
        project.add_contributor(person)
        response, _ = self._card_html(client)
        assertContains(response, "Ada Lovelace")
        assertContains(response, "Institute of Deep Time")


@pytest.mark.django_db
class TestProjectListingQueryCount:
    @staticmethod
    def _build_projects(count, start=0):
        from controlled_vocabularies.models import Record

        keywords = list(
            Record.objects.filter(
                scheme__uri=CONTRIBUTOR_ROLES, type=Record.Type.CONCEPT
            ).order_by("pk")[:3]
        )
        for index in range(start, start + count):
            project = ProjectFactory(
                name=f"Survey {index}", visibility=Visibility.PUBLIC
            )
            ProjectDescriptionFactory(
                related=project,
                type_id=f"{DESCRIPTION_TYPES}/abstract",
                value=f"## Survey {index}\n\nWe measured **heat flow** here.",
            )
            project.keywords.add(*keywords)
            project.add_contributor(PersonFactory())
            project.add_contributor(OrganizationFactory())
            DatasetFactory(project=project, visibility=Visibility.PUBLIC)
            DatasetFactory(project=project, visibility=Visibility.PRIVATE)

    def test_listing_query_count_does_not_grow_with_the_number_of_projects(
        self, client, django_assert_num_queries
    ):
        url = reverse("project-list")

        self._build_projects(1)
        client.get(url)  # warm up one-time per-process and per-image setup
        with CaptureQueriesContext(connection) as one_project:
            response = client.get(url)
            assert response.status_code == 200
        baseline = len(one_project.captured_queries)

        self._build_projects(2, start=1)
        client.get(url)
        with django_assert_num_queries(baseline):
            response = client.get(url)
            assert response.status_code == 200
            assert len(response.context["object_list"]) == 3


@pytest.mark.django_db
class TestDeletionPageBackControl:
    def test_the_back_control_is_a_non_empty_link_that_resolves(self, client):
        project = ProjectFactory(name="Has A Back Link")
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:delete", kwargs={"uuid": project.uuid})

        response = client.get(url)
        content = response.content.decode()

        match = re.search(
            r'<a[^>]*href="([^"]*)"[^>]*>\s*<i class="bi bi-arrow-left"', content
        )
        assert match is not None, "the back control is not rendered as a link"
        back_href = match.group(1)
        assert back_href != ""
        resolve(back_href)
