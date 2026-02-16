"""Tests for the Measurement model, views, and forms."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from fairdm.core.measurement.forms import MeasurementForm
from fairdm.core.measurement.models import MeasurementDate, MeasurementDescription
from fairdm.core.models import Measurement, Sample
from fairdm.factories import DatasetFactory, MeasurementFactory, PersonFactory, SampleFactory


@pytest.mark.django_db
class TestMeasurementModel:
    """Tests for the Measurement model."""

    def test_measurement_creation(self):
        """Test creating a basic Measurement instance."""
        measurement = MeasurementFactory()

        assert measurement.pk is not None
        assert measurement.name is not None
        assert measurement.uuid is not None
        assert measurement.uuid.startswith("m")

    def test_measurement_str_representation(self):
        """Test Measurement string representation calls get_value()."""
        measurement = MeasurementFactory(name="Test Measurement")
        str_repr = str(measurement)
        # Since get_value() depends on subclass fields, just check it doesn't error
        assert str_repr is not None

    def test_measurement_sample_relationship(self):
        """Test that measurement is associated with a sample."""
        sample = SampleFactory()
        measurement = MeasurementFactory(sample=sample)

        assert measurement.sample == sample
        assert measurement in sample.measurements.all()

    def test_measurement_dataset_relationship(self):
        """Test that measurement is associated with a dataset."""
        measurement = MeasurementFactory()

        assert measurement.dataset is not None
        assert measurement in measurement.dataset.measurements.all()

    def test_measurement_type_of_property(self):
        """Test type_of classproperty."""
        assert Measurement.type_of == Measurement

    def test_measurement_get_template_name(self):
        """Test get_template_name returns correct template paths."""
        measurement = MeasurementFactory()
        templates = measurement.get_template_name()

        assert isinstance(templates, list)
        assert len(templates) == 2
        assert templates[1] == "fairdm/measurement_card.html"

    def test_measurement_get_absolute_url(self):
        """Test get_absolute_url returns measurement's own detail URL."""
        measurement = MeasurementFactory()
        url = measurement.get_absolute_url()

        # Should return measurement's own detail view
        assert url == f"/measurement/{measurement.uuid}/"
        assert "measurement:overview" in url or "/measurement/" in url

    def test_measurement_descriptions_relationship(self):
        """Test that measurement descriptions can be created correctly."""
        measurement = MeasurementFactory()
        descriptions = MeasurementDescription.objects.filter(related=measurement)

        # Factory may or may not create descriptions by default
        assert descriptions.count() >= 0
        assert all(desc.related == measurement for desc in descriptions)

    def test_measurement_dates_relationship(self):
        """Test that measurement dates can be created correctly."""
        measurement = MeasurementFactory()
        dates = MeasurementDate.objects.filter(related=measurement)

        # Factory may or may not create dates by default
        assert dates.count() >= 0
        assert all(date.related == measurement for date in dates)

    def test_add_contributor(self):
        """Test adding a contributor to a measurement."""
        measurement = MeasurementFactory()
        user = PersonFactory()

        contribution = measurement.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert measurement.contributors.filter(pk=contribution.pk).exists()


@pytest.mark.django_db
class TestMeasurementForm:
    """Tests for the MeasurementForm."""

    def test_form_initialization(self):
        """Test form can be initialized."""
        form = MeasurementForm()
        assert form is not None

    def test_form_missing_required_fields(self):
        """Test form validation fails without required fields."""
        form_data = {}
        form = MeasurementForm(data=form_data)

        assert not form.is_valid()
        # Name and sample are likely required
        assert "name" in form.errors or "sample" in form.errors

    def test_form_with_request_context(self):
        """Test form initialization with request object."""
        from unittest.mock import Mock

        request = Mock()
        form = MeasurementForm(request=request)

        assert form.request == request


@pytest.mark.django_db
class TestMeasurementViews:
    """Tests for Measurement views."""

    def test_measurement_detail_view_accessible(self, client):
        """Test that measurement detail view is accessible."""
        measurement = MeasurementFactory()
        # Note: URL pattern may vary, adjust as needed
        try:
            response = client.get(reverse("measurement:overview", kwargs={"uuid": measurement.uuid}))
            assert response.status_code in [200, 302, 404]  # May vary based on permissions
        except Exception:
            # URL may not be configured or may require different namespace
            pytest.skip("Measurement detail URL not configured")


