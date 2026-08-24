"""
Integration tests for fairdm.core.project views.

Tests the interaction between views, forms, and models, verifying complete
request/response cycles for project CRUD operations.
"""

import re
import time

import pytest
from django import forms
from django.urls import reverse
from django.views.generic import CreateView
from guardian.shortcuts import assign_perm
from pytest_django.asserts import assertContains, assertNotContains

from fairdm.contrib.contributors.models import Organization
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.project.views import ProjectCreateView, ProjectListView
from fairdm.factories import (
    OrganizationFactory,
    PersonFactory,
    ProjectDateFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from fairdm.views import FairDMCreateView, FairDMListView


@pytest.mark.django_db
class TestProjectCreateView:
    """Integration tests for project creation view."""

    def test_authenticated_user_can_access_create_view(self, authenticated_client):
        """Test that authenticated users can access the project creation page.

        Requirement: FR-001 - Users must be able to create projects.
        User Story: US1 - Access to streamlined project creation form.
        """
        # Access create view
        url = reverse("project-create")
        response = authenticated_client.get(url)

        # Verify successful access
        assert response.status_code == 200
        assert "form" in response.context

        # T018 — The form offers exactly name, status and visibility, and nothing
        # else. Set equality, not presence: an extra field (owner, image, funding —
        # all present on the full ProjectForm) would pass a presence check but defeats
        # the point of a streamlined creation form.
        form = response.context["form"]
        assert set(form.fields.keys()) == {"name", "status", "visibility"}

    def test_anonymous_user_redirects_to_login(self, client):
        """Test that anonymous users are redirected to login.

        Requirement: FR-001 - Project creation requires authentication.
        User Story: US1 - Security control for project creation.
        """
        url = reverse("project-create")
        response = client.get(url)

        # Verify redirect to login
        assert response.status_code == 302
        assert "/accounts/login/" in response.url or "/login/" in response.url

    def test_create_project_redirects_to_detail(self, authenticated_client):
        """Test that successful project creation redirects to detail page.

        Requirement: FR-001 - Successful creation shows project details.
        User Story: US1 - User is redirected to project detail after creation.

        T024 — The redirect target is asserted by reversal against the current route
        name (`project:overview`), not against a literal path: the address moved in an
        earlier story and a literal would pin the wrong thing.
        """
        # Create user and organization
        owner = Organization.objects.create(name="Test Organization")

        # Submit create form
        url = reverse("project-create")
        form_data = {
            "name": "New Test Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
        }
        response = authenticated_client.post(url, data=form_data)

        # Verify redirect to detail page
        assert response.status_code == 302

        # Verify project was created
        project = Project.objects.get(name="New Test Project")
        assert project.pk is not None

        # Verify the redirect targets the project's own page, at its exact address.
        expected_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assert response.url == expected_url

    def test_create_project_records_creator(self, authenticated_client, user):
        """Test that creating a project through the portal records the requesting
        user as its creator.

        Requirement: FR-017 - A project must record the user who created it.
        User Story: US7 - Know who made a project and when it last changed.

        T023 — After creation the project records the signed-in user as its creator.
        """
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
        """Test that validation errors are displayed inline.

        Requirement: FR-001 - Clear validation feedback.
        User Story: US1 - Users see helpful error messages.

        T020 — Submitting without a name reports an error and creates nothing. Asserted
        as a count as well as the error, since an error alone does not rule out a
        project having been created anyway.
        """
        # Submit form with missing required field (name)
        url = reverse("project-create")
        form_data = {
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
        }
        response = authenticated_client.post(url, data=form_data)

        # Verify form redisplays with errors
        assert response.status_code == 200
        assert "form" in response.context

        form = response.context["form"]
        assert not form.is_valid()
        assert "name" in form.errors
        assert Project.objects.count() == 0


# ---------------------------------------------------------------------------
# Phase 3 — User Story 1: Browse and Search the Project List
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectListViewEmitsNoDeprecationWarning:
    """T072 — `has_create_permission`/`has_list_permission` are the superseded names the
    interface layer still honours, with a warning, until it removes them in 0.18. The suite
    silences warnings file-wide, so the assertion needs its own explicit filter."""

    @pytest.mark.filterwarnings("error::mvp.warnings.MVPDeprecationWarning")
    def test_rendering_the_listing_emits_no_deprecation_warning(self, client):
        response = client.get(reverse("project-list"))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 013 US-1: Find a project — reaching, searching, ordering and filtering the
# public listing. Uses the project test package's conftest fixtures for
# public/private projects and permission-holding users, per Article X.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectListing:
    """T006-T016 — the public project listing: reachability, visibility,
    search, ordering, filters, empty state and the listing entry's link."""

    def test_listing_returns_200_for_anonymous_visitor(self, client):
        """T006 — the listing at `project-list` returns 200 to an anonymous
        visitor."""
        response = client.get(reverse("project-list"))
        assert response.status_code == 200

    def test_listing_shows_only_the_public_project_to_an_anonymous_visitor(
        self, client, public_project, private_project
    ):
        """T007 — with a public and a private project, an anonymous visitor
        sees only the public one. Asserts the entries, not the queryset."""
        response = client.get(reverse("project-list"))
        entries = list(response.context["object_list"])
        assert public_project in entries
        assert private_project not in entries

    def test_listing_excludes_the_signed_in_owners_own_private_project(
        self, client, user_with_change_permission
    ):
        """T007 — a signed-in user who owns a private project still does not
        see it in the listing; the listing shows public projects only."""
        client.force_login(user_with_change_permission)
        response = client.get(reverse("project-list"))
        entries = list(response.context["object_list"])
        assert user_with_change_permission.project not in entries

    def test_listing_search_by_name_returns_the_matching_project_only(
        self, client
    ):
        """T008 — a distinctive word from one project's name, searched,
        returns that project and excludes the others."""
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

    def test_listing_search_by_identifier_value_returns_the_project(
        self, client
    ):
        """T009 — searching a project's identifier value returns that
        project."""
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        identifier = ProjectIdentifierFactory(related=project)
        response = client.get(reverse("project-list"), {"q": identifier.value})
        entries = list(response.context["object_list"])
        assert project in entries

    def test_listing_ordered_by_name_returns_alphabetical_order(self, client):
        """T010 — `?o=name` returns projects in alphabetical order."""
        bravo = ProjectFactory(name="Bravo Project", visibility=Visibility.PUBLIC)
        alpha = ProjectFactory(name="Alpha Project", visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"o": "name"})
        entries = list(response.context["object_list"])
        assert entries.index(alpha) < entries.index(bravo)

    def test_listing_ordered_by_name_reversed_returns_reverse_alphabetical_order(
        self, client
    ):
        """T010 — `?o=-name` returns the reverse order. Asserted separately
        from the ascending case, since an unordered queryset that happens to
        arrive sorted would pass a single-direction check."""
        bravo = ProjectFactory(name="Bravo Project", visibility=Visibility.PUBLIC)
        alpha = ProjectFactory(name="Alpha Project", visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"o": "-name"})
        entries = list(response.context["object_list"])
        assert entries.index(bravo) < entries.index(alpha)

    def test_listing_ordered_by_date_added_returns_oldest_first(self, client):
        """T011 — `?o=added` returns the oldest project first."""
        older = ProjectFactory(visibility=Visibility.PUBLIC)
        time.sleep(0.01)
        newer = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"o": "added"})
        entries = list(response.context["object_list"])
        assert entries.index(older) < entries.index(newer)

    def test_listing_ordered_by_date_added_reversed_returns_newest_first(
        self, client
    ):
        """T011 — `?o=-added` returns the newest project first. Asserted
        separately from the ascending case."""
        older = ProjectFactory(visibility=Visibility.PUBLIC)
        time.sleep(0.01)
        newer = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"o": "-added"})
        entries = list(response.context["object_list"])
        assert entries.index(newer) < entries.index(older)

    def test_listing_status_filter_narrows_to_the_matching_status(self, client):
        """T012 — applying the status filter returns only projects of that
        status. Attaches the portal's existing `ProjectFilter` (already
        `filterset_class` on `ProjectListView`) rather than a new filter."""
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
        """T013 — the portal's owner filter narrows the listing to projects
        held by the chosen owner."""
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
        """T013 — the portal's contributor filter narrows the listing to
        projects crediting the chosen contributor."""
        person = PersonFactory()
        matching = ProjectFactory(visibility=Visibility.PUBLIC)
        matching.add_contributor(person)
        other = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project-list"), {"contributor": person.pk})
        entries = list(response.context["object_list"])
        assert matching in entries
        assert other not in entries

    def test_listing_tag_filter_narrows_to_the_matching_tag(self, client):
        """T013 — the portal's tag filter narrows the listing to projects
        carrying the chosen tag."""
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
        """T014 — a search matching no project renders the listing's own
        empty state, rather than a blank page."""
        response = client.get(
            reverse("project-list"), {"q": "no-project-should-match-this-term"}
        )
        assert response.status_code == 200
        assert list(response.context["object_list"]) == []
        assertContains(response, "There&#x27;s nothing here yet")

    def test_listing_entry_links_to_its_projects_page(self, client, public_project):
        """T015 — each listing entry links to its project's page, reached
        through the record's own `get_absolute_url`."""
        response = client.get(reverse("project-list"))
        expected_url = public_project.get_absolute_url()
        assertContains(response, f'href="{expected_url}"')

    def test_listing_view_derives_from_the_portals_own_list_base_class(self):
        """T016 — `ProjectListView` derives from the portal's own
        `FairDMListView`, rather than from Django's generic `ListView`
        directly."""
        assert FairDMListView in ProjectListView.__bases__


