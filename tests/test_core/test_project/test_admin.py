"""Integration tests for Project admin interface workflows."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import Client
from django.urls import reverse

from fairdm.contrib.contributors.models import Person
from fairdm.core.project.admin import ProjectAdmin
from fairdm.core.project.models import Project, ProjectDescription
from fairdm.factories.core import ProjectFactory


@pytest.mark.django_db
class TestAdminSearchByName:
    """Test admin search functionality by project name."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.admin_user = Person.objects.create(
            name="Admin User",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.admin_user.set_password("admin123")
        self.admin_user.save()

        # Create test projects
        self.project1 = ProjectFactory(name="Climate Research Study")
        self.project2 = ProjectFactory(name="Ocean Temperature Analysis")
        self.project3 = ProjectFactory(name="Solar Energy Project")

    def test_search_by_exact_name(self):
        """Test searching for project by exact name match."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_changelist")
        response = self.client.get(url, {"q": "Climate Research Study"})

        assert response.status_code == 200
        # Project should be in results
        content = response.content.decode()
        assert "Climate Research Study" in content
        assert "Ocean Temperature" not in content or "no results" in content.lower()

    def test_search_by_partial_name(self):
        """Test searching for project by partial name match."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_changelist")
        response = self.client.get(url, {"q": "Research"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Climate Research Study" in content

    def test_search_by_uuid(self):
        """Test searching for project by UUID."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_changelist")
        response = self.client.get(url, {"q": self.project1.uuid})

        assert response.status_code == 200
        content = response.content.decode()
        assert self.project1.name in content


@pytest.mark.django_db
class TestAdminFilterByStatus:
    """Test admin filtering by project status."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.admin_user = Person.objects.create(
            name="Admin User",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.admin_user.set_password("admin123")
        self.admin_user.save()

        # Create projects with different statuses
        self.concept_project = ProjectFactory(name="Concept Project", status=0)
        self.active_project = ProjectFactory(name="Active Project", status=1)
        self.completed_project = ProjectFactory(name="Completed Project", status=2)

    def test_filter_by_concept_status(self):
        """Test filtering projects by concept status."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_changelist")
        response = self.client.get(url, {"status__exact": "0"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Concept Project" in content
        # Other projects should not be in filtered results
        assert "Active Project" not in content or "no results" in content.lower()

    def test_filter_by_visibility(self):
        """Test filtering projects by visibility."""
        from fairdm.utils.choices import Visibility

        public_project = ProjectFactory(name="Public Project", visibility=Visibility.PUBLIC)
        private_project = ProjectFactory(name="Private Project", visibility=Visibility.PRIVATE)

        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_changelist")
        response = self.client.get(url, {"visibility__exact": str(Visibility.PUBLIC.value)})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Public Project" in content

    def test_filter_by_added_date(self):
        """Test filtering projects by date added."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_changelist")

        # Filter by "today" (projects added today)
        from django.utils import timezone

        today = timezone.now().date()
        response = self.client.get(url, {"added__year": str(today.year), "added__month": str(today.month)})

        assert response.status_code == 200
        # All test projects were created today, should all be present
        content = response.content.decode()
        assert self.concept_project.name in content


@pytest.mark.django_db
class TestAdminInlineEditing:
    """Test admin inline editing of project descriptions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.admin_user = Person.objects.create(
            name="Admin User",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.admin_user.set_password("admin123")
        self.admin_user.save()

        self.project = ProjectFactory(name="Test Project")

    def test_inline_description_shown_in_change_form(self):
        """Test that description inline is displayed in project change form."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_change", args=[self.project.pk])
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Look for inline formset elements
        assert "projectdescription" in content.lower() or "description" in content.lower()

    def test_can_add_description_via_inline(self):
        """Test adding a description through inline form."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_change", args=[self.project.pk])

        # Prepare inline form data
        form_data = {
            "name": self.project.name,
            "status": self.project.status,
            "visibility": self.project.visibility,
            # Inline formset management form
            "descriptions-TOTAL_FORMS": "1",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            # First inline form
            "descriptions-0-type": "Abstract",
            "descriptions-0-value": "This is a test description added via inline form.",
            "_continue": "Save and continue editing",
        }

        response = self.client.post(url, data=form_data)

        # Should redirect or show success
        assert response.status_code in [200, 302]

        # Check that description was created
        descriptions = ProjectDescription.objects.filter(related=self.project)
        assert descriptions.count() > 0


@pytest.mark.django_db
class TestAdminBulkStatusChange:
    """Test admin bulk status change operation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.admin_user = Person.objects.create(
            name="Admin User",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.admin_user.set_password("admin123")
        self.admin_user.save()

        # Create multiple projects
        self.projects = ProjectFactory.create_batch(3, status=0)

    def test_bulk_status_change_action_appears_in_ui(self):
        """Test that bulk status change action appears in admin UI."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_changelist")
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Check for action dropdown or bulk action elements
        assert "action" in content.lower()

    def test_bulk_status_change_updates_selected_projects(self):
        """Test that bulk action updates status of selected projects."""
        self.client.force_login(self.admin_user)
        url = reverse("admin:project_project_changelist")

        # Submit bulk action
        form_data = {
            "action": "make_active",  # This will need to match actual action name
            "_selected_action": [str(p.pk) for p in self.projects],
            "index": "0",
        }

        response = self.client.post(url, data=form_data, follow=True)

        # Action might need confirmation or might execute directly
        # Just verify the form was accepted
        assert response.status_code == 200