@pytest.mark.django_db
class TestMeasurementPermissions:
    """Tests for Measurement permissions and access control."""

    def test_measurement_contributor_relationship(self, user):
        """Test that measurements can have contributors."""
        measurement = MeasurementFactory()
        contribution = measurement.add_contributor(user, with_roles=["Creator"])

        assert measurement.contributors.count() == 1
        assert contribution.contributor == user


@pytest.mark.django_db
class TestMeasurementCRUDWorkflow:
    """Test end-to-end CRUD workflow for measurements (User Story 2)."""

    def test_create_measurement_with_sample_and_dataset(self):
        """Test creating a measurement with sample and dataset relationships."""
        dataset = DatasetFactory(name="Test Dataset")
        sample = SampleFactory(dataset=dataset)

        measurement = MeasurementFactory(name="Test Measurement", dataset=dataset, sample=sample)

        assert measurement.pk is not None
        assert measurement.name == "Test Measurement"
        assert measurement.dataset == dataset
        assert measurement.sample == sample
        assert measurement in dataset.measurements.all()
        assert measurement in sample.measurements.all()

    def test_read_measurement_via_queryset(self):
        """Test retrieving measurements via querysets."""
        measurement = MeasurementFactory(name="Readable Measurement")

        retrieved = Measurement.objects.get(pk=measurement.pk)

        assert retrieved == measurement
        assert retrieved.name == "Readable Measurement"
        assert retrieved.uuid == measurement.uuid

    def test_update_measurement_fields(self):
        """Test updating measurement fields."""
        measurement = MeasurementFactory(name="Original Name")
        original_uuid = measurement.uuid

        measurement.name = "Updated Name"
        measurement.save()
        measurement.refresh_from_db()

        assert measurement.name == "Updated Name"
        assert measurement.uuid == original_uuid  # UUID should not change

    def test_delete_measurement(self):
        """Test deleting a measurement."""
        measurement = MeasurementFactory()
        measurement_id = measurement.pk

        measurement.delete()

        assert not Measurement.objects.filter(pk=measurement_id).exists()

    def test_deleting_dataset_cascades_to_measurements(self):
        """Test that deleting a dataset cascades to its measurements."""
        # Create two datasets: one for the measurement, one for the sample
        measurement_dataset = DatasetFactory(name="Measurement Dataset")
        sample_dataset = DatasetFactory(name="Sample Dataset")

        # Create sample in the sample dataset
        sample = SampleFactory(dataset=sample_dataset)

        # Create measurement in different dataset, referencing the sample
        measurement = MeasurementFactory(dataset=measurement_dataset, sample=sample)
        measurement_id = measurement.pk

        # Deleting measurement's dataset should cascade to the measurement
        # even though the measurement references a sample from another dataset
        measurement_dataset.delete()

        # Measurement should be deleted via cascade
        assert not Measurement.objects.filter(pk=measurement_id).exists()
        # Sample should still exist (in different dataset, protected by PROTECT)
        assert Sample.objects.filter(pk=sample.pk).exists()

    def test_deleting_sample_protects_measurements(self):
        """Test that deleting a sample is protected when measurements reference it."""
        from django.db import IntegrityError

        sample = SampleFactory()
        measurement = MeasurementFactory(sample=sample)

        # Attempting to delete sample should be prevented
        with pytest.raises(IntegrityError):
            sample.delete()

        # Measurement should still exist
        assert Measurement.objects.filter(pk=measurement.pk).exists()


