"""Unit tests for Sample model."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse

from demo.factories import RockSampleFactory, WaterSampleFactory
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
from fairdm.core.vocabularies import (
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
    SAMPLE_STATUS,
    collection_members,
)
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
    def test_sample_is_named_by_its_name(self):
        assert str(RockSampleFactory(name="Test Sample")) == "Test Sample"


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


@pytest.mark.django_db
class TestSampleStatus:
    def test_no_status_stated_reads_as_unknown(self, dataset):
        sample = RockSample.objects.create(
            name="Unstated Status Rock",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        sample.refresh_from_db()

        assert sample.status_id == f"{SAMPLE_STATUS}/unknown"


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
        assert loaded.status_id == f"{SAMPLE_STATUS}/unknown"

        created = RockSample.objects.create(
            name="Offline Rock",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        created.refresh_from_db()
        assert created.status_id == f"{SAMPLE_STATUS}/unknown"


@pytest.mark.django_db
class TestStatusMigration:
    def test_forward_rewrites_every_status_to_unknown(self, dataset):
        import importlib

        from django.apps import apps as django_apps
        from django.db import connection

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

        table = Sample._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table} SET status_id = %s WHERE id = %s",  # noqa: S608
                [f"{SAMPLE_STATUS}/stored", rock.pk],
            )
            cursor.execute(
                f"UPDATE {table} SET status_id = %s WHERE id = %s",  # noqa: S608
                [f"{SAMPLE_STATUS}/destroyed", water.pk],
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

        assert Sample.objects.get(pk=rock.pk).status_id == f"{SAMPLE_STATUS}/unknown"
        assert Sample.objects.get(pk=water.pk).status_id == f"{SAMPLE_STATUS}/unknown"


@pytest.mark.django_db
class TestBaseSampleRefused:
    def test_validation_refuses_a_bare_sample(self, dataset):
        sample = Sample(name="Direct", dataset=dataset)

        with pytest.raises(ValidationError):
            sample.full_clean()

    def test_form_refuses_a_bare_sample(self, dataset):
        form = SampleForm(
            data={
                "name": "Direct",
                "dataset": dataset.pk,
                "status": f"{SAMPLE_STATUS}/unknown",
            }
        )

        assert not form.is_valid()

    def test_admin_refuses_the_base_content_type(self, admin_client):
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(Sample)
        response = admin_client.get(
            reverse("admin:sample_sample_add"), {"ct_id": ct.pk}
        )

        assert response.status_code == 403

    def test_direct_save_refuses_a_bare_sample(self, dataset):
        sample = Sample(name="Direct", dataset=dataset)

        with pytest.raises(ValidationError):
            sample.save()

    def test_fixture_loading_refuses_a_bare_sample(self, dataset):
        from django.core import serializers

        payload = (
            '[{"model": "sample.sample", "pk": null, '
            f'"fields": {{"name": "Direct", "dataset": {dataset.pk}}}}}]'
        )
        (deserialized,) = serializers.deserialize("json", payload)

        with pytest.raises(ValidationError):
            deserialized.save()


@pytest.mark.django_db
class TestSampleLocation:
    def test_the_database_refuses_an_elevation_without_a_location(self, dataset):
        from django.db import transaction

        with pytest.raises(IntegrityError), transaction.atomic():
            RockSampleFactory(dataset=dataset, location=None, location_elevation=12.0)

    def test_the_database_refuses_an_uncertainty_without_a_location(self, dataset):
        from django.db import transaction

        with pytest.raises(IntegrityError), transaction.atomic():
            RockSampleFactory(dataset=dataset, location=None, location_uncertainty=2.0)

    def test_the_database_refuses_a_negative_uncertainty(self, dataset):
        from django.contrib.gis.geos import Point as GEOSPoint
        from django.db import transaction

        with pytest.raises(IntegrityError), transaction.atomic():
            RockSampleFactory(
                dataset=dataset,
                location=GEOSPoint(8.4115, 49.0094, srid=4326),
                location_uncertainty=-1.0,
            )

    def test_the_database_accepts_a_location_with_elevation_and_uncertainty(
        self, dataset
    ):
        from django.contrib.gis.geos import Point as GEOSPoint

        sample = RockSampleFactory(
            dataset=dataset,
            location=GEOSPoint(8.4115, 49.0094, srid=4326),
            location_elevation=-12.5,
            location_uncertainty=0,
        )

        stored = Sample.objects.get(pk=sample.pk)
        assert (stored.location.x, stored.location.y) == (8.4115, 49.0094)
        assert (stored.location_elevation, stored.location_uncertainty) == (-12.5, 0)

    def test_clearing_the_location_in_the_form_clears_elevation_and_uncertainty(
        self, dataset
    ):
        from django import forms
        from django.contrib.gis.geos import Point as GEOSPoint
        from django.test import RequestFactory

        from fairdm.core.sample.forms import SampleFormMixin

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "status", "location"]

        sample = RockSampleFactory(
            dataset=dataset,
            location=GEOSPoint(8.4115, 49.0094, srid=4326),
            location_elevation=112.0,
            location_uncertainty=5.0,
        )
        data = {
            "name": sample.name,
            "dataset": dataset.pk,
            "status": f"{SAMPLE_STATUS}/unknown",
            "location_first": "",
            "location_second": "",
            "location_elevation": "",
            "location_uncertainty": "",
        }
        request = RequestFactory().get("/")
        request.user = PersonFactory(is_active=True)

        form = RockSampleForm(data, instance=sample, request=request)
        assert form.is_valid(), form.errors
        form.save()

        stored = RockSample.objects.get(pk=sample.pk)
        assert stored.location is None
        assert (stored.location_elevation, stored.location_uncertainty) == (None, None)


@pytest.mark.django_db
class TestSamplePrefetch:
    def _build(self, n_samples, n_related):
        dataset = DatasetFactory()
        description_types = [
            concept.uri for concept in SampleDescription.get_type_concepts()
        ]
        date_types = [concept.uri for concept in SampleDate.get_type_concepts()]
        identifier_types = [
            concept.uri for concept in SampleIdentifier.get_type_concepts()
        ]
        role_types = [role.uri for role in collection_members(Sample.CONTRIBUTOR_ROLES)]

        for _ in range(n_samples):
            sample = RockSampleFactory(dataset=dataset)
            for i in range(n_related):
                SampleDescriptionFactory(related=sample, type=description_types[i])
                SampleDateFactory(related=sample, type=date_types[i])
                sample.add_contributor(
                    PersonFactory(is_active=True), with_roles=[role_types[i]]
                )
            # The sample identifier collection has only two members (IGSN, DOI), and
            # a sample can carry at most one identifier per type, so this is capped rather
            # than indexed by `n_related` like the other related-record types above.
            for i in range(min(n_related, len(identifier_types))):
                SampleIdentifierFactory(related=sample, type=identifier_types[i])
        return dataset

    def _load(self, dataset):
        samples = list(
            Sample.objects.filter(dataset=dataset)
            .with_related()
            .with_metadata()
            .with_keywords()
        )
        for sample in samples:
            _ = sample.dataset.project
            _ = sample.location
            for contribution in sample.contributors.all():
                _ = contribution.contributor
                list(contribution.roles.all())
            list(sample.descriptions.all())
            list(sample.dates.all())
            list(sample.identifiers.all())
            list(sample.keywords.all())
        return samples

    def _count_queries(self, dataset):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as context:
            self._load(dataset)
        return len(context.captured_queries)

    def test_query_count_does_not_grow_with_specimens_or_related_records(self):
        small = self._build(n_samples=1, n_related=1)
        large = self._build(n_samples=3, n_related=3)
        # Evaluate once first so one-off lookups (content types, vocabulary) are cached
        # and only the per-row queries are left to compare.
        assert len(self._load(small)) == 1
        assert len(self._load(large)) == 3

        assert self._count_queries(small) == self._count_queries(large)


@pytest.mark.django_db
class TestSampleQuerySetChaining:
    def test_methods_chain_in_either_order_and_return_the_right_rows(self, dataset):
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
class TestSampleQuerySetByRelationship:
    def test_by_relationship_filters_by_type(self):
        parent = RockSampleFactory()
        child1 = RockSampleFactory()
        child2 = RockSampleFactory()
        RockSampleFactory()  # in no relation

        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        results = Sample.objects.by_relationship(relationship_type="child_of")

        # Every sample in a matching relation, the targets as well as the sources.
        assert set(results.values_list("pk", flat=True)) == {
            parent.pk,
            child1.pk,
            child2.pk,
        }

    def test_by_relationship_returns_empty_for_no_matches(self):
        _sample = RockSampleFactory()

        results = Sample.objects.by_relationship(relationship_type="nonexistent_type")

        assert results.count() == 0

    def test_by_relationship_to_a_sample_returns_its_children(self, dataset):
        parent = RockSampleFactory(dataset=dataset)
        child1 = RockSampleFactory(dataset=dataset)
        child2 = RockSampleFactory(dataset=dataset)
        RockSampleFactory(dataset=dataset)

        SampleRelation.objects.create(source=child1, target=parent, type="child_of")
        SampleRelation.objects.create(source=child2, target=parent, type="child_of")

        children = Sample.objects.by_relationship(
            related_to=parent, relationship_type="child_of"
        )

        assert set(children) == {child1, child2}


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


@pytest.mark.django_db
class TestSampleRelationCreation:
    def test_a_relation_reads_as_source_type_target(self, dataset):
        parent = RockSampleFactory(dataset=dataset)
        child = RockSampleFactory(dataset=dataset)

        relation = SampleRelation.objects.create(
            source=child,
            target=parent,
            type="child_of",
        )

        assert str(relation) == f"{child} child_of {parent}"


@pytest.mark.django_db
class TestSampleRelationValidation:
    def test_prevent_self_reference(self, dataset):
        sample = RockSampleFactory(dataset=dataset)

        relation = SampleRelation(
            source=sample,
            target=sample,
            type="child_of",
        )
        with pytest.raises(ValidationError):
            relation.clean()

    def test_prevent_direct_circular_relationship(self, dataset):
        sample_a = RockSampleFactory(dataset=dataset)
        sample_b = RockSampleFactory(dataset=dataset)

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
        _, parent, child = sample_hierarchy_chain

        assert set(parent.get_descendants()) == {child}

    def test_all_ancestors_from_the_bottom_of_the_chain(self, sample_hierarchy_chain):
        grandparent, parent, child = sample_hierarchy_chain

        assert set(child.get_ancestors()) == {grandparent, parent}

    def test_all_ancestors_from_the_middle_of_the_chain(self, sample_hierarchy_chain):
        grandparent, parent, _ = sample_hierarchy_chain

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
        root, level1, _, _ = four_level_chain

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
class TestSampleTypeVocabulary:
    def test_a_description_type_outside_the_collection_is_refused_naming_it(
        self, rock_sample
    ):
        description = SampleDescription(
            related=rock_sample,
            type_id=f"{DESCRIPTION_TYPES}/not-a-real-type",
            value="text",
        )

        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()

        assert "type" in exc_info.value.error_dict
        message = str(exc_info.value.error_dict["type"][0])
        assert "not-a-real-type" in message


@pytest.mark.django_db
class TestIGSNFormat:
    @pytest.mark.parametrize(
        "value",
        [
            "10.60516/AU1101",  # DataCite DOI form
            "10273/BGRB5054RX05201",  # legacy handle form
        ],
    )
    def test_well_formed_igsn_is_accepted(self, rock_sample, value):
        identifier = SampleIdentifier(
            related=rock_sample, type_id=f"{IDENTIFIER_TYPES}/igsn", value=value
        )

        identifier.full_clean()

    def test_a_pasted_resolver_address_is_accepted_and_stored_bare(self, rock_sample):
        identifier = SampleIdentifier(
            related=rock_sample,
            type_id=f"{IDENTIFIER_TYPES}/igsn",
            value="https://doi.org/10.60516/AU1101",
        )

        identifier.full_clean()

        assert identifier.value == "10.60516/AU1101"

    def test_malformed_igsn_is_refused(self, rock_sample):
        identifier = SampleIdentifier(
            related=rock_sample,
            type_id=f"{IDENTIFIER_TYPES}/igsn",
            value="not-an-identifier",
        )

        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()

        assert "value" in exc_info.value.error_dict


@pytest.mark.django_db
class TestIGSNNormalisation:
    # The stripped display prefix must be written back to `value`: the uniqueness
    # index and the cross-record check both compare the stored string exactly.
    def test_a_prefixed_form_of_an_identifier_already_stored_bare_is_refused(
        self, dataset
    ):
        first = RockSampleFactory(dataset=dataset)
        SampleIdentifierFactory(
            related=first, type_id=f"{IDENTIFIER_TYPES}/igsn", value="10.60516/AU1101"
        )

        second = RockSampleFactory(dataset=dataset)
        clashing = SampleIdentifier(
            related=second,
            type_id=f"{IDENTIFIER_TYPES}/igsn",
            value="doi:10.60516/AU1101",
        )

        with pytest.raises(ValidationError) as exc_info:
            clashing.full_clean()

        assert "value" in exc_info.value.error_dict


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
        other_dataset = DatasetFactory(project=dataset.project)
        assign_perm("change_dataset", user, other_dataset)

        assert user.has_perm("sample.change_sample", rock_sample) is False


@pytest.mark.django_db
class TestMoveKeepsManager:
    """A sample's ``clean`` applies the shared rule that ``RecordAccess`` tests."""

    def test_a_move_to_a_dataset_that_gives_no_manager_is_refused(
        self, make_manager, dataset
    ):
        make_manager(dataset)
        sample = RockSampleFactory(dataset=dataset)
        sample.dataset = DatasetFactory(project=dataset.project)

        with pytest.raises(ValidationError) as refused:
            sample.clean()

        assert refused.value.error_dict["dataset"][0].code == "no_manager"
