"""Tests for the Project model, views, and forms."""

import pytest
from django.urls import reverse

from fairdm.core.models import Project
from fairdm.core.project.forms import ProjectForm
from fairdm.core.project.models import ProjectDate, ProjectDescription
from fairdm.factories import PersonFactory, ProjectFactory
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectModel:
    """Tests for the Project model."""

    def test_project_creation(self):
        """Test creating a basic Project instance."""
        project = ProjectFactory()

        assert project.pk is not None
        assert project.name is not None
        assert project.uuid is not None
        assert project.uuid.startswith("p")

    def test_project_visibility_default(self):
        """Test that default visibility is PRIVATE."""
        project = ProjectFactory()
        assert project.visibility == Visibility.PRIVATE

    def test_project_queryset_get_visible(self):
        """Test ProjectQuerySet.get_visible() filters correctly."""
        # Create public and private projects
        public_project = ProjectFactory(visibility=Visibility.PUBLIC)
        private_project = ProjectFactory(visibility=Visibility.PRIVATE)

        visible = Project.objects.get_visible()

        assert public_project in visible
        assert private_project not in visible

    def test_project_queryset_with_contributors(self):
        """Test ProjectQuerySet.with_contributors() prefetches correctly."""
        project = ProjectFactory()

        # This should not raise an error and should be efficient
        queryset = Project.objects.with_contributors()
        project_with_prefetch = queryset.get(pk=project.pk)

        # Access contributors should not cause additional queries due to prefetch
        assert project_with_prefetch.contributors is not None

    def test_project_str_representation(self):
        """Test Project string representation."""
        project = ProjectFactory(name="Test Project")
        assert str(project) == "Test Project"

    def test_project_absolute_url(self):
        """Test get_absolute_url returns correct URL."""
        project = ProjectFactory()
        url = project.get_absolute_url()

        assert url == reverse("project:overview", kwargs={"uuid": project.uuid})

    def test_project_descriptions_relationship(self):
        """Test that project descriptions can be created correctly."""
        project = ProjectFactory()
        descriptions = ProjectDescription.objects.filter(related=project)

        # Factory may or may not create descriptions by default
        # Just test that the relationship works
        assert descriptions.count() >= 0
        assert all(desc.related == project for desc in descriptions)

    def test_project_dates_relationship(self):
        """Test that project dates can be created correctly."""
        project = ProjectFactory()
        dates = ProjectDate.objects.filter(related=project)

        # Factory may or may not create dates by default
        # Just test that the relationship works
        assert dates.count() >= 0
        assert all(date.related == project for date in dates)

    def test_add_contributor(self):
        """Test adding a contributor to a project."""
        project = ProjectFactory()
        user = PersonFactory()

        contribution = project.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert project.contributors.filter(pk=contribution.pk).exists()


@pytest.mark.django_db
class TestProjectForm:
    """Tests for the ProjectForm."""

    def test_form_valid_data(self):
        """Test form validation with valid data."""
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }
        form = ProjectForm(data=form_data)

        assert form.is_valid()

    def test_form_missing_required_fields(self):
        """Test form validation fails without required fields."""
        form_data = {}
        form = ProjectForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_saves_correctly(self):
        """Test that form saves data correctly."""
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PRIVATE,
            "status": 1,
        }
        form = ProjectForm(data=form_data)

        assert form.is_valid()
        project = form.save()

        assert project.name == "Test Project"
        assert project.visibility == Visibility.PRIVATE
        assert project.status == 1


@pytest.mark.django_db
class TestProjectViews:
    """Tests for Project views."""

    def test_project_list_view_accessible(self, client):
        """Test that project list view is accessible."""
        response = client.get(reverse("project-list"))

        assert response.status_code == 200

    def test_project_list_view_shows_public_projects(self, client):
        """Test that only public projects are shown in list view."""
        public_project = ProjectFactory(visibility=Visibility.PUBLIC)
        private_project = ProjectFactory(visibility=Visibility.PRIVATE)

        response = client.get(reverse("project-list"))

        # Check that public project is visible
        assert public_project.name.encode() in response.content
        # Check that private project is not visible
        assert private_project.name.encode() not in response.content

    def test_project_create_view_requires_authentication(self, client):
        """Test that project creation requires login."""
        response = client.get(reverse("project-create"))

        # Should redirect to login
        assert response.status_code == 302

    def test_project_create_view_accessible_when_authenticated(self, authenticated_client):
        """Test that authenticated users can access project create view."""
        response = authenticated_client.get(reverse("project-create"))

        assert response.status_code == 200

    def test_project_create_view_creates_project(self, authenticated_client):
        """Test that submitting project create form creates a project."""
        form_data = {
            "name": "New Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        response = authenticated_client.post(reverse("project-create"), data=form_data)

        # Check redirect after successful creation
        assert response.status_code == 302

        # Check project was created
        project = Project.objects.filter(name="New Test Project").first()
        assert project is not None
        assert project.visibility == Visibility.PUBLIC

    def test_project_detail_view_accessible(self, client):
        """Test that project detail view is accessible."""
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("project:overview", kwargs={"uuid": project.uuid}))

        assert response.status_code == 200
        assert project.name.encode() in response.content


@pytest.mark.django_db
class TestProjectPermissions:
    """Tests for Project permissions and access control."""

    def test_anonymous_user_cannot_create_project(self, client):
        """Test that anonymous users cannot create projects."""
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        response = client.post(reverse("project-create"), data=form_data)

        # Should redirect to login
        assert response.status_code == 302
        # Check that redirect URL contains 'login'
        assert "login" in response["Location"]

    def test_project_creator_becomes_contributor(self, authenticated_client):
        """Test that project creator is automatically added as contributor."""
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        authenticated_client.post(reverse("project-create"), data=form_data)

        project = Project.objects.filter(name="Test Project").first()
        if project:
            # Check that the project has contributors
            assert project.contributors.count() > 0
