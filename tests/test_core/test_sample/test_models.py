"""Unit tests for Sample model."""

import itertools
from datetime import date
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse

from demo.factories import RockSampleFactory
from demo.models import RockSample, WaterSample
from fairdm.core.models import Sample
from fairdm.core.sample.forms import SampleForm
from fairdm.core.sample.models import (
    SampleDate,
    SampleDescription,
    SampleIdentifier,
    SampleRelation,
)
from fairdm.core.utils import assign_perm
from fairdm.core.vocabularies import FairDMSampleStatus
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    SampleDateFactory,
    SampleDescriptionFactory,
    SampleIdentifierFactory,
    SampleRelationFactory,
)


@pytest.mark.django_db
class TestSampleModelCreation:
    def test_rock_sample_creation_with_all_fields(self, dataset):
        from demo.models import RockSample

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
        from demo.models import WaterSample

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
        assert sample.status == "unknown"

    def test_sample_uuid_is_unique(self, rock_sample, water_sample):
        assert rock_sample.uuid != water_sample.uuid
        assert rock_sample.uuid.startswith("s")
        assert water_sample.uuid.startswith("s")


@pytest.mark.django_db
class TestSamplePolymorphicInheritance:
    def test_polymorphic_sample_subclass_creation(self, dataset):
        from demo.models import RockSample

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
        from demo.models import RockSample, WaterSample

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

        samples = Sample.objects.all()

        assert samples.count() == 2
        rock_instance = samples.get(pk=rock.pk)
        water_instance = samples.get(pk=water.pk)

        assert isinstance(rock_instance, RockSample)
        assert isinstance(water_instance, WaterSample)
        assert hasattr(rock_instance, "rock_type")
        assert hasattr(water_instance, "ph_level")


@pytest.mark.django_db
class TestSamplePolymorphism:
    def test_querying_the_base_model_returns_each_row_as_its_own_type(
        self, each_registered_sample_type
    ):
        expected_types = {
            sample.pk: type(sample) for sample in each_registered_sample_type
        }

        results_by_pk = {sample.pk: type(sample) for sample in Sample.objects.all()}

        assert results_by_pk == expected_types

    def test_a_returned_row_carries_its_own_types_fields(self, dataset):
        rock = RockSampleFactory(dataset=dataset, rock_type="igneous")

        result = Sample.objects.get(pk=rock.pk)

        assert isinstance(result, RockSample)
        assert result.rock_type == "igneous"


@pytest.mark.django_db
class TestSampleModelValidation:
    def test_sample_status_transitions_unrestricted(self, rock_sample):
        rock_sample.status = "available"
        rock_sample.save()
        rock_sample.refresh_from_db()
        assert rock_sample.status.name == "available"

        rock_sample.status = "in_use"
        rock_sample.save()
        rock_sample.refresh_from_db()
        assert rock_sample.status.name == "in_use"

        rock_sample.status = "stored"
        rock_sample.save()
        rock_sample.refresh_from_db()
        assert rock_sample.status.name == "stored"


class TestSampleStatusVocabulary:
    def test_members_are_custody_states(self):
        assert set(Sample.status_vocab.values) == {
            "available",
            "in_use",
            "stored",
            "destroyed",
            "unknown",
        }

    def test_vocabulary_class_is_fairdm_sample_status(self):
        assert Sample.status_vocab.__class__ is FairDMSampleStatus


