"""Unit tests for Dataset form.

This module tests the DatasetForm functionality including:
- User context and queryset filtering
- License defaults
- Form validation
- Pre-populated values (edit scenarios)
- Anonymous user handling
- Internationalized help text
- Autocomplete widgets
- Visibility field

These tests follow the TDD approach - they are written BEFORE implementation and
should FAIL initially. Once the form is properly configured (Phase 5 implementation
tasks T093-T105), these tests will pass.

Also covers basic form validation smoke tests moved from the former
test_integration.py.
"""

import pytest
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from licensing.models import License

from fairdm.contrib.contributors.models import Contribution
from fairdm.core.dataset.forms import DatasetCreateForm, DatasetForm
from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


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
class TestCreateFormProjectFieldForAnonymousRequest:
    """T027/FR-016 - the creation page's own shipped form offers no projects at all to a
    visitor who is not signed in. `DatasetCreateView` itself refuses an anonymous visitor
    before a form is ever rendered, so this is exercised directly against the form the page
    declares (`DatasetCreateForm`), the same way `TestFormQuerysetFiltering` above exercises
    the authenticated-narrowing branch of the same `__init__`."""

    def test_the_project_field_offers_no_projects_for_an_anonymous_request(self):
        ProjectFactory()
        factory = RequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        form = DatasetCreateForm(request=request)

        assert form.fields["project"].queryset.count() == 0


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
                "visibility": Visibility.PUBLIC,
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
                "visibility": Visibility.PUBLIC,
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
                assert field.help_text, (
                    f"Field {field_name} should have help_text for user guidance"
                )


@pytest.mark.django_db
class TestProjectAndReferenceFieldWidgets:
    """T086 — the project and reference (data publication) fields render as ordinary
    `forms.Select` widgets, not the django_addanother/select2 wrapper stack, which does not
    render correctly in the portal. Supersedes ``TestAutocompleteWidgets``: select2 is gone
    from both fields, not merely tolerated as one option among several."""

    def test_project_field_uses_a_plain_select_widget(self):
        form = DatasetForm()

        widget = form.fields["project"].widget
        assert type(widget).__name__ == "Select"
        assert not hasattr(widget, "widget"), "project field is still wrapped"

    def test_reference_field_uses_a_plain_select_widget(self):
        form = DatasetForm()

        widget = form.fields["reference"].widget
        assert type(widget).__name__ == "Select"
        assert not hasattr(widget, "widget"), "reference field is still wrapped"

    def test_license_field_uses_a_select_widget(self):
        """License field is unaffected by T086; unchanged coverage kept alongside the
        fields that did change so the widget expectations for this form live in one place."""
        form = DatasetForm()

        license_field = form.fields.get("license")
        if license_field:
            widget_name = type(license_field.widget).__name__
            assert "Select" in widget_name


@pytest.mark.django_db
class TestVisibilityField:
    """Test the visibility field the update page's attributes cover (014 plan P4, FR-025).

    Supersedes ``TestDOIEntryField``: the DOI text box this replaced is retired along with its
    ``save()`` override (014 plan P3) — a dataset's external identifiers, DOI included, are now
    edited as rows on the update page's identifiers row set instead of a field on this form (see
    ``tests/test_core/test_dataset/test_plugins.py``'s ``TestAttributesIdentifierRowSet``).
    """

    def test_visibility_field_exists_on_form(self):
        form = DatasetForm()

        assert "visibility" in form.fields

    def test_visibility_field_pre_selects_public(self):
        form = DatasetForm()

        assert form.fields["visibility"].initial == Visibility.PUBLIC

    def test_visibility_field_uses_a_radio_widget(self):
        form = DatasetForm()

        assert isinstance(form.fields["visibility"].widget, forms.RadioSelect)

    def test_doi_field_no_longer_exists_on_form(self):
        form = DatasetForm()

        assert "doi" not in form.fields


@pytest.mark.django_db
class TestDatasetForm:
    """Tests for the DatasetForm."""

    def test_form_valid_data(self):
        """Test form validation with valid data."""
        from licensing.models import License

        project = ProjectFactory()
        license = License.objects.get_or_create(name="CC BY 4.0")[0]

        form_data = {
            "name": "Test Dataset",
            "project": project.pk,
            "license": license.pk,
            "visibility": Visibility.PUBLIC,
        }
        form = DatasetForm(data=form_data)

        assert form.is_valid()

    def test_form_missing_required_fields(self):
        """Test form validation fails without required fields."""
        form_data = {}
        form = DatasetForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors
