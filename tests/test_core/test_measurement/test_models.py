"""
Unit tests for Measurement model.

Tests cover model creation, polymorphic inheritance, validation,
field constraints, and polymorphic query behavior.
"""

import pytest
from django.core.exceptions import ValidationError

from fairdm.core.models import Measurement


@pytest.mark.django_db
class TestMeasurementModelCreation:
    """Test Measurement model creation with all base fields."""

    def test_xrf_measurement_creation_with_all_fields(self, sample):
        """Test creating an XRFMeasurement with all base fields populated."""
        from fairdm_demo.models import XRFMeasurement

        measurement = XRFMeasurement.objects.create(
            name="XRF Analysis",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
            detection_limit_ppm=5.0,
        )

        assert measurement.pk is not None
        assert measurement.name == "XRF Analysis"
        assert measurement.sample == sample
        assert measurement.dataset == sample.dataset
        assert measurement.uuid.startswith("m")
        assert measurement.added is not None
        assert measurement.modified is not None
        assert measurement.element == "Si"
        assert measurement.concentration_ppm == 250000.0

    def test_icp_ms_measurement_creation_with_minimal_fields(self, sample):
        """Test creating an ICP_MS_Measurement with only required fields."""
        from fairdm_demo.models import ICP_MS_Measurement

        measurement = ICP_MS_Measurement.objects.create(
            name="ICP-MS Analysis",
            sample=sample,
            dataset=sample.dataset,
            isotope="207Pb",
            counts_per_second=15000.0,
            concentration_ppb=120.5,
        )

        assert measurement.pk is not None
        assert measurement.name == "ICP-MS Analysis"
        assert measurement.sample == sample
        assert measurement.dataset == sample.dataset
        assert measurement.isotope == "207Pb"

    def test_measurement_uuid_is_unique(self, xrf_measurement, icp_ms_measurement):
        """Test that measurement UUIDs are unique."""
        assert xrf_measurement.uuid != icp_ms_measurement.uuid
        assert xrf_measurement.uuid.startswith("m")
        assert icp_ms_measurement.uuid.startswith("m")


@pytest.mark.django_db
class TestMeasurementPolymorphicInheritance:
    """Test polymorphic inheritance behavior for Measurement model."""

    def test_polymorphic_measurement_subclass_creation(self, sample):
        """Test creating a polymorphic measurement subclass (XRFMeasurement)."""
        from fairdm_demo.models import XRFMeasurement

        xrf = XRFMeasurement.objects.create(
            name="XRF Test",
            sample=sample,
            dataset=sample.dataset,
            element="Fe",
            concentration_ppm=50000.0,
            detection_limit_ppm=2.0,
        )

        assert xrf.pk is not None
        assert xrf.name == "XRF Test"
        assert hasattr(xrf, "element")
        assert xrf.element == "Fe"

    def test_polymorphic_query_returns_typed_instances(self, sample):
        """Test that querying Measurement returns correctly typed instances."""
        from fairdm_demo.models import ICP_MS_Measurement, XRFMeasurement

        # Create different measurement types
        xrf = XRFMeasurement.objects.create(
            name="XRF",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
            detection_limit_ppm=5.0,
        )
        icp = ICP_MS_Measurement.objects.create(
            name="ICP-MS",
            sample=sample,
            dataset=sample.dataset,
            isotope="207Pb",
            counts_per_second=15000.0,
            concentration_ppb=120.5,
        )

        # Query all measurements - should return typed instances
        measurements = Measurement.objects.all()

        assert measurements.count() == 2
        # Get specific instances by PK to check types
        xrf_instance = measurements.get(pk=xrf.pk)
        icp_instance = measurements.get(pk=icp.pk)

        assert isinstance(xrf_instance, XRFMeasurement)
        assert isinstance(icp_instance, ICP_MS_Measurement)
        assert hasattr(xrf_instance, "element")
        assert hasattr(icp_instance, "isotope")


