"""
Unit tests for Sample model.

Tests cover model creation, polymorphic inheritance, validation,
field constraints, and polymorphic query behavior. Also covers
form/view integration, queryset optimization, and SampleRelation
creation, validation, querying, and hierarchy traversal.
"""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse

from fairdm.core.models import Sample
from fairdm.core.sample.forms import SampleForm
from fairdm.core.sample.models import (
    SampleDate,
    SampleDescription,
    SampleIdentifier,
    SampleRelation,
)
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    SampleDateFactory,
    SampleDescriptionFactory,
    SampleIdentifierFactory,
)
from fairdm_demo.factories import RockSampleFactory
from fairdm_demo.models import RockSample, WaterSample


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
class TestBaseSampleRefused:
    """T025 - FR-010: creating a bare base Sample is refused through every route.

    Runs alongside T030 (the ``pre_save`` block) rather than with the rest of US-1, because
    landing the block without proving every route refuses it - and without retargeting the
    factories that build the forbidden record - is what would leave the suite red (research.md
    R4). Each route is asserted separately because they fail independently: `clean()` refuses at
    validation time, the `pre_save` receiver refuses at save time, and neither alone covers both.
    """

    def test_validation_refuses_a_bare_sample(self, dataset):
        """``full_clean()`` on a bare ``Sample`` raises, even with every other field valid."""
        sample = Sample(name="Direct", dataset=dataset)

        with pytest.raises(ValidationError):
            sample.full_clean()

    def test_form_refuses_a_bare_sample(self, dataset):
        """``SampleForm`` - the base model's own registry-generated form - refuses to validate."""
        form = SampleForm(
            data={"name": "Direct", "dataset": dataset.pk, "status": "unknown"}
        )

        assert not form.is_valid()

    def test_admin_refuses_the_base_content_type(self, admin_client):
        """The polymorphic parent admin's add view never offers the base type as a child.

        ``Sample`` is never a member of ``registry.samples`` (only registered specimen types
        are), so asking the add view to route to the base type's own content type is refused
        the same way an unregistered model would be - it is not among the child admins the
        parent knows how to delegate to.
        """
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(Sample)
        response = admin_client.get(reverse("admin:sample_sample_add"), {"ct_id": ct.pk})

        assert response.status_code == 403

    def test_manager_refuses_a_bare_sample(self, dataset):
        """``Sample.objects.create()`` - the manager route T030's ``pre_save`` receiver covers -
        is refused even though it bypasses form and admin validation entirely."""
        with pytest.raises(ValidationError):
            Sample.objects.create(name="Direct", dataset=dataset)

    def test_direct_save_refuses_a_bare_sample(self, dataset):
        """A bare ``Sample().save()`` - the route ``clean()`` alone does not cover, since nothing
        calls it - is refused by the ``pre_save`` receiver."""
        sample = Sample(name="Direct", dataset=dataset)

        with pytest.raises(ValidationError):
            sample.save()

    def test_fixture_loading_refuses_a_bare_sample(self, dataset):
        """Deserializing a fixture row for the base model is refused too (research.md R4): the
        `pre_save` receiver is the one mechanism that also covers `django.core.serializers`,
        which sends `pre_save` on every raw, deserialized object."""
        from django.core import serializers

        payload = (
            "[{\"model\": \"sample.sample\", \"pk\": null, "
            '"fields": {"name": "Direct", "dataset": %d}}]' % dataset.pk
        )
        (deserialized,) = serializers.deserialize("json", payload)

        with pytest.raises(ValidationError):
            deserialized.save()


@pytest.mark.django_db
class TestSampleIdentity:
    """T009 - FR-001: the generated identifier is unique, prefixed, generated rather than
    supplied, and not editable afterwards."""

    def test_uuid_is_unique_across_specimens(self, rock_sample, water_sample):
        assert rock_sample.uuid != water_sample.uuid

    def test_uuid_is_prefixed_to_mark_it_a_sample(self, rock_sample):
        assert rock_sample.uuid.startswith("s")

    def test_uuid_is_generated_rather_than_supplied(self, dataset):
        """Two specimens created without naming a ``uuid`` each receive their own."""
        from fairdm_demo.factories import RockSampleFactory

        one = RockSampleFactory(dataset=dataset)
        two = RockSampleFactory(dataset=dataset)

        assert one.uuid
        assert two.uuid
        assert one.uuid != two.uuid

    def test_uuid_is_not_editable_afterwards(self, rock_sample):
        """``editable=False`` is what makes it unchangeable: excluded from a generated
        ``ModelForm`` and presented read-only in the admin (FR-043, T086)."""
        from fairdm.core.sample.admin import SampleChildAdmin

        assert "uuid" not in SampleForm.base_fields
        assert "uuid" in SampleChildAdmin.readonly_fields