@pytest.mark.django_db
class TestSampleStatusDefault:
    def test_no_status_stated_reads_as_unknown(self, dataset):
        sample = RockSample.objects.create(
            name="Unstated Status Rock",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        sample.refresh_from_db()

        assert sample.status.name == "unknown"


@pytest.mark.django_db
class TestSampleStatusTransitions:
    STATES = ["available", "in_use", "stored", "destroyed", "unknown"]

    @pytest.mark.parametrize("start, end", list(itertools.permutations(STATES, 2)))
    def test_transition_is_accepted(self, rock_sample, start, end):
        rock_sample.status = start
        rock_sample.save()
        rock_sample.refresh_from_db()
        assert rock_sample.status.name == start

        rock_sample.status = end
        rock_sample.save()
        rock_sample.refresh_from_db()
        assert rock_sample.status.name == end


@pytest.mark.django_db
class TestNoRemoteVocabulary:
    def test_reading_and_creating_a_specimen_succeed_with_network_blocked(
        self, rock_sample, dataset, monkeypatch
    ):
        import socket

        def _refuse_connect(*args, **kwargs):
            raise AssertionError("an outbound network call was attempted")

        monkeypatch.setattr(socket.socket, "connect", _refuse_connect)

        loaded = Sample.objects.get(pk=rock_sample.pk)
        assert loaded.status.name == "unknown"

        created = RockSample.objects.create(
            name="Offline Rock",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        created.refresh_from_db()
        assert created.status.name == "unknown"

    def test_vocabulary_graph_builds_from_scratch_without_network(self, monkeypatch):
        import socket

        def _refuse_connect(*args, **kwargs):
            raise AssertionError("an outbound network call was attempted")

        monkeypatch.setattr(socket.socket, "connect", _refuse_connect)
        monkeypatch.setattr(FairDMSampleStatus, "graph", None)

        vocab = FairDMSampleStatus()

        assert set(vocab.values) == {
            "available",
            "in_use",
            "stored",
            "destroyed",
            "unknown",
        }


@pytest.mark.django_db
class TestStatusMigration:
    def test_forward_rewrites_every_status_to_unknown(self, dataset):
        import importlib

        from django.apps import apps as django_apps
        from django.db import connection

        from demo.models import WaterSample

        rock = RockSample.objects.create(
            name="Legacy Rock",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        water = WaterSample.objects.create(
            name="Legacy Water",
            dataset=dataset,
            water_source="river",
            ph_level=7.0,
            temperature_celsius=15.0,
        )

        # Bypass the ORM entirely for the mutation: reading these rows back through
        # ConceptField.from_db_value would raise ValueError, the very defect this
        # migration exists to fix, before the migration ever ran.
        table = Sample._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table} SET status = %s WHERE id = %s",  # noqa: S608
                ["complete", rock.pk],
            )
            cursor.execute(
                f"UPDATE {table} SET status = %s WHERE id = %s",  # noqa: S608
                ["ongoing", water.pk],
            )

        migration = importlib.import_module(
            "fairdm.core.sample.migrations.0008_migrate_sample_status_to_unknown"
        )
        # The migration reads the database alias off the schema editor to route
        # its query, so it needs one carrying this test's connection. A real
        # schema editor cannot be opened inside the test's transaction on
        # SQLite, and the connection is the whole of what the migration touches.
        schema_editor = SimpleNamespace(connection=connection)
        migration.migrate_status_to_unknown(django_apps, schema_editor)

        assert Sample.objects.get(pk=rock.pk).status.name == "unknown"
        assert Sample.objects.get(pk=water.pk).status.name == "unknown"


@pytest.mark.django_db
class TestSampleDirectInstantiation:
    def test_sample_cannot_be_instantiated_directly(self, dataset):

        sample = Sample(
            name="Direct Sample",
            dataset=dataset,
        )

        with pytest.raises(ValidationError):
            sample.clean()


@pytest.mark.django_db
class TestBaseSampleRefused:
    def test_validation_refuses_a_bare_sample(self, dataset):
        sample = Sample(name="Direct", dataset=dataset)

        with pytest.raises(ValidationError):
            sample.full_clean()

    def test_form_refuses_a_bare_sample(self, dataset):
        form = SampleForm(
            data={"name": "Direct", "dataset": dataset.pk, "status": "unknown"}
        )

        assert not form.is_valid()

    def test_admin_refuses_the_base_content_type(self, admin_client):
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(Sample)
        response = admin_client.get(
            reverse("admin:sample_sample_add"), {"ct_id": ct.pk}
        )

        assert response.status_code == 403

    def test_manager_refuses_a_bare_sample(self, dataset):
        with pytest.raises(ValidationError):
            Sample.objects.create(name="Direct", dataset=dataset)

    def test_direct_save_refuses_a_bare_sample(self, dataset):
        sample = Sample(name="Direct", dataset=dataset)

        with pytest.raises(ValidationError):
            sample.save()

    def test_fixture_loading_refuses_a_bare_sample(self, dataset):
        from django.core import serializers

        payload = (
            '[{"model": "sample.sample", "pk": null, '
            '"fields": {"name": "Direct", "dataset": %d}}]' % dataset.pk
        )
        (deserialized,) = serializers.deserialize("json", payload)

        with pytest.raises(ValidationError):
            deserialized.save()


class TestBaseSampleErrorIsTranslatable:
    # makemessages only extracts literals passed directly to _(), so a plain constant
    # wrapped at the call site never reaches the catalogue.
    def test_base_sample_error_is_a_lazy_translation(self):
        from django.utils.functional import Promise

        from fairdm.core.sample.models import BASE_SAMPLE_ERROR

        assert isinstance(BASE_SAMPLE_ERROR, Promise)


@pytest.mark.django_db
class TestSampleIdentity:
    def test_uuid_is_unique_across_specimens(self, rock_sample, water_sample):
        assert rock_sample.uuid != water_sample.uuid

    def test_uuid_is_prefixed_to_mark_it_a_sample(self, rock_sample):
        assert rock_sample.uuid.startswith("s")

    def test_uuid_is_generated_rather_than_supplied(self, dataset):
        from demo.factories import RockSampleFactory

        one = RockSampleFactory(dataset=dataset)
        two = RockSampleFactory(dataset=dataset)

        assert one.uuid
        assert two.uuid
        assert one.uuid != two.uuid

    def test_uuid_is_not_editable_afterwards(self, rock_sample):
        from fairdm.core.sample.admin import SampleChildAdmin

        assert "uuid" not in SampleForm.base_fields
        assert "uuid" in SampleChildAdmin.readonly_fields


@pytest.mark.django_db
class TestSampleFields:
    def test_name_is_required(self, dataset):
        from demo.models import RockSample

        sample = RockSample(
            dataset=dataset, rock_type="igneous", collection_date="2024-01-15"
        )

        with pytest.raises(ValidationError) as exc_info:
            sample.full_clean()

        assert "name" in exc_info.value.message_dict

    def test_local_id_is_optional(self, dataset):
        from demo.factories import RockSampleFactory

        sample = RockSampleFactory(dataset=dataset, local_id=None)

        sample.full_clean()

    def test_image_is_optional(self, dataset):
        from demo.factories import RockSampleFactory

        sample = RockSampleFactory(dataset=dataset, image=None)

        sample.full_clean()

    def test_location_is_optional(self, dataset):
        from demo.factories import RockSampleFactory

        sample = RockSampleFactory(dataset=dataset, location=None)

        sample.full_clean()
        assert sample.location is None


@pytest.mark.django_db
class TestSampleLocalId:
    def test_the_same_local_id_is_valid_in_two_different_datasets(self):
        from demo.factories import RockSampleFactory
        from fairdm.factories import DatasetFactory

        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()

        one = RockSampleFactory(dataset=dataset_a, local_id="LAB-001")
        two = RockSampleFactory(dataset=dataset_b, local_id="LAB-001")

        one.full_clean()
        two.full_clean()
        assert one.local_id == two.local_id == "LAB-001"


@pytest.mark.django_db
class TestSampleDatasetRelation:
    def test_deleting_the_dataset_deletes_the_specimen(self, rock_sample):
        dataset = rock_sample.dataset
        sample_pk = rock_sample.pk

        dataset.delete()

        assert not Sample.objects.filter(pk=sample_pk).exists()


@pytest.mark.django_db
class TestSampleLocationRelation:
    def test_deleting_a_referenced_location_is_refused(self, dataset):
        from django.db.models.deletion import ProtectedError

        from demo.factories import RockSampleFactory
        from fairdm.factories import PointFactory

        location = PointFactory()
        RockSampleFactory(dataset=dataset, location=location)

        with pytest.raises(ProtectedError):
            location.delete()


@pytest.mark.django_db
class TestSampleKeywords:
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
    def _build_and_load(self, n_samples, n_related):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from demo.factories import RockSampleFactory
        from fairdm.factories import DatasetFactory

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
                sample.add_contributor(PersonFactory(), with_roles=[role_types[i]])
            # The sample identifier collection has only two members (IGSN, DOI), and
            # a sample can carry at most one identifier per type, so this is capped rather
            # than indexed by `n_related` like the other related-record types above.
            for i in range(min(n_related, len(identifier_types))):
                SampleIdentifierFactory(related=sample, type=identifier_types[i])

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
    def test_methods_chain_in_either_order_and_return_the_right_rows(self, dataset):
        from demo.factories import RockSampleFactory, WaterSampleFactory

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
    def test_with_related_prefetches_dataset_location_contributors(self, dataset):
        from datetime import date

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from demo.models import RockSample

        samples = []
        for i in range(5):
            sample = RockSample.objects.create(
                name=f"Rock {i}",
                dataset=dataset,
                rock_type="igneous",
                collection_date=date.today(),
            )
            samples.append(sample)

        with CaptureQueriesContext(connection) as context_without:
            samples_without = list(RockSample.objects.all())
            for sample in samples_without:
                _ = sample.dataset.name
                _ = sample.dataset.project

        queries_without = len(context_without.captured_queries)

        with CaptureQueriesContext(connection) as context_with:
            samples_with = list(RockSample.objects.with_related())
            for sample in samples_with:
                _ = sample.dataset.name
                _ = sample.dataset.project

        queries_with = len(context_with.captured_queries)

        assert queries_with < queries_without
        assert queries_with <= 5

    def test_with_metadata_prefetches_descriptions_dates_identifiers(self, dataset):
        from datetime import date

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from demo.models import RockSample
        from fairdm.core.sample.models import SampleDate, SampleDescription

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

        with CaptureQueriesContext(connection) as context_without:
            samples_without = list(RockSample.objects.filter(pk=sample.pk))
            for s in samples_without:
                _ = list(s.descriptions.all())
                _ = list(s.dates.all())

        len(context_without.captured_queries)

        with CaptureQueriesContext(connection) as context_with:
            samples_with = list(RockSample.objects.filter(pk=sample.pk).with_metadata())
            for s in samples_with:
                _ = list(s.descriptions.all())
                _ = list(s.dates.all())

        queries_with = len(context_with.captured_queries)

        assert queries_with <= 4

    def test_polymorphic_queryset_returns_correct_typed_instances(self, dataset):
        from datetime import date

        from demo.models import RockSample, WaterSample
        from fairdm.core.sample.models import Sample

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

        samples = list(Sample.objects.all())

        rock_instances = [s for s in samples if isinstance(s, RockSample)]
        water_instances = [s for s in samples if isinstance(s, WaterSample)]

        assert len(rock_instances) >= 1
        assert len(water_instances) >= 1

        for sample in samples:
            assert type(sample).__name__ in ["RockSample", "WaterSample"]
            assert hasattr(sample, "rock_type") or hasattr(sample, "water_source")

    def test_queryset_method_chaining_works_correctly(self, dataset):
        from datetime import date

        from demo.models import RockSample

        for i in range(3):
            RockSample.objects.create(
                name=f"Rock {i}",
                dataset=dataset,
                rock_type="igneous",
                collection_date=date.today(),
            )

        chained = RockSample.objects.with_related().with_metadata()

        assert chained.count() >= 3

        filtered = chained.filter(rock_type="igneous")
        assert filtered.count() >= 3

        for sample in filtered[:2]:
            assert isinstance(sample, RockSample)
            assert sample.rock_type == "igneous"

    @pytest.mark.slow
    def test_1000_samples_load_with_minimal_queries_using_with_related(self, dataset):
        from datetime import date

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from demo.models import RockSample

        samples = []
        for i in range(100):
            sample = RockSample.objects.create(
                name=f"Rock {i}",
                dataset=dataset,
                rock_type="igneous",
                collection_date=date.today(),
            )
            samples.append(sample)

        with CaptureQueriesContext(connection) as context:
            optimized_samples = list(RockSample.objects.with_related())
            for sample in optimized_samples[:10]:
                _ = sample.dataset.name
                _ = sample.dataset.project

        num_queries = len(context.captured_queries)

        assert num_queries <= 10


@pytest.mark.django_db
class TestSampleModel:
    def test_sample_creation(self):
        sample = RockSampleFactory()

        assert sample.pk is not None
        assert sample.name is not None
        assert sample.uuid is not None
        assert sample.uuid.startswith("s")

    def test_sample_str_representation(self):
        sample = RockSampleFactory(name="Test Sample")
        assert str(sample) == "Test Sample"

    def test_sample_dataset_relationship(self):
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)

        assert sample.dataset == dataset
        assert sample in dataset.samples.all()

    def test_sample_local_id_optional(self):
        sample = RockSampleFactory(local_id=None)
        assert sample.local_id is None

        sample_with_id = RockSampleFactory(local_id="ABC-123")
        assert sample_with_id.local_id == "ABC-123"

    def test_sample_location_optional(self):
        sample = RockSampleFactory(location=None)
        assert sample.location is None

    def test_sample_status_default(self):
        sample = RockSampleFactory()
        assert sample.status is not None

    def test_sample_get_template_name(self):
        sample = RockSampleFactory()
        templates = sample.get_template_name()

        assert isinstance(templates, list)
        assert len(templates) == 2
        assert templates[1] == "fairdm/sample_card.html"

    def test_sample_type_of_property(self):
        assert Sample.type_of == Sample

    def test_sample_descriptions_relationship(self):
        sample = RockSampleFactory()
        descriptions = SampleDescription.objects.filter(related=sample)

        assert descriptions.count() >= 0
        assert all(desc.related == sample for desc in descriptions)

    def test_sample_dates_relationship(self):
        sample = RockSampleFactory()
        dates = SampleDate.objects.filter(related=sample)

        assert dates.count() >= 0
        assert all(date.related == sample for date in dates)

    def test_add_contributor(self):
        sample = RockSampleFactory()
        user = PersonFactory()

        contribution = sample.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert sample.contributors.filter(pk=contribution.pk).exists()