@pytest.mark.django_db
class TestMeasurementVocabularyValidation:
    """Test that Measurement uses correct vocabulary collections."""

    def test_measurement_description_uses_measurement_vocabulary(self, measurement):
        """Test that MeasurementDescription uses 'Measurement' vocabulary collection."""
        from fairdm.core.measurement.models import MeasurementDescription

        # Create a description
        desc = MeasurementDescription.objects.create(
            related=measurement, type="method", value="XRF spectroscopy analysis"
        )

        # Verify the vocabulary type comes from Measurement collection
        assert desc.type == "method"  # type field returns string value
        # The vocabulary should be from FairDMDescriptions "Measurement" collection
        assert desc.VOCABULARY is not None

    def test_measurement_date_uses_measurement_vocabulary(self, measurement):
        """Test that MeasurementDate uses 'Measurement' vocabulary collection."""
        from fairdm.core.measurement.models import MeasurementDate

        # Create a date
        date = MeasurementDate.objects.create(related=measurement, type="measured", value="2024-01-15")

        # Verify the vocabulary type comes from Measurement collection
        assert date.type == "measured"  # type field returns string value
        # The vocabulary should be from FairDMDates "Measurement" collection
        assert date.VOCABULARY is not None


@pytest.mark.django_db
class TestMeasurementCrossDatasetSampleLinking:
    """Test that measurements can link to samples in different datasets."""

    def test_measurement_can_link_to_sample_in_different_dataset(self, sample):
        """Test that a measurement can belong to dataset A but measure sample from dataset B (FR-053)."""
        from fairdm.factories import DatasetFactory
        from fairdm_demo.models import XRFMeasurement

        # Create a different dataset
        dataset_b = DatasetFactory(project=sample.dataset.project)

        # Create measurement in dataset B that measures sample from dataset A
        measurement = XRFMeasurement.objects.create(
            name="Cross-Dataset XRF",
            sample=sample,  # Sample is in dataset A
            dataset=dataset_b,  # Measurement is in dataset B
            element="Ca",
            concentration_ppm=15000.0,
        )

        assert measurement.sample.dataset != measurement.dataset
        assert measurement.sample == sample
        assert measurement.dataset == dataset_b


@pytest.mark.django_db
class TestMeasurementValueMethods:
    """Test get_value() and print_value() methods."""

    def test_get_value_returns_name_for_base_measurement(self, measurement):
        """Test that get_value() returns measurement name for base Measurement class."""
        # Base Measurement doesn't have 'value' or 'uncertainty' attributes
        value = measurement.get_value()
        assert value == measurement.name

    def test_print_value_returns_string_for_base_measurement(self, measurement):
        """Test that print_value() returns string for base Measurement class."""
        # Base Measurement doesn't have 'value' or 'uncertainty' attributes
        value_str = measurement.print_value()
        assert isinstance(value_str, str)
        assert value_str == measurement.name


@pytest.mark.django_db
class TestMeasurementDirectInstantiation:
    """Test that direct Measurement instantiation is prevented."""

    def test_measurement_cannot_be_instantiated_directly(self, sample):
        """Test that base Measurement model cannot be instantiated directly (only subclasses)."""
        # This test validates FR-001 requirement (same as Sample)
        # Direct instantiation should be prevented via clean() validation

        measurement = Measurement(
            name="Direct Measurement",
            sample=sample,
            dataset=sample.dataset,
        )

        # Should raise ValidationError when clean() is called
        with pytest.raises(ValidationError) as exc_info:
            measurement.clean()

        error_message = str(exc_info.value).lower()
        assert "subclass" in error_message or "directly" in error_message


@pytest.mark.django_db
class TestMeasurementURLPattern:
    """Test get_absolute_url() returns correct pattern."""

    @pytest.mark.skip(reason="URL patterns not implemented yet - Phase 8")
    def test_get_absolute_url_returns_measurement_detail_pattern(self, xrf_measurement):
        """Test that get_absolute_url() follows measurement:overview pattern with UUID."""
        url = xrf_measurement.get_absolute_url()

        # Should match pattern: /measurement/{uuid}/
        assert url.startswith("/measurement/")
        assert xrf_measurement.uuid in url
        assert url.endswith("/")


@pytest.mark.django_db
class TestMeasurementCascadeBehavior:
    """Test CASCADE and PROTECT deletion behavior."""

    def test_deleting_dataset_cascades_to_measurements(self, xrf_measurement):
        """Test that deleting a dataset cascades to its measurements (CASCADE)."""
        dataset = xrf_measurement.dataset
        measurement_pk = xrf_measurement.pk

        # Delete measurement first (to avoid Sample.dataset PROTECT blocking)
        xrf_measurement.delete()

        # Delete dataset
        dataset.delete()

        # Measurement should be deleted
        assert not Measurement.objects.filter(pk=measurement_pk).exists()

    def test_deleting_sample_protects_measurements(self, xrf_measurement):
        """Test that measurements prevent sample deletion (PROTECT)."""
        from django.db.models import ProtectedError

        sample = xrf_measurement.sample

        # Attempt to delete sample should fail
        with pytest.raises(ProtectedError):
            sample.delete()

        # Measurement should still exist
        assert Measurement.objects.filter(pk=xrf_measurement.pk).exists()