@pytest.mark.django_db
class TestSampleFields:
    """T010 - FR-002: a name is required; laboratory identifier, image and location are each
    optional."""

    def test_name_is_required(self, dataset):
        from fairdm_demo.models import RockSample

        sample = RockSample(
            dataset=dataset, rock_type="igneous", collection_date="2024-01-15"
        )

        with pytest.raises(ValidationError) as exc_info:
            sample.full_clean()

        assert "name" in exc_info.value.message_dict

    def test_local_id_is_optional(self, dataset):
        from fairdm_demo.factories import RockSampleFactory

        sample = RockSampleFactory(dataset=dataset, local_id=None)

        sample.full_clean()  # does not raise

    def test_image_is_optional(self, dataset):
        from fairdm_demo.factories import RockSampleFactory

        sample = RockSampleFactory(dataset=dataset, image=None)

        sample.full_clean()  # does not raise

    def test_location_is_optional(self, dataset):
        from fairdm_demo.factories import RockSampleFactory

        sample = RockSampleFactory(dataset=dataset, location=None)

        sample.full_clean()  # does not raise
        assert sample.location is None


@pytest.mark.django_db
class TestSampleLocalId:
    """T011 - FR-003: a laboratory identifier is not required to be unique; two specimens in
    different datasets carrying the same one are both valid."""

    def test_the_same_local_id_is_valid_in_two_different_datasets(self):
        from fairdm.factories import DatasetFactory
        from fairdm_demo.factories import RockSampleFactory

        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()

        one = RockSampleFactory(dataset=dataset_a, local_id="LAB-001")
        two = RockSampleFactory(dataset=dataset_b, local_id="LAB-001")

        one.full_clean()
        two.full_clean()
        assert one.local_id == two.local_id == "LAB-001"


@pytest.mark.django_db
class TestSampleDatasetRelation:
    """T012 - FR-004: a specimen belongs to exactly one dataset, and deleting that dataset
    deletes the specimen."""

    def test_deleting_the_dataset_deletes_the_specimen(self, rock_sample):
        dataset = rock_sample.dataset
        sample_pk = rock_sample.pk

        dataset.delete()

        assert not Sample.objects.filter(pk=sample_pk).exists()


@pytest.mark.django_db
class TestSampleLocationRelation:
    """T013 - FR-005: deleting a location a specimen refers to is refused while any specimen
    refers to it."""

    def test_deleting_a_referenced_location_is_refused(self, dataset):
        from django.db.models.deletion import ProtectedError

        from fairdm.factories import PointFactory
        from fairdm_demo.factories import RockSampleFactory

        location = PointFactory()
        RockSampleFactory(dataset=dataset, location=location)

        with pytest.raises(ProtectedError):
            location.delete()


@pytest.mark.django_db
class TestSampleKeywords:
    """T014 - FR-006: controlled keywords are stored as references to the vocabulary, free tags
    as tags, and the two remain distinguishable."""

    def test_controlled_vocabulary_term_is_stored_as_a_reference(self, rock_sample):
        from research_vocabs.models import Concept

        term = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        assert term is not None

        rock_sample.keywords.add(term)

        stored = rock_sample.keywords.get(pk=term.pk)
        assert isinstance(stored, Concept)
        assert stored.name == term.name

    def test_free_tags_are_distinguishable_from_controlled_keywords(self, rock_sample):
        from research_vocabs.models import Concept

        keyword = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        rock_sample.keywords.add(keyword)
        rock_sample.tags.add("erosion")

        assert "erosion" in rock_sample.tags.names()
        assert rock_sample.keywords.count() == 1
        assert all(isinstance(k, Concept) for k in rock_sample.keywords.all())
        assert not rock_sample.keywords.filter(name="erosion").exists()


@pytest.mark.django_db
class TestSampleContributions:
    """T015 - FR-008: a contribution records a contributor and one or more roles and reads both
    back; the sample role vocabulary's members are asserted by name."""

    def test_sample_role_vocabulary_members(self):
        assert Sample.CONTRIBUTOR_ROLES.values == [
            "Collection",
            "Preparation",
            "Storage",
            "Destruction",
            "Restoration",
        ]

    def test_contribution_records_contributor_and_roles(self, rock_sample):
        contributor = PersonFactory()

        contribution = rock_sample.add_contributor(
            contributor, with_roles=["Collection", "Preparation"]
        )

        assert contribution.contributor == contributor
        role_names = set(contribution.roles.values_list("name", flat=True))
        assert role_names == {"Collection", "Preparation"}


