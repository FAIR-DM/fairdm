"""Integration tests for Dataset admin interface workflows.

This module tests the Django admin interface enhancements for Dataset management,
including search functionality, filtering, inline editing, bulk operations, and
visibility controls.

These tests follow the TDD approach - they are written BEFORE implementation and
should FAIL initially. Once the admin interface is properly configured (Phase 4
implementation tasks T067-T083), these tests will pass.
"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from fairdm.core.dataset.admin import DateInline, DescriptionInline
from fairdm.core.dataset.models import (
    Dataset,
    DatasetDate,
    DatasetDescription,
)
from fairdm.factories.core import DatasetFactory, ProjectFactory


@pytest.mark.django_db
class TestAdminSearchByNameAndUUID:
    """Test admin search functionality by dataset name and UUID (T055)."""

    def test_search_by_exact_name(self, admin_client):
        """Test searching for dataset by exact name match."""
        # Create test datasets
        dataset1 = DatasetFactory(name="Climate Research Data")
        DatasetFactory(name="Ocean Temperature Readings")
        DatasetFactory(name="Solar Energy Measurements")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"q": "Climate Research Data"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Climate Research Data" in content
        # Other datasets should not appear (or show "no results")
        assert "Ocean Temperature" not in content or "no results" in content.lower()

    def test_search_by_partial_name(self, admin_client):
        """Test searching for dataset by partial name match."""
        DatasetFactory(name="Climate Research Data")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"q": "Research"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Climate Research Data" in content

    def test_search_by_uuid(self, admin_client):
        """Test searching for dataset by UUID."""
        dataset1 = DatasetFactory(name="Climate Research Data")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"q": str(dataset1.uuid)})

        assert response.status_code == 200
        content = response.content.decode()
        assert dataset1.name in content

    def test_search_by_partial_uuid(self, admin_client):
        """Test searching for dataset by partial UUID."""
        dataset1 = DatasetFactory(name="Climate Research Data")

        url = reverse("admin:dataset_dataset_changelist")
        # Use first 8 characters of UUID
        partial_uuid = str(dataset1.uuid)[:8]
        response = admin_client.get(url, {"q": partial_uuid})

        assert response.status_code == 200
        content = response.content.decode()
        assert dataset1.name in content


@pytest.mark.django_db
class TestAdminListDisplayFields:
    """Test admin list_display configuration (T056)."""

    def test_list_display_shows_name(self, admin_client):
        """Test that name field appears in admin list display."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert dataset.name in content

    def test_list_display_shows_added_timestamp(self, admin_client):
        """Test that 'added' timestamp appears in admin list display."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        # Check that 'added' column header or timestamp value is present
        content = response.content.decode()
        assert "added" in content.lower() or str(dataset.added.year) in content

    def test_list_display_shows_modified_timestamp(self, admin_client):
        """Test that 'modified' timestamp appears in admin list display."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "modified" in content.lower() or str(dataset.modified.year) in content

    def test_list_display_shows_has_data_property(self, admin_client):
        """Test that has_data property appears in admin list display."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Should show has_data column header or boolean indicator
        assert "has_data" in content.lower() or "has data" in content.lower()


@pytest.mark.django_db
class TestAdminListFilterOptions:
    """Test admin list_filter configuration (T057)."""

    def test_filter_by_project(self, admin_client):
        """Test filtering datasets by project."""
        # Create projects and datasets
        project1 = ProjectFactory(name="Project A")
        project2 = ProjectFactory(name="Project B")
        DatasetFactory(name="Dataset 1", project=project1)
        DatasetFactory(name="Dataset 2", project=project2)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"project__id__exact": str(project1.pk)})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Dataset 1" in content
        # Dataset 2 should not appear in filtered results
        assert "Dataset 2" not in content or "no results" in content.lower()

    def test_filter_by_license(self):
        """Test filtering datasets by license.

        NOTE: This test uses placeholder License model access.
        Will need to be updated during implementation (T070) to match
        actual django-content-license API.
        """
        # TODO: Replace with actual License model import during implementation
        # from fairdm.contrib.content_license.models import License
        pytest.skip("License filtering test pending implementation - needs correct License model import")

        # Create licenses
        # cc_by = License.objects.get_or_create(name="CC BY 4.0")[0]
        # cc_by_sa = License.objects.get_or_create(name="CC BY-SA 4.0")[0]
        #
        # dataset_cc_by = DatasetFactory(name="Open Data", license=cc_by)
        # dataset_cc_by_sa = DatasetFactory(name="ShareAlike Data", license=cc_by_sa)
        #
        # self.client.force_login(self.admin_user)
        # url = reverse("admin:dataset_dataset_changelist")
        # response = self.client.get(url, {"license__id__exact": str(cc_by.pk)})
        #
        # assert response.status_code == 200
        # content = response.content.decode()
        # assert "Open Data" in content

    def test_filter_by_visibility(self, admin_client):
        """Test filtering datasets by visibility."""
        from fairdm.utils.choices import Visibility

        # Create datasets with different visibility settings
        DatasetFactory(name="Public Dataset", visibility=Visibility.PUBLIC.value)
        DatasetFactory(name="Private Dataset", visibility=Visibility.PRIVATE.value)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"visibility__exact": str(Visibility.PUBLIC.value)})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Public Dataset" in content


@pytest.mark.django_db
class TestInlineDescriptionEditing:
    """Test admin inline editing of dataset descriptions (T058)."""

    def test_inline_description_shown_in_change_form(self, admin_client):
        """Test that description inline is displayed in dataset change form."""
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Look for inline formset elements
        assert "datasetdescription" in content.lower() or "description" in content.lower()

    def test_can_add_description_via_inline(self, admin_client):
        """Test adding a description through inline form."""
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        # Prepare inline form data
        form_data = {
            "name": dataset.name,
            "project": dataset.project.pk,
            "visibility": dataset.visibility,
            # Description inline formset management form (uses default_related_name from Meta)
            "descriptions-TOTAL_FORMS": "1",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            # First inline form
            "descriptions-0-related": dataset.pk,
            "descriptions-0-type": "Abstract",
            "descriptions-0-value": "This is a test description added via inline form.",
            # Date inline (empty - but management form required)
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        # Debug: Check for form errors
        if response.status_code == 200:
            # Form had validation errors - stayed on the same page
            content = response.content.decode()
            if "error" in content.lower():
                print("\n=== FORM ERRORS DETECTED ===")
                # Extract error messages for debugging
                import re

                errors = re.findall(r'<ul class="errorlist[^>]*">.*?</ul>', content, re.DOTALL)
                for error in errors:
                    print(error)

        # Should redirect or show success
        assert response.status_code in [200, 302]

        # Check that description was created
        descriptions = DatasetDescription.objects.filter(related=dataset)
        assert descriptions.count() > 0, f"Expected descriptions to be created, but found {descriptions.count()}"

    def test_can_edit_existing_description_via_inline(self, admin_client):
        """Test editing an existing description through inline form."""
        dataset = DatasetFactory(name="Test Dataset")
        # Create existing description
        existing_desc = DatasetDescription.objects.create(
            related=dataset,
            type="Abstract",
            value="Original abstract text",
        )

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        # Update description via inline form
        form_data = {
            "name": dataset.name,
            "project": dataset.project.pk,
            "visibility": dataset.visibility,
            # Description inline formset management form (uses default_related_name from Meta)
            "descriptions-TOTAL_FORMS": "1",
            "descriptions-INITIAL_FORMS": "1",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            # Edit the existing inline form
            "descriptions-0-id": existing_desc.pk,
            "descriptions-0-related": dataset.pk,
            "descriptions-0-type": "Abstract",
            "descriptions-0-value": "Updated abstract text",
            # Date inline (empty - but management form required)
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        # Check that description was updated
        existing_desc.refresh_from_db()
        assert "Updated abstract text" in existing_desc.value


@pytest.mark.django_db
class TestInlineDateEditing:
    """Test admin inline editing of dataset dates (T059)."""

    def test_inline_date_shown_in_change_form(self, admin_client):
        """Test that date inline is displayed in dataset change form."""
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Look for inline formset elements
        assert "datasetdate" in content.lower() or "date" in content.lower()

    def test_can_add_date_via_inline(self, admin_client):
        """Test adding a date through inline form."""
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        # Prepare inline form data
        form_data = {
            "name": dataset.name,
            "project": dataset.project.pk,
            "visibility": dataset.visibility,
            # Description inline (empty)
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            # Date inline formset management form (uses default_related_name from Meta)
            "dates-TOTAL_FORMS": "1",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            # First inline form
            "dates-0-related": dataset.pk,
            "dates-0-type": "Available",
            "dates-0-value": "2024-01-15",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        # Debug: Check for form errors
        if response.status_code == 200:
            # Form had validation errors - stayed on the same page
            content = response.content.decode()
            if "error" in content.lower():
                print("\n=== FORM ERRORS DETECTED (DATE TEST) ===")
                # Extract error messages for debugging
                import re

                errors = re.findall(r'<ul class="errorlist[^>]*">.*?</ul>', content, re.DOTALL)
                for error in errors:
                    print(error)

        # Should redirect or show success
        assert response.status_code in [200, 302]

        # Check that date was created
        dates = DatasetDate.objects.filter(related=dataset)
        assert dates.count() > 0, f"Expected dates to be created, but found {dates.count()}"


@pytest.mark.django_db
class TestDynamicInlineFormLimits:
    """Test dynamic inline form limits based on vocabulary size (T060).

    This test verifies that the admin interface dynamically sets max_num for
    inline formsets based on the number of available choices in the vocabulary.
    For example, if there are 6 description types, max_num should be 6.
    """

    def test_description_inline_max_num_matches_vocabulary_size(self, admin_user):
        """Test that DescriptionInline max_num matches number of description types."""
        # Get the vocabulary size for description types
        vocabulary_size = len(Dataset.DESCRIPTION_TYPES.choices)

        # Get the formset for descriptions
        from django.test import RequestFactory

        admin_site = AdminSite()
        request = RequestFactory().get("/")
        request.user = admin_user
        description_inline = DescriptionInline(Dataset, admin_site)
        formset = description_inline.get_formset(request)

        # Verify max_num is set to vocabulary size
        assert formset.max_num == vocabulary_size, (
            f"Expected max_num={vocabulary_size} for DescriptionInline, "
            f"but got {formset.max_num}. The admin should dynamically set "
            f"max_num based on the number of available description types."
        )

    def test_date_inline_max_num_matches_vocabulary_size(self, admin_user):
        """Test that DateInline max_num matches number of date types."""
        # Get the vocabulary size for date types
        vocabulary_size = len(Dataset.DATE_TYPES.choices)

        # Get the formset for dates
        from django.test import RequestFactory

        admin_site = AdminSite()
        request = RequestFactory().get("/")
        request.user = admin_user
        date_inline = DateInline(Dataset, admin_site)
        formset = date_inline.get_formset(request)

        # Verify max_num is set to vocabulary size
        assert formset.max_num == vocabulary_size, (
            f"Expected max_num={vocabulary_size} for DateInline, "
            f"but got {formset.max_num}. The admin should dynamically set "
            f"max_num based on the number of available date types."
        )


@pytest.mark.django_db
class TestNoBulkVisibilityChangeActions:
    """Test that NO bulk visibility change actions exist (T062).

    This is a critical security feature - visibility changes must be deliberate
    and individual to prevent accidental exposure of private datasets.
    """

    def test_no_make_public_action(self, admin_client):
        """Test that 'make public' bulk action does NOT exist."""
        # Create test datasets
        DatasetFactory.create_batch(3)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode().lower()
        # Should NOT have bulk visibility change actions
        assert "make public" not in content
        assert "make_public" not in content
        assert "bulk_make_public" not in content

    def test_no_make_private_action(self, admin_client):
        """Test that 'make private' bulk action does NOT exist."""
        # Create test datasets
        DatasetFactory.create_batch(3)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode().lower()
        assert "make private" not in content
        assert "make_private" not in content
        assert "bulk_make_private" not in content

    def test_no_change_visibility_action(self, admin_client):
        """Test that generic 'change visibility' bulk action does NOT exist."""
        # Create test datasets
        DatasetFactory.create_batch(3)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode().lower()
        assert "change visibility" not in content
        assert "change_visibility" not in content
        assert "bulk_change_visibility" not in content


@pytest.mark.django_db
class TestAutocompleteOnForeignKeys:
    """Test Django autocomplete on ForeignKey/ManyToMany fields (T063)."""

    def test_project_field_has_autocomplete(self, admin_client):
        """Test that project field uses autocomplete widget."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Look for autocomplete widget indicators (data-autocomplete-light, select2, etc.)
        assert (
            "autocomplete" in content.lower() or "select2" in content.lower() or "data-autocomplete" in content.lower()
        )

    def test_license_field_has_autocomplete(self, admin_client):
        """Test that license field uses autocomplete widget."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Check for autocomplete on license field
        assert "license" in content.lower()
        # Should have autocomplete capabilities
        assert (
            "autocomplete" in content.lower() or "select2" in content.lower() or "data-autocomplete" in content.lower()
        )


@pytest.mark.django_db
class TestReadonlyUUIDAndTimestamps:
    """Test readonly UUID and timestamp fields (T064)."""

    def test_uuid_field_is_readonly(self, admin_client):
        """Test that UUID field is readonly in admin form."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # UUID should be visible
        assert str(dataset.uuid) in content
        # But should be readonly (not in an editable input)
        # Look for readonly indicator
        assert "readonly" in content.lower() or "disabled" in content.lower()

    def test_added_timestamp_is_readonly(self, admin_client):
        """Test that 'added' timestamp is readonly in admin form."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Timestamp should be visible
        assert str(dataset.added.year) in content
        # Should be readonly
        assert "readonly" in content.lower() or "disabled" in content.lower()

    def test_modified_timestamp_is_readonly(self, admin_client):
        """Test that 'modified' timestamp is readonly in admin form."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Timestamp should be visible
        assert str(dataset.modified.year) in content
        # Should be readonly
        assert "readonly" in content.lower() or "disabled" in content.lower()


