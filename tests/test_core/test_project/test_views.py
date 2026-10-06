"""Integration tests for the project list, create, update and delete views."""

import re
import time

import pytest
from bs4 import BeautifulSoup
from django import forms
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse
from django.views.generic import CreateView
from pytest_django.asserts import assertContains, assertNotContains

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Organization
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.project.views import ProjectCreateView, ProjectListView
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectDateFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from fairdm.views import FairDMCreateView, FairDMListView


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

    def test_anonymous_user_redirects_to_login(self, client):
        url = reverse("project-create")
        response = client.get(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url or "/login/" in response.url

    def test_create_project_redirects_to_detail(self, authenticated_client):
        owner = Organization.objects.create(name="Test Organization")

        url = reverse("project-create")
        form_data = {
            "name": "New Test Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
        }
        response = authenticated_client.post(url, data=form_data)

        assert response.status_code == 302

        project = Project.objects.get(name="New Test Project")
        assert project.pk is not None

        expected_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assert response.url == expected_url

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

    def test_create_form_displays_validation_errors(self, authenticated_client):
        url = reverse("project-create")
        form_data = {
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
        }
        response = authenticated_client.post(url, data=form_data)

        assert response.status_code == 200
        assert "form" in response.context

        form = response.context["form"]
        assert not form.is_valid()
        assert "name" in form.errors
        assert Project.objects.count() == 0


@pytest.mark.django_db
class TestProjectListViewEmitsNoDeprecationWarning:
    @pytest.mark.filterwarnings("error::mvp.warnings.MVPDeprecationWarning")
    def test_rendering_the_listing_emits_no_deprecation_warning(self, client):
        response = client.get(reverse("project-list"))
        assert response.status_code == 200


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

    def test_listing_ordered_by_name_returns_alphabetical_order(self, client):
        bravo = ProjectFactory(name="Bravo Project", visibility=Visibility.PUBLIC)
        alpha = ProjectFactory(name="Alpha Project", visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"o": "name"})
        entries = list(response.context["object_list"])
        assert entries.index(alpha) < entries.index(bravo)

    def test_listing_ordered_by_name_reversed_returns_reverse_alphabetical_order(
        self, client
    ):
        # Separate from the ascending case: an unordered queryset that arrives sorted
        # would pass one.
        bravo = ProjectFactory(name="Bravo Project", visibility=Visibility.PUBLIC)
        alpha = ProjectFactory(name="Alpha Project", visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"o": "-name"})
        entries = list(response.context["object_list"])
        assert entries.index(bravo) < entries.index(alpha)

    def test_listing_ordered_by_date_added_returns_oldest_first(self, client):
        older = ProjectFactory(visibility=Visibility.PUBLIC)
        time.sleep(0.01)
        newer = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"o": "added"})
        entries = list(response.context["object_list"])
        assert entries.index(older) < entries.index(newer)

    def test_listing_ordered_by_date_added_reversed_returns_newest_first(self, client):
        older = ProjectFactory(visibility=Visibility.PUBLIC)
        time.sleep(0.01)
        newer = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"o": "-added"})
        entries = list(response.context["object_list"])
        assert entries.index(newer) < entries.index(older)

    def test_listing_status_filter_narrows_to_the_matching_status(self, client):
        concept = ProjectFactory(
            status=ProjectStatus.CONCEPT, visibility=Visibility.PUBLIC
        )
        complete = ProjectFactory(
            status=ProjectStatus.COMPLETE, visibility=Visibility.PUBLIC
        )
        response = client.get(
            reverse("project-list"), {"status": ProjectStatus.CONCEPT}
        )
        entries = list(response.context["object_list"])
        assert concept in entries
        assert complete not in entries

    def test_listing_owner_filter_narrows_to_the_matching_owner(self, client):
        owner = OrganizationFactory()
        matching = ProjectFactory(owner=owner, visibility=Visibility.PUBLIC)
        other = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"owner": owner.pk})
        entries = list(response.context["object_list"])
        assert matching in entries
        assert other not in entries

    def test_listing_contributor_filter_narrows_to_the_matching_contributor(
        self, client
    ):
        person = PersonFactory()
        matching = ProjectFactory(visibility=Visibility.PUBLIC)
        matching.add_contributor(person)
        other = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"contributor": person.pk})
        entries = list(response.context["object_list"])
        assert matching in entries
        assert other not in entries

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

    def test_listing_view_derives_from_the_portals_own_list_base_class(self):
        assert FairDMListView in ProjectListView.__bases__


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

    def test_project_create_authenticated_200(self, authenticated_client):
        url = reverse("project-create")
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_visibility_renders_as_radio_with_public_preselected(
        self, authenticated_client
    ):
        url = reverse("project-create")
        response = authenticated_client.get(url)
        form = response.context["form"]

        assert isinstance(form.fields["visibility"].widget, forms.RadioSelect)

        content = response.content.decode()
        public_input = re.search(
            rf'<input[^>]*name="visibility"[^>]*value="{Visibility.PUBLIC}"[^>]*>',
            content,
        )
        private_input = re.search(
            rf'<input[^>]*name="visibility"[^>]*value="{Visibility.PRIVATE}"[^>]*>',
            content,
        )
        assert public_input is not None and "checked" in public_input.group(0)
        assert private_input is not None and "checked" not in private_input.group(0)

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
        role_names = list(contributor.roles.values_list("name", flat=True))
        for role in ["Creator", "ProjectMember", "ContactPerson"]:
            assert role in role_names, f"Missing contributor role: {role}"

    def test_create_view_derives_from_portal_create_base(self):
        assert issubclass(ProjectCreateView, FairDMCreateView)
        assert FairDMCreateView in ProjectCreateView.__mro__
        assert CreateView not in ProjectCreateView.__bases__


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
    def test_project_update_anonymous_redirects_to_login(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_project_update_without_permission_on_a_private_project_404(self, client):
        project = ProjectFactory()
        other_user = UserFactory()
        client.force_login(other_user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_project_update_without_permission_on_a_public_project_403(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        other_user = UserFactory()
        client.force_login(other_user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_project_update_without_permission_anonymous_on_a_private_project_404(
        self, client
    ):
        project = ProjectFactory()
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_project_update_with_permission_200(self, client):
        project = ProjectFactory()
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_changing_name_status_visibility_and_owner_each_persists(self, client):
        org = Organization.objects.create(name="Original Org")
        other_org = Organization.objects.create(name="Other Org")
        user = UserFactory()

        base_data = {
            "name": "Original Name",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": org.pk,
        }
        changes = {
            "name": "Changed Name",
            "status": ProjectStatus.IN_PROGRESS,
            "visibility": Visibility.PUBLIC,
            "owner": other_org.pk,
        }

        for field, new_value in changes.items():
            project = ProjectFactory(
                name="Original Name",
                status=ProjectStatus.CONCEPT,
                visibility=Visibility.PRIVATE,
                owner=org,
            )
            ContributionFactory(
                content_object=project, contributor=user, level=ContributionLevel.EDIT
            )
            client.force_login(user)
            url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
            data = {
                **base_data,
                field: new_value,
                **_identifier_management_data(),
                **_date_management_data(),
            }

            response = client.post(url, data=data)

            assert response.status_code == 302, response.context["form"].errors
            project.refresh_from_db()
            if field == "owner":
                assert project.owner_id == other_org.pk
            else:
                assert getattr(project, field) == new_value

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
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
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

    def test_submitting_an_empty_name_reports_an_error_and_saves_nothing(self, client):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                "name": "",
                "status": project.status,
                "visibility": project.visibility,
                "owner": org.pk,
            },
        )

        assert response.status_code == 200
        assert "name" in response.context["form"].errors
        project.refresh_from_db()
        assert project.name == "Original Name"

    def test_project_update_success_redirects_to_detail(self, client):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.post(
            url,
            data={
                "name": "Updated Name",
                "status": project.status,
                "visibility": project.visibility,
                "owner": org.pk,
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )
        assert response.status_code == 302
        expected_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assert response.url == expected_url


def _project_field_data(project):
    """Return the attributes form's field values, unchanged from `project`."""
    return {
        "name": project.name,
        "status": project.status,
        "visibility": project.visibility,
        "owner": project.owner_id,
    }


@pytest.mark.django_db
class TestAttributesIdentifierRowSet:
    def test_existing_identifiers_are_presented_one_row_each_with_no_blank_row_beyond_them(
        self, client
    ):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Identifier", owner=org)
        ProjectIdentifierFactory(related=project, type="DOI", value="10.1/existing")
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        identifier_formset = formsets["identifiers"]
        assert identifier_formset.initial_form_count() == 1
        assert len(identifier_formset.forms) == 1

    def test_adding_an_identifier_of_a_chosen_type_records_it_against_the_project(
        self, client
    ):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="No Identifiers Yet", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/new-identifier",
            },
        )

        assert response.status_code == 302
        assert project.identifiers.filter(
            type="DOI", value="10.1/new-identifier"
        ).exists()

    def test_changing_an_existing_identifiers_value_persists(self, client):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Identifier", owner=org)
        identifier = ProjectIdentifierFactory(
            related=project, type="DOI", value="10.1/original"
        )
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(total=1, initial=1),
                **_date_management_data(),
                "identifiers-0-id": identifier.pk,
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/changed",
            },
        )

        assert response.status_code == 302
        identifier.refresh_from_db()
        assert identifier.value == "10.1/changed"

    def test_removing_an_identifier_row_deletes_it_from_the_project(self, client):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Identifier", owner=org)
        identifier = ProjectIdentifierFactory(
            related=project, type="DOI", value="10.1/to-remove"
        )
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(total=1, initial=1),
                **_date_management_data(),
                "identifiers-0-id": identifier.pk,
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/to-remove",
                "identifiers-0-DELETE": "on",
            },
        )

        assert response.status_code == 302
        assert not project.identifiers.filter(pk=identifier.pk).exists()

    def test_a_value_already_recorded_against_a_different_project_is_refused(
        self, client
    ):
        org = Organization.objects.create(name="Test Org")
        other_project = ProjectFactory(name="Other Project", owner=org)
        ProjectIdentifierFactory(related=other_project, type="DOI", value="10.1/taken")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                "name": "Renamed",
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/taken",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert "value" in formsets["identifiers"].forms[0].errors
        assert not project.identifiers.filter(value="10.1/taken").exists()
        project.refresh_from_db()
        assert project.name == "Original Name"

    def test_the_same_value_submitted_twice_in_one_submission_reports_the_collision(
        self, client
    ):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="No Identifiers Yet", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(total=2, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/duplicated",
                "identifiers-1-type": "GRANT_NUMBER",
                "identifiers-1-value": "10.1/duplicated",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert formsets["identifiers"].non_form_errors()
        assert not project.identifiers.filter(value="10.1/duplicated").exists()


@pytest.mark.django_db
class TestAttributesDateRowSet:
    def test_existing_dates_are_presented_one_row_each_with_no_blank_row_beyond_them(
        self, client
    ):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Date", owner=org)
        ProjectDateFactory(related=project, type="Start", value="2020-01-01")
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        date_formset = formsets["dates"]
        assert date_formset.initial_form_count() == 1
        assert len(date_formset.forms) == 1

    def test_adding_a_date_of_a_chosen_type_records_it_against_the_project(
        self, client
    ):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="No Dates Yet", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=0),
                "dates-0-type": "Start",
                "dates-0-value": "2020-01-01",
            },
        )

        assert response.status_code == 302
        assert project.dates.filter(type="Start", value="2020-01-01").exists()

    def test_changing_an_existing_dates_value_persists(self, client):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Date", owner=org)
        date = ProjectDateFactory(related=project, type="Start", value="2020-01-01")
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=1),
                "dates-0-id": date.pk,
                "dates-0-type": "Start",
                "dates-0-value": "2021-06-15",
            },
        )

        assert response.status_code == 302
        date.refresh_from_db()
        assert str(date.value) == "2021-06-15"

    def test_removing_a_date_row_deletes_it_from_the_project(self, client):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Date", owner=org)
        date = ProjectDateFactory(related=project, type="Start", value="2020-01-01")
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=1),
                "dates-0-id": date.pk,
                "dates-0-type": "Start",
                "dates-0-value": "2020-01-01",
                "dates-0-DELETE": "on",
            },
        )

        assert response.status_code == 302
        assert not project.dates.filter(pk=date.pk).exists()

    def test_a_backwards_pair_both_newly_added_is_refused_and_saves_nothing(
        self, client
    ):
        # A per-row check sees neither date, since each looks its sibling up in the
        # database.
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Backwards Pair", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(),
                **_date_management_data(total=2, initial=0),
                "dates-0-type": "Start",
                "dates-0-value": "2020-06-01",
                "dates-1-type": "End",
                "dates-1-value": "2010-01-01",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert formsets["dates"].non_form_errors()
        assert not project.dates.exists()

    def test_a_backwards_pair_with_the_start_already_stored_is_refused_and_saves_nothing(
        self, client
    ):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Backwards Pair", owner=org)
        start = ProjectDateFactory(related=project, type="Start", value="2020-06-01")
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(),
                **_date_management_data(total=2, initial=1),
                "dates-0-id": start.pk,
                "dates-0-type": "Start",
                "dates-0-value": "2020-06-01",
                "dates-1-type": "End",
                "dates-1-value": "2010-01-01",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert not formsets["dates"].is_valid()
        assert not project.dates.filter(type="End").exists()

    def test_a_start_date_with_no_end_date_is_accepted(self, client):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Start Only", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=0),
                "dates-0-type": "Start",
                "dates-0-value": "2020-06-01",
            },
        )

        assert response.status_code == 302
        assert project.dates.filter(type="Start", value="2020-06-01").exists()


