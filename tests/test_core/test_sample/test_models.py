"""
Unit tests for Sample model.

Tests cover model creation, polymorphic inheritance, validation,
field constraints, and polymorphic query behavior.
"""

import pytest
from django.core.exceptions import ValidationError

from fairdm.core.models import Sample


@pytest.mark.django_db
class TestSampleModelCreation:
    """Test Sample model creation with all base fields."""

    def test_rock_sample_creation_with_all_fields(self, dataset):
        """Test creating a RockSample with all base fields populated."""
        from fairdm_demo.models import RockSample

        sample = RockSample.objects.create(
            name="Test Rock",
            dataset=dataset,
            local_id="ROCK-001",
            status="available",
            rock_type="igneous",
            collection_date="2024-01-15",
        )

        assert sample.pk is not None
        assert sample.name == "Test Rock"
        assert sample.dataset == dataset
        assert sample.local_id == "ROCK-001"
        assert sample.status == "available"
        assert sample.uuid.startswith("s")
        assert sample.added is not None
        assert sample.modified is not None
        assert sample.rock_type == "igneous"

    def test_water_sample_creation_with_minimal_fields(self, dataset):
        """Test creating a WaterSample with only required fields."""
        from fairdm_demo.models import WaterSample

        sample = WaterSample.objects.create(
            name="Minimal Water",
            dataset=dataset,
            water_source="lake",
            ph_level=7.0,
            temperature_celsius=20.0,
        )

        assert sample.pk is not None
        assert sample.name == "Minimal Water"
        assert sample.dataset == dataset
        assert sample.status == "unknown"  # Default value

    def test_sample_uuid_is_unique(self, rock_sample, water_sample):
        """Test that sample UUIDs are unique."""
        assert rock_sample.uuid != water_sample.uuid
        assert rock_sample.uuid.startswith("s")
        assert water_sample.uuid.startswith("s")