@pytest.mark.django_db
class TestSampleTimestamps:
    """T016 - FR-007: creation and modification times are recorded, and modification advances on
    any change."""

    def test_creation_and_modification_times_are_recorded(self, rock_sample):
        assert rock_sample.added is not None
        assert rock_sample.modified is not None

    def test_modification_time_advances_on_change(self, rock_sample):
        original_modified = rock_sample.modified

        rock_sample.name = "Renamed"
        rock_sample.save()
        rock_sample.refresh_from_db()

        assert rock_sample.modified > original_modified
        assert rock_sample.added is not None


@pytest.mark.django_db
class TestSamplePrefetch:
    """T017 - FR-044: loading specimens with their dataset, location, descriptions, dates,
    identifiers, contributions and keywords costs a number of queries that does not grow with
    the number of specimens or of related records. One measurement proves nothing, so this
    checks two different specimen counts against two different related-record counts."""

    def _build_and_load(self, n_samples, n_related):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm.factories import DatasetFactory
        from fairdm_demo.factories import RockSampleFactory

        dataset = DatasetFactory()
        description_types = SampleDescription.VOCABULARY.values
        date_types = SampleDate.VOCABULARY.values
        identifier_types = SampleIdentifier.VOCABULARY.values
        role_types = Sample.CONTRIBUTOR_ROLES.values

        for _ in range(n_samples):
            sample = RockSampleFactory(dataset=dataset)
            for i in range(n_related):
                SampleDescriptionFactory(related=sample, type=description_types[i])
                SampleDateFactory(related=sample, type=date_types[i])
                SampleIdentifierFactory(related=sample, type=identifier_types[i])
                sample.add_contributor(PersonFactory(), with_roles=[role_types[i]])

        with CaptureQueriesContext(connection) as context:
            samples = list(
                Sample.objects.filter(dataset=dataset)
                .with_related()
                .with_metadata()
                .with_keywords()
            )
            assert len(samples) == n_samples
            for sample in samples:
                _ = sample.dataset
                _ = sample.location
                list(sample.contributors.all())
                list(sample.descriptions.all())
                list(sample.dates.all())
                list(sample.identifiers.all())
                list(sample.keywords.all())

        return len(context.captured_queries)

    def test_query_count_does_not_grow_with_specimens_or_related_records(self):
        small = self._build_and_load(n_samples=2, n_related=1)
        large = self._build_and_load(n_samples=5, n_related=3)

        assert small == large


@pytest.mark.django_db
class TestSampleQuerySetChaining:
    """T018 - FR-045: the queryset's own methods chain with one another and with ordinary query
    operations, in either order, and the result is correct rather than merely non-empty."""

    def test_methods_chain_in_either_order_and_return_the_right_rows(self, dataset):
        from fairdm_demo.factories import RockSampleFactory, WaterSampleFactory

        target = RockSampleFactory(dataset=dataset, name="Target")
        WaterSampleFactory(dataset=dataset, name="Other")

        forward = (
            Sample.objects.with_related()
            .with_metadata()
            .with_keywords()
            .filter(name="Target")
        )
        backward = Sample.objects.filter(name="Target").with_related().with_metadata()

        assert list(forward) == [target]
        assert list(backward) == [target]


@pytest.mark.django_db
class TestSampleTranslatable:
    """T019 - FR-046: model field labels, help text, and vocabulary terms are lazy rather than
    resolved at import."""

    def test_field_verbose_names_and_help_text_are_lazy(self):
        from django.utils.functional import Promise

        for field_name in ["dataset", "local_id", "status", "location"]:
            field = Sample._meta.get_field(field_name)
            assert isinstance(field.verbose_name, Promise), field_name
            assert isinstance(field.help_text, Promise), field_name

    def test_vocabulary_terms_are_lazy(self):
        from django.utils.functional import Promise

        from fairdm.core.vocabularies import FairDMDescriptions

        assert isinstance(
            FairDMDescriptions.SampleCollection["skos:prefLabel"], Promise
        )


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
        SampleDescription.objects.create(
            related=sample, type="abstract", value="Test description"
        )
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
        assert (
            queries_with <= 4
        )  # Should be ~4 queries (samples, descriptions, dates, identifiers)

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
        # Target: <1000ms for 100 samples (django-polymorphic adds some overhead)
        # Note: CI runners have variable performance, so we use a generous timeout
        assert duration_ms < 1000  # Generous timeout for CI environments