# ---------------------------------------------------------------------------
# Phase 4 — User Story 2: Create a New Project (additional tests)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectCreateViewExtended:
    """Additional tests for ProjectCreateView (US2, T017-T025)."""

    def test_project_create_anonymous_redirects_to_login(self, client):
        """T017 — An anonymous visitor opening the creation page is redirected to the exact
        sign-in address, not merely redirected somewhere."""
        url = reverse("project-create")
        response = client.get(url)
        assert response.status_code == 302
        expected_url = f"{reverse('account_login')}?next={url}"
        assert response.url == expected_url

    def test_project_create_authenticated_200(self, authenticated_client):
        """T017 — GET /projects/create/ by authenticated client returns 200."""
        url = reverse("project-create")
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_visibility_renders_as_radio_with_public_preselected(self, authenticated_client):
        """T019 — Visibility renders as a visible choice between its options, with Public
        pre-selected. The model's own default stays Private — it serves records created
        outside the portal, where no one sees a control — and the form's default is
        deliberately Public. The two disagreeing is a recorded decision (decisions.md)."""
        url = reverse("project-create")
        response = authenticated_client.get(url)
        form = response.context["form"]

        assert isinstance(form.fields["visibility"].widget, forms.RadioSelect)
        assertContains(response, "Private")
        assertContains(response, "Public")

        content = response.content.decode()
        public_input = re.search(
            rf'<input[^>]*name="visibility"[^>]*value="{Visibility.PUBLIC}"[^>]*>', content
        )
        private_input = re.search(
            rf'<input[^>]*name="visibility"[^>]*value="{Visibility.PRIVATE}"[^>]*>', content
        )
        assert public_input is not None and "checked" in public_input.group(0)
        assert private_input is not None and "checked" not in private_input.group(0)

    def test_project_create_redirects_to_detail(self, authenticated_client):
        """T024 — Valid POST redirects to the project's own registered page (project:overview),
        asserted by reversal against the route name, at its exact address."""
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
        """T021 — After creation the creator holds view, change, delete, change-metadata
        and change-settings permission on the new project. Each of the five is asserted
        by name, then the assignment itself."""
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

    def test_creator_added_as_contributor_with_roles(self, client, user):
        """T022 — After creation the creator appears among the project's contributors
        carrying Creator, ProjectMember and ContactPerson. The three roles are asserted
        on the contribution, not merely that a contribution exists."""
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
        """T025 — The creation view derives from the portal's own create base class,
        FairDMCreateView, rather than Django's generic CreateView directly."""
        assert issubclass(ProjectCreateView, FairDMCreateView)
        assert FairDMCreateView in ProjectCreateView.__mro__
        assert CreateView not in ProjectCreateView.__bases__


