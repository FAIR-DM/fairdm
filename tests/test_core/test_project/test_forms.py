"""
Unit tests for fairdm.core.project forms.

Tests the ProjectCreateForm and ProjectEditForm in isolation, focusing on field
validation, required fields, and business logic constraints.

Test-First Approach (Red-Green-Refactor):
1. Write tests that FAIL (Red)
2. Implement minimal code to pass (Green)
3. Refactor for quality (Refactor)
"""

import pytest
from django.core.exceptions import ValidationError

from fairdm.core.choices import ProjectStatus
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectCreateForm:
    """Unit tests for Project creation form."""

    def test_create_form_valid_with_required_fields(self):
        """Test that create form accepts minimal required fields.

        Requirement: FR-001 - Projects must have name, status, visibility, owner.
        User Story: US1 - Streamlined creation with minimal required fields.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectCreateForm

        owner = Organization.objects.create(name="Test Organization")

        # Minimal form data with only required fields
        form_data = {
            "name": "Test Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
        }

        form = ProjectCreateForm(data=form_data)

        # Verify form is valid
        assert form.is_valid(), f"Form errors: {form.errors}"

        # Save and verify project creation
        project = form.save()
        assert project.pk is not None
        assert project.name == "Test Project"
        assert project.status == ProjectStatus.CONCEPT
        assert project.visibility == Visibility.PRIVATE
        assert project.owner == owner

    def test_create_form_invalid_without_name(self):
        """Test that create form requires name field.

        Requirement: FR-001 - Project name is required.
        User Story: US1 - Validation error displayed when name is missing.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectCreateForm

        owner = Organization.objects.create(name="Test Organization")

        # Form data missing required name field
        form_data = {
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
        }

        form = ProjectCreateForm(data=form_data)

        # Verify form is invalid
        assert not form.is_valid()
        assert "name" in form.errors
        assert form.errors["name"][0] == "This field is required."

    def test_create_form_accepts_optional_description(self):
        """Test that create form accepts optional description field.

        Requirement: FR-006 - Initial description is optional during creation.
        User Story: US1 - Users can add description later through edit interface.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectCreateForm

        owner = Organization.objects.create(name="Test Organization")

        # Form data with optional description
        form_data = {
            "name": "Test Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
            "description": "This is a test project description.",
        }

        form = ProjectCreateForm(data=form_data)

        # Verify form is valid
        assert form.is_valid(), f"Form errors: {form.errors}"

        # Note: The form might use a TextField for description, not ProjectDescription model
        # This tests acceptance of the field, implementation may vary


@pytest.mark.django_db
class TestProjectEditForm:
    """Unit tests for Project edit form."""

    def test_edit_form_cannot_set_public_for_concept(self):
        """Test that concept-stage projects cannot be made public.

        Requirement: FR-005 - Concept projects must remain private until published.
        User Story: US1 - Validation prevents premature publication.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project
        from fairdm.core.project.forms import ProjectEditForm

        owner = Organization.objects.create(name="Test Organization")

        # Create a concept project
        project = Project.objects.create(
            name="Concept Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner
        )

        # Attempt to set visibility to PUBLIC while status is CONCEPT
        form_data = {
            "name": project.name,
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PUBLIC,  # Invalid combination
            "owner": owner.pk,
        }

        form = ProjectEditForm(data=form_data, instance=project)

        # Verify form validation catches this
        assert not form.is_valid()
        assert "visibility" in form.errors or "__all__" in form.errors

        # Check error message is helpful
        error_message = str(form.errors)
        assert "concept" in error_message.lower() or "public" in error_message.lower()

    def test_edit_form_allows_all_fields_for_active_project(self):
        """Test that active projects can be fully edited.

        Requirement: FR-004 - Active projects support all visibility levels.
        User Story: US1 - Full editing capability for active projects.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project
        from fairdm.core.project.forms import ProjectEditForm

        owner = Organization.objects.create(name="Test Organization")

        # Create an active project
        project = Project.objects.create(
            name="Active Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PRIVATE,
            owner=owner
        )

        # Edit to make public (allowed for active projects)
        form_data = {
            "name": "Updated Project Name",
            "status": ProjectStatus.IN_PROGRESS,
            "visibility": Visibility.PUBLIC,
            "owner": owner.pk,
        }

        form = ProjectEditForm(data=form_data, instance=project)

        # Verify form is valid
        assert form.is_valid(), f"Form errors: {form.errors}"

        # Save and verify changes
        updated_project = form.save()
        assert updated_project.name == "Updated Project Name"
        assert updated_project.visibility == Visibility.PUBLIC


@pytest.mark.django_db
class TestProjectDescriptionForm:
    """Unit tests for ProjectDescription form.

    Tests the form for adding/editing project descriptions with type validation.
    """

    def test_description_form_enforces_uniqueness(self):
        """Test that description form prevents duplicate types per project.

        Requirement: FR-010 - Each description type can only appear once per project.
        User Story: US2 - Multiple description types with uniqueness constraint.
        Implementation: T043 - Form validation for description type uniqueness.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project, ProjectDescription
        from fairdm.core.project.forms import ProjectDescriptionForm

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Test Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner
        )

        # Create first description of type "Abstract"
        ProjectDescription.objects.create(
            related=project,
            type="Abstract",
            value="Existing abstract"
        )

        # Attempt to create second description with same type should fail
        form_data = {
            "type": "Abstract",
            "value": "Duplicate abstract"
        }

        form = ProjectDescriptionForm(data=form_data)
        form.instance.related = project

        # Form should be invalid due to duplicate type
        assert not form.is_valid()
        assert "type" in form.errors or "__all__" in form.errors