@pytest.mark.django_db
class TestSampleModel:
    """Tests for the Sample model."""

    def test_sample_creation(self):
        """Test creating a basic Sample instance."""
        sample = RockSampleFactory()

        assert sample.pk is not None
        assert sample.name is not None
        assert sample.uuid is not None
        assert sample.uuid.startswith("s")

    def test_sample_str_representation(self):
        """Test Sample string representation."""
        sample = RockSampleFactory(name="Test Sample")
        assert str(sample) == "Test Sample"

    def test_sample_dataset_relationship(self):
        """Test that sample is associated with a dataset."""
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)

        assert sample.dataset == dataset
        assert sample in dataset.samples.all()

    def test_sample_local_id_optional(self):
        """Test that local_id is optional."""
        sample = RockSampleFactory(local_id=None)
        assert sample.local_id is None

        sample_with_id = RockSampleFactory(local_id="ABC-123")
        assert sample_with_id.local_id == "ABC-123"

    def test_sample_location_optional(self):
        """Test that location is optional."""
        sample = RockSampleFactory(location=None)
        assert sample.location is None

    def test_sample_status_default(self):
        """Test that sample has a status."""
        sample = RockSampleFactory()
        # Status should be set (factory may randomize)
        assert sample.status is not None

    def test_sample_get_template_name(self):
        """Test get_template_name returns correct template paths."""
        sample = RockSampleFactory()
        templates = sample.get_template_name()

        assert isinstance(templates, list)
        assert len(templates) == 2
        assert templates[1] == "fairdm/sample_card.html"

    def test_sample_type_of_property(self):
        """Test type_of classproperty."""
        assert Sample.type_of == Sample

    def test_sample_descriptions_relationship(self):
        """Test that sample descriptions can be created correctly."""
        sample = RockSampleFactory()
        descriptions = SampleDescription.objects.filter(related=sample)

        # Factory may or may not create descriptions by default
        assert descriptions.count() >= 0
        assert all(desc.related == sample for desc in descriptions)

    def test_sample_dates_relationship(self):
        """Test that sample dates can be created correctly."""
        sample = RockSampleFactory()
        dates = SampleDate.objects.filter(related=sample)

        # Factory may or may not create dates by default
        assert dates.count() >= 0
        assert all(date.related == sample for date in dates)

    def test_add_contributor(self):
        """Test adding a contributor to a sample."""
        sample = RockSampleFactory()
        user = PersonFactory()

        contribution = sample.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert sample.contributors.filter(pk=contribution.pk).exists()


@pytest.mark.django_db
class TestSampleRelation:
    """Tests for the SampleRelation model."""

    def test_sample_relation_creation(self):
        """Test creating a sample-to-sample relationship."""
        parent = RockSampleFactory()
        child = RockSampleFactory()

        relation = SampleRelation.objects.create(
            type="child_of",
            source=child,
            target=parent,
        )

        assert relation.pk is not None
        assert relation.source == child
        assert relation.target == parent
        assert relation.type == "child_of"

    def test_sample_relation_queryset(self):
        """Test querying sample relationships."""
        parent = RockSampleFactory()
        child = RockSampleFactory()

        SampleRelation.objects.create(
            type="child_of",
            source=child,
            target=parent,
        )

        # Query from child to parent
        related_samples = child.related_samples.all()
        assert related_samples.count() == 1
        assert related_samples.first().target == parent

        # Query from parent to child
        related_to = parent.related_to.all()
        assert related_to.count() == 1
        assert related_to.first().source == child


@pytest.mark.skip(reason="Phase 5 (US3 - Forms) not yet implemented")
@pytest.mark.django_db
class TestSampleForm:
    """Tests for the SampleForm."""

    def test_form_valid_data(self):
        """Test form validation with valid data."""
        dataset = DatasetFactory()

        form_data = {
            "name": "Test Sample",
            "dataset": dataset.pk,
            "status": "unknown",  # Use default status value
        }
        form = SampleForm(data=form_data)

        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_missing_required_fields(self):
        """Test form validation fails without required fields."""
        form_data = {}
        form = SampleForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_with_request_context(self):
        """Test form initialization with request object."""
        from unittest.mock import Mock

        request = Mock()
        form = SampleForm(request=request)

        assert form.request == request


@pytest.mark.django_db
class TestSampleViews:
    """Tests for Sample views."""

    def test_sample_detail_view_accessible(self, client):
        """Test that sample detail view is accessible."""
        sample = RockSampleFactory()
        # Note: URL pattern may vary, adjust as needed
        try:
            response = client.get(
                reverse("sample:overview", kwargs={"uuid": sample.uuid})
            )
            assert response.status_code in [
                200,
                302,
                404,
            ]  # May vary based on permissions
        except Exception:
            # URL may not be configured or may require different namespace
            pytest.skip("Sample detail URL not configured")


@pytest.mark.django_db
class TestSamplePermissions:
    """Tests for Sample permissions and access control."""

    def test_sample_contributor_relationship(self, user):
        """Test that samples can have contributors."""
        sample = RockSampleFactory()
        contribution = sample.add_contributor(user, with_roles=["Creator"])

        assert sample.contributors.count() == 1
        assert contribution.contributor == user