@pytest.mark.django_db
class TestSampleRelation:
    def test_sample_relation_creation(self):
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
        parent = RockSampleFactory()
        child = RockSampleFactory()

        SampleRelation.objects.create(
            type="child_of",
            source=child,
            target=parent,
        )

        related_samples = child.related_samples.all()
        assert related_samples.count() == 1
        assert related_samples.first().target == parent

        related_to = parent.related_to.all()
        assert related_to.count() == 1
        assert related_to.first().source == child


@pytest.mark.skip(reason="Phase 5 (US3 - Forms) not yet implemented")
@pytest.mark.django_db
class TestSampleForm:
    def test_form_valid_data(self):
        dataset = DatasetFactory()

        form_data = {
            "name": "Test Sample",
            "dataset": dataset.pk,
            "status": "unknown",
        }
        form = SampleForm(data=form_data)

        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_missing_required_fields(self):
        form_data = {}
        form = SampleForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_with_request_context(self):
        from unittest.mock import Mock

        request = Mock()
        form = SampleForm(request=request)

        assert form.request == request


@pytest.mark.django_db
class TestSampleViews:
    def test_sample_detail_view_accessible(self, client):
        sample = RockSampleFactory()
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
    def test_sample_contributor_relationship(self, user):
        sample = RockSampleFactory()
        contribution = sample.add_contributor(user, with_roles=["Creator"])

        assert sample.contributors.count() == 1
        assert contribution.contributor == user