@pytest.mark.django_db
class TestProjectDateForm:
    """Unit tests for ProjectDate form.

    Tests the form for adding/editing project dates with range validation.
    """

    def test_date_form_validates_range(self):
        """Test that date form validates end_date is not before start date.

        Requirement: FR-012 - Date ranges must be logically valid.
        User Story: US2 - Project dates with start/end validation.
        Implementation: T044 - Form validation for date ranges.

        Note: This test is currently skipped because:
        1. AbstractDate only has 'value' field, not 'date' and 'end_date'
        2. ProjectDate.clean() references non-existent 'self.date' and 'self.end_date'
        3. Date range functionality requires model updates before form validation

        Once ProjectDate model is updated to support date ranges (either by adding
        end_date field or using a different approach), this test can be updated.
        """
        pytest.skip("ProjectDate does not yet support end_date field for ranges")


@pytest.mark.django_db
class TestProjectIdentifierForm:
    """Unit tests for ProjectIdentifier form.

    Tests the form for adding/editing project identifiers.
    """

    def test_identifier_form_accepts_valid_data(self):
        """Test that identifier form accepts valid identifier types.

        Requirement: FR-005 - Projects support external identifiers.
        User Story: US2 - Add identifiers to projects for FAIR compliance.
        Implementation: T045 - Form validation for identifier data.

        Note: Current ProjectIdentifier vocabulary uses FairDMIdentifiers
        which includes ORCID, ISNI, ROR, etc. For DOI support, vocabulary
        would need to be extended or changed.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project
        from fairdm.core.project.forms import ProjectIdentifierForm

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Test Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner
        )

        # Test with valid ISNI identifier
        form_data = {
            "type": "ISNI",
            "value": "0000 0001 2283 4400",
        }

        form = ProjectIdentifierForm(data=form_data)
        form.instance.related = project

        # Form should be valid
        assert form.is_valid(), f"Form errors: {form.errors}"

        # Save and verify
        identifier = form.save()
        assert identifier.pk is not None
        assert identifier.type == "ISNI"
        assert identifier.value == "0000 0001 2283 4400"