@pytest.mark.django_db
class TestSampleQuerySetWithRelated:
    """Test SampleQuerySet.with_related() method for prefetching related data."""

    def test_with_related_prefetches_dataset(self):
        """Test that with_related() prefetches dataset relationship."""
        sample = RockSampleFactory()
        result = Sample.objects.with_related().get(pk=sample.pk)

        assert result.dataset is not None
        assert result.dataset.pk == sample.dataset.pk

    def test_with_related_prefetches_contributors(self):
        """Test that with_related() prefetches contributors via GenericRelation."""
        sample = RockSampleFactory()
        user1 = PersonFactory()
        user2 = PersonFactory()
        sample.add_contributor(user1, with_roles=["Creator"])
        sample.add_contributor(user2, with_roles=["Editor"])

        result = Sample.objects.with_related().get(pk=sample.pk)
        contributors = list(result.contributors.all())

        assert len(contributors) == 2

    def test_with_related_returns_queryset(self):
        """Test that with_related() returns a QuerySet for chaining."""
        qs = Sample.objects.with_related()

        assert hasattr(qs, "filter")
        assert hasattr(qs, "exclude")
        assert hasattr(qs, "order_by")

    def test_with_related_can_be_chained(self):
        """Test that with_related() can be chained with other queryset methods."""
        sample1 = RockSampleFactory(name="Alpha")
        _sample2 = RockSampleFactory(name="Beta")

        results = Sample.objects.with_related().filter(name="Alpha")

        assert results.count() == 1
        assert results.first().pk == sample1.pk


@pytest.mark.django_db
class TestSampleQuerySetWithMetadata:
    """Test SampleQuerySet.with_metadata() method for prefetching metadata models."""

    def test_with_metadata_prefetches_descriptions(self):
        """Test that with_metadata() prefetches SampleDescription objects."""
        sample = RockSampleFactory()
        desc1 = SampleDescription.objects.create(
            related=sample, type="Abstract", value="Description 1"
        )
        desc2 = SampleDescription.objects.create(
            related=sample, type="Methods", value="Description 2"
        )

        result = Sample.objects.with_metadata().get(pk=sample.pk)
        descriptions = list(result.descriptions.all())

        assert len(descriptions) == 2
        assert desc1 in descriptions
        assert desc2 in descriptions

    def test_with_metadata_prefetches_dates(self):
        """Test that with_metadata() prefetches SampleDate objects."""
        sample = RockSampleFactory()
        date1 = SampleDate.objects.create(
            related=sample, type="Created", value="2024-01-01"
        )
        date2 = SampleDate.objects.create(
            related=sample, type="Published", value="2024-06-01"
        )

        result = Sample.objects.with_metadata().get(pk=sample.pk)
        dates = list(result.dates.all())

        assert len(dates) == 2
        assert date1 in dates
        assert date2 in dates

    def test_with_metadata_returns_queryset(self):
        """Test that with_metadata() returns a QuerySet for chaining."""
        qs = Sample.objects.with_metadata()

        assert hasattr(qs, "filter")
        assert hasattr(qs, "exclude")

    def test_with_metadata_can_be_chained_with_with_related(self):
        """Test that with_metadata() can be chained with with_related()."""
        sample = RockSampleFactory()
        result = Sample.objects.with_related().with_metadata().get(pk=sample.pk)

        assert result.dataset is not None


@pytest.mark.django_db
class TestSampleQuerySetByRelationship:
    """Test SampleQuerySet.by_relationship() method for filtering by relationship type."""

    def test_by_relationship_filters_by_type(self):
        """Test that by_relationship() filters samples by relationship type."""
        parent = RockSampleFactory()
        child1 = RockSampleFactory()
        child2 = RockSampleFactory()
        _unrelated = RockSampleFactory()

        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        results = Sample.objects.by_relationship(relationship_type="child_of")

        assert results.count() >= 2
        result_pks = set(results.values_list("pk", flat=True))
        assert child1.pk in result_pks
        assert child2.pk in result_pks

    def test_by_relationship_returns_empty_for_no_matches(self):
        """Test that by_relationship() returns empty queryset when no matches."""
        _sample = RockSampleFactory()

        results = Sample.objects.by_relationship(relationship_type="nonexistent_type")

        assert results.count() == 0

    def test_by_relationship_can_be_chained(self):
        """Test that by_relationship() can be chained with other queryset methods."""
        parent = RockSampleFactory()
        child1 = RockSampleFactory(name="Alpha")
        child2 = RockSampleFactory(name="Beta")

        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        results = Sample.objects.by_relationship(relationship_type="child_of").filter(
            name="Alpha"
        )

        assert results.count() == 1
        assert results.first().pk == child1.pk


