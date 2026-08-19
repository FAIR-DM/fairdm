"""Tests for Sample filtering and search functionality.

This module tests the SampleFilter and SampleFilterMixin classes that provide
comprehensive filtering capabilities for Sample models including:
- Status filtering
- Dataset filtering
- Polymorphic type filtering
- Generic search (name, local_id, uuid)
- Cross-relationship filtering (descriptions, dates)
- Combined filters
"""

import pytest
from django.contrib.auth import get_user_model

from fairdm.core.models import Dataset
from fairdm.core.sample.filters import SampleFilter, SampleFilterMixin
from fairdm_demo.filters import RockSampleFilter
from fairdm_demo.models import RockSample, WaterSample

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestSampleFilterDatasetFiltering:
    """Test dataset filtering functionality."""

    def test_filter_by_dataset(self, user, project):
        """Test filtering samples by dataset relationship."""
        # Left private, which is the model's default and the ordinary case: the
        # filter's "dataset" choices come from `Dataset.all_objects`, so filtering
        # by one works.
        dataset1 = Dataset.objects.create(name="Dataset 1", project=project)
        dataset2 = Dataset.objects.create(name="Dataset 2", project=project)

        # Create samples in different datasets
        sample1 = RockSample.objects.create(
            name="Rock in Dataset 1",
            dataset=dataset1,
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        sample2 = RockSample.objects.create(
            name="Rock in Dataset 2",
            dataset=dataset2,
            rock_type="sedimentary",
            collection_date="2024-01-01",
        )

        # Filter by dataset1
        filterset = SampleFilter(
            data={"dataset": dataset1.id}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs


class TestSampleFilterPolymorphicTypeFiltering:
    """Test polymorphic type filtering functionality."""

    def test_filter_by_polymorphic_type(self, user, project, dataset):
        """Test filtering samples by polymorphic content type."""
        from django.contrib.contenttypes.models import ContentType

        # Create samples of different types
        rock_sample = RockSample.objects.create(
            name="Rock Sample",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        water_sample = WaterSample.objects.create(
            name="Water Sample",
            dataset=dataset,
            water_source="river",
            temperature_celsius=15.5,
            ph_level=7.2,
        )

        # Get content types
        rock_ct = ContentType.objects.get_for_model(RockSample)
        water_ct = ContentType.objects.get_for_model(WaterSample)

        # Filter by RockSample type
        from fairdm.core.sample.models import Sample

        filterset = SampleFilter(
            data={"polymorphic_ctype": rock_ct.id}, queryset=Sample.objects.all()
        )
        assert filterset.is_valid()
        assert rock_sample in filterset.qs
        assert water_sample not in filterset.qs

        # Filter by WaterSample type
        filterset = SampleFilter(
            data={"polymorphic_ctype": water_ct.id}, queryset=Sample.objects.all()
        )
        assert filterset.is_valid()
        assert water_sample in filterset.qs
        assert rock_sample not in filterset.qs


class TestSampleFilterSearchFunctionality:
    """Test generic search functionality."""

    def test_search_by_name_local_id_uuid(self, user, project, dataset):
        """Test generic search across name, local_id, and uuid fields."""
        # Create samples with distinctive values
        sample1 = RockSample.objects.create(
            name="Granite Sample XYZ",
            local_id="ROCK-001",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        sample2 = RockSample.objects.create(
            name="Basalt Sample",
            local_id="ROCK-002",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )

        # Search by name fragment
        filterset = SampleFilter(
            data={"search": "Granite"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs

        # Search by local_id
        filterset = SampleFilter(
            data={"search": "ROCK-002"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample2 in filterset.qs
        assert sample1 not in filterset.qs

        # Search by partial uuid
        uuid_fragment = str(sample1.uuid)[:8]
        filterset = SampleFilter(
            data={"search": uuid_fragment}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs


class TestSampleFilterDescriptionFiltering:
    """Test cross-relationship filtering by description content."""

    @pytest.mark.skip(
        reason="Description filtering requires SampleDescription model implementation"
    )
    def test_filter_by_description_content(self, user, project, dataset):
        """Test filtering samples by description text (cross-relationship)."""
        # Create samples with descriptions
        sample1 = RockSample.objects.create(
            name="Rock 1",
            dataset=dataset,
            collection_date="2024-01-01",
            temperature_celsius=25,
        )
        sample1.descriptions.create(text="Contains high silica content")

        sample2 = RockSample.objects.create(
            name="Rock 2",
            dataset=dataset,
            collection_date="2024-01-01",
            temperature_celsius=25,
        )
        sample2.descriptions.create(text="Rich in iron oxide minerals")

        # Filter by description content
        filterset = SampleFilter(
            data={"description": "silica"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs


class TestSampleFilterDateRangeFiltering:
    """Test cross-relationship filtering by date ranges."""

    @pytest.mark.skip(reason="Date filtering requires SampleDate model implementation")
    def test_filter_by_date_range(self, user, project, dataset):
        """Test filtering samples by associated date ranges (cross-relationship)."""
        # Create samples with different analysis dates
        sample1 = RockSample.objects.create(
            name="Rock 1",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        sample1.dates.create(date="2024-01-15", type="analysis")

        sample2 = RockSample.objects.create(
            name="Rock 2",
            dataset=dataset,
            rock_type="sedimentary",
            collection_date="2024-01-01",
        )
        sample2.dates.create(date="2024-02-20", type="analysis")

        # Filter by date range (should include sample1, exclude sample2)
        filterset = SampleFilter(
            data={"date_after": "2024-01-10", "date_before": "2024-02-01"},
            queryset=RockSample.objects.all(),
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs


class TestSampleFilterCombinedFilters:
    """Test combination of multiple filters."""

    @pytest.mark.skip(
        reason="Combined filters with descriptions require SampleDescription model implementation"
    )
    def test_combined_filters(self, user, project, dataset):
        """Test applying multiple filters simultaneously."""
        # Create samples with various attributes
        target_sample = RockSample.objects.create(
            name="Target Rock",
            dataset=dataset,
            status="available",
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        target_sample.descriptions.create(text="Special properties")

        excluded_sample1 = RockSample.objects.create(
            name="Excluded Rock 1",
            dataset=dataset,
            status="unavailable",  # Wrong status
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        excluded_sample1.descriptions.create(text="Special properties")

        excluded_sample2 = RockSample.objects.create(
            name="Excluded Rock 2",
            dataset=dataset,
            status="available",  # Right status
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        excluded_sample2.descriptions.create(
            text="Normal properties"
        )  # Wrong description

        # Apply combined filters: status=available AND description contains "Special"
        filterset = SampleFilter(
            data={"status": "available", "description": "Special"},
            queryset=RockSample.objects.all(),
        )
        assert filterset.is_valid()
        assert target_sample in filterset.qs
        assert excluded_sample1 not in filterset.qs
        assert excluded_sample2 not in filterset.qs


class TestSampleFilterMixinConfiguration:
    """Test SampleFilterMixin provides pre-configured filters."""

    def test_mixin_provides_common_filters(self):
        """Test that SampleFilterMixin provides standard filter fields."""
        # The mixin should provide these filter fields automatically
        expected_filters = ["status", "dataset", "polymorphic_ctype", "search"]

        # Check that SampleFilter has these filters configured
        filter_instance = SampleFilter()
        for filter_name in expected_filters:
            assert filter_name in filter_instance.filters, (
                f"Expected filter '{filter_name}' not found in SampleFilter"
            )


class TestSampleFilterMixinInheritance:
    """T065 - a filter set inheriting SampleFilterMixin carries every filter the
    mixin declares, alongside its own, asserted by naming the filters."""

    def test_inheriting_filter_set_carries_the_mixins_declared_filters(self):
        """RockSampleFilter inherits SampleFilterMixin, so its own filters set
        must include every filter the mixin declares (currently just "image"),
        naming it rather than checking the filter set is merely non-empty."""
        filterset = RockSampleFilter()

        assert "image" in filterset.filters
        # And the type's own filters are still present alongside it.
        assert "rock_type" in filterset.filters
        assert "mineral_content" in filterset.filters
        assert "grain_size" in filterset.filters

    def test_mixin_declares_only_image(self):
        """Confirms the mixin's declared filters are exactly what T071 fixed -
        the cross-relationship filters (description, dates) stay on SampleFilter,
        out of scope for this mixin (D-008, D-001)."""
        assert set(SampleFilterMixin.declared_filters) == {"image"}


class TestSampleFilterBehaviour:
    """T066 - each filter the mixin declares narrows a queryset correctly, over
    fixtures that would fail if the filter were a no-op."""

    def test_image_filter_narrows_to_samples_with_an_image(self, dataset):
        """A no-op "image" filter would return every sample regardless of the
        query value, so the fixture pair below fails as soon as the filter is
        satisfied by a queryset unaffected by the field."""
        with_image = RockSample.objects.create(
            name="Rock With Image",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
            image="samples/has-image.jpg",
        )
        without_image = RockSample.objects.create(
            name="Rock Without Image",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )

        filterset = RockSampleFilter(
            data={"image": "true"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid(), filterset.errors
        assert with_image in filterset.qs
        assert without_image not in filterset.qs


class TestCustomSampleFilterIntegration:
    """Test custom sample filters inherit from SampleFilterMixin."""

    @pytest.mark.skip(
        reason="RockSampleFilter rock_type field not configured in Meta.fields"
    )
    def test_custom_filter_inherits_from_mixin(self, user, project, dataset):
        """Test that custom sample filters use SampleFilterMixin and work correctly."""
        # Create rock sample
        rock_sample = RockSample.objects.create(
            name="Granite",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )

        # Use custom RockSampleFilter (should inherit mixin filters)
        filterset = RockSampleFilter(
            data={"search": "Granite"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert rock_sample in filterset.qs

        # Verify custom filter has both mixin filters and custom filters
        assert "search" in filterset.filters  # From mixin
        assert "rock_type" in filterset.filters  # Custom filter