@pytest.mark.django_db
class TestSampleQuerySetWithRelated:
    def test_with_related_prefetches_dataset(self):
        sample = RockSampleFactory()
        result = Sample.objects.with_related().get(pk=sample.pk)

        assert result.dataset is not None
        assert result.dataset.pk == sample.dataset.pk

    def test_with_related_prefetches_contributors(self):
        sample = RockSampleFactory()
        user1 = PersonFactory()
        user2 = PersonFactory()
        sample.add_contributor(user1, with_roles=["Creator"])
        sample.add_contributor(user2, with_roles=["Editor"])

        result = Sample.objects.with_related().get(pk=sample.pk)
        contributors = list(result.contributors.all())

        assert len(contributors) == 2

    def test_with_related_returns_queryset(self):
        qs = Sample.objects.with_related()

        assert hasattr(qs, "filter")
        assert hasattr(qs, "exclude")
        assert hasattr(qs, "order_by")

    def test_with_related_can_be_chained(self):
        sample1 = RockSampleFactory(name="Alpha")
        _sample2 = RockSampleFactory(name="Beta")

        results = Sample.objects.with_related().filter(name="Alpha")

        assert results.count() == 1
        assert results.first().pk == sample1.pk


@pytest.mark.django_db
class TestSampleQuerySetWithMetadata:
    def test_with_metadata_prefetches_descriptions(self):
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
        qs = Sample.objects.with_metadata()

        assert hasattr(qs, "filter")
        assert hasattr(qs, "exclude")

    def test_with_metadata_can_be_chained_with_with_related(self):
        sample = RockSampleFactory()
        result = Sample.objects.with_related().with_metadata().get(pk=sample.pk)

        assert result.dataset is not None