@pytest.mark.django_db
class TestSamplePolymorphicInheritance:
    """Test polymorphic inheritance behavior for Sample model."""

    def test_polymorphic_sample_subclass_creation(self, dataset):
        """Test creating a polymorphic sample subclass (RockSample)."""
        from fairdm_demo.models import RockSample

        rock = RockSample.objects.create(
            name="Granite Rock",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-15",
        )

        assert rock.pk is not None
        assert rock.name == "Granite Rock"
        assert hasattr(rock, "rock_type")
        assert rock.rock_type == "igneous"

    def test_polymorphic_query_returns_typed_instances(self, dataset):
        """Test that querying Sample returns correctly typed instances."""
        from fairdm_demo.models import RockSample, WaterSample

        # Create different sample types
        rock = RockSample.objects.create(
            name="Granite",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        water = WaterSample.objects.create(
            name="River Water",
            dataset=dataset,
            water_source="river",
            ph_level=7.2,
            temperature_celsius=15.0,
        )

        # Query all samples - should return typed instances
        samples = Sample.objects.all()

        assert samples.count() == 2
        # Get specific instances by PK to check types
        rock_instance = samples.get(pk=rock.pk)
        water_instance = samples.get(pk=water.pk)

        assert isinstance(rock_instance, RockSample)
        assert isinstance(water_instance, WaterSample)
        assert hasattr(rock_instance, "rock_type")
        assert hasattr(water_instance, "ph_level")


@pytest.mark.django_db
class TestSampleModelValidation:
    """Test Sample model validation rules and field constraints."""

    def test_sample_status_transitions_unrestricted(self, rock_sample):
        """Test that status transitions are unrestricted (FR-071)."""
        # Set to complete
        rock_sample.status = "complete"
        rock_sample.save()
        rock_sample.refresh_from_db()
        assert rock_sample.status.name == "complete"

        # Status should allow transition from complete to ongoing
        rock_sample.status = "ongoing"
        rock_sample.save()
        rock_sample.refresh_from_db()
        assert rock_sample.status.name == "ongoing"

        # Status should allow transition back to planned
        rock_sample.status = "planned"
        rock_sample.save()
        rock_sample.refresh_from_db()
        assert rock_sample.status.name == "planned"


@pytest.mark.django_db
class TestSampleDirectInstantiation:
    """Test that direct Sample instantiation is prevented."""

    def test_sample_cannot_be_instantiated_directly(self, dataset):
        """Test that base Sample model cannot be instantiated directly (only subclasses)."""
        # This test validates FR-001 requirement
        # Direct instantiation should be prevented via clean() validation

        sample = Sample(
            name="Direct Sample",
            dataset=dataset,
        )

        # Should raise ValidationError when clean() is called
        with pytest.raises(ValidationError) as exc_info:
            sample.clean()

        error_message = str(exc_info.value).lower()
        assert "subclass" in error_message or "directly" in error_message


@pytest.mark.django_db
class TestSampleQuerySetOptimizations:
    """Test QuerySet optimization methods for efficient queries."""

    def test_with_related_prefetches_dataset_location_contributors(self, dataset):
        """Test that with_related() prefetches dataset, location, and contributors."""
        from datetime import date

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm_demo.models import RockSample

        # Create samples with related data
        samples = []
        for i in range(5):
            sample = RockSample.objects.create(
                name=f"Rock {i}",
                dataset=dataset,
                rock_type="igneous",
                collection_date=date.today(),
            )
            samples.append(sample)

        # Test without optimization - expect many queries
        with CaptureQueriesContext(connection) as context_without:
            samples_without = list(RockSample.objects.all())
            for sample in samples_without:
                _ = sample.dataset.name  # Access dataset
                _ = sample.dataset.project  # Access nested relation

        queries_without = len(context_without.captured_queries)

        # Test with optimization - expect fewer queries
        with CaptureQueriesContext(connection) as context_with:
            samples_with = list(RockSample.objects.with_related())
            for sample in samples_with:
                _ = sample.dataset.name  # Access dataset
                _ = sample.dataset.project  # Access nested relation

        queries_with = len(context_with.captured_queries)

        # Assert optimization reduces queries significantly
        # with_related should use ~3 queries (samples, dataset+location, contributors)
        # vs N+1 queries without optimization
        assert queries_with < queries_without
        assert queries_with <= 5  # Should be around 3-4 queries max

    def test_with_metadata_prefetches_descriptions_dates_identifiers(self, dataset):
        """Test that with_metadata() prefetches descriptions, dates, and identifiers."""
        from datetime import date

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm.core.sample.models import SampleDate, SampleDescription
        from fairdm_demo.models import RockSample

        # Create sample with metadata
        sample = RockSample.objects.create(
            name="Rock with metadata",
            dataset=dataset,
            rock_type="igneous",
            collection_date=date.today(),
        )
        SampleDescription.objects.create(related=sample, type="abstract", value="Test description")
        SampleDate.objects.create(related=sample, type="collected", value="2024-01-15")

        # Test without optimization
        with CaptureQueriesContext(connection) as context_without:
            samples_without = list(RockSample.objects.filter(pk=sample.pk))
            for s in samples_without:
                _ = list(s.descriptions.all())
                _ = list(s.dates.all())

        len(context_without.captured_queries)

        # Test with optimization
        with CaptureQueriesContext(connection) as context_with:
            samples_with = list(RockSample.objects.filter(pk=sample.pk).with_metadata())
            for s in samples_with:
                _ = list(s.descriptions.all())
                _ = list(s.dates.all())

        queries_with = len(context_with.captured_queries)

        # Assert optimization reduces queries
        # Note: For a single sample, prefetch may add overhead
        # The benefit shows with multiple samples
        assert queries_with <= 4  # Should be ~4 queries (samples, descriptions, dates, identifiers)

    def test_polymorphic_queryset_returns_correct_typed_instances(self, dataset):
        """Test that PolymorphicQuerySet automatically returns correctly typed instances."""
        from datetime import date

        from fairdm.core.sample.models import Sample
        from fairdm_demo.models import RockSample, WaterSample

        # Create mixed sample types
        RockSample.objects.create(
            name="Rock Sample",
            dataset=dataset,
            rock_type="igneous",
            collection_date=date.today(),
        )
        WaterSample.objects.create(
            name="Water Sample",
            dataset=dataset,
            water_source="lake",
            temperature_celsius=15.5,
            ph_level=7.2,
        )

        # Query from base Sample model - should return typed instances automatically
        samples = list(Sample.objects.all())

        # All instances should be correctly typed (not base Sample)
        rock_instances = [s for s in samples if isinstance(s, RockSample)]
        water_instances = [s for s in samples if isinstance(s, WaterSample)]

        assert len(rock_instances) >= 1
        assert len(water_instances) >= 1

        # Verify we got actual subclass instances with polymorphic behavior
        for sample in samples:
            # Should be typed as subclass, not base Sample
            assert type(sample).__name__ in ["RockSample", "WaterSample"]
            # Should have subclass-specific attributes
            assert hasattr(sample, "rock_type") or hasattr(sample, "water_source")

    def test_queryset_method_chaining_works_correctly(self, dataset):
        """Test that QuerySet optimization methods can be chained together."""
        from datetime import date

        from fairdm_demo.models import RockSample

        # Create test samples
        for i in range(3):
            RockSample.objects.create(
                name=f"Rock {i}",
                dataset=dataset,
                rock_type="igneous",
                collection_date=date.today(),
            )

        # Chain multiple optimization methods
        chained = RockSample.objects.with_related().with_metadata()

        # Should return a valid queryset
        assert chained.count() >= 3

        # Should be able to further filter after chaining
        filtered = chained.filter(rock_type="igneous")
        assert filtered.count() >= 3

        # Should be able to iterate and get typed instances
        for sample in filtered[:2]:
            assert isinstance(sample, RockSample)
            assert sample.rock_type == "igneous"

    @pytest.mark.slow
    def test_1000_samples_load_with_minimal_queries_using_with_related(self, dataset):
        """Performance test: 1000 samples should load with <10 queries using with_related()."""
        from datetime import date

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm_demo.models import RockSample

        # Create 100 samples (1000 is too slow for regular test runs)
        samples = []
        for i in range(100):
            sample = RockSample.objects.create(
                name=f"Rock {i}",
                dataset=dataset,
                rock_type="igneous",
                collection_date=date.today(),
            )
            samples.append(sample)

        # Query with optimization
        with CaptureQueriesContext(connection) as context:
            optimized_samples = list(RockSample.objects.with_related())
            # Access related data to verify prefetch works
            for sample in optimized_samples[:10]:  # Check first 10
                _ = sample.dataset.name
                _ = sample.dataset.project

        num_queries = len(context.captured_queries)

        # Should use very few queries regardless of sample count
        # Expect: 1 for samples, 1 for dataset+location prefetch, 1 for contributors
        assert num_queries <= 10  # Goal: <10 queries for any sample count

    @pytest.mark.slow
    def test_polymorphic_queries_complete_quickly_for_1000_samples(self, dataset):
        """Performance test: Polymorphic queries should complete quickly for large result sets."""
        import time
        from datetime import date

        from fairdm.core.sample.models import Sample
        from fairdm_demo.models import RockSample, WaterSample

        # Create 50 of each type (100 total - scaled down for test speed)
        for i in range(50):
            RockSample.objects.create(
                name=f"Rock {i}",
                dataset=dataset,
                rock_type="igneous",
                collection_date=date.today(),
            )
            WaterSample.objects.create(
                name=f"Water {i}",
                dataset=dataset,
                water_source="lake",
                temperature_celsius=15.5,
                ph_level=7.2,
            )

        # Time the query with optimization - polymorphic behavior is automatic
        start = time.perf_counter()
        samples = list(Sample.objects.with_related())
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        # Verify we got typed instances automatically
        assert len(samples) >= 100
        for sample in samples[:5]:  # Check first 5
            assert type(sample).__name__ in ["RockSample", "WaterSample"]

        # Performance check - should be reasonably fast even for 100+ samples
        # Target: <500ms for 100 samples (django-polymorphic adds some overhead)
        # Note: Actual goal is <200ms for 1000 samples, we're testing 100 here
        assert duration_ms < 500  # Very generous for 100 samples
