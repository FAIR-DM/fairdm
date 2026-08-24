"""
Unit tests for fairdm.core.project forms.

Tests the ProjectCreateForm and ProjectForm in isolation, focusing on field
validation, required fields, and business logic constraints.

Test-First Approach (Red-Green-Refactor):
1. Write tests that FAIL (Red)
2. Implement minimal code to pass (Green)
3. Refactor for quality (Refactor)
"""

import pytest

from fairdm.core.choices import ProjectStatus
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectCreateForm:
    """Unit tests for Project creation form."""

    def test_create_form_valid_with_required_fields(self):
        """Test that create form accepts minimal required fields.

        Requirement: FR-011 - ProjectCreateForm includes only name, status, visibility.
        User Story: US1 - Streamlined creation with minimal required fields.
        """
        from fairdm.core.project.forms import ProjectCreateForm

        # Minimal form data with only required fields (no owner — FR-011)
        form_data = {
            "name": "Test Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
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
class TestProjectUpdateForm:
    """Unit tests for Project edit form."""

    def test_the_field_set_is_exactly_image_name_status_visibility_owner(self):
        """T029 — Asserted as set equality, never a presence check: a field added to the form
        without being pinned here would pass silently."""
        from fairdm.core.project.forms import ProjectForm

        form = ProjectForm()

        assert set(form.fields) == {"image", "name", "status", "visibility", "owner"}

    def test_the_form_offers_no_description_keyword_tag_contributor_or_funding_field(
        self,
    ):
        """T030 — Those are edited on other pages (descriptions, keywords, contributors) or
        not at all (funding, T088): the attributes form must not offer them."""
        from fairdm.core.project.forms import ProjectForm

        form = ProjectForm()

        for name in ("description", "keyword", "tag", "contributor", "funding"):
            assert name not in form.fields

    def test_image_field_renders_no_label_text(self):
        """The image field is captioned by its widget, so it must render an empty
        label. A boolean suppresses nothing and renders the word "False"."""
        from fairdm.core.project.forms import ProjectForm

        form = ProjectForm()

        assert "False" not in form["image"].label_tag()

    def test_form_allows_concept_public_combination(self):
        """T057 — CONCEPT + PUBLIC is a valid combination; form must accept it."""
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectForm
        from fairdm.core.project.models import Project

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Concept Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )
        form_data = {
            "name": project.name,
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PUBLIC,
            "owner": owner.pk,
        }
        form = ProjectForm(data=form_data, instance=project)
        assert form.is_valid(), (
            f"Expected CONCEPT+PUBLIC to be valid, got errors: {form.errors}"
        )
        assert "visibility" not in form.errors
        assert "__all__" not in form.errors

    def test_edit_form_allows_all_fields_for_active_project(self):
        """Test that active projects can be fully edited.

        Requirement: FR-004 - Active projects support all visibility levels.
        User Story: US1 - Full editing capability for active projects.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.forms import ProjectForm
        from fairdm.core.project.models import Project

        owner = Organization.objects.create(name="Test Organization")

        # Create an active project
        project = Project.objects.create(
            name="Active Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        # Edit to make public (allowed for active projects)
        form_data = {
            "name": "Updated Project Name",
            "status": ProjectStatus.IN_PROGRESS,
            "visibility": Visibility.PUBLIC,
            "owner": owner.pk,
        }

        form = ProjectForm(data=form_data, instance=project)

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
        from fairdm.core.project.forms import ProjectDescriptionForm
        from fairdm.core.project.models import Project, ProjectDescription

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Test Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        # Create first description of type "Abstract"
        ProjectDescription.objects.create(
            related=project, type="Abstract", value="Existing abstract"
        )

        # Attempt to create second description with same type should fail
        form_data = {"type": "Abstract", "value": "Duplicate abstract"}

        form = ProjectDescriptionForm(data=form_data)
        form.instance.related = project

        # Form should be invalid due to duplicate type
        assert not form.is_valid()
        assert "type" in form.errors or "__all__" in form.errors
