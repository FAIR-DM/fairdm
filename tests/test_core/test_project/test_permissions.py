"""
Integration tests for fairdm.core.project permissions.

Tests object-level permissions using django-guardian, verifying that project
creators receive appropriate permissions and access control works correctly.
"""

import pytest
from guardian.shortcuts import get_perms

from fairdm.core.choices import ProjectStatus
from fairdm.factories import UserFactory
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectPermissions:
    """Integration tests for project-level permissions."""

    def test_creator_gets_full_permissions(self, client):
        """Test that project creator receives all permissions automatically.

        Requirement: FR-007 - Creator receives full project permissions.
        User Story: US1 - Automatic permission assignment on creation.
        """
        from django.urls import reverse

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        # Create user and organization
        user = UserFactory(email="creator@example.com")
        owner = Organization.objects.create(name="Test Organization")
        client.force_login(user)

        # Create project through view
        url = reverse("project-create")
        form_data = {
            "name": "Creator's Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
        }
        response = client.post(url, data=form_data)

        # Get created project
        project = Project.objects.get(name="Creator's Project")

        # Verify creator has all project permissions
        user_perms = get_perms(user, project)

        # Expected permissions for creator
        expected_perms = [
            "view_project",
            "change_project",
            "delete_project",
            "change_project_metadata",
            "change_project_settings",
        ]

        for perm in expected_perms:
            assert perm in user_perms, f"Creator missing '{perm}' permission"

    def test_non_contributor_cannot_edit_private_project(self, client):
        """Test that non-contributors cannot edit private projects.

        Requirement: FR-004 - Private projects require permissions.
        User Story: US1 - Access control for private projects.
        """
        from django.urls import reverse

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        # Create owner and project
        owner_user = UserFactory(email="owner@example.com")
        owner_org = Organization.objects.create(name="Owner Organization")

        project = Project.objects.create(
            name="Private Project", status=ProjectStatus.CONCEPT, visibility=Visibility.PRIVATE, owner=owner_org
        )

        # Create different user (non-contributor)
        other_user = UserFactory(email="other@example.com")
        client.force_login(other_user)

        # Attempt to access edit view
        url = reverse("project-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        # Verify access denied (403) or redirect
        assert response.status_code in [403, 302]

    def test_user_with_change_permission_can_edit(self, client):
        """Test that users with change permission can edit projects.

        Requirement: FR-007 - Object-level permissions control access.
        User Story: US1 - Granular permission assignment.
        """
        from django.urls import reverse
        from guardian.shortcuts import assign_perm

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        # Create owner and project
        owner_org = Organization.objects.create(name="Owner Organization")

        project = Project.objects.create(
            name="Shared Project", status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PRIVATE, owner=owner_org
        )

        # Create editor user and assign permission
        editor = UserFactory(email="editor@example.com")
        assign_perm("change_project", editor, project)
        assign_perm("view_project", editor, project)

        client.force_login(editor)

        # Access edit view
        url = reverse("project-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        # Verify successful access
        assert response.status_code == 200
        assert "form" in response.context