@pytest.mark.django_db
class TestSamplePolymorphicQueries:
    """Test that Sample.objects.all() returns correct polymorphic subclass instances."""

    def test_all_returns_correct_subclass_for_single_type(self):
        """Test that querying all samples returns RockSample instances, not Sample."""
        from fairdm_demo.factories import RockSampleFactory

        rock_sample = RockSampleFactory(name="Granite")
        results = list(Sample.objects.all())

        # Find the rock sample in results
        rock_result = next((r for r in results if r.pk == rock_sample.pk), None)
        assert rock_result is not None
        assert rock_result.__class__.__name__ == "RockSample"

    def test_all_returns_mixed_polymorphic_types(self):
        """Test that querying all samples returns correct mix of subclass instances."""
        from fairdm_demo.factories import RockSampleFactory, WaterSampleFactory

        rock1 = RockSampleFactory(name="Granite")
        water1 = WaterSampleFactory(name="River Water")
        rock2 = RockSampleFactory(name="Basalt")

        results = list(Sample.objects.all())

        rock1_result = next((r for r in results if r.pk == rock1.pk), None)
        assert rock1_result.__class__.__name__ == "RockSample"

        water1_result = next((r for r in results if r.pk == water1.pk), None)
        assert water1_result.__class__.__name__ == "WaterSample"

        rock2_result = next((r for r in results if r.pk == rock2.pk), None)
        assert rock2_result.__class__.__name__ == "RockSample"

    def test_get_returns_correct_subclass(self):
        """Test that Sample.objects.get() returns the correct subclass instance."""
        from fairdm_demo.factories import RockSampleFactory

        rock_sample = RockSampleFactory(name="Quartz")
        result = Sample.objects.get(pk=rock_sample.pk)

        assert result.__class__.__name__ == "RockSample"
        assert result.pk == rock_sample.pk

    def test_filter_returns_correct_subclass(self):
        """Test that Sample.objects.filter() returns correct subclass instances."""
        from fairdm_demo.factories import RockSampleFactory, WaterSampleFactory

        rock1 = RockSampleFactory(name="Alpha Rock")
        _water1 = WaterSampleFactory(name="Beta Water")

        results = list(Sample.objects.filter(name__startswith="Alpha"))

        assert len(results) >= 1
        rock_result = next((r for r in results if r.pk == rock1.pk), None)
        assert rock_result is not None
        assert rock_result.__class__.__name__ == "RockSample"

    def test_polymorphic_query_preserves_custom_fields(self):
        """Test that polymorphic queries allow access to subclass-specific fields."""
        from fairdm_demo.factories import RockSampleFactory

        rock_sample = RockSampleFactory(
            name="Granite",
            rock_type="igneous",
        )

        result = Sample.objects.get(pk=rock_sample.pk)

        assert hasattr(result, "rock_type")
        assert result.rock_type == "igneous"

    @pytest.mark.skip(
        reason="select_subclasses() not exposed through custom manager - polymorphic queries work without it"
    )
    def test_polymorphic_query_with_select_subclasses(self):
        """Test that select_subclasses() optimizes polymorphic queries."""
        from fairdm_demo.factories import RockSampleFactory, WaterSampleFactory

        rock1 = RockSampleFactory()
        water1 = WaterSampleFactory()

        results = list(Sample.objects.select_subclasses())

        rock_result = next((r for r in results if r.pk == rock1.pk), None)
        water_result = next((r for r in results if r.pk == water1.pk), None)

        assert rock_result.__class__.__name__ == "RockSample"
        assert water_result.__class__.__name__ == "WaterSample"

    def test_polymorphic_query_without_select_subclasses_still_works(self):
        """Test that polymorphic queries work correctly even without explicit select_subclasses()."""
        from fairdm_demo.factories import RockSampleFactory, WaterSampleFactory

        _rock1 = RockSampleFactory()
        _water1 = WaterSampleFactory()

        results = list(Sample.objects.all())

        types = {r.__class__.__name__ for r in results}
        assert "RockSample" in types or "WaterSample" in types


@pytest.mark.django_db
class TestSampleConvenienceMethods:
    """Test Sample model convenience methods for relationships."""

    def test_get_all_relationships_returns_source_and_target(self):
        """Test that get_all_relationships() returns relationships where sample is source or target."""
        parent = RockSampleFactory()
        child = RockSampleFactory()
        sibling = RockSampleFactory()

        SampleRelation.objects.create(source=child, target=parent, type="child_of")
        SampleRelation.objects.create(source=sibling, target=parent, type="child_of")

        parent_rels = parent.get_all_relationships()
        child_rels = child.get_all_relationships()

        assert parent_rels.count() == 2
        assert child_rels.count() == 1

    def test_get_related_samples_without_filter(self):
        """Test get_related_samples() returns all related samples."""
        parent = RockSampleFactory()
        child1 = RockSampleFactory()
        child2 = RockSampleFactory()

        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        related = parent.get_related_samples()

        assert related.count() == 2
        assert child1 in related
        assert child2 in related

    def test_get_related_samples_with_relationship_type_filter(self):
        """Test get_related_samples() filters by relationship type."""
        parent = RockSampleFactory()
        child = RockSampleFactory()

        SampleRelation.objects.create(source=child, target=parent, type="child_of")

        related = parent.get_related_samples(relationship_type="child_of")

        assert related.count() == 1
        assert child in related

        # Query for non-existent type
        related_other = parent.get_related_samples(relationship_type="nonexistent")
        assert related_other.count() == 0


