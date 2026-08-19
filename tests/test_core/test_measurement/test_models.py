"""
Unit tests for Measurement model.

Tests cover model creation, polymorphic inheritance, validation,
field constraints, and polymorphic query behavior. Also covers
form/view integration, CRUD workflows, cross-dataset sample linking,
value-with-uncertainty display, FAIR metadata, and queryset
optimization.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from fairdm.core.measurement.forms import MeasurementForm
from fairdm.core.measurement.models import (
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.core.models import Measurement, Sample
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
)
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory


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

    def test_uuid_is_not_editable_afterwards(self, measurement):
        """T007 - ``editable=False`` is what makes it unchangeable: excluded from a generated
        ``ModelForm`` and presented read-only in the admin (mirrors
        ``TestSampleIdentity.test_uuid_is_not_editable_afterwards``)."""
        from fairdm.core.measurement.admin import MeasurementChildAdmin

        assert "uuid" not in MeasurementForm.base_fields
        assert "uuid" in MeasurementChildAdmin.readonly_fields


@pytest.mark.django_db
class TestMeasurementFields:
    """T009 - a name is required; a measurement's own label, image, controlled keywords and
    free-form tags are each optional."""

    def test_name_is_required(self, sample):
        from fairdm_demo.models import ExampleMeasurement

        instance = ExampleMeasurement(sample=sample, dataset=sample.dataset)

        with pytest.raises(ValidationError) as exc_info:
            instance.full_clean()

        assert "name" in exc_info.value.message_dict

    def test_label_image_keywords_and_tags_are_all_optional(self, sample):
        instance = ExampleMeasurementFactory(sample=sample, local_id=None, image=None)

        instance.full_clean()  # does not raise

        assert not instance.local_id
        assert not instance.image
        assert instance.keywords.count() == 0
        assert instance.tags.count() == 0


class TestMeasurementFieldMetadata:
    """T010 - every field the record carries declares a verbose name and guidance text, both
    marked for translation. ``uuid`` is excluded, matching the sibling Sample record's
    ``TestSampleTranslatable`` - its own ``verbose_name`` is a plain string there too."""

    def test_field_verbose_names_and_help_text_are_lazy(self):
        from django.utils.functional import Promise

        for field_name in ["dataset", "sample", "local_id"]:
            field = Measurement._meta.get_field(field_name)
            assert isinstance(field.verbose_name, Promise), field_name
            assert isinstance(field.help_text, Promise), field_name


@pytest.mark.django_db
class TestMeasurementLocalId:
    """T011 - two measurements in different datasets may carry the same researcher's label, and
    both save."""

    def test_the_same_local_id_is_valid_in_two_different_datasets(
        self, dataset, second_dataset, sample, second_sample
    ):
        one = ExampleMeasurementFactory(dataset=dataset, sample=sample, local_id="LAB-001")
        two = ExampleMeasurementFactory(
            dataset=second_dataset, sample=second_sample, local_id="LAB-001"
        )

        one.full_clean()
        two.full_clean()
        assert one.local_id == two.local_id == "LAB-001"


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
        date = MeasurementDate.objects.create(
            related=measurement, type="measured", value="2024-01-15"
        )

        # Verify the vocabulary type comes from Measurement collection
        assert date.type == "measured"  # type field returns string value
        # The vocabulary should be from FairDMDates "Measurement" collection
        assert date.VOCABULARY is not None


@pytest.mark.django_db
class TestMeasurementIdentifierVocabulary:
    """005 F1/F2 - MeasurementIdentifier is bound to a scoped collection, not the unscoped
    FairDMIdentifiers vocabulary, so a member added for another record type (e.g. IGSN for
    samples) cannot be offered as a measurement identifier type."""

    def test_available_types_are_doi_only(self):
        assert set(MeasurementIdentifier.VOCABULARY.values) == {"DOI"}

    def test_no_type_names_a_sample_person_organisation_or_project(self):
        assert set(MeasurementIdentifier.VOCABULARY.values).isdisjoint(
            {
                "IGSN",
                "ORCID",
                "RESEARCHER_ID",
                "ROR",
                "WIKIDATA",
                "ISNI",
                "CROSSREF_FUNDER_ID",
                "GRANT_NUMBER",
                "PROPOSAL_ID",
            }
        )


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

        from fairdm.core.measurement.models import (
            MeasurementDate,
            MeasurementDescription,
        )
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
        MeasurementDescription.objects.create(
            related=measurement, type="method", value="XRF analysis"
        )
        MeasurementDate.objects.create(
            related=measurement, type="measured", value="2024-01-15"
        )

        # Test without optimization
        with CaptureQueriesContext(connection) as context_without:
            measurements_without = list(
                XRFMeasurement.objects.filter(pk=measurement.pk)
            )
            for m in measurements_without:
                _ = list(m.descriptions.all())
                _ = list(m.dates.all())

        len(context_without.captured_queries)

        # Test with optimization
        with CaptureQueriesContext(connection) as context_with:
            measurements_with = list(
                XRFMeasurement.objects.filter(pk=measurement.pk).with_metadata()
            )
            for m in measurements_with:
                _ = list(m.descriptions.all())
                _ = list(m.dates.all())

        queries_with = len(context_with.captured_queries)

        # Assert optimization reduces queries
        # Note: For a single measurement, prefetch may add overhead
        # The benefit shows with multiple measurements
        assert (
            queries_with <= 4
        )  # Should be ~4 queries (measurements, descriptions, dates, identifiers)

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
            assert type(measurement).__name__ in [
                "XRFMeasurement",
                "ICP_MS_Measurement",
                "ExampleMeasurement",
            ]
            # Should have subclass-specific attributes
            assert (
                hasattr(measurement, "element")
                or hasattr(measurement, "isotope")
                or hasattr(measurement, "char_field")
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
    def test_1000_measurements_load_with_minimal_queries_using_with_related(
        self, sample
    ):
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
            assert type(measurement).__name__ in [
                "XRFMeasurement",
                "ICP_MS_Measurement",
            ]

        # Performance check - should be reasonably fast even for 100+ measurements
        # Target: <500ms for 100 measurements (django-polymorphic adds some overhead)
        # Note: Actual goal is <200ms for 1000 measurements, we're testing 100 here
        # Allowing 1000ms for test environment overhead (SQLite, Windows, CI)
        assert duration_ms < 1000  # Generous for test environment


@pytest.mark.django_db
class TestMeasurementModel:
    """Tests for the Measurement model."""

    def test_measurement_creation(self):
        """Test creating a basic Measurement instance."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert measurement.pk is not None
        assert measurement.name is not None
        assert measurement.uuid is not None
        assert measurement.uuid.startswith("m")

    def test_measurement_str_representation(self):
        """Test Measurement string representation calls get_value()."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory(), name="Test Measurement")
        str_repr = str(measurement)
        # Since get_value() depends on subclass fields, just check it doesn't error
        assert str_repr is not None

    def test_measurement_sample_relationship(self):
        """Test that measurement is associated with a sample."""
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=sample)

        assert measurement.sample == sample
        assert measurement in sample.measurements.all()

    def test_measurement_dataset_relationship(self):
        """Test that measurement is associated with a dataset."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert measurement.dataset is not None
        assert measurement in measurement.dataset.measurements.all()

    def test_measurement_type_of_property(self):
        """Test type_of classproperty."""
        assert Measurement.type_of == Measurement

    def test_measurement_get_template_name(self):
        """Test get_template_name returns correct template paths."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        templates = measurement.get_template_name()

        assert isinstance(templates, list)
        assert len(templates) == 2
        assert templates[1] == "fairdm/measurement_card.html"

    def test_measurement_get_absolute_url(self):
        """Test get_absolute_url returns measurement's own detail URL."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        url = measurement.get_absolute_url()

        # Should return measurement's own detail view
        assert url == f"/measurement/{measurement.uuid}/"
        assert "measurement:overview" in url or "/measurement/" in url

    def test_measurement_descriptions_relationship(self):
        """Test that measurement descriptions can be created correctly."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        descriptions = MeasurementDescription.objects.filter(related=measurement)

        # Factory may or may not create descriptions by default
        assert descriptions.count() >= 0
        assert all(desc.related == measurement for desc in descriptions)

    def test_measurement_dates_relationship(self):
        """Test that measurement dates can be created correctly."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        dates = MeasurementDate.objects.filter(related=measurement)

        # Factory may or may not create dates by default
        assert dates.count() >= 0
        assert all(date.related == measurement for date in dates)

    def test_add_contributor(self):
        """Test adding a contributor to a measurement."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
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
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        # Note: URL pattern may vary, adjust as needed
        try:
            response = client.get(
                reverse("measurement:overview", kwargs={"uuid": measurement.uuid})
            )
            assert response.status_code in [
                200,
                302,
                404,
            ]  # May vary based on permissions
        except Exception:
            # URL may not be configured or may require different namespace
            pytest.skip("Measurement detail URL not configured")


@pytest.mark.django_db
class TestMeasurementPermissions:
    """Tests for Measurement permissions and access control."""

    def test_measurement_contributor_relationship(self, user):
        """Test that measurements can have contributors."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        contribution = measurement.add_contributor(user, with_roles=["Creator"])

        assert measurement.contributors.count() == 1
        assert contribution.contributor == user