# ---------------------------------------------------------------------------
# Phase 5 — User Story 3: Edit Project Core Attributes
# ---------------------------------------------------------------------------


def _identifier_management_data(total=0, initial=0):
    """Management-form boilerplate for the attributes page's identifiers row set
    (`fairdm/core/related_records.py` `ProjectIdentifierInline`, prefix `identifiers` from
    `AbstractIdentifier.Meta.default_related_name`)."""
    return {
        "identifiers-TOTAL_FORMS": str(total),
        "identifiers-INITIAL_FORMS": str(initial),
        "identifiers-MIN_NUM_FORMS": "0",
        "identifiers-MAX_NUM_FORMS": "1000",
    }


def _date_management_data(total=0, initial=0):
    """Management-form boilerplate for the attributes page's dates row set
    (`fairdm/core/related_records.py` `ProjectDateInline`, prefix `dates` from
    `AbstractDate.Meta.default_related_name`)."""
    return {
        "dates-TOTAL_FORMS": str(total),
        "dates-INITIAL_FORMS": str(initial),
        "dates-MIN_NUM_FORMS": "0",
        "dates-MAX_NUM_FORMS": "1000",
    }


@pytest.mark.django_db
class TestProjectUpdateView:
    """Smoke tests and behaviour tests for ProjectUpdateView (US3)."""

    def test_project_update_anonymous_redirects_to_login(self, client):
        """T022 — GET /projects/<uuid>/update/ by anonymous client returns 302."""
        project = ProjectFactory()
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_project_update_without_permission_403(self, client):
        """T023 — Authenticated client without change_project returns 403."""
        project = ProjectFactory()
        other_user = UserFactory()
        client.force_login(other_user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_project_update_with_permission_200(self, client):
        """T024 — Client with change_project permission returns 200."""
        project = ProjectFactory()
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_changing_name_status_visibility_and_owner_each_persists(self, client):
        """T031 — Each of name, status, visibility and owner is changed and submitted, and each
        persists, asserted one field at a time against a fresh copy of the same starting
        project."""
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
            assign_perm("change_project", user, project)
            client.force_login(user)
            url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})
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
        """T032 — An uploaded image persists, and submitting the clear checkbox removes it."""
        import io

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Image", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})
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
        """T033 — An empty name is refused, and the project's stored name is unchanged."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T024a — Valid POST by permitted user returns 302 to project-detail URL.

        T034 — Updated to carry the identifiers row set's management-form data: the page now
        attaches that formset (`fairdm/core/related_records.py` `ProjectIdentifierInline`), and
        a submission carrying no bookkeeping for it fails formset validation.

        T040 — Updated again to carry the dates row set's management-form data for the same
        reason, once that formset is attached too.
        """
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})
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
    """The attributes form's own field values, unchanged from `project`."""
    return {
        "name": project.name,
        "status": project.status,
        "visibility": project.visibility,
        "owner": project.owner_id,
    }