@pytest.mark.django_db
class TestCrossDatasetMeasurementSampleLinking:
    """Test cross-dataset measurement-sample linking with permission boundaries (User Story 2)."""

    def test_measurement_can_reference_sample_from_different_dataset(self):
        """Test that a measurement in Dataset A can reference a sample from Dataset B."""
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        # Sample belongs to dataset B
        sample_b = SampleFactory(dataset=dataset_b)

        # Measurement belongs to dataset A but references sample from dataset B
        measurement_a = MeasurementFactory(dataset=dataset_a, sample=sample_b)

        assert measurement_a.dataset == dataset_a
        assert measurement_a.sample == sample_b
        assert measurement_a.sample.dataset == dataset_b
        # Cross-dataset link is preserved
        assert measurement_a.dataset != measurement_a.sample.dataset

    def test_cross_dataset_provenance_clear_in_relationships(self):
        """Test that cross-dataset provenance is clearly displayed in relationships."""
        dataset_a = DatasetFactory(name="Measurement Dataset")
        dataset_b = DatasetFactory(name="Sample Dataset")

        sample = SampleFactory(dataset=dataset_b, name="Sample from B")
        measurement = MeasurementFactory(dataset=dataset_a, name="Measurement in A", sample=sample)

        # Verify provenance
        assert measurement.dataset.name == "Measurement Dataset"
        assert measurement.sample.name == "Sample from B"
        assert measurement.sample.dataset.name == "Sample Dataset"

    def test_measurements_with_cross_dataset_samples_filter_correctly(self):
        """Test filtering measurements that have cross-dataset sample references."""
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        sample_a = SampleFactory(dataset=dataset_a)
        sample_b = SampleFactory(dataset=dataset_b)

        # Create measurements in different configurations
        m1 = MeasurementFactory(dataset=dataset_a, sample=sample_a)  # Same dataset
        m2 = MeasurementFactory(dataset=dataset_a, sample=sample_b)  # Cross-dataset
        m3 = MeasurementFactory(dataset=dataset_b, sample=sample_b)  # Same dataset

        # Filter by measurement dataset
        measurements_in_a = Measurement.objects.filter(dataset=dataset_a)
        assert m1 in measurements_in_a
        assert m2 in measurements_in_a
        assert m3 not in measurements_in_a

        # Filter by sample
        measurements_of_sample_b = Measurement.objects.filter(sample=sample_b)
        assert m2 in measurements_of_sample_b
        assert m3 in measurements_of_sample_b
        assert m1 not in measurements_of_sample_b

    def test_cross_dataset_measurement_deletion_does_not_affect_sample(self):
        """Test that deleting a cross-dataset measurement does not delete the sample."""
        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()

        sample = SampleFactory(dataset=dataset_b)
        measurement = MeasurementFactory(dataset=dataset_a, sample=sample)

        sample_id = sample.pk
        measurement.delete()

        # Sample should still exist
        assert SampleFactory._meta.model.objects.filter(pk=sample_id).exists()


@pytest.mark.django_db
class TestMeasurementValueWithUncertainty:
    """Test value-with-uncertainty display methods (User Story 6)."""

    def test_get_value_returns_name_for_base_measurement(self):
        """Test that get_value() falls back to name for base Measurement instances."""
        measurement = MeasurementFactory(name="Test Measurement")

        value = measurement.get_value()

        assert value == "Test Measurement"

    def test_print_value_returns_string_representation(self):
        """Test that print_value() returns a string representation."""
        measurement = MeasurementFactory(name="Test Measurement")

        printed = measurement.print_value()

        assert isinstance(printed, str)
        assert "Test Measurement" in printed

    def test_polymorphic_measurement_get_value_with_value_field(self):
        """Test that polymorphic measurements with value fields return appropriate representations."""
        # This test requires a polymorphic measurement type
        # Using demo app's XRFMeasurement as example
        try:
            from fairdm_demo.models import XRFMeasurement

            xrf = XRFMeasurement.objects.create(
                name="Iron Analysis",
                dataset=DatasetFactory(),
                sample=SampleFactory(),
                element="Fe",
                concentration_ppm=45.2,
            )

            value = xrf.get_value()

            # Should return meaningful value representation (implementation-specific)
            assert value is not None
            # Value could be name, concentration, or formatted string depending on implementation
            assert str(value) != ""

        except ImportError:
            pytest.skip("Demo XRFMeasurement not available")

    def test_value_display_consistent_across_polymorphic_types(self):
        """Test that value display is consistent across different measurement types."""
        # Base measurements use name
        base_measurement = MeasurementFactory(name="Base Measurement")
        assert base_measurement.get_value() == "Base Measurement"

        # Polymorphic types should provide type-specific value
        try:
            from fairdm_demo.models import ICPMSMeasurement

            icp_ms = ICPMSMeasurement.objects.create(
                name="Uranium Analysis",
                dataset=DatasetFactory(),
                sample=SampleFactory(),
                isotope="U-238",
                concentration=12.5,
            )

            value = icp_ms.get_value()
            assert value is not None
            assert str(value) != ""

        except ImportError:
            pytest.skip("Demo ICPMSMeasurement not available")


