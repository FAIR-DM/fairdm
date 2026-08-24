"""
Integration tests for fairdm.core.project views.

Tests the interaction between views, forms, and models, verifying complete
request/response cycles for project CRUD operations.
"""

import time

import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from fairdm.contrib.contributors.models import Organization
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.factories import (
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


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

        # Verify form has required fields
        form = response.context["form"]
        assert "name" in form.fields
        assert "status" in form.fields
        assert "visibility" in form.fields

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

        # Verify redirect URL contains project UUID
        assert project.uuid in response.url

    def test_create_project_records_creator(self, authenticated_client, user):
        """Test that creating a project through the portal records the requesting
        user as its creator.

        Requirement: FR-017 - A project must record the user who created it.
        User Story: US7 - Know who made a project and when it last changed.
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


# ---------------------------------------------------------------------------
# Phase 3 — User Story 1: Browse and Search the Project List
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectListView:
    """Smoke tests and behaviour tests for ProjectListView (US1)."""

    def test_project_list_anonymous_200(self, client):
        """T010 — GET /projects/ returns 200 for anonymous users."""
        url = reverse("project-list")
        response = client.get(url)
        assert response.status_code == 200

    def test_project_list_shows_only_public(self, client):
        """T011 — List shows only PUBLIC projects; PRIVATE projects are hidden."""
        public = ProjectFactory(name="Public Project", visibility=Visibility.PUBLIC)
        ProjectFactory(name="Private Project", visibility=Visibility.PRIVATE)

        url = reverse("project-list")
        response = client.get(url)

        assert response.status_code == 200
        assert public.name in str(response.content)
        assert "Private Project" not in str(response.content)

    def test_project_list_order_by_added(self, client):
        """T012 — ?o=added and ?o=-added return results in expected chronological order."""
        older = ProjectFactory(name="Older Project", visibility=Visibility.PUBLIC)
        time.sleep(0.01)
        newer = ProjectFactory(name="Newer Project", visibility=Visibility.PUBLIC)

        url = reverse("project-list")

        response_asc = client.get(url, {"o": "added"})
        assert response_asc.status_code == 200
        content_asc = str(response_asc.content)
        assert content_asc.index(older.name) < content_asc.index(newer.name)

        response_desc = client.get(url, {"o": "-added"})
        assert response_desc.status_code == 200
        content_desc = str(response_desc.content)
        assert content_desc.index(newer.name) < content_desc.index(older.name)


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


# ---------------------------------------------------------------------------
# Phase 4 — User Story 2: Create a New Project (additional tests)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectCreateViewExtended:
    """Additional tests for ProjectCreateView (US2, T016-T018a)."""

    def test_project_create_anonymous_redirects_to_login(self, client):
        """T016 — GET /projects/create/ by anonymous client returns 302 to login."""
        url = reverse("project-create")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_project_create_authenticated_200(self, authenticated_client):
        """T017 — GET /projects/create/ by authenticated client returns 200."""
        url = reverse("project-create")
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_project_create_redirects_to_detail(self, authenticated_client):
        """T018 — Valid POST redirects to the project's own registered page (project:overview)."""
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

    def test_project_create_assigns_permissions_and_roles(self, client, user):
        """T018a — After valid POST, creating user holds all 5 permissions and contributor roles."""
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

        contributor = project.contributors.filter(contributor=user).first()
        assert contributor is not None, "User should be a contributor"
        role_names = list(contributor.roles.values_list("name", flat=True))
        for role in ["Creator", "ProjectMember", "ContactPerson"]:
            assert role in role_names, f"Missing contributor role: {role}"


# ---------------------------------------------------------------------------
# Phase 5 — User Story 3: Edit Project Core Attributes
# ---------------------------------------------------------------------------


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

    def test_project_update_success_redirects_to_detail(self, client):
        """T024a — Valid POST by permitted user returns 302 to project-detail URL."""
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
            },
        )
        assert response.status_code == 302
        expected_url = reverse("project:overview", kwargs={"uuid": project.uuid})
        assert response.url == expected_url


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

    def test_project_delete_blocks_public_datasets(self, client):
        """T032 — POST correct name but project has PUBLIC dataset returns 200 with protected_datasets; not deleted."""
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
        assert "protected_datasets" in response.context
        assert Project.objects.filter(pk=project.pk).exists()

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