@pytest.mark.django_db
class TestAttributesIdentifierRowSet:
    """The attributes page's identifier row set (013 plan P3): existing identifiers presented
    one row each, added, changed and removed through the page."""

    def test_existing_identifiers_are_presented_one_row_each_with_no_blank_row_beyond_them(
        self, client
    ):
        """T034 — Opening the page with an existing identifier offers exactly one row for it
        and no blank row beyond."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Identifier", owner=org)
        ProjectIdentifierFactory(related=project, type="DOI", value="10.1/existing")
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        identifier_formset = formsets["identifiers"]
        assert identifier_formset.initial_form_count() == 1
        assert len(identifier_formset.forms) == 1

    def test_adding_an_identifier_of_a_chosen_type_records_it_against_the_project(
        self, client
    ):
        """T035 — A newly added identifier row is recorded against the project."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="No Identifiers Yet", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T036 — Submitting a changed value for an existing identifier row persists it."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Identifier", owner=org)
        identifier = ProjectIdentifierFactory(
            related=project, type="DOI", value="10.1/original"
        )
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T037 — Checking DELETE on an existing identifier row and submitting removes it."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Identifier", owner=org)
        identifier = ProjectIdentifierFactory(
            related=project, type="DOI", value="10.1/to-remove"
        )
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T038 — Submitting an identifier value already recorded against a different project
        reports the error on that field and saves nothing, including the project's own
        attributes changed in the same submission (`AbstractIdentifier.clean()`,
        `fairdm/core/abstract.py:354`, checks `value` across every concrete subclass)."""
        org = Organization.objects.create(name="Test Org")
        other_project = ProjectFactory(name="Other Project", owner=org)
        ProjectIdentifierFactory(related=other_project, type="DOI", value="10.1/taken")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T039 — Two new rows carrying the same identifier value in one submission report
        the collision and save neither (`value` carries `unique=True` on the concrete model,
        so `BaseModelFormSet.validate_unique()` catches the in-formset duplicate)."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="No Identifiers Yet", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
    """The attributes page's date row set (013 plan P3): existing dates presented one row each,
    built from the shared declaration (`related_records.ProjectDateInline`) with the
    date-ordering rule (`formsets.date_ordering_formset`, parameterised on
    `ProjectDate.START_TYPE`/`END_TYPE`)."""

    def test_existing_dates_are_presented_one_row_each_with_no_blank_row_beyond_them(
        self, client
    ):
        """T040 — Opening the page with an existing date offers exactly one row for it and no
        blank row beyond."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Date", owner=org)
        ProjectDateFactory(related=project, type="Start", value="2020-01-01")
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

        response = client.get(url)

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        date_formset = formsets["dates"]
        assert date_formset.initial_form_count() == 1
        assert len(date_formset.forms) == 1

    def test_adding_a_date_of_a_chosen_type_records_it_against_the_project(self, client):
        """T041 — A newly added date row is recorded against the project."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="No Dates Yet", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T042 — Submitting a changed value for an existing date row persists it."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Date", owner=org)
        date = ProjectDateFactory(related=project, type="Start", value="2020-01-01")
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T043 — Checking DELETE on an existing date row and submitting removes it."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Has Date", owner=org)
        date = ProjectDateFactory(related=project, type="Start", value="2020-01-01")
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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

    def test_a_backwards_pair_both_newly_added_is_refused_and_saves_nothing(self, client):
        """T044 — An end date earlier than the start date, both submitted as new rows in the
        same submission, is refused. A per-row check would see neither, since each looks its
        sibling up in the database and finds no unsaved sibling
        (`ProjectDate.clean()`, `fairdm/core/project/models.py:196-239`) — this is exactly the
        case the formset-level rule exists for (`formsets.date_ordering_formset`)."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Backwards Pair", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T044 — An end date earlier than an already-stored start date is refused too, with
        the existing start row resubmitted unchanged alongside the new end row. Here the
        per-row model check (`ProjectDate.clean()`) already catches it, since the sibling is in
        the database — unlike the both-new case above, where it is the formset-level rule
        alone that does."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Backwards Pair", owner=org)
        start = ProjectDateFactory(related=project, type="Start", value="2020-06-01")
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T045 — A start date submitted with no end date is accepted: the ordering rule only
        compares the pair when both sides are present (`date_ordering_formset`)."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Start Only", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
    """The attributes page saves the parent and every row set inside one transaction
    (`mvp.views.inline.InlinesMixin.form_valid`): an invalid row anywhere refuses the whole
    submission, including changes to the project's own fields."""

    def test_an_invalid_identifier_row_blocks_the_projects_own_field_changes_too(
        self, client
    ):
        """T046 — An identifier row missing its required value, submitted alongside a valid
        name change, saves neither."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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
        """T047 — A valid submission redirects to the project's own page."""
        org = Organization.objects.create(name="Test Org")
        project = ProjectFactory(name="Original Name", owner=org)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})

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