@pytest.mark.django_db
class TestAttributesSaveIsOneAtomicSubmission:
    def test_an_invalid_identifier_row_blocks_the_projects_own_field_changes_too(
        self, client
    ):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                "name": "Renamed",
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "",
            },
        )

        assert response.status_code == 200
        assert project.identifiers.count() == 0
        project.refresh_from_db()
        assert project.name == "Original Name"

    def test_a_successful_submission_redirects_to_the_projects_own_page(self, client):
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})

        response = client.post(
            url,
            data={
                **_project_field_data(project),
                "name": "Renamed",
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )

        assert response.status_code == 302
        assert response.url == reverse(
            "project:overview", kwargs={"uuid": project.uuid}
        )


@pytest.mark.django_db
class TestProjectDeleteView:
    def test_project_delete_anonymous_redirects_to_login(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

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
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert Project.objects.filter(pk=project.pk).exists()

    def test_project_delete_without_permission_on_a_private_project_404(self, client):
        project = ProjectFactory()
        user = UserFactory()
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_project_delete_without_permission_on_a_public_project_403(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_project_delete_without_permission_anonymous_on_a_private_project_404(
        self, client
    ):
        project = ProjectFactory()
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_project_delete_with_permission_200(self, client):
        project = ProjectFactory()
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_project_delete_wrong_name_shows_error(self, client):
        project = ProjectFactory(name="My Project")
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Wrong Name"})
        assert response.status_code == 200
        assert "confirmation" in response.context["form"].errors
        assert Project.objects.filter(pk=project.pk).exists()

    def test_project_delete_confirmation_ignores_surrounding_whitespace(self, client):
        project = ProjectFactory(name="Spaced Project")
        pk = project.pk
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "  Spaced Project  "})
        assert response.status_code == 302
        assert response.url == reverse("project-list")
        assert not Project.objects.filter(pk=pk).exists()

    def test_project_delete_blocks_public_datasets(self, client):
        project = ProjectFactory(name="Dataset Project")
        Dataset.objects.create(
            name="Public Dataset", project=project, visibility=Visibility.PUBLIC
        )
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Dataset Project"})
        assert response.status_code == 200
        assertContains(response, "Public Dataset")
        assert Project.objects.filter(pk=project.pk).exists()

    def test_project_delete_refused_page_hides_confirmation_and_delete_control(
        self, client
    ):
        project = ProjectFactory(name="Dataset Project")
        Dataset.objects.create(
            name="Public Dataset", project=project, visibility=Visibility.PUBLIC
        )
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Dataset Project"})
        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assertNotContains(response, 'id="id_confirmation"')
        assertNotContains(response, 'id="delete-submit-btn"')

    def test_project_delete_get_shows_refusal_without_submitting(self, client):
        project = ProjectFactory(name="Dataset Project")
        Dataset.objects.create(
            name="Public Dataset", project=project, visibility=Visibility.PUBLIC
        )
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assertContains(response, "Public Dataset")
        assertNotContains(response, 'id="id_confirmation"')

    def test_project_delete_evaluates_visibility_at_submission_time(self, client):
        project = ProjectFactory(name="Dataset Project")
        dataset = Dataset.objects.create(
            name="Soon Public Dataset", project=project, visibility=Visibility.PRIVATE
        )
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})

        get_response = client.get(url)
        assert get_response.status_code == 200
        assert get_response.context["is_protected"] is False

        dataset.visibility = Visibility.PUBLIC
        dataset.save()

        response = client.post(url, data={"confirmation": "Dataset Project"})
        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assertContains(response, "Soon Public Dataset")
        assert Project.objects.filter(pk=project.pk).exists()

    def test_project_delete_allows_private_only_datasets(self, client):
        project = ProjectFactory(name="Private Dataset Project")
        Dataset.objects.create(
            name="Private Dataset", project=project, visibility=Visibility.PRIVATE
        )
        pk = project.pk
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Private Dataset Project"})
        assert response.status_code == 302
        assert response.url == reverse("project-list")
        assert not Project.objects.filter(pk=pk).exists()

    def test_project_delete_no_datasets_success(self, client):
        project = ProjectFactory(name="Empty Project")
        pk = project.pk
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Empty Project"})
        assert response.status_code == 302
        assert response.url == reverse("project-list")
        assert not Project.objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestProjectCardRendering:
    def _card_html(self, client):
        response = client.get(reverse("project-list"))
        assert response.status_code == 200
        return response, response.content.decode()

    def test_card_shows_the_status_label(self, client):
        project = ProjectFactory(
            name="Rift Basin Survey",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
        )
        response, _ = self._card_html(client)
        assertContains(response, project.get_status_display())

    def test_card_reports_the_public_dataset_count(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        response, _ = self._card_html(client)
        assertContains(response, "2 datasets")

    def test_card_counts_one_dataset_in_the_singular(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        response, _ = self._card_html(client)
        assertContains(response, "1 dataset")

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

    def test_the_whole_card_is_the_link(self, client, public_project):
        response, _ = self._card_html(client)
        assertContains(response, f'href="{public_project.get_absolute_url()}"')

    def test_card_renders_the_abstract_as_plain_text(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        ProjectDescriptionFactory(
            related=project,
            type="Abstract",
            value="## Objectives\n\nWe measure **heat flow** across the rift.",
        )
        response, html = self._card_html(client)
        assertContains(response, "Objectives")
        assertContains(response, "heat flow")
        assert "## Objectives" not in html
        assert "**heat flow**" not in html

    def test_card_caps_a_long_abstract_at_400_characters(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        ProjectDescriptionFactory(
            related=project, type="Abstract", value="borehole " * 200
        )
        response, _ = self._card_html(client)
        assert len(project.get_abstract_summary()) <= 400
        assertContains(response, project.get_abstract_summary()[:120])

    def test_card_renders_keywords_as_badges_and_not_as_links(self, client):
        from research_vocabs.models import Concept

        keyword = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        project.keywords.add(keyword)
        response, html = self._card_html(client)
        assertContains(response, keyword.label)
        assert f'href="?keywords={keyword.pk}"' not in html
        assert f">{keyword.label}</a>" not in html

    def test_card_shows_the_project_uuid_with_a_copy_control(
        self, client, public_project
    ):
        response, html = self._card_html(client)
        assertContains(response, public_project.uuid)
        assert "clipboard" in html

    def test_card_shows_the_last_modified_date(self, client, public_project):
        response, _ = self._card_html(client)
        assertContains(response, public_project.modified.strftime("%b"))

    def test_card_shows_contributor_names_and_the_owning_organization(self, client):
        person = PersonFactory(name="Ada Lovelace")
        organization = OrganizationFactory(name="Institute of Deep Time")
        project = ProjectFactory(owner=organization, visibility=Visibility.PUBLIC)
        project.add_contributor(person)
        response, _ = self._card_html(client)
        assertContains(response, "Ada Lovelace")
        assertContains(response, "Institute of Deep Time")

    def test_the_placeholder_is_hidden_from_assistive_technology(self, client):
        ProjectFactory(image=None, visibility=Visibility.PUBLIC)
        _, html = self._card_html(client)
        placeholder = re.search(r'<span class="record-card__placeholder"([^>]*)>', html)
        assert placeholder
        assert 'aria-hidden="true"' in placeholder.group(1)

    def test_stylesheet_is_linked_once_per_page_not_once_per_card(self, client):
        for _ in range(3):
            ProjectFactory(visibility=Visibility.PUBLIC)
        response, html = self._card_html(client)
        assert html.count("css/fairdm.css") == 1
        assert len(response.context["object_list"]) == 3

    def test_stylesheet_is_linked_from_the_base_template_not_a_page_template(
        self, client
    ):
        response = client.get(reverse("dataset-list"))
        assert response.status_code == 200
        assert "css/fairdm.css" in response.content.decode()


@pytest.mark.django_db
class TestProjectListingQueryCount:
    @staticmethod
    def _build_projects(count):
        from research_vocabs.models import Concept

        keywords = list(Concept.objects.filter(vocabulary__name="fairdm-roles")[:3])
        for index in range(count):
            project = ProjectFactory(
                name=f"Survey {index}", visibility=Visibility.PUBLIC
            )
            ProjectDescriptionFactory(
                related=project,
                type="Abstract",
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

        self._build_projects(19)
        client.get(url)
        with django_assert_num_queries(baseline):
            response = client.get(url)
            assert response.status_code == 200
            assert len(response.context["object_list"]) == 20


@pytest.mark.django_db
class TestProjectCardEmitsNoTemplateComments:
    # A multi-line `{# #}` is not a comment: its text is emitted verbatim (#330).
    def test_no_comment_syntax_survives_into_the_rendered_page(self, client):
        from research_vocabs.models import Concept

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        project.keywords.add(
            *Concept.objects.filter(vocabulary__name="fairdm-roles")[:3]
        )
        project.add_contributor(PersonFactory())
        ProjectDescriptionFactory(
            related=project, type="Abstract", value="An abstract."
        )

        html = client.get(reverse("project-list")).content.decode()

        assert "{#" not in html
        assert "#}" not in html
        assert "{%" not in html


@pytest.mark.django_db
class TestDeletionPageBackControl:
    def test_the_back_control_is_a_non_empty_link_that_resolves(self, client):
        project = ProjectFactory(name="Has A Back Link")
        user = UserFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})

        response = client.get(url)
        content = response.content.decode()

        match = re.search(
            r'<a[^>]*href="([^"]*)"[^>]*><i class="bi bi-arrow-left"', content
        )
        assert match is not None, "the back control is not rendered as a link"
        back_href = match.group(1)
        assert back_href != ""
        resolve(back_href)