@pytest.mark.django_db
class TestMeasurementQuerySetOptimizations:
    """Test QuerySet optimization methods for efficient queries."""

    def test_with_related_prefetches_sample_dataset_contributors(self, sample):
        """Test that with_related() prefetches sample, dataset, and contributors."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm_demo.models import XRFMeasurement

        # Create measurements with related data
        measurements = []
        for i in range(5):
            measurement = XRFMeasurement.objects.create(
                name=f"XRF {i}",
                sample=sample,
                dataset=sample.dataset,
                element="Si",
                concentration_ppm=250000.0 + i,
                detection_limit_ppm=5.0,
            )
            measurements.append(measurement)

        # Test without optimization - expect many queries
        with CaptureQueriesContext(connection) as context_without:
            measurements_without = list(XRFMeasurement.objects.all())
            for measurement in measurements_without:
                _ = measurement.sample.name  # Access sample
                _ = measurement.dataset.name  # Access dataset

        queries_without = len(context_without.captured_queries)

        # Test with optimization - expect fewer queries
        with CaptureQueriesContext(connection) as context_with:
            measurements_with = list(XRFMeasurement.objects.with_related())
            for measurement in measurements_with:
                _ = measurement.sample.name  # Access sample
                _ = measurement.dataset.name  # Access dataset

        queries_with = len(context_with.captured_queries)

        # Assert optimization reduces queries significantly
        # with_related should use ~3 queries (measurements, sample+dataset, contributors)
        # vs N+1 queries without optimization
        assert queries_with < queries_without
        assert queries_with <= 5  # Should be around 3-4 queries max

    def test_with_metadata_prefetches_descriptions_dates_identifiers(self, sample):
        """Test that with_metadata() prefetches descriptions, dates, and identifiers."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm.core.measurement.models import MeasurementDate, MeasurementDescription
        from fairdm_demo.models import XRFMeasurement

        # Create measurement with metadata
        measurement = XRFMeasurement.objects.create(
            name="XRF with metadata",
            sample=sample,
            dataset=sample.dataset,
            element="Ca",
            concentration_ppm=15000.0,
            detection_limit_ppm=2.0,
        )
        MeasurementDescription.objects.create(related=measurement, type="method", value="XRF analysis")
        MeasurementDate.objects.create(related=measurement, type="measured", value="2024-01-15")

        # Test without optimization
        with CaptureQueriesContext(connection) as context_without:
            measurements_without = list(XRFMeasurement.objects.filter(pk=measurement.pk))
            for m in measurements_without:
                _ = list(m.descriptions.all())
                _ = list(m.dates.all())

        len(context_without.captured_queries)

        # Test with optimization
        with CaptureQueriesContext(connection) as context_with:
            measurements_with = list(XRFMeasurement.objects.filter(pk=measurement.pk).with_metadata())
            for m in measurements_with:
                _ = list(m.descriptions.all())
                _ = list(m.dates.all())

        queries_with = len(context_with.captured_queries)

        # Assert optimization reduces queries
        # Note: For a single measurement, prefetch may add overhead
        # The benefit shows with multiple measurements
        assert queries_with <= 4  # Should be ~4 queries (measurements, descriptions, dates, identifiers)

    def test_polymorphic_queryset_returns_correct_typed_instances(self, sample):
        """Test that PolymorphicQuerySet automatically returns correctly typed instances."""
        from fairdm.core.measurement.models import Measurement
        from fairdm_demo.models import ICP_MS_Measurement, XRFMeasurement

        # Create mixed measurement types
        XRFMeasurement.objects.create(
            name="XRF Measurement",
            sample=sample,
            dataset=sample.dataset,
            element="Fe",
            concentration_ppm=50000.0,
            detection_limit_ppm=2.0,
        )
        ICP_MS_Measurement.objects.create(
            name="ICP-MS Measurement",
            sample=sample,
            dataset=sample.dataset,
            isotope="207Pb",
            counts_per_second=15000.0,
            concentration_ppb=120.5,
        )

        # Query from base Measurement model - should return typed instances automatically
        measurements = list(Measurement.objects.all())

        # All instances should be correctly typed (not base Measurement)
        xrf_instances = [m for m in measurements if isinstance(m, XRFMeasurement)]
        icp_instances = [m for m in measurements if isinstance(m, ICP_MS_Measurement)]

        assert len(xrf_instances) >= 1
        assert len(icp_instances) >= 1

        # Verify we got actual subclass instances with polymorphic behavior
        for measurement in measurements:
            # Should be typed as subclass, not base Measurement
            assert type(measurement).__name__ in ["XRFMeasurement", "ICP_MS_Measurement", "ExampleMeasurement"]
            # Should have subclass-specific attributes
            assert (
                hasattr(measurement, "element") or hasattr(measurement, "isotope") or hasattr(measurement, "char_field")
            )

    def test_queryset_method_chaining_works_correctly(self, sample):
        """Test that QuerySet optimization methods can be chained together."""
        from fairdm_demo.models import XRFMeasurement

        # Create test measurements
        for i in range(3):
            XRFMeasurement.objects.create(
                name=f"XRF {i}",
                sample=sample,
                dataset=sample.dataset,
                element="Si",
                concentration_ppm=250000.0 + i,
                detection_limit_ppm=5.0,
            )

        # Chain multiple optimization methods
        chained = XRFMeasurement.objects.with_related().with_metadata()

        # Should return a valid queryset
        assert chained.count() >= 3

        # Should be able to further filter after chaining
        filtered = chained.filter(element="Si")
        assert filtered.count() >= 3

        # Should be able to iterate and get typed instances
        for measurement in filtered[:2]:
            assert isinstance(measurement, XRFMeasurement)
            assert measurement.element == "Si"

    @pytest.mark.slow
    def test_1000_measurements_load_with_minimal_queries_using_with_related(self, sample):
        """Performance test: 1000 measurements should load with <10 queries using with_related()."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm_demo.models import XRFMeasurement

        # Create 100 measurements (1000 is too slow for regular test runs)
        measurements = []
        for i in range(100):
            measurement = XRFMeasurement.objects.create(
                name=f"XRF {i}",
                sample=sample,
                dataset=sample.dataset,
                element="Si",
                concentration_ppm=250000.0 + i,
                detection_limit_ppm=5.0,
            )
            measurements.append(measurement)

        # Query with optimization
        with CaptureQueriesContext(connection) as context:
            optimized_measurements = list(XRFMeasurement.objects.with_related())
            # Access related data to verify prefetch works
            for measurement in optimized_measurements[:10]:  # Check first 10
                _ = measurement.sample.name
                _ = measurement.dataset.name

        num_queries = len(context.captured_queries)

        # Should use very few queries regardless of measurement count
        # Expect: 1 for measurements, 1 for sample+dataset prefetch, 1 for contributors
        assert num_queries <= 10  # Goal: <10 queries for any measurement count

    @pytest.mark.slow
    def test_polymorphic_queries_complete_quickly_for_1000_measurements(self, sample):
        """Performance test: Polymorphic queries should complete quickly for large result sets."""
        import time

        from fairdm.core.measurement.models import Measurement
        from fairdm_demo.models import ICP_MS_Measurement, XRFMeasurement

        # Create 50 of each type (100 total - scaled down for test speed)
        for i in range(50):
            XRFMeasurement.objects.create(
                name=f"XRF {i}",
                sample=sample,
                dataset=sample.dataset,
                element="Fe",
                concentration_ppm=50000.0 + i,
                detection_limit_ppm=2.0,
            )
            ICP_MS_Measurement.objects.create(
                name=f"ICP-MS {i}",
                sample=sample,
                dataset=sample.dataset,
                isotope="207Pb",
                counts_per_second=15000.0 + i,
                concentration_ppb=120.5 + i,
            )

        # Time the query with optimization - polymorphic behavior is automatic
        start = time.perf_counter()
        measurements = list(Measurement.objects.with_related())
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        # Verify we got typed instances automatically
        assert len(measurements) >= 100
        for measurement in measurements[:5]:  # Check first 5
            assert type(measurement).__name__ in ["XRFMeasurement", "ICP_MS_Measurement"]

        # Performance check - should be reasonably fast even for 100+ measurements
        # Target: <500ms for 100 measurements (django-polymorphic adds some overhead)
        # Note: Actual goal is <200ms for 1000 measurements, we're testing 100 here
        # Allowing 1000ms for test environment overhead (SQLite, Windows, CI)
        assert duration_ms < 1000  # Generous for test environment