# ---------------------------------------------------------------------------
# Phase 6 — User Story 4: Delete a Project
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectDeleteView:
    """Smoke tests and behaviour tests for ProjectDeleteView (US4)."""

    def test_project_delete_anonymous_redirects_to_login(self, client):
        """T028 — GET /projects/<uuid>/delete/ by anonymous client returns 302."""
        project = ProjectFactory()
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_project_delete_without_permission_403(self, client):
        """T029 — Authenticated client without delete_project returns 403."""
        project = ProjectFactory()
        user = UserFactory()
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_project_delete_with_permission_200(self, client):
        """T030 — Client with delete_project permission GET returns 200."""
        project = ProjectFactory()
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_project_delete_wrong_name_shows_error(self, client):
        """T031/T048 — POST with mismatched confirmation field returns 200 with form error; project not deleted."""
        project = ProjectFactory(name="My Project")
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Wrong Name"})
        assert response.status_code == 200
        assert "confirmation" in response.context["form"].errors
        assert Project.objects.filter(pk=project.pk).exists()

    def test_project_delete_confirmation_ignores_surrounding_whitespace(self, client):
        """T078 — the project's name typed with leading/trailing spaces is accepted (FR-037)."""
        project = ProjectFactory(name="Spaced Project")
        pk = project.pk
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "  Spaced Project  "})
        assert response.status_code == 302
        assert response.url == reverse("project-list")
        assert not Project.objects.filter(pk=pk).exists()

    def test_project_delete_blocks_public_datasets(self, client):
        """T083 — the refused page names each blocking public dataset in the rendered content
        (rewritten from asserting the invented ``protected_datasets`` context key, plan P4)."""
        project = ProjectFactory(name="Dataset Project")
        Dataset.objects.create(
            name="Public Dataset", project=project, visibility=Visibility.PUBLIC
        )
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Dataset Project"})
        assert response.status_code == 200
        assertContains(response, "Public Dataset")
        assert Project.objects.filter(pk=project.pk).exists()

    def test_project_delete_refused_page_hides_confirmation_and_delete_control(self, client):
        """T084 — the refused page explains why and offers neither the confirmation field nor a
        delete control; the shell's own protected-object branch withholds both."""
        project = ProjectFactory(name="Dataset Project")
        Dataset.objects.create(
            name="Public Dataset", project=project, visibility=Visibility.PUBLIC
        )
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Dataset Project"})
        assert response.status_code == 200
        assertContains(response, "This record cannot be deleted.")
        assertNotContains(response, 'id="id_confirmation"')
        assertNotContains(response, 'id="delete-submit-btn"')

    def test_project_delete_allows_private_only_datasets(self, client):
        """T032a — POST correct name + only PRIVATE datasets → project deleted, redirect to project-list."""
        project = ProjectFactory(name="Private Dataset Project")
        Dataset.objects.create(
            name="Private Dataset", project=project, visibility=Visibility.PRIVATE
        )
        pk = project.pk
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Private Dataset Project"})
        assert response.status_code == 302
        assert response.url == reverse("project-list")
        assert not Project.objects.filter(pk=pk).exists()

    def test_project_delete_no_datasets_success(self, client):
        """T032b — POST correct name + zero datasets → project deleted, redirect to project-list."""
        project = ProjectFactory(name="Empty Project")
        pk = project.pk
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)
        url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        response = client.post(url, data={"confirmation": "Empty Project"})
        assert response.status_code == 302
        assert response.url == reverse("project-list")
        assert not Project.objects.filter(pk=pk).exists()