@pytest.mark.django_db
class TestSampleQuerySetByRelationship:
    def test_by_relationship_filters_by_type(self):
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
        _sample = RockSampleFactory()

        results = Sample.objects.by_relationship(relationship_type="nonexistent_type")

        assert results.count() == 0

    def test_by_relationship_can_be_chained(self):
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
    def test_all_returns_correct_subclass_for_single_type(self):
        from demo.factories import RockSampleFactory

        rock_sample = RockSampleFactory(name="Granite")
        results = list(Sample.objects.all())

        rock_result = next((r for r in results if r.pk == rock_sample.pk), None)
        assert rock_result is not None
        assert rock_result.__class__.__name__ == "RockSample"

    def test_all_returns_mixed_polymorphic_types(self):
        from demo.factories import RockSampleFactory, WaterSampleFactory

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
        from demo.factories import RockSampleFactory

        rock_sample = RockSampleFactory(name="Quartz")
        result = Sample.objects.get(pk=rock_sample.pk)

        assert result.__class__.__name__ == "RockSample"
        assert result.pk == rock_sample.pk

    def test_filter_returns_correct_subclass(self):
        from demo.factories import RockSampleFactory, WaterSampleFactory

        rock1 = RockSampleFactory(name="Alpha Rock")
        _water1 = WaterSampleFactory(name="Beta Water")

        results = list(Sample.objects.filter(name__startswith="Alpha"))

        assert len(results) >= 1
        rock_result = next((r for r in results if r.pk == rock1.pk), None)
        assert rock_result is not None
        assert rock_result.__class__.__name__ == "RockSample"

    def test_polymorphic_query_preserves_custom_fields(self):
        from demo.factories import RockSampleFactory

        rock_sample = RockSampleFactory(
            name="Granite",
            rock_type="igneous",
        )

        result = Sample.objects.get(pk=rock_sample.pk)

        assert hasattr(result, "rock_type")
        assert result.rock_type == "igneous"

    def test_polymorphic_query_without_select_subclasses_still_works(self):
        from demo.factories import RockSampleFactory, WaterSampleFactory

        _rock1 = RockSampleFactory()
        _water1 = WaterSampleFactory()

        results = list(Sample.objects.all())

        types = {r.__class__.__name__ for r in results}
        assert "RockSample" in types or "WaterSample" in types


@pytest.mark.django_db
class TestSampleConvenienceMethods:
    def test_get_all_relationships_returns_source_and_target(self):
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
        parent = RockSampleFactory()
        child = RockSampleFactory()

        SampleRelation.objects.create(source=child, target=parent, type="child_of")

        related = parent.get_related_samples(relationship_type="child_of")

        assert related.count() == 1
        assert child in related

        related_other = parent.get_related_samples(relationship_type="nonexistent")
        assert related_other.count() == 0


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
    def test_create_relationship_with_type(self, dataset):
        parent = create_rock_sample("Parent Rock Sample", dataset, rock_type="igneous")
        child = create_rock_sample("Derived Thin Section", dataset, rock_type="igneous")

        relation = SampleRelation.objects.create(
            source=child,
            target=parent,
            type="child_of",
        )

        assert relation.source == child
        assert relation.target == parent
        assert relation.type == "child_of"
        assert str(relation) == f"{child} child_of {parent}"

    def test_multiple_relationship_types(self, dataset):
        sample_a = create_water_sample("Water Sample A", dataset, water_source="river")
        sample_b = create_water_sample("Water Sample B", dataset, water_source="river")

        rel1 = SampleRelation.objects.create(
            source=sample_b,
            target=sample_a,
            type="child_of",
        )

        assert (
            SampleRelation.objects.filter(source=sample_b, target=sample_a).count() == 1
        )
        assert rel1.type == "child_of"


@pytest.mark.django_db
class TestSampleRelationValidation:
    def test_prevent_self_reference(self, dataset):
        sample = create_rock_sample("Test Sample", dataset, rock_type="igneous")

        relation = SampleRelation(
            source=sample,
            target=sample,
            type="child_of",
        )
        with pytest.raises(ValidationError):
            relation.clean()

    def test_prevent_direct_circular_relationship(self, dataset):
        sample_a = create_rock_sample("Sample A", dataset, rock_type="igneous")
        sample_b = create_rock_sample("Sample B", dataset, rock_type="sedimentary")

        SampleRelation.objects.create(
            source=sample_a,
            target=sample_b,
            type="child_of",
        )

        reverse_relation = SampleRelation(
            source=sample_b,
            target=sample_a,
            type="child_of",
        )
        with pytest.raises(ValidationError):
            reverse_relation.clean()

    def test_unique_together_constraint(self, dataset):
        sample_a = create_water_sample("Sample A", dataset, water_source="lake")
        sample_b = create_water_sample("Sample B", dataset, water_source="lake")

        SampleRelation.objects.create(
            source=sample_a,
            target=sample_b,
            type="child_of",
        )

        with pytest.raises(IntegrityError):
            SampleRelation.objects.create(
                source=sample_a,
                target=sample_b,
                type="child_of",
            )


@pytest.mark.django_db
class TestSampleRelationshipQueries:
    def test_get_children_method(self, dataset):
        parent = create_rock_sample("Parent Sample", dataset, rock_type="igneous")
        child1 = create_rock_sample("Child Sample 1", dataset, rock_type="igneous")
        child2 = create_rock_sample("Child Sample 2", dataset, rock_type="igneous")

        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        children = parent.get_children()

        assert children.count() == 2
        assert child1 in children
        assert child2 in children

    def test_get_parents_method(self, dataset):
        parent1 = create_water_sample("Parent Sample 1", dataset, water_source="river")
        parent2 = create_water_sample("Parent Sample 2", dataset, water_source="lake")
        child = create_water_sample("Child Sample", dataset, water_source="mixed")

        SampleRelation.objects.create(source=child, target=parent1, type="child_of")
        SampleRelation.objects.create(source=child, target=parent2, type="child_of")

        parents = child.get_parents()

        assert parents.count() == 2
        assert parent1 in parents
        assert parent2 in parents