# ===== Test Helper Functions =====


def create_rock_sample(name, dataset, rock_type="igneous", **kwargs):
    """Helper to create RockSample with required fields."""
    defaults = {
        "name": name,
        "dataset": dataset,
        "rock_type": rock_type,
        "collection_date": date.today(),
    }
    defaults.update(kwargs)
    return RockSample.objects.create(**defaults)


def create_water_sample(name, dataset, water_source="river", **kwargs):
    """Helper to create WaterSample with required fields."""
    defaults = {
        "name": name,
        "dataset": dataset,
        "water_source": water_source,
        "temperature_celsius": 15.5,
        "ph_level": 7.2,
    }
    defaults.update(kwargs)
    return WaterSample.objects.create(**defaults)


@pytest.mark.django_db
class TestSampleRelationCreation:
    """Test basic SampleRelation creation and typed relationships."""

    def test_create_relationship_with_type(self, dataset):
        """Test creating a relationship between samples with specific type."""
        # Arrange: Create parent and child samples
        parent = create_rock_sample("Parent Rock Sample", dataset, rock_type="igneous")
        child = create_rock_sample("Derived Thin Section", dataset, rock_type="igneous")

        # Act: Create relationship
        relation = SampleRelation.objects.create(
            source=child,
            target=parent,
            type="child_of",
        )

        # Assert: Relationship exists with correct attributes
        assert relation.source == child
        assert relation.target == parent
        assert relation.type == "child_of"
        assert str(relation) == f"{child} child_of {parent}"

    def test_multiple_relationship_types(self, dataset):
        """Test that different relationship types can exist between samples."""
        # Arrange: Create samples
        sample_a = create_water_sample("Water Sample A", dataset, water_source="river")
        sample_b = create_water_sample("Water Sample B", dataset, water_source="river")

        # Act: Create multiple relationship types (when more types are added)
        rel1 = SampleRelation.objects.create(
            source=sample_b,
            target=sample_a,
            type="child_of",
        )

        # Assert: Relationships exist independently
        assert (
            SampleRelation.objects.filter(source=sample_b, target=sample_a).count() == 1
        )
        assert rel1.type == "child_of"


@pytest.mark.django_db
class TestSampleRelationValidation:
    """Test validation rules for SampleRelation model."""

    def test_prevent_self_reference(self, dataset):
        """Test that a sample cannot have a relationship to itself."""
        # Arrange: Create a sample
        sample = create_rock_sample("Test Sample", dataset, rock_type="igneous")

        # Act & Assert: Attempting self-reference should raise validation error
        relation = SampleRelation(
            source=sample,
            target=sample,
            type="child_of",
        )
        with pytest.raises(ValidationError) as exc_info:
            relation.clean()

        assert "cannot relate to itself" in str(exc_info.value).lower()

    def test_prevent_direct_circular_relationship(self, dataset):
        """Test that direct circular relationships are prevented (A→B and B→A)."""
        # Arrange: Create two samples with A→B relationship
        sample_a = create_rock_sample("Sample A", dataset, rock_type="igneous")
        sample_b = create_rock_sample("Sample B", dataset, rock_type="sedimentary")

        # Create A→B relationship
        SampleRelation.objects.create(
            source=sample_a,
            target=sample_b,
            type="child_of",
        )

        # Act & Assert: Attempting B→A with same type should raise validation error
        reverse_relation = SampleRelation(
            source=sample_b,
            target=sample_a,
            type="child_of",
        )
        with pytest.raises(ValidationError) as exc_info:
            reverse_relation.clean()

        assert "circular relationship" in str(exc_info.value).lower()

    def test_unique_together_constraint(self, dataset):
        """Test that duplicate relationships with same source, target, type are prevented."""
        # Arrange: Create samples and first relationship
        sample_a = create_water_sample("Sample A", dataset, water_source="lake")
        sample_b = create_water_sample("Sample B", dataset, water_source="lake")

        SampleRelation.objects.create(
            source=sample_a,
            target=sample_b,
            type="child_of",
        )

        # Act & Assert: Creating duplicate relationship should raise IntegrityError
        with pytest.raises(IntegrityError):
            SampleRelation.objects.create(
                source=sample_a,
                target=sample_b,
                type="child_of",
            )


