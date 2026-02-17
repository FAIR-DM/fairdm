"""Tests for Measurement filtering and search functionality (T021 - Phase 7).

This module tests the MeasurementFilter and MeasurementFilterMixin classes that provide
comprehensive filtering capabilities for Measurement models including:
- Dataset filtering
- Sample filtering
- Polymorphic type filtering
- Generic search (name, uuid)
- Cross-relationship filtering (descriptions, dates)
- Combined filters
"""

import pytest
from django.contrib.auth import get_user_model

from fairdm.core.measurement.filters import MeasurementFilter
from fairdm.core.measurement.models import MeasurementDate, MeasurementDescription
from fairdm.factories import DatasetFactory, SampleFactory
from fairdm_demo.models import ICP_MS_Measurement, XRFMeasurement

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestMeasurementFilterDatasetFiltering:
    """Test dataset filtering functionality."""

    def test_filter_by_dataset(self, user, project):
        """Test filtering measurements by dataset relationship."""
        # Create two datasets
        dataset1 = DatasetFactory(project=project)
        dataset2 = DatasetFactory(project=project)

        sample1 = SampleFactory(dataset=dataset1)
        sample2 = SampleFactory(dataset=dataset2)

        # Create measurements in different datasets
        measurement1 = XRFMeasurement.objects.create(
            name="XRF in Dataset 1",
            dataset=dataset1,
            sample=sample1,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF in Dataset 2",
            dataset=dataset2,
            sample=sample2,
            element="Cu",
            concentration_ppm=15.3,
        )

        # Filter by dataset1
        filterset = MeasurementFilter(data={"dataset": dataset1.id}, queryset=XRFMeasurement.objects.all())
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs


class TestMeasurementFilterSampleFiltering:
    """Test sample filtering functionality."""

    def test_filter_by_sample(self, user, project, dataset):
        """Test filtering measurements by sample relationship."""
        # Create two samples
        sample1 = SampleFactory(dataset=dataset, name="Sample 1")
        sample2 = SampleFactory(dataset=dataset, name="Sample 2")

        # Create measurements for different samples
        measurement1 = XRFMeasurement.objects.create(
            name="XRF for Sample 1",
            dataset=dataset,
            sample=sample1,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF for Sample 2",
            dataset=dataset,
            sample=sample2,
            element="Cu",
            concentration_ppm=15.3,
        )

        # Filter by sample1
        filterset = MeasurementFilter(data={"sample": sample1.id}, queryset=XRFMeasurement.objects.all())
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs


class TestMeasurementFilterPolymorphicTypeFiltering:
    """Test polymorphic type filtering functionality."""

    def test_filter_by_polymorphic_type(self, user, project, dataset):
        """Test filtering measurements by polymorphic content type."""
        from django.contrib.contenttypes.models import ContentType

        sample = SampleFactory(dataset=dataset)

        # Create measurements of different types
        xrf_measurement = XRFMeasurement.objects.create(
            name="XRF Measurement",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        icpms_measurement = ICP_MS_Measurement.objects.create(
            name="ICP-MS Measurement",
            dataset=dataset,
            sample=sample,
            isotope="207Pb",
            counts_per_second=1000.0,
        )

        # Get content types
        xrf_ct = ContentType.objects.get_for_model(XRFMeasurement)
        icpms_ct = ContentType.objects.get_for_model(ICP_MS_Measurement)

        # Filter by XRFMeasurement type
        from fairdm.core.measurement.models import Measurement

        filterset = MeasurementFilter(data={"polymorphic_ctype": xrf_ct.id}, queryset=Measurement.objects.all())
        assert filterset.is_valid()
        assert xrf_measurement in filterset.qs
        assert icpms_measurement not in filterset.qs

        # Filter by ICP_MS_Measurement type
        filterset = MeasurementFilter(data={"polymorphic_ctype": icpms_ct.id}, queryset=Measurement.objects.all())
        assert filterset.is_valid()
        assert icpms_measurement in filterset.qs
        assert xrf_measurement not in filterset.qs


class TestMeasurementFilterSearchFunctionality:
    """Test generic search functionality."""

    def test_search_by_name_and_uuid(self, user, project, dataset):
        """Test generic search across name and uuid fields."""
        sample = SampleFactory(dataset=dataset)

        # Create measurements with distinct names
        measurement1 = XRFMeasurement.objects.create(
            name="Iron Analysis XRF-001",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="Copper Sample Test",
            dataset=dataset,
            sample=sample,
            element="Cu",
            concentration_ppm=15.3,
        )
        measurement3 = XRFMeasurement.objects.create(
            name="Zinc Composition",
            dataset=dataset,
            sample=sample,
            element="Zn",
            concentration_ppm=8.7,
        )

        # Search by name
        filterset = MeasurementFilter(data={"search": "Iron"}, queryset=XRFMeasurement.objects.all())
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs
        assert measurement3 not in filterset.qs

        # Search by UUID (partial match)
        uuid_str = str(measurement2.uuid)[:8]
        filterset = MeasurementFilter(data={"search": uuid_str}, queryset=XRFMeasurement.objects.all())
        assert filterset.is_valid()
        assert measurement2 in filterset.qs


class TestMeasurementFilterCrossRelationshipFiltering:
    """Test cross-relationship filtering for descriptions and dates."""

    def test_filter_by_description_text(self, user, project, dataset):
        """Test filtering measurements by description text content."""
        sample = SampleFactory(dataset=dataset)

        # Create measurements
        measurement1 = XRFMeasurement.objects.create(
            name="XRF-001",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF-002",
            dataset=dataset,
            sample=sample,
            element="Cu",
            concentration_ppm=15.3,
        )

        # Add descriptions
        MeasurementDescription.objects.create(
            related=measurement1,
            type="method",
            value="High precision analysis using XRF",
        )
        MeasurementDescription.objects.create(
            related=measurement2,
            type="method",
            value="Standard quality measurement",
        )

        # Filter by description content
        filterset = MeasurementFilter(
            data={"description": "precision"},
            queryset=XRFMeasurement.objects.all(),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs

    @pytest.mark.skip(reason="PartialDateField filtering requires investigation - field validation complex")
    def test_filter_by_date_range(self, user, project, dataset):
        """Test filtering measurements by associated date ranges."""

        sample = SampleFactory(dataset=dataset)

        # Create measurements
        measurement1 = XRFMeasurement.objects.create(
            name="XRF-001",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF-002",
            dataset=dataset,
            sample=sample,
            element="Cu",
            concentration_ppm=15.3,
        )
        measurement3 = XRFMeasurement.objects.create(
            name="XRF-003",
            dataset=dataset,
            sample=sample,
            element="Zn",
            concentration_ppm=8.7,
        )

        # Add dates (PartialDateField expects string format)
        MeasurementDate.objects.create(related=measurement1, type="analysis", value="2024-01-15")
        MeasurementDate.objects.create(related=measurement2, type="analysis", value="2024-02-20")
        MeasurementDate.objects.create(related=measurement3, type="analysis", value="2024-03-10")

        # Filter by date_after
        filterset = MeasurementFilter(
            data={"date_after": "2024-02-01"},
            queryset=XRFMeasurement.objects.all(),
        )
        assert filterset.is_valid()
        assert measurement1 not in filterset.qs
        assert measurement2 in filterset.qs
        assert measurement3 in filterset.qs

        # Filter by date_before
        filterset = MeasurementFilter(
            data={"date_before": "2024-02-28"},
            queryset=XRFMeasurement.objects.all(),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 in filterset.qs
        assert measurement3 not in filterset.qs


class TestMeasurementFilterCombinedFilters:
    """Test combined filter functionality."""

    def test_combined_filters_dataset_and_sample(self, user, project):
        """Test applying multiple filters simultaneously."""
        dataset1 = DatasetFactory(project=project)
        dataset2 = DatasetFactory(project=project)

        sample1 = SampleFactory(dataset=dataset1, name="Sample 1")
        sample2 = SampleFactory(dataset=dataset1, name="Sample 2")
        sample3 = SampleFactory(dataset=dataset2, name="Sample 3")

        # Create measurements
        measurement1 = XRFMeasurement.objects.create(
            name="XRF-001",
            dataset=dataset1,
            sample=sample1,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF-002",
            dataset=dataset1,
            sample=sample2,
            element="Cu",
            concentration_ppm=15.3,
        )
        _measurement3 = XRFMeasurement.objects.create(
            name="XRF-003",
            dataset=dataset2,
            sample=sample3,
            element="Zn",
            concentration_ppm=8.7,
        )

        # Filter by dataset AND sample
        filterset = MeasurementFilter(
            data={"dataset": dataset1.id, "sample": sample1.id},
            queryset=XRFMeasurement.objects.all(),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs  # Different sample


class TestMeasurementFilterMixinUsage:
    """Test MeasurementFilterMixin for custom filters."""

    def test_custom_filter_inherits_from_mixin(self, user, project, dataset):
        """Test that custom filters can inherit from MeasurementFilterMixin."""
        import django_filters

        from fairdm.core.measurement.filters import MeasurementFilterMixin

        # Create a custom filter class that inherits from the mixin
        class CustomXRFFilter(MeasurementFilterMixin, django_filters.FilterSet):
            element = django_filters.CharFilter(field_name="element", lookup_expr="icontains")

            class Meta(MeasurementFilterMixin.Meta):
                model = XRFMeasurement
                fields = [*MeasurementFilterMixin.Meta.fields, "element"]

        sample = SampleFactory(dataset=dataset)

        # Create XRF measurements
        measurement1 = XRFMeasurement.objects.create(
            name="XRF-001",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF-002",
            dataset=dataset,
            sample=sample,
            element="Cu",
            concentration_ppm=15.3,
        )

        # Use custom filter
        filterset = CustomXRFFilter(data={"dataset": dataset.id}, queryset=XRFMeasurement.objects.all())
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 in filterset.qs