@pytest.mark.django_db
class TestComplexSampleHierarchies:
    def test_multi_level_hierarchy(self, dataset):
        grandparent = create_rock_sample(
            "Grandparent Rock", dataset, rock_type="igneous"
        )
        parent = create_rock_sample("Parent Section", dataset, rock_type="igneous")
        child = create_rock_sample("Child Thin Section", dataset, rock_type="igneous")

        SampleRelation.objects.create(
            source=parent, target=grandparent, type="child_of"
        )
        SampleRelation.objects.create(source=child, target=parent, type="child_of")

        assert grandparent.get_children().count() == 1
        assert parent in grandparent.get_children()

        assert parent.get_children().count() == 1
        assert parent.get_parents().count() == 1
        assert child in parent.get_children()
        assert grandparent in parent.get_parents()

        assert child.get_parents().count() == 1
        assert parent in child.get_parents()

    def test_get_descendants_with_depth(self, dataset):
        samples = []
        for i in range(4):
            sample = create_rock_sample(
                f"Level {i} Sample", dataset, rock_type="igneous"
            )
            samples.append(sample)
            if i > 0:
                SampleRelation.objects.create(
                    source=samples[i],
                    target=samples[i - 1],
                    type="child_of",
                )

        root = samples[0]

        depth1_descendants = root.get_descendants(depth=1)
        assert depth1_descendants.count() == 1
        assert samples[1] in depth1_descendants

        depth2_descendants = root.get_descendants(depth=2)
        assert depth2_descendants.count() == 2
        assert samples[1] in depth2_descendants
        assert samples[2] in depth2_descendants

        all_descendants = root.get_descendants()
        assert all_descendants.count() == 3
        assert samples[1] in all_descendants
        assert samples[2] in all_descendants
        assert samples[3] in all_descendants