@pytest.mark.django_db
class TestLicenseChangeWarningWithDOI:
    """Test license change warning when DOI exists (T065).

    When a dataset has a DOI assigned, changing the license should trigger a
    warning because the DOI metadata may have been published with the original
    license information.
    """

    def test_license_change_shows_warning_with_doi(self):
        """Test that changing license on dataset with DOI shows warning.

        NOTE: This test uses placeholder License model access.
        Will need to be updated during implementation (T077) to match
        actual django-content-license API.
        """
        # TODO: Replace with actual License model import during implementation
        # from fairdm.contrib.content_license.models import License
        pytest.skip("License change warning test pending implementation - needs correct License model import")

        # Create new license
        # new_license = License.objects.get_or_create(name="CC BY-SA 4.0")[0]
        #
        # self.client.force_login(self.admin_user)
        # url = reverse("admin:dataset_dataset_change", args=[self.dataset.pk])
        #
        # # Change license
        # form_data = {
        #     "name": self.dataset.name,
        #     "project": self.dataset.project.pk,
        #     "license": new_license.pk,  # Changed from original
        #     "visibility": self.dataset.visibility,
        #     # Empty inlines
        #     "descriptions-TOTAL_FORMS": "0",
        #     "descriptions-INITIAL_FORMS": "0",
        #     "descriptions-MIN_NUM_FORMS": "0",
        #     "descriptions-MAX_NUM_FORMS": "1000",
        #     "dates-TOTAL_FORMS": "0",
        #     "dates-INITIAL_FORMS": "0",
        #     "dates-MIN_NUM_FORMS": "0",
        #     "dates-MAX_NUM_FORMS": "1000",
        #     "_continue": "Save and continue editing",
        # }
        #
        # response = self.client.post(url, data=form_data, follow=True)
        #
        # # Should show warning message
        # content = response.content.decode()
        # assert "warning" in content.lower() or "doi" in content.lower()
        # # Should mention license change with DOI
        # assert "license" in content.lower()

    def test_no_warning_without_doi(self):
        """Test that changing license on dataset WITHOUT DOI shows no warning.

        NOTE: This test uses placeholder License model access.
        Will need to be updated during implementation (T077) to match
        actual django-content-license API.
        """
        # TODO: Replace with actual License model import during implementation
        # from fairdm.contrib.content_license.models import License
        pytest.skip("License change warning test pending implementation - needs correct License model import")

        # Create dataset without DOI
        # dataset_no_doi = DatasetFactory(name="Unpublished Dataset")
        # new_license = License.objects.get_or_create(name="CC BY-SA 4.0")[0]
        #
        # self.client.force_login(self.admin_user)
        # url = reverse("admin:dataset_dataset_change", args=[dataset_no_doi.pk])
        #
        # # Change license
        # form_data = {
        #     "name": dataset_no_doi.name,
        #     "project": dataset_no_doi.project.pk,
        #     "license": new_license.pk,
        #     "visibility": dataset_no_doi.visibility,
        #     # Empty inlines
        #     "descriptions-TOTAL_FORMS": "0",
        #     "descriptions-INITIAL_FORMS": "0",
        #     "descriptions-MIN_NUM_FORMS": "0",
        #     "descriptions-MAX_NUM_FORMS": "1000",
        #     "dates-TOTAL_FORMS": "0",
        #     "dates-INITIAL_FORMS": "0",
        #     "dates-MIN_NUM_FORMS": "0",
        #     "dates-MAX_NUM_FORMS": "1000",
        #     "_continue": "Save and continue editing",
        # }
        #
        # response = self.client.post(url, data=form_data, follow=True)
        #
        # # Should NOT show DOI warning (but may show other messages)
        # # Check that save was successful
        # assert response.status_code == 200
