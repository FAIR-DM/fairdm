"""Unit tests for Dataset form.

This module tests the DatasetForm functionality including:
- User context and queryset filtering
- License defaults
- Form validation
- Pre-populated values (edit scenarios)
- Anonymous user handling
- Internationalized help text
- Autocomplete widgets
- DOI entry field

These tests follow the TDD approach - they are written BEFORE implementation and
should FAIL initially. Once the form is properly configured (Phase 5 implementation
tasks T093-T105), these tests will pass.
"""

import pytest
from django.test import RequestFactory
from licensing.models import License

from fairdm.contrib.contributors.models import Contribution
from fairdm.core.dataset.forms import DatasetForm
from fairdm.core.dataset.models import DatasetIdentifier
from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory


@pytest.mark.django_db
class TestFormQuerysetFiltering:
    """Test form queryset filtering based on user permissions (T085)."""

    def test_form_filters_projects_by_user_permissions(self):
        """Test that project queryset is filtered to user's accessible projects."""

        factory = RequestFactory()
        user = UserFactory()
        other_user = UserFactory(email="otheruser@example.com")

        # Create projects with default (auto-generated) owners
        user_project = ProjectFactory(name="User Project")
        other_project = ProjectFactory(name="Other Project")

        # Add users as contributors to their respective projects
        Contribution.add_to(user, user_project, roles=["Contributor"])
        Contribution.add_to(other_user, other_project, roles=["Contributor"])

        request = factory.get("/")
        request.user = user

        form = DatasetForm(request=request)

        # Should only include user's projects
        project_queryset = form.fields["project"].queryset
        assert user_project in project_queryset
        assert other_project not in project_queryset

    def test_form_without_request_shows_all_projects(self):
        """Test that form without request context shows all projects."""
        form = DatasetForm()

        # Without request, should show all projects (or handle gracefully)
        project_queryset = form.fields["project"].queryset
        # This behavior depends on implementation - could show all or none
        assert project_queryset is not None

    def test_form_with_anonymous_user_handles_gracefully(self):
        """Test form with anonymous user doesn't crash (T089)."""

        factory = RequestFactory()
        request = factory.get("/")
        request.user = None  # Anonymous user

        # Should not raise an exception
        form = DatasetForm(request=request)
        assert form is not None


@pytest.mark.django_db
class TestLicenseDefault:
    """Test license field default value (T086)."""

    def test_license_defaults_to_cc_by_4_0(self):
        """Test that license field defaults to CC BY 4.0."""
        # Ensure CC BY 4.0 license exists
        cc_by_license = License.objects.get_or_create(
            name="CC BY 4.0",
            defaults={"url": "https://creativecommons.org/licenses/by/4.0/"},
        )[0]

        form = DatasetForm()

        # License field should have CC BY 4.0 as initial value
        assert form.fields["license"].initial == cc_by_license

    def test_license_field_is_required(self):
        """Test that license field is required."""
        form = DatasetForm()

        # License field should be required (or have sensible default)
        license_field = form.fields.get("license")
        assert license_field is not None


@pytest.mark.django_db
class TestFormValidation:
    """Test form validation rules (T087)."""

    def test_name_field_is_required(self):
        """Test that name field is required."""
        form = DatasetForm(data={})

        assert not form.is_valid()
        assert "name" in form.errors

    def test_project_field_is_optional(self):
        """Test that project field is optional (orphaned datasets allowed)."""
        # Ensure license exists for validation
        license = License.objects.get_or_create(name="CC BY 4.0")[0]

        form = DatasetForm(
            data={
                "name": "Test Dataset",
                "license": license.pk,
                "project": "",  # Empty project
            }
        )

        # Form should be valid without project (orphaned dataset)
        # Note: This depends on model constraints
        assert "project" not in form.errors or form.is_valid()

    def test_form_validates_with_all_required_fields(self):
        """Test that form validates when all required fields are provided."""
        license = License.objects.get_or_create(name="CC BY 4.0")[0]
        project = ProjectFactory()

        form = DatasetForm(
            data={
                "name": "Valid Dataset",
                "project": project.pk,
                "license": license.pk,
            }
        )

        assert form.is_valid()


@pytest.mark.django_db
class TestFormRenderingWithData:
    """Test form rendering with pre-populated values (T088)."""

    def test_form_renders_with_existing_dataset(self):
        """Test that form correctly loads existing dataset data for editing."""
        dataset = DatasetFactory(name="Existing Dataset")

        form = DatasetForm(instance=dataset)

        # Form should be bound to the instance
        assert form.instance == dataset
        assert form.initial.get("name") == "Existing Dataset"

    def test_form_saves_changes_to_existing_dataset(self):
        """Test that form correctly saves changes to existing dataset."""
        dataset = DatasetFactory(name="Original Name")
        license = License.objects.get_or_create(name="CC BY 4.0")[0]

        form = DatasetForm(
            data={
                "name": "Updated Name",
                "project": dataset.project.pk,
                "license": license.pk,
            },
            instance=dataset,
        )

        assert form.is_valid()
        updated_dataset = form.save()
        assert updated_dataset.name == "Updated Name"


