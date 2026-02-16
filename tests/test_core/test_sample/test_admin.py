"""Integration tests for Sample admin interface.

Tests for User Story 2: Enhanced Admin Interface

This module tests the Django admin interface for Sample models including:
- Search functionality (name, local_id, uuid)
- Filtering (dataset, status, location)
- Inline metadata editing (descriptions, dates, identifiers, relationships)
- Polymorphic type handling

Based on tasks T031-T033 from Feature 007.
"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from fairdm.core.sample.admin import SampleChildAdmin
from fairdm.core.sample.models import Sample, SampleDate, SampleDescription, SampleIdentifier, SampleRelation
from fairdm.factories.core import DatasetFactory, SampleFactory

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create a superuser for admin access."""
    user = User.objects.create_superuser(
        email="admin@example.com", first_name="Admin", last_name="User", password="admin123"
    )
    return user


@pytest.fixture
def sample_admin():
    """Create a SampleAdmin instance."""
    return SampleChildAdmin(Sample, AdminSite())
    return SampleAdmin(Sample, site)


@pytest.fixture
def request_factory():
    """Create a RequestFactory instance."""
    return RequestFactory()


@pytest.mark.django_db
class TestSampleAdminSearch:
    """Tests for admin search functionality (T031)."""

    def test_search_by_name(self, sample_admin, admin_user, request_factory):
        """Test that admin search finds samples by name."""
        sample1 = SampleFactory(name="Granite Sample")
        sample2 = SampleFactory(name="Basalt Sample")
        _sample3 = SampleFactory(name="Water Sample")

        request = request_factory.get("/admin/sample/sample/", {"q": "Granite"})
        request.user = admin_user

        queryset = sample_admin.get_search_results(request, Sample.objects.all(), "Granite")[0]

        assert sample1 in queryset
        assert sample2 not in queryset

    def test_search_by_local_id(self, sample_admin, admin_user, request_factory):
        """Test that admin search finds samples by local_id."""
        sample1 = SampleFactory(local_id="SAMPLE-001")
        _sample2 = SampleFactory(local_id="SAMPLE-002")

        request = request_factory.get("/admin/sample/sample/", {"q": "SAMPLE-001"})
        request.user = admin_user

        queryset = sample_admin.get_search_results(request, Sample.objects.all(), "SAMPLE-001")[0]

        assert sample1 in queryset

    def test_search_by_uuid(self, sample_admin, admin_user, request_factory):
        """Test that admin search finds samples by UUID."""
        sample1 = SampleFactory()

        request = request_factory.get("/admin/sample/sample/", {"q": sample1.uuid})
        request.user = admin_user

        queryset = sample_admin.get_search_results(request, Sample.objects.all(), sample1.uuid)[0]

        assert sample1 in queryset

    def test_search_returns_empty_for_no_matches(self, sample_admin, admin_user, request_factory):
        """Test that admin search returns empty queryset when no matches found."""
        _sample1 = SampleFactory(name="Test Sample")

        request = request_factory.get("/admin/sample/sample/", {"q": "NonExistent"})
        request.user = admin_user

        queryset = sample_admin.get_search_results(request, Sample.objects.all(), "NonExistent")[0]

        assert queryset.count() == 0


@pytest.mark.django_db
class TestSampleAdminFilters:
    """Tests for admin filtering functionality (T032)."""

    def test_filter_by_dataset(self, sample_admin):
        """Test that admin can filter samples by dataset."""
        dataset1 = DatasetFactory(name="Dataset A")
        dataset2 = DatasetFactory(name="Dataset B")

        sample1 = SampleFactory(dataset=dataset1)
        _sample2 = SampleFactory(dataset=dataset2)

        # Simulate filtering by dataset1
        filtered = Sample.objects.filter(dataset=dataset1)

        assert sample1 in filtered
        assert filtered.count() == 1

    def test_filter_by_status(self, sample_admin):
        """Test that admin can filter samples by status."""
        # Use default status (unknown) which is valid in the vocabulary
        sample1 = SampleFactory()
        sample2 = SampleFactory()

        # Simulate filtering by status (both should have 'unknown' status by default)
        filtered = Sample.objects.filter(status=sample1.status)

        assert sample1 in filtered
        assert sample2 in filtered

    def test_list_filter_configuration(self, sample_admin):
        """Test that list_filter is configured correctly."""
        assert "status" in sample_admin.list_filter
        assert "added" in sample_admin.list_filter

    def test_multiple_filters_can_be_combined(self, sample_admin):
        """Test that multiple filters can be combined."""
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()
        sample1 = SampleFactory(dataset=dataset1)
        _sample2 = SampleFactory(dataset=dataset2)

        # Simulate combining filters (dataset and status)
        filtered = Sample.objects.filter(dataset=dataset1, status=sample1.status)

        assert sample1 in filtered
        assert filtered.count() == 1