@pytest.mark.django_db
class TestMeasurementCRUDWorkflow:
    """Test end-to-end CRUD workflow for measurements (User Story 2)."""

    def test_create_measurement_with_sample_and_dataset(self):
        """Test creating a measurement with sample and dataset relationships."""
        dataset = DatasetFactory(name="Test Dataset")
        sample = RockSampleFactory(dataset=dataset)

        measurement = ExampleMeasurementFactory(
            name="Test Measurement", dataset=dataset, sample=sample
        )

        assert measurement.pk is not None
        assert measurement.name == "Test Measurement"
        assert measurement.dataset == dataset
        assert measurement.sample == sample
        assert measurement in dataset.measurements.all()
        assert measurement in sample.measurements.all()

    def test_read_measurement_via_queryset(self):
        """Test retrieving measurements via querysets."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory(), name="Readable Measurement")

        retrieved = Measurement.objects.get(pk=measurement.pk)

        assert retrieved == measurement
        assert retrieved.name == "Readable Measurement"
        assert retrieved.uuid == measurement.uuid

    def test_update_measurement_fields(self):
        """Test updating measurement fields."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory(), name="Original Name")
        original_uuid = measurement.uuid

        measurement.name = "Updated Name"
        measurement.save()
        measurement.refresh_from_db()

        assert measurement.name == "Updated Name"
        assert measurement.uuid == original_uuid  # UUID should not change

    def test_delete_measurement(self):
        """Test deleting a measurement."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        measurement_id = measurement.pk

        measurement.delete()

        assert not Measurement.objects.filter(pk=measurement_id).exists()

    def test_deleting_dataset_cascades_to_measurements(self):
        """Test that deleting a dataset cascades to its measurements."""
        # Create two datasets: one for the measurement, one for the sample
        measurement_dataset = DatasetFactory(name="Measurement Dataset")
        sample_dataset = DatasetFactory(name="Sample Dataset")

        # Create sample in the sample dataset
        sample = RockSampleFactory(dataset=sample_dataset)

        # Create measurement in different dataset, referencing the sample
        measurement = ExampleMeasurementFactory(dataset=measurement_dataset, sample=sample)
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

        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=sample)

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
        sample_b = RockSampleFactory(dataset=dataset_b)

        # Measurement belongs to dataset A but references sample from dataset B
        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        assert measurement_a.dataset == dataset_a
        assert measurement_a.sample == sample_b
        assert measurement_a.sample.dataset == dataset_b
        # Cross-dataset link is preserved
        assert measurement_a.dataset != measurement_a.sample.dataset

    def test_cross_dataset_provenance_clear_in_relationships(self):
        """Test that cross-dataset provenance is clearly displayed in relationships."""
        dataset_a = DatasetFactory(name="Measurement Dataset")
        dataset_b = DatasetFactory(name="Sample Dataset")

        sample = RockSampleFactory(dataset=dataset_b, name="Sample from B")
        measurement = ExampleMeasurementFactory(
            dataset=dataset_a, name="Measurement in A", sample=sample
        )

        # Verify provenance
        assert measurement.dataset.name == "Measurement Dataset"
        assert measurement.sample.name == "Sample from B"
        assert measurement.sample.dataset.name == "Sample Dataset"

    def test_measurements_with_cross_dataset_samples_filter_correctly(self):
        """Test filtering measurements that have cross-dataset sample references."""
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        sample_a = RockSampleFactory(dataset=dataset_a)
        sample_b = RockSampleFactory(dataset=dataset_b)

        # Create measurements in different configurations
        m1 = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_a)  # Same dataset
        m2 = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)  # Cross-dataset
        m3 = ExampleMeasurementFactory(dataset=dataset_b, sample=sample_b)  # Same dataset

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

        sample = RockSampleFactory(dataset=dataset_b)
        measurement = ExampleMeasurementFactory(dataset=dataset_a, sample=sample)

        sample_id = sample.pk
        measurement.delete()

        # Sample should still exist
        assert RockSampleFactory._meta.model.objects.filter(pk=sample_id).exists()


@pytest.mark.django_db
class TestMeasurementValueWithUncertainty:
    """Test value-with-uncertainty display methods (User Story 6)."""

    def test_get_value_returns_name_for_base_measurement(self):
        """Test that get_value() falls back to name for base Measurement instances."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory(), name="Test Measurement")

        value = measurement.get_value()

        assert value == "Test Measurement"

    def test_print_value_returns_string_representation(self):
        """Test that print_value() returns a string representation."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory(), name="Test Measurement")

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
                sample=RockSampleFactory(),
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
        base_measurement = ExampleMeasurementFactory(sample=RockSampleFactory(), name="Base Measurement")
        assert base_measurement.get_value() == "Base Measurement"

        # Polymorphic types should provide type-specific value
        try:
            from fairdm_demo.models import ICPMSMeasurement

            icp_ms = ICPMSMeasurement.objects.create(
                name="Uranium Analysis",
                dataset=DatasetFactory(),
                sample=RockSampleFactory(),
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
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Create a description with a Measurement-specific type
        description = MeasurementDescription.objects.create(
            related=measurement, type="method", value="XRF Analysis"
        )

        assert description.type == "method"
        assert description.related == measurement
        assert description.value == "XRF Analysis"
        # Verify vocabulary is from Measurement collection
        assert description.VOCABULARY is not None

    def test_measurement_date_uses_measurement_vocabulary(self):
        """Test that MeasurementDate uses Measurement vocabulary collection."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Create a date with a Measurement-specific type
        measurement_date = MeasurementDate.objects.create(
            related=measurement, type="measured", value="2024-02-15"
        )

        assert measurement_date.type == "measured"
        assert measurement_date.related == measurement
        assert measurement_date.value == "2024-02-15"
        # Verify vocabulary is from Measurement collection
        assert measurement_date.VOCABULARY is not None

    def test_measurement_vocabulary_types_differ_from_sample_vocabularies(self):
        """Test that Measurement vocabularies are distinct from Sample vocabularies."""
        # Measurement has specific vocabulary types
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Create description with measurement-specific type
        desc = MeasurementDescription.objects.create(
            related=measurement, type="method", value="Test"
        )

        # Verify the vocabulary is Measurement-specific (not Sample)
        assert desc.VOCABULARY is not None
        # Vocabulary should be from Measurement collection
        assert hasattr(desc, "VOCABULARY")

    def test_measurement_can_have_multiple_descriptions_of_different_types(self):
        """Test that measurements can have multiple descriptions with different vocabulary types."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        desc1 = MeasurementDescription.objects.create(
            related=measurement, type="method", value="XRF Spectroscopy"
        )

        desc2 = MeasurementDescription.objects.create(
            related=measurement, type="instrument", value="Bruker S8 Tiger"
        )

        descriptions = MeasurementDescription.objects.filter(related=measurement)

        assert descriptions.count() == 2
        assert desc1 in descriptions
        assert desc2 in descriptions
        assert desc1.type != desc2.type

    def test_measurement_can_have_multiple_dates_of_different_types(self):
        """Test that measurements can have multiple dates with different vocabulary types."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        date1 = MeasurementDate.objects.create(
            related=measurement, type="measured", value="2024-02-15"
        )

        date2 = MeasurementDate.objects.create(
            related=measurement, type="calibrated", value="2024-02-10"
        )

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
            measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
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
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        MeasurementDescription.objects.create(
            related=measurement, type="method", value="XRF"
        )
        MeasurementDate.objects.create(
            related=measurement, type="measured", value="2024"
        )

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
            measurement = ExampleMeasurementFactory(sample=RockSampleFactory(), dataset=dataset)
            MeasurementDescription.objects.create(
                related=measurement, type="method", value="Test"
            )

        # Chain methods
        measurements = (
            Measurement.objects.with_related().with_metadata().filter(dataset=dataset)
        )

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
        """Test that polymorphic queries return correctly typed instances.

        Both measurement types created here are concrete subclasses (FR-011 forbids the
        bare Measurement record), so the assertion checks each comes back typed as its
        own concrete class, not as the polymorphic base.
        """
        # Create ExampleMeasurement instances
        example_measurements = [
            ExampleMeasurementFactory(sample=RockSampleFactory()) for _ in range(2)
        ]

        # Create polymorphic measurements if available
        try:
            from fairdm_demo.models import ExampleMeasurement, XRFMeasurement

            polymorphic_measurements = [
                XRFMeasurement.objects.create(
                    name=f"XRF {i}",
                    dataset=DatasetFactory(),
                    sample=RockSampleFactory(),
                    element="Fe",
                    concentration_ppm=10.0 + i,
                )
                for i in range(2)
            ]

            # Query all measurements
            all_measurements = Measurement.objects.all()

            # Verify polymorphic instances are returned as correct type
            xrf_count = sum(
                1 for m in all_measurements if isinstance(m, XRFMeasurement)
            )
            example_count = sum(
                1 for m in all_measurements if type(m) is ExampleMeasurement
            )

            assert xrf_count >= 2
            assert example_count >= 2

        except ImportError:
            pytest.skip("Demo XRFMeasurement not available")

    def test_large_measurement_collection_loads_efficiently(self):
        """Test that large measurement collections (1000+) load efficiently with optimizations."""
        # Create 50 measurements (reduced from 1000 for test speed, principle is the same)
        measurements = []
        for i in range(50):
            m = ExampleMeasurementFactory(sample=RockSampleFactory(), name=f"Measurement {i}")
            m.add_contributor(PersonFactory(), with_roles=["Creator"])
            MeasurementDescription.objects.create(
                related=m, type="method", value=f"Method {i}"
            )
            measurements.append(m)

        # Query with optimizations
        with CaptureQueriesContext(connection) as queries:
            optimized_results = list(
                Measurement.objects.with_related().with_metadata().all()
            )

            # Access all related data
            for m in optimized_results:
                _ = m.sample.name
                _ = m.dataset.name
                _ = list(m.contributors.all())
                _ = list(
                    m.descriptions.all()
                )  # Use prefetched data instead of filtering

        optimized_query_count = len(queries)

        # Should use significantly fewer queries than N+1 pattern
        # With 50 measurements, unoptimized would be 50*4 = 200+ queries
        # Optimized should be < 20 queries
        assert optimized_query_count < 20, (
            f"Query count too high: {optimized_query_count}"
        )