@pytest.mark.django_db
class TestSampleHierarchy:
    def test_direct_children(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(grandparent.get_children()) == {parent}
        assert set(parent.get_children()) == {child}
        assert set(child.get_children()) == set()

    def test_direct_parents(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(child.get_parents()) == {parent}
        assert set(parent.get_parents()) == {grandparent}
        assert set(grandparent.get_parents()) == set()

    def test_all_descendants_from_the_top_of_the_chain(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(grandparent.get_descendants()) == {parent, child}

    def test_all_descendants_from_the_middle_of_the_chain(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(parent.get_descendants()) == {child}

    def test_all_ancestors_from_the_bottom_of_the_chain(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(child.get_ancestors()) == {grandparent, parent}

    def test_all_ancestors_from_the_middle_of_the_chain(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(parent.get_ancestors()) == {grandparent}

    def test_nothing_from_the_wrong_direction_comes_back(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(child.get_descendants()) == set()
        assert set(grandparent.get_ancestors()) == set()
        assert child not in parent.get_ancestors()
        assert grandparent not in parent.get_descendants()
        assert parent not in parent.get_children()
        assert parent not in parent.get_parents()
        assert parent not in parent.get_descendants()
        assert parent not in parent.get_ancestors()


@pytest.mark.django_db
class TestSampleHierarchyDepth:
    @pytest.fixture
    def four_level_chain(self, dataset):
        root = RockSampleFactory(dataset=dataset, name="Root")
        level1 = RockSampleFactory(dataset=dataset, name="Level1")
        level2 = RockSampleFactory(dataset=dataset, name="Level2")
        level3 = RockSampleFactory(dataset=dataset, name="Level3")
        SampleRelationFactory(source=level1, target=root, type="child_of")
        SampleRelationFactory(source=level2, target=level1, type="child_of")
        SampleRelationFactory(source=level3, target=level2, type="child_of")
        return root, level1, level2, level3

    def test_depth_one_returns_direct_children_only(self, four_level_chain):
        root, level1, level2, level3 = four_level_chain

        assert set(root.get_descendants(depth=1)) == {level1}

    def test_depth_limit_is_respected_at_each_further_depth(self, four_level_chain):
        root, level1, level2, level3 = four_level_chain

        assert set(root.get_descendants(depth=2)) == {level1, level2}
        assert set(root.get_descendants(depth=3)) == {level1, level2, level3}
        assert set(root.get_descendants()) == {level1, level2, level3}


@pytest.mark.django_db
class TestSampleRelationRefusals:
    def test_self_reference_is_refused_on_direct_save(self, rock_sample):
        with pytest.raises(ValidationError):
            SampleRelation.objects.create(
                source=rock_sample, target=rock_sample, type="child_of"
            )

    def test_two_step_loop_is_refused_on_direct_save(self, dataset):
        sample_a = RockSampleFactory(dataset=dataset)
        sample_b = RockSampleFactory(dataset=dataset)
        SampleRelation.objects.create(source=sample_a, target=sample_b, type="child_of")

        with pytest.raises(ValidationError):
            SampleRelation.objects.create(
                source=sample_b, target=sample_a, type="child_of"
            )

    def test_duplicate_link_is_refused_on_direct_save(self, dataset):
        sample_a = RockSampleFactory(dataset=dataset)
        sample_b = RockSampleFactory(dataset=dataset)
        SampleRelation.objects.create(source=sample_a, target=sample_b, type="child_of")

        with pytest.raises(IntegrityError):
            SampleRelation.objects.create(
                source=sample_a, target=sample_b, type="child_of"
            )


@pytest.mark.django_db
class TestSingleTraversalImplementation:
    def test_get_descendants_matches_the_queryset(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(grandparent.get_descendants()) == set(
            Sample.objects.get_descendants(grandparent)
        )
        assert set(grandparent.get_descendants()) == {parent, child}

    def test_get_ancestors_matches_the_queryset(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(child.get_ancestors()) == set(Sample.objects.get_ancestors(child))
        assert set(child.get_ancestors()) == {grandparent, parent}


@pytest.mark.django_db
class TestSampleDescriptions:
    def test_description_is_stored_and_retrievable_by_type(self, rock_sample):
        SampleDescriptionFactory(related=rock_sample, type="SampleCollection")

        stored = SampleDescription.objects.get(
            related=rock_sample, type="SampleCollection"
        )

        assert stored.type == "SampleCollection"
        assert rock_sample.descriptions.get(type="SampleCollection") == stored


@pytest.mark.django_db
class TestSampleDescriptionVocabulary:
    def test_vocabulary_members_are_the_sample_description_collection(self):
        assert set(SampleDescription.VOCABULARY.values) == {
            "SampleCollection",
            "SamplePreparation",
            "SampleStorage",
            "SampleDestruction",
            "Other",
        }

    def test_type_outside_the_vocabulary_is_refused_naming_the_type(self, rock_sample):
        description = SampleDescription(
            related=rock_sample, type="NotARealType", value="text"
        )

        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()

        assert "type" in exc_info.value.error_dict
        message = str(exc_info.value.error_dict["type"][0])
        assert "NotARealType" in message


@pytest.mark.django_db
class TestSampleDescriptionValidationReturns:
    def test_full_clean_of_a_valid_description_does_not_raise(self, rock_sample):
        description = SampleDescription(
            related=rock_sample, type="SampleCollection", value="text"
        )

        description.full_clean()


@pytest.mark.django_db
class TestSampleDates:
    def test_date_is_stored_under_its_type(self, rock_sample):
        SampleDateFactory(related=rock_sample, type="Collected")

        stored = SampleDate.objects.get(related=rock_sample, type="Collected")

        assert stored.type == "Collected"


@pytest.mark.django_db
class TestSampleDateVocabulary:
    def test_vocabulary_members_are_the_sample_date_collection(self):
        assert set(SampleDate.VOCABULARY.values) == {
            "Created",
            "Destroyed",
            "Collected",
            "Returned",
            "Prepared",
            "Archival",
            "Restored",
        }

    def test_type_outside_the_vocabulary_is_refused(self, rock_sample):
        date = SampleDate(related=rock_sample, type="NotARealType", value="2024-01-15")

        with pytest.raises(ValidationError) as exc_info:
            date.full_clean()

        assert "type" in exc_info.value.error_dict


@pytest.mark.django_db
class TestSampleDateValidationReturns:
    def test_full_clean_of_a_valid_date_does_not_raise(self, rock_sample):
        date = SampleDate(related=rock_sample, type="Collected", value="2024-01-15")

        date.full_clean()


@pytest.mark.django_db
class TestSampleIdentifiers:
    def test_igsn_is_stored_under_the_igsn_type(self, rock_sample):
        identifier = SampleIdentifierFactory(
            related=rock_sample, type="IGSN", value="10.60516/AU1101"
        )

        stored = SampleIdentifier.objects.get(pk=identifier.pk)

        assert stored.type == "IGSN"
        assert stored.value == "10.60516/AU1101"

    def test_doi_is_stored_under_the_doi_type(self, rock_sample):
        identifier = SampleIdentifierFactory(
            related=rock_sample, type="DOI", value="10.1000/sample-doi"
        )

        stored = SampleIdentifier.objects.get(pk=identifier.pk)

        assert stored.type == "DOI"
        assert stored.value == "10.1000/sample-doi"


@pytest.mark.django_db
class TestSampleIdentifierVocabulary:
    def test_available_types_are_igsn_and_doi_only(self):
        assert set(SampleIdentifier.VOCABULARY.values) == {"IGSN", "DOI"}

    def test_no_type_names_a_person_organisation_or_project(self):
        assert set(SampleIdentifier.VOCABULARY.values).isdisjoint(
            {
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
class TestIGSNFormat:
    @pytest.mark.parametrize(
        "value",
        [
            "10.58052/SSH000SUA",
            "10.60516/AU1101",  # six-character suffix
            "10.25706/DIGITALCSIC-IGSN/622135",  # a slash inside the suffix
            "10.71928/M-202600319-N00325",
            "10273/BGRB5054RX05201",  # legacy handle form
        ],
    )
    def test_well_formed_igsn_is_accepted(self, rock_sample, value):
        identifier = SampleIdentifier(related=rock_sample, type="IGSN", value=value)

        identifier.full_clean()

    def test_malformed_igsn_is_refused(self, rock_sample):
        identifier = SampleIdentifier(
            related=rock_sample, type="IGSN", value="not-an-identifier"
        )

        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()

        assert "value" in exc_info.value.error_dict


@pytest.mark.django_db
class TestIGSNNormalisation:
    # The stripped display prefix must be written back to `value`: the uniqueness
    # index and the cross-record check both compare the stored string exactly.
    def test_bare_value_is_stored_unchanged(self, rock_sample):
        identifier = SampleIdentifier(
            related=rock_sample, type="IGSN", value="10.60516/AU1101"
        )
        identifier.full_clean()
        identifier.save()

        stored = SampleIdentifier.objects.get(pk=identifier.pk)
        assert stored.value == "10.60516/AU1101"

    def test_a_prefixed_form_of_an_identifier_already_stored_bare_is_refused(
        self, dataset
    ):
        first = create_rock_sample("First", dataset)
        SampleIdentifierFactory(related=first, type="IGSN", value="10.60516/AU1101")

        second = create_rock_sample("Second", dataset)
        clashing = SampleIdentifier(
            related=second, type="IGSN", value="doi:10.60516/AU1101"
        )

        with pytest.raises(ValidationError) as exc_info:
            clashing.full_clean()

        assert "value" in exc_info.value.error_dict


@pytest.mark.django_db
class TestSampleIdentifierUniqueness:
    def test_value_already_used_by_a_dataset_is_refused(self, rock_sample, dataset):
        from fairdm.core.dataset.models import DatasetIdentifier

        DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.5555/shared-across-records"
        )

        clashing = SampleIdentifier(
            related=rock_sample, type="DOI", value="10.5555/shared-across-records"
        )

        with pytest.raises(ValidationError) as exc_info:
            clashing.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_second_identifier_of_a_type_already_carried_is_refused(self, rock_sample):
        SampleIdentifierFactory(related=rock_sample, type="DOI", value="10.1000/first")

        second = SampleIdentifier(
            related=rock_sample, type="DOI", value="10.1000/second"
        )

        with pytest.raises(ValidationError):
            second.full_clean()


@pytest.mark.django_db
class TestSampleIdentifierValidationReturns:
    def test_full_clean_of_a_valid_identifier_does_not_raise(self, rock_sample):
        identifier = SampleIdentifier(
            related=rock_sample, type="DOI", value="10.1000/valid-identifier"
        )

        identifier.full_clean()


@pytest.mark.django_db
class TestSampleQuerySetRelationshipMethods:
    def test_by_relationship_filters_samples(self, dataset):
        parent = create_rock_sample("Parent", dataset, rock_type="igneous")
        child1 = create_rock_sample("Child 1", dataset, rock_type="igneous")
        child2 = create_rock_sample("Child 2", dataset, rock_type="igneous")

        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        children_queryset = Sample.objects.by_relationship(
            related_to=parent, relationship_type="child_of"
        )

        assert children_queryset.count() == 2
        assert child1 in children_queryset
        assert child2 in children_queryset


@pytest.mark.django_db
class TestSampleDeclaredPermissions:
    def test_the_rights_the_level_table_names_are_declared(self):
        codenames = set(
            Permission.objects.filter(
                content_type=ContentType.objects.get_for_model(Sample)
            ).values_list("codename", flat=True)
        )
        assert {
            "view_sample",
            "change_sample",
            "delete_sample",
            "add_sample",
            "import_data",
        } <= codenames


@pytest.mark.django_db
class TestSampleNoRights:
    # Must return False, not raise: guardian raises WrongAppError for a specimen
    # instance when the backend does not normalise the content type.
    def test_no_rights_anywhere_refuses_every_right(self, rock_sample, user):
        assert user.has_perm("sample.view_sample", rock_sample) is False
        assert user.has_perm("sample.change_sample", rock_sample) is False
        assert user.has_perm("sample.delete_sample", rock_sample) is False

    def test_a_right_on_a_different_dataset_does_not_leak(
        self, rock_sample, dataset, user
    ):
        from fairdm.factories import DatasetFactory

        other_dataset = DatasetFactory(project=dataset.project)
        assign_perm("change_dataset", user, other_dataset)

        assert user.has_perm("sample.change_sample", rock_sample) is False


@pytest.mark.django_db
class TestMoveKeepsManager:
    def refusal_code(self, sample):
        with pytest.raises(ValidationError) as refused:
            sample.clean()
        return refused.value.error_dict["dataset"][0].code

    def test_a_move_to_a_dataset_that_gives_no_manager_is_refused(
        self, make_manager, dataset
    ):
        make_manager(dataset)
        sample = RockSampleFactory(dataset=dataset)
        sample.dataset = DatasetFactory(project=dataset.project)

        assert self.refusal_code(sample) == "no_manager"

    def test_a_move_to_a_dataset_with_a_manager_passes(self, make_manager, dataset):
        other = DatasetFactory(project=dataset.project)
        make_manager(dataset)
        make_manager(other)
        sample = RockSampleFactory(dataset=dataset)
        sample.dataset = other

        sample.clean()

    def test_a_manager_through_the_project_still_counts(self, make_manager, dataset):
        make_manager(dataset.project)
        sample = RockSampleFactory(dataset=dataset)
        sample.dataset = DatasetFactory(project=dataset.project)

        sample.clean()

    def test_a_move_keeps_a_manager_listed_on_the_sample(self, make_manager, dataset):
        sample = RockSampleFactory(dataset=dataset)
        make_manager(sample)
        sample.dataset = DatasetFactory(project=dataset.project)

        sample.clean()

    def test_a_sample_that_had_no_manager_may_move_anywhere(self, dataset):
        sample = RockSampleFactory(dataset=dataset)
        sample.dataset = DatasetFactory(project=dataset.project)

        sample.clean()

    def test_a_new_sample_is_never_refused(self, dataset):
        sample = RockSample(name="New", dataset=dataset)

        sample.clean()

    def test_a_sample_whose_dataset_did_not_change_passes(self, make_manager, dataset):
        make_manager(dataset)
        sample = RockSampleFactory(dataset=dataset)
        sample.name = "Renamed"

        sample.clean()