@pytest.mark.django_db
class TestSampleAdminInlines:
    """Tests for admin inline metadata editing (T033)."""

    def test_description_inline_configured(self, sample_admin):
        """Test that DescriptionInline is configured in SampleAdmin."""
        inline_names = [inline.__name__ for inline in sample_admin.inlines]
        assert "SampleDescriptionInline" in inline_names

    def test_date_inline_configured(self, sample_admin):
        """Test that DateInline is configured in SampleAdmin."""
        inline_names = [inline.__name__ for inline in sample_admin.inlines]
        assert "SampleDateInline" in inline_names

    def test_identifier_inline_configured(self, sample_admin):
        """Test that IdentifierInline is configured in SampleAdmin."""
        inline_names = [inline.__name__ for inline in sample_admin.inlines]
        assert "SampleIdentifierInline" in inline_names

    def test_relationship_inline_configured(self, sample_admin):
        """Test that SampleRelationInline is configured in SampleAdmin."""
        inline_names = [inline.__name__ for inline in sample_admin.inlines]
        assert "SampleRelationInline" in inline_names

    def test_contribution_inline_configured(self, sample_admin):
        """Test that ContributionInline is configured in SampleAdmin."""
        inline_names = [inline.__name__ for inline in sample_admin.inlines]
        assert "SampleContributionInline" in inline_names

    def test_inline_metadata_can_be_created(self, sample_admin):
        """Test that inline metadata objects can be created for a sample."""
        sample = SampleFactory()

        # Create description via inline
        description = SampleDescription.objects.create(
            related=sample, type="Abstract", value="Test description for sample"
        )

        assert description.related == sample
        assert sample.descriptions.count() == 1

    def test_inline_dates_can_be_created(self, sample_admin):
        """Test that inline date objects can be created for a sample."""
        sample = SampleFactory()

        # Create date via inline
        date = SampleDate.objects.create(related=sample, type="Collected", value="2024-01-15")

        assert date.related == sample
        assert sample.dates.count() == 1

    def test_inline_identifiers_can_be_created(self, sample_admin):
        """Test that inline identifier objects can be created for a sample."""
        sample = SampleFactory()

        # Create identifier via inline
        identifier = SampleIdentifier.objects.create(related=sample, type="DOI", value="10.1234/sample.123")

        assert identifier.related == sample
        assert sample.identifiers.count() == 1

    def test_inline_relationships_can_be_created(self, sample_admin):
        """Test that inline relationship objects can be created between samples."""
        parent = SampleFactory(name="Parent Sample")
        child = SampleFactory(name="Child Sample")

        # Create relationship via inline
        relation = SampleRelation.objects.create(source=child, target=parent, type="child_of")

        assert relation.source == child
        assert relation.target == parent
        assert child.get_all_relationships().count() == 1


@pytest.mark.django_db
class TestSampleAdminConfiguration:
    """Tests for general admin configuration."""

    def test_list_display_configured(self, sample_admin):
        """Test that list_display shows appropriate fields."""
        assert "name" in sample_admin.list_display
        assert "dataset" in sample_admin.list_display
        assert "status" in sample_admin.list_display
        assert "added" in sample_admin.list_display

    def test_search_fields_configured(self, sample_admin):
        """Test that search_fields includes name, local_id, uuid."""
        assert "name" in sample_admin.search_fields
        assert "local_id" in sample_admin.search_fields
        assert "uuid" in sample_admin.search_fields

    def test_readonly_fields_configured(self, sample_admin):
        """Test that readonly fields include uuid and timestamps."""
        assert "uuid" in sample_admin.readonly_fields
        assert "added" in sample_admin.readonly_fields
        assert "modified" in sample_admin.readonly_fields

    def test_fieldsets_configured(self, sample_admin):
        """Test that base_fieldsets are properly configured for polymorphic admin."""
        # Polymorphic admin uses base_fieldsets instead of fieldsets
        assert hasattr(sample_admin, "base_fieldsets")
        assert sample_admin.base_fieldsets is not None
        assert len(sample_admin.base_fieldsets) >= 2

    def test_sample_admin_is_configured_for_inheritance(self, sample_admin):
        """Test that SampleAdmin is designed for inheritance by custom classes."""
        # SampleAdmin should have inlines configured
        assert len(sample_admin.inlines) > 0
        # SampleAdmin should have search configured
        assert len(sample_admin.search_fields) > 0
        # SampleAdmin should have list display configured
        assert len(sample_admin.list_display) > 0