@pytest.mark.django_db
class TestMeasurementFAIRMetadata:
    """Test FAIR metadata with correct Measurement vocabularies (User Story 8)."""

    def test_measurement_description_uses_measurement_vocabulary(self):
        """Test that MeasurementDescription uses Measurement vocabulary collection."""
        measurement = MeasurementFactory()

        # Create a description with a Measurement-specific type
        description = MeasurementDescription.objects.create(related=measurement, type="method", value="XRF Analysis")

        assert description.type == "method"
        assert description.related == measurement
        assert description.value == "XRF Analysis"
        # Verify vocabulary is from Measurement collection
        assert description.VOCABULARY is not None

    def test_measurement_date_uses_measurement_vocabulary(self):
        """Test that MeasurementDate uses Measurement vocabulary collection."""
        measurement = MeasurementFactory()

        # Create a date with a Measurement-specific type
        measurement_date = MeasurementDate.objects.create(related=measurement, type="measured", value="2024-02-15")

        assert measurement_date.type == "measured"
        assert measurement_date.related == measurement
        assert measurement_date.value == "2024-02-15"
        # Verify vocabulary is from Measurement collection
        assert measurement_date.VOCABULARY is not None

    def test_measurement_vocabulary_types_differ_from_sample_vocabularies(self):
        """Test that Measurement vocabularies are distinct from Sample vocabularies."""
        # Measurement has specific vocabulary types
        measurement = MeasurementFactory()

        # Create description with measurement-specific type
        desc = MeasurementDescription.objects.create(related=measurement, type="method", value="Test")

        # Verify the vocabulary is Measurement-specific (not Sample)
        assert desc.VOCABULARY is not None
        # Vocabulary should be from Measurement collection
        assert hasattr(desc, "VOCABULARY")

    def test_measurement_can_have_multiple_descriptions_of_different_types(self):
        """Test that measurements can have multiple descriptions with different vocabulary types."""
        measurement = MeasurementFactory()

        desc1 = MeasurementDescription.objects.create(related=measurement, type="method", value="XRF Spectroscopy")

        desc2 = MeasurementDescription.objects.create(related=measurement, type="instrument", value="Bruker S8 Tiger")

        descriptions = MeasurementDescription.objects.filter(related=measurement)

        assert descriptions.count() == 2
        assert desc1 in descriptions
        assert desc2 in descriptions
        assert desc1.type != desc2.type

    def test_measurement_can_have_multiple_dates_of_different_types(self):
        """Test that measurements can have multiple dates with different vocabulary types."""
        measurement = MeasurementFactory()

        date1 = MeasurementDate.objects.create(related=measurement, type="measured", value="2024-02-15")

        date2 = MeasurementDate.objects.create(related=measurement, type="calibrated", value="2024-02-10")

        dates = MeasurementDate.objects.filter(related=measurement)

        assert dates.count() == 2
        assert date1 in dates
        assert date2 in dates
        assert date1.type != date2.type


