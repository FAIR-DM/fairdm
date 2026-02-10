"""
Integration tests for fairdm.core.project views.

Tests the interaction between views, forms, and models, verifying complete
request/response cycles for project CRUD operations.
"""

import pytest
from django.urls import reverse

from fairdm.core.choices import ProjectStatus
from fairdm.factories import UserFactory
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
        from fairdm.contrib.contributors.models import Organization

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
        from fairdm.core.project.models import Project

        project = Project.objects.get(name="New Test Project")
        assert project.pk is not None

        # Verify redirect URL contains project UUID
        assert project.uuid in response.url

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


@pytest.mark.django_db
class TestProjectDetailView:
    """Integration tests for project detail view."""

    def test_owner_can_view_private_project(self, client):
        """Test that project owner can view their private project.

        Requirement: FR-004 - Owners have full access to their projects.
        User Story: US1 - Project detail view accessible to owner.
        """
        from guardian.shortcuts import assign_perm

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        user = UserFactory(email="owner@example.com")
        owner_org = Organization.objects.create(name="Owner Organization")

        project = Project.objects.create(
            name="Private Project", status=ProjectStatus.CONCEPT, visibility=Visibility.PRIVATE, owner=owner_org
        )

        # Assign view permission to user
        assign_perm("view_project", user, project)

        client.force_login(user)
        url = reverse("project-detail", kwargs={"uuid": project.uuid})
        response = client.get(url)

        assert response.status_code == 200
        assert project.name in str(response.content)

    def test_public_project_accessible_without_login(self, client):
        """Test that public projects are accessible to anonymous users.

        Requirement: FR-004 - Public projects are discoverable.
        User Story: US1 - Public visibility enables sharing.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        owner = Organization.objects.create(name="Public Organization")

        project = Project.objects.create(
            name="Public Project", status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC, owner=owner
        )

        # Access without login
        url = reverse("project-detail", kwargs={"uuid": project.uuid})
        response = client.get(url)

        assert response.status_code == 200
        assert project.name in str(response.content)

    @pytest.mark.skip(
        reason="Detail/overview page for Project is not yet finalized, so this test is pending implementation."
    )
    def test_metadata_displays_on_detail_page(self, client):
        """Test that project metadata (descriptions, dates, identifiers) displays on detail page.

        Requirement: FR-010, FR-011, FR-005 - Metadata must be visible on detail pages.
        User Story: US2 - Rich metadata displays correctly for discovery and reuse.
        Implementation: T049 - Integration test for metadata display.

        Workflow:
        1. Create a project with metadata
        2. Access project detail page
        3. Verify all metadata types are displayed
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import (
            Project,
            ProjectDate,
            ProjectDescription,
            ProjectIdentifier,
        )

        owner = Organization.objects.create(name="Test Organization")

        # Create project
        project = Project.objects.create(
            name="Metadata Rich Project", status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC, owner=owner
        )

        # Add metadata
        ProjectDescription.objects.create(
            related=project, type="Abstract", value="This is a comprehensive abstract describing the project."
        )

        ProjectDate.objects.create(
            related=project,
            type="Start",
            value="2024-01-01",  # PartialDateField expects string format
        )

        ProjectIdentifier.objects.create(related=project, type="ISNI", value="0000 0001 2283 4400")

        # Access detail page
        url = reverse("project-detail", kwargs={"uuid": project.uuid})
        response = client.get(url)

        # Verify response is successful
        assert response.status_code == 200
        content = str(response.content)

        # Verify metadata is displayed
        assert "comprehensive abstract" in content.lower()
        assert "2024-01-01" in content or "January" in content  # Date format may vary
        assert "0000 0001 2283 4400" in content or "isni" in content.lower()