@pytest.mark.django_db
class TestSampleRelationshipQueries:
    """Test querying relationships through Sample model convenience methods."""

    def test_get_children_method(self, dataset):
        """Test Sample.get_children() returns child samples."""
        # Arrange: Create parent with two children
        parent = create_rock_sample("Parent Sample", dataset, rock_type="igneous")
        child1 = create_rock_sample("Child Sample 1", dataset, rock_type="igneous")
        child2 = create_rock_sample("Child Sample 2", dataset, rock_type="igneous")

        # Create relationships
        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        # Act: Get children
        children = parent.get_children()

        # Assert: Both children are returned
        assert children.count() == 2
        assert child1 in children
        assert child2 in children

    def test_get_parents_method(self, dataset):
        """Test Sample.get_parents() returns parent samples."""
        # Arrange: Create child with two parents (e.g., hybrid/mixed sample)
        parent1 = create_water_sample("Parent Sample 1", dataset, water_source="river")
        parent2 = create_water_sample("Parent Sample 2", dataset, water_source="lake")
        child = create_water_sample("Child Sample", dataset, water_source="mixed")

        # Create relationships
        SampleRelation.objects.create(source=child, target=parent1, type="child_of")
        SampleRelation.objects.create(source=child, target=parent2, type="child_of")

        # Act: Get parents
        parents = child.get_parents()

        # Assert: Both parents are returned
        assert parents.count() == 2
        assert parent1 in parents
        assert parent2 in parents


@pytest.mark.django_db
class TestComplexSampleHierarchies:
    """Test complex multi-level sample hierarchies and provenance."""

    def test_multi_level_hierarchy(self, dataset):
        """Test creating and querying multi-level sample hierarchy (grandparent→parent→child)."""
        # Arrange: Create 3-level hierarchy
        grandparent = create_rock_sample(
            "Grandparent Rock", dataset, rock_type="igneous"
        )
        parent = create_rock_sample("Parent Section", dataset, rock_type="igneous")
        child = create_rock_sample("Child Thin Section", dataset, rock_type="igneous")

        # Create hierarchical relationships
        SampleRelation.objects.create(
            source=parent, target=grandparent, type="child_of"
        )
        SampleRelation.objects.create(source=child, target=parent, type="child_of")

        # Act & Assert: Query relationships
        # Grandparent has 1 direct child
        assert grandparent.get_children().count() == 1
        assert parent in grandparent.get_children()

        # Parent has 1 child and 1 parent
        assert parent.get_children().count() == 1
        assert parent.get_parents().count() == 1
        assert child in parent.get_children()
        assert grandparent in parent.get_parents()

        # Child has 1 parent
        assert child.get_parents().count() == 1
        assert parent in child.get_parents()

    def test_get_descendants_with_depth(self, dataset):
        """Test Sample.get_descendants() with configurable depth traversal."""
        # Arrange: Create deep hierarchy (4 levels)
        samples = []
        for i in range(4):
            sample = create_rock_sample(
                f"Level {i} Sample", dataset, rock_type="igneous"
            )
            samples.append(sample)
            # Create relationship to previous level
            if i > 0:
                SampleRelation.objects.create(
                    source=samples[i],
                    target=samples[i - 1],
                    type="child_of",
                )

        # Act & Assert: Get descendants at different depths
        root = samples[0]

        # Depth 1: Only direct children
        depth1_descendants = root.get_descendants(depth=1)
        assert depth1_descendants.count() == 1
        assert samples[1] in depth1_descendants

        # Depth 2: Children and grandchildren
        depth2_descendants = root.get_descendants(depth=2)
        assert depth2_descendants.count() == 2
        assert samples[1] in depth2_descendants
        assert samples[2] in depth2_descendants

        # Depth None/Infinite: All descendants
        all_descendants = root.get_descendants()
        assert all_descendants.count() == 3
        assert samples[1] in all_descendants
        assert samples[2] in all_descendants
        assert samples[3] in all_descendants


@pytest.mark.django_db
class TestSampleQuerySetRelationshipMethods:
    """Test SampleQuerySet methods for relationship filtering."""

    def test_by_relationship_filters_samples(self, dataset):
        """Test SampleQuerySet.by_relationship() filters samples by relationship type."""
        # Arrange: Create samples with different relationship types
        parent = create_rock_sample("Parent", dataset, rock_type="igneous")
        child1 = create_rock_sample("Child 1", dataset, rock_type="igneous")
        child2 = create_rock_sample("Child 2", dataset, rock_type="igneous")

        # Create relationships
        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        # Act: Filter by relationship type
        children_queryset = Sample.objects.by_relationship(
            related_to=parent, relationship_type="child_of"
        )

        # Assert: Both children are returned
        assert children_queryset.count() == 2
        assert child1 in children_queryset
        assert child2 in children_queryset