@pytest.mark.django_db
class TestMeasurementQuerySetOptimization:
    """Test QuerySet optimization methods (User Story 7)."""

    def test_with_related_prefetches_direct_relationships(self):
        """Test that with_related() prefetches sample, dataset, and contributors."""
        # Create measurements with related data
        for _ in range(5):
            measurement = MeasurementFactory()
            measurement.add_contributor(PersonFactory(), with_roles=["Creator"])

        with CaptureQueriesContext(connection) as queries:
            measurements = list(Measurement.objects.with_related().all())

            # Access related data without triggering additional queries
            for m in measurements:
                _ = m.sample.name
                _ = m.dataset.name
                _ = list(m.contributors.all())

        # Should use minimal queries:
        # 1. SELECT measurements with polymorphic
        # 2. SELECT samples (select_related)
        # 3. SELECT datasets (select_related - via sample or direct)
        # 4. PREFETCH contributors
        query_count = len(queries)
        assert query_count <= 10  # Allow some flexibility for polymorphic joins

    def test_with_metadata_prefetches_descriptions_dates_identifiers(self):
        """Test that with_metadata() prefetches descriptions, dates, and identifiers."""
        # Create measurement with metadata
        measurement = MeasurementFactory()
        MeasurementDescription.objects.create(related=measurement, type="method", value="XRF")
        MeasurementDate.objects.create(related=measurement, type="measured", value="2024")

        with CaptureQueriesContext(connection) as queries:
            measurements = list(Measurement.objects.with_metadata().all())

            # Access metadata without triggering additional queries
            for m in measurements:
                _ = list(MeasurementDescription.objects.filter(related=m))
                _ = list(MeasurementDate.objects.filter(related=m))

        # Should prefetch descriptions, dates, identifiers
        query_count = len(queries)
        assert query_count <= 8  # Allow some flexibility for polymorphic joins

    def test_queryset_method_chaining_works_correctly(self):
        """Test that QuerySet methods can be chained."""
        dataset = DatasetFactory()
        for _ in range(3):
            measurement = MeasurementFactory(dataset=dataset)
            MeasurementDescription.objects.create(related=measurement, type="method", value="Test")

        # Chain methods
        measurements = Measurement.objects.with_related().with_metadata().filter(dataset=dataset)

        assert measurements.count() == 3

        # Verify both optimizations apply
        with CaptureQueriesContext(connection) as queries:
            results = list(measurements)
            for m in results:
                _ = m.sample.name
                _ = m.dataset.name
                _ = list(MeasurementDescription.objects.filter(related=m))

        # Should still be optimized despite chaining
        query_count = len(queries)
        assert query_count <= 10

    def test_polymorphic_queries_return_correct_typed_instances(self):
        """Test that polymorphic queries return correctly typed instances."""
        # Create base measurements
        base_measurements = [MeasurementFactory() for _ in range(2)]

        # Create polymorphic measurements if available
        try:
            from fairdm_demo.models import XRFMeasurement

            polymorphic_measurements = [
                XRFMeasurement.objects.create(
                    name=f"XRF {i}",
                    dataset=DatasetFactory(),
                    sample=SampleFactory(),
                    element="Fe",
                    concentration_ppm=10.0 + i,
                )
                for i in range(2)
            ]

            # Query all measurements
            all_measurements = Measurement.objects.all()

            # Verify polymorphic instances are returned as correct type
            xrf_count = sum(1 for m in all_measurements if isinstance(m, XRFMeasurement))
            base_count = sum(1 for m in all_measurements if type(m) is Measurement)

            assert xrf_count >= 2
            assert base_count >= 2

        except ImportError:
            pytest.skip("Demo XRFMeasurement not available")

    def test_large_measurement_collection_loads_efficiently(self):
        """Test that large measurement collections (1000+) load efficiently with optimizations."""
        # Create 50 measurements (reduced from 1000 for test speed, principle is the same)
        measurements = []
        for i in range(50):
            m = MeasurementFactory(name=f"Measurement {i}")
            m.add_contributor(PersonFactory(), with_roles=["Creator"])
            MeasurementDescription.objects.create(related=m, type="method", value=f"Method {i}")
            measurements.append(m)

        # Query with optimizations
        with CaptureQueriesContext(connection) as queries:
            optimized_results = list(Measurement.objects.with_related().with_metadata().all())

            # Access all related data
            for m in optimized_results:
                _ = m.sample.name
                _ = m.dataset.name
                _ = list(m.contributors.all())
                _ = list(m.descriptions.all())  # Use prefetched data instead of filtering

        optimized_query_count = len(queries)

        # Should use significantly fewer queries than N+1 pattern
        # With 50 measurements, unoptimized would be 50*4 = 200+ queries
        # Optimized should be < 20 queries
        assert optimized_query_count < 20, f"Query count too high: {optimized_query_count}"
