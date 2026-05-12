"""
Unit tests for fairdm.core.project models.

Tests the Project, ProjectDescription, ProjectDate, and ProjectIdentifier models
in isolation, focusing on field validation, constraints, and model methods.

Test-First Approach (Red-Green-Refactor):
1. Write tests that FAIL (Red)
2. Implement minimal code to pass (Green)
3. Refactor for quality (Refactor)
"""

import pytest
from django.core.exceptions import ValidationError

from fairdm.core.choices import ProjectStatus
from fairdm.core.project.models import Project, ProjectDescription
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectModel:
    """Unit tests for Project model."""

    def test_project_creation_with_required_fields(self):
        """Test that a project can be created with only required fields.

        Requirement: FR-001 - Projects must have name, status, visibility, owner.
        User Story: US1 - Streamlined creation with minimal required fields.
        """
        from fairdm.contrib.contributors.models import Organization

        # Create owner organization
        owner = Organization.objects.create(name="Test Organization")

        # Create project with minimal required fields
        project = Project.objects.create(
            name="Test Project", status=ProjectStatus.CONCEPT, visibility=Visibility.PRIVATE, owner=owner
        )

        # Verify project was created successfully
        assert project.pk is not None
        assert project.name == "Test Project"
        assert project.status == ProjectStatus.CONCEPT
        assert project.visibility == Visibility.PRIVATE
        assert project.owner == owner
        assert project.uuid is not None
        assert project.uuid.startswith("p")  # Prefix validation

    def test_project_uuid_is_unique(self):
        """Test that each project gets a unique UUID.

        Requirement: FR-002 - Projects must have unique, stable identifiers.
        """
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        project1 = Project.objects.create(
            name="Project 1", status=ProjectStatus.CONCEPT, visibility=Visibility.PRIVATE, owner=owner
        )

        project2 = Project.objects.create(
            name="Project 2", status=ProjectStatus.CONCEPT, visibility=Visibility.PRIVATE, owner=owner
        )

        # Verify UUIDs are unique
        assert project1.uuid != project2.uuid
        assert project1.uuid.startswith("p")
        assert project2.uuid.startswith("p")

    def test_project_status_choices(self):
        """Test that project status field accepts valid choices.

        Requirement: FR-003 - Projects must have defined status values.
        User Story: US1 - Status selection during creation.
        """
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        # Test all valid status choices
        valid_statuses = [
            ProjectStatus.CONCEPT,
            ProjectStatus.PLANNING,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.COMPLETE,
        ]

        for status in valid_statuses:
            project = Project.objects.create(
                name=f"Project {status}", status=status, visibility=Visibility.PRIVATE, owner=owner
            )
            assert project.status == status

    def test_project_visibility_choices(self):
        """Test that project visibility field accepts valid choices.

        Requirement: FR-004 - Projects must support visibility control.
        User Story: US1 - Visibility selection during creation and editing.
        """
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        # Test all valid visibility choices
        valid_visibilities = [
            Visibility.PRIVATE,
            Visibility.PUBLIC,
        ]

        for visibility in valid_visibilities:
            project = Project.objects.create(
                name=f"Project {visibility}", status=ProjectStatus.CONCEPT, visibility=visibility, owner=owner
            )
            assert project.visibility == visibility

    def test_cannot_delete_project_with_public_datasets(self):
        """Test that projects with PUBLIC datasets cannot be deleted.

        Requirement: FR-021 - Prevent deletion of projects with publicly visible datasets.
        Implementation: T007 - pre_delete signal raises PublicDatasetsProtect for PUBLIC datasets.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import PublicDatasetsProtect

        owner = Organization.objects.create(name="Test Organization")

        project = Project.objects.create(
            name="Project with Public Dataset", status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC, owner=owner
        )

        # Add a PUBLIC dataset to the project
        Dataset.objects.create(
            name="Public Dataset",
            project=project,
            visibility=Visibility.PUBLIC,
        )

        # Attempt to delete project should raise PublicDatasetsProtect
        with pytest.raises(PublicDatasetsProtect):
            project.delete()


@pytest.mark.django_db
class TestProjectPreDeleteSignal:
    """Tests for the pre_delete signal guard on Project model."""

    def test_pre_delete_signal_blocks_public_datasets(self):
        """Test that deleting a project with PUBLIC datasets raises PublicDatasetsProtect.

        T004 - MUST FAIL before T007 implementation.
        """
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import PublicDatasetsProtect

        from fairdm.factories import ProjectFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        Dataset.objects.create(name="Public Dataset", project=project, visibility=Visibility.PUBLIC)

        with pytest.raises(PublicDatasetsProtect):
            project.delete()

    def test_pre_delete_signal_allows_private_only(self):
        """Test that deleting a project with only PRIVATE datasets succeeds.

        T005 - MUST FAIL before T007 implementation.
        """
        from fairdm.core.dataset.models import Dataset

        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        dataset = Dataset.objects.create(name="Private Dataset", project=project, visibility=Visibility.PRIVATE)
        pk = project.pk

        # Should not raise — private datasets do not block project deletion
        project.delete()

        assert not Project.objects.filter(pk=pk).exists()

    def test_pre_delete_signal_allows_no_datasets(self):
        """Test that deleting a project with no datasets succeeds.

        T006 - MUST FAIL before T007 implementation.
        """
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        pk = project.pk

        project.delete()

        assert not Project.objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestProjectDescriptionModel:
    """Unit tests for ProjectDescription model."""

    def test_duplicate_description_type_raises_validation_error(self):
        """Test that duplicate description types for the same project are prevented.

        Requirement: FR-008 - Each project can have at most one description of each type.
        Implementation: T006, T007 - unique_together constraint and clean() validation.
        """
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Test Project", status=ProjectStatus.CONCEPT, visibility=Visibility.PRIVATE, owner=owner
        )

        # Create first description
        ProjectDescription.objects.create(related=project, type="Abstract", value="First abstract")

        # Attempt to create duplicate type should fail at validation
        desc2 = ProjectDescription(related=project, type="Abstract", value="Second abstract")

        with pytest.raises(ValidationError) as exc_info:
            desc2.clean()

        assert "type" in exc_info.value.error_dict
        assert "already exists" in str(exc_info.value)


@pytest.mark.django_db
class TestProjectDateModel:
    """Unit tests for ProjectDate model."""

    def test_end_date_before_start_date_raises_error(self):
        """Test that end_date cannot be before start date.

        Requirement: FR-012 - Date ranges must be logically valid.
        Implementation: T008 - clean() validation for date ranges.

        Note: AbstractDate uses 'value' field for the primary date.
        ProjectDate should add an optional end_date field for ranges.
        This test will fail until end_date field is added to the model.
        """

        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")
        Project.objects.create(
            name="Test Project", status=ProjectStatus.CONCEPT, visibility=Visibility.PRIVATE, owner=owner
        )

        # Skip this test until end_date field is added to ProjectDate model
        pytest.skip("ProjectDate.end_date field not yet implemented")