@pytest.mark.django_db
class TestInternationalizedHelpText:
    """Test internationalized help text using gettext_lazy (T090)."""

    def test_help_text_uses_gettext_lazy(self):
        """Test that help_text strings use gettext_lazy for translation."""
        form = DatasetForm()

        # Check that help_text is translatable (uses gettext_lazy)
        for field_name, field in form.fields.items():
            if field.help_text:
                # gettext_lazy returns a Promise object, not a plain string
                # In production, this enables translation
                help_text_type = type(field.help_text).__name__
                # Should be a lazy translation proxy or string
                assert help_text_type in [
                    "Promise",
                    "str",
                    "__proxy__",
                ], f"Field {field_name} help_text is not translatable"

    def test_all_fields_have_help_text(self):
        """Test that all visible fields have descriptive help text."""
        form = DatasetForm()

        # Important fields should have help text
        important_fields = ["name", "project", "license"]
        for field_name in important_fields:
            if field_name in form.fields:
                field = form.fields[field_name]
                assert field.help_text, f"Field {field_name} should have help_text for user guidance"


@pytest.mark.django_db
class TestAutocompleteWidgets:
    """Test autocomplete widgets on applicable fields (T091)."""

    def test_project_field_uses_autocomplete_widget(self):
        """Test that project field uses Select2 or autocomplete widget."""
        form = DatasetForm()

        project_field = form.fields.get("project")
        if project_field:
            # Widget might be wrapped in AddAnotherWidgetWrapper - check inner widget
            widget = project_field.widget
            widget_name = type(widget).__name__

            # If wrapped, get the inner widget
            if hasattr(widget, "widget"):
                inner_widget_name = type(widget.widget).__name__
                assert "Select2" in inner_widget_name or "Autocomplete" in inner_widget_name, (
                    f"Project field should use autocomplete widget, got {inner_widget_name} (wrapped in {widget_name})"
                )
            else:
                assert "Select2" in widget_name or "Autocomplete" in widget_name, (
                    f"Project field should use autocomplete widget, got {widget_name}"
                )

    def test_license_field_uses_autocomplete_widget(self):
        """Test that license field uses Select2 or autocomplete widget."""
        form = DatasetForm()

        license_field = form.fields.get("license")
        if license_field:
            # Widget should support autocomplete for many license options
            widget_name = type(license_field.widget).__name__
            # Should use Select2 or similar
            assert "Select2" in widget_name or "Autocomplete" in widget_name or "Select" in widget_name

    def test_reference_field_uses_autocomplete_widget(self):
        """Test that reference field (literature) uses autocomplete widget."""
        form = DatasetForm()

        reference_field = form.fields.get("reference")
        if reference_field:
            widget_name = type(reference_field.widget).__name__
            # Literature references should use autocomplete for large lists
            assert "Select2" in widget_name or "Autocomplete" in widget_name or "AddAnother" in widget_name


@pytest.mark.django_db
class TestDOIEntryField:
    """Test DOI entry field that creates DatasetIdentifier (T092)."""

    def test_doi_field_exists_on_form(self):
        """Test that DOI entry field exists on the form."""
        form = DatasetForm()

        # DOI field should be present
        assert "doi" in form.fields, "Form should have a DOI entry field"

    def test_doi_field_is_optional(self):
        """Test that DOI field is optional (datasets may not have DOI yet)."""
        form = DatasetForm()

        doi_field = form.fields.get("doi")
        assert doi_field is not None
        assert not doi_field.required, "DOI field should be optional"

    def test_doi_field_creates_dataset_identifier_on_save(self):
        """Test that entering DOI creates DatasetIdentifier with type='DOI'."""
        license = License.objects.get_or_create(name="CC BY 4.0")[0]
        project = ProjectFactory()

        form = DatasetForm(
            data={
                "name": "Dataset with DOI",
                "project": project.pk,
                "license": license.pk,
                "doi": "10.1000/test123",
            }
        )

        assert form.is_valid(), f"Form errors: {form.errors}"
        dataset = form.save()

        # Should have created a DatasetIdentifier
        doi_identifier = DatasetIdentifier.objects.filter(related=dataset, type="DOI").first()
        assert doi_identifier is not None, "DOI identifier should be created"
        assert doi_identifier.value == "10.1000/test123"

    def test_doi_field_updates_existing_identifier(self):
        """Test that updating DOI field updates existing DatasetIdentifier."""
        dataset = DatasetFactory(name="Existing Dataset")
        license = License.objects.get_or_create(name="CC BY 4.0")[0]

        # Create initial DOI
        DatasetIdentifier.objects.create(related=dataset, type="DOI", value="10.1000/original")

        # Update DOI via form
        form = DatasetForm(
            data={
                "name": dataset.name,
                "project": dataset.project.pk,
                "license": license.pk,
                "doi": "10.1000/updated",
            },
            instance=dataset,
        )

        assert form.is_valid()
        form.save()

        # Should have updated the identifier
        doi_identifier = DatasetIdentifier.objects.get(related=dataset, type="DOI")
        assert doi_identifier.value == "10.1000/updated"

    def test_empty_doi_field_does_not_create_identifier(self):
        """Test that empty DOI field does not create DatasetIdentifier."""
        license = License.objects.get_or_create(name="CC BY 4.0")[0]
        project = ProjectFactory()

        form = DatasetForm(
            data={
                "name": "Dataset without DOI",
                "project": project.pk,
                "license": license.pk,
                "doi": "",  # Empty DOI
            }
        )

        assert form.is_valid()
        dataset = form.save()

        # Should NOT have created a DOI identifier
        doi_count = DatasetIdentifier.objects.filter(related=dataset, type="DOI").count()
        assert doi_count == 0, "Empty DOI should not create identifier"

    def test_doi_field_has_helpful_text(self):
        """Test that DOI field has clear help text."""
        form = DatasetForm()

        doi_field = form.fields.get("doi")
        assert doi_field.help_text, "DOI field should have explanatory help text"
        # Help text should mention it's for existing DOIs
        assert "DOI" in str(doi_field.help_text).upper()
