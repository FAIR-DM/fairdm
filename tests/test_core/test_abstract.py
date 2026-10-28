"""Tests for GenericModel and its QuerySet ordering functionality (fairdm/core/abstract.py)."""

import pytest
from django.db import connection

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.dataset.models import DatasetDescription
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    DATE_TYPES,
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
)
from fairdm.factories import PersonFactory
from fairdm.factories.contributors import ContributorIdentifierFactory
from fairdm.factories.core import (
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    MeasurementDescriptionFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    SampleDescriptionFactory,
)


@pytest.mark.django_db
class TestGenericModelQuerySet:
    def test_description_queryset_in_order(self):
        dataset = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="This is the abstract",
        )
        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/other",
            value="Some other info",
        )
        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/methods",
            value="The methods used",
        )
        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/technical-info",
            value="Technical details",
        )

        ordered = dataset.descriptions.in_order()

        expected_types = [
            f"{DESCRIPTION_TYPES}/abstract",
            f"{DESCRIPTION_TYPES}/methods",
            f"{DESCRIPTION_TYPES}/technical-info",
            f"{DESCRIPTION_TYPES}/other",
        ]
        actual_types = [d.type_id for d in ordered]

        assert actual_types == expected_types

    def test_date_queryset_in_order(self):
        dataset = DatasetFactory.create()

        DatasetDateFactory.create(
            related=dataset, type_id=f"{DATE_TYPES}/collection-end", value="2024-12-31"
        )
        DatasetDateFactory.create(
            related=dataset,
            type_id=f"{DATE_TYPES}/collection-start",
            value="2024-01-01",
        )
        DatasetDateFactory.create(
            related=dataset, type_id=f"{DATE_TYPES}/available", value="2024-06-15"
        )

        ordered = dataset.dates.in_order()

        expected_types = [
            f"{DATE_TYPES}/available",
            f"{DATE_TYPES}/collection-start",
            f"{DATE_TYPES}/collection-end",
        ]
        actual_types = [d.type_id for d in ordered]

        assert actual_types == expected_types

    def test_filtered_queryset_in_order(self):
        dataset = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset, type_id=f"{DESCRIPTION_TYPES}/abstract", value="Abstract 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset, type_id=f"{DESCRIPTION_TYPES}/methods", value="Methods 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset, type_id=f"{DESCRIPTION_TYPES}/other", value="Other 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/technical-info",
            value="Tech 1",
        )
        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/series-information",
            value="Series 1",
        )

        filtered = dataset.descriptions.filter(
            type__in=[
                f"{DESCRIPTION_TYPES}/other",
                f"{DESCRIPTION_TYPES}/abstract",
                f"{DESCRIPTION_TYPES}/methods",
            ]
        )
        ordered = filtered.in_order()

        expected_types = [
            f"{DESCRIPTION_TYPES}/abstract",
            f"{DESCRIPTION_TYPES}/methods",
            f"{DESCRIPTION_TYPES}/other",
        ]
        actual_types = [d.type_id for d in ordered]

        assert actual_types == expected_types
        assert len(ordered) == 3

    def test_manager_in_order(self):
        dataset1 = DatasetFactory.create()
        dataset2 = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset1, type_id=f"{DESCRIPTION_TYPES}/other", value="Other 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset1,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Abstract 1",
        )
        DatasetDescriptionFactory.create(
            related=dataset2, type_id=f"{DESCRIPTION_TYPES}/methods", value="Methods 1"
        )

        all_ordered = DatasetDescription.objects.in_order()

        assert len(all_ordered) >= 3

        # Other tests may leave rows behind, so only the items created here are compared.
        our_items = [
            d for d in all_ordered if d.value in ["Other 1", "Abstract 1", "Methods 1"]
        ]
        actual_types = [d.type_id for d in our_items]

        assert actual_types == [
            f"{DESCRIPTION_TYPES}/abstract",
            f"{DESCRIPTION_TYPES}/methods",
            f"{DESCRIPTION_TYPES}/other",
        ]

    def test_empty_queryset_in_order(self):
        dataset = DatasetFactory.create()

        ordered = dataset.descriptions.in_order()

        assert ordered == []

    def test_single_item_queryset_in_order(self):
        dataset = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset, type_id=f"{DESCRIPTION_TYPES}/abstract", value="Only one"
        )

        ordered = dataset.descriptions.in_order()

        assert len(ordered) == 1
        assert ordered[0].type_id == f"{DESCRIPTION_TYPES}/abstract"

    def test_duplicate_type_raises_integrity_error(self):
        from django.db import IntegrityError

        dataset = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="First abstract",
        )

        with pytest.raises(IntegrityError):
            DatasetDescriptionFactory.create(
                related=dataset,
                type_id=f"{DESCRIPTION_TYPES}/abstract",
                value="Second abstract",
            )

    def test_duplicate_type_different_related_object_allowed(self):
        dataset1 = DatasetFactory.create()
        dataset2 = DatasetFactory.create()

        desc1 = DatasetDescriptionFactory.create(
            related=dataset1,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="First abstract",
        )
        desc2 = DatasetDescriptionFactory.create(
            related=dataset2,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Second abstract",
        )

        assert desc1.type == desc2.type
        assert desc1.related != desc2.related

    def test_different_types_same_related_object_allowed(self):
        dataset = DatasetFactory.create()

        desc1 = DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Abstract text",
        )
        desc2 = DatasetDescriptionFactory.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/methods",
            value="Methods text",
        )

        assert desc1.related == desc2.related
        assert desc1.type != desc2.type
        assert DatasetDescription.objects.filter(related=dataset).count() == 2


@pytest.mark.django_db
class TestAddContributor:
    def test_second_credit_adds_its_role_to_the_first(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        first = dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/data-collector"]
        )
        second = dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/researcher"]
        )

        assert second.pk == first.pk
        assert {role.uri for role in second.roles.all()} == {
            f"{CONTRIBUTOR_ROLES}/data-collector",
            f"{CONTRIBUTOR_ROLES}/researcher",
        }
        assert dataset.contributors.filter(contributor=person).count() == 1

    def test_a_repeated_role_is_not_recorded_twice(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/data-collector"]
        )
        contribution = dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/data-collector"]
        )

        assert [role.uri for role in contribution.roles.all()] == [
            f"{CONTRIBUTOR_ROLES}/data-collector"
        ]

    def test_crediting_without_roles_leaves_existing_roles_alone(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        dataset.add_contributor(
            person, with_roles=[f"{CONTRIBUTOR_ROLES}/data-collector"]
        )
        contribution = dataset.add_contributor(person)

        assert {role.uri for role in contribution.roles.all()} == {
            f"{CONTRIBUTOR_ROLES}/data-collector"
        }


@pytest.mark.django_db
class TestNameIndex:
    # Asserted on Sample/Measurement's own table: a polymorphic child such as
    # RockSample does not hold `name` in its own table.
    def _has_index_on_name(self, table_name: str) -> bool:
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table_name)
        return any(
            details["columns"] == ["name"] and (details["index"] or details["unique"])
            for details in constraints.values()
        )

    def test_sample_table_has_a_name_index(self):
        assert self._has_index_on_name(Sample._meta.db_table)

    def test_measurement_table_has_a_name_index(self):
        assert self._has_index_on_name(Measurement._meta.db_table)

    def test_every_registered_types_default_search_field_is_indexed(self):
        from fairdm.registry import registry

        for model_class in [*registry.samples, *registry.measurements]:
            config = registry.get_for_model(model_class)
            if config.search_fields:
                continue
            assert config.get_search_fields() == ["name"]

        assert self._has_index_on_name(Sample._meta.db_table)
        assert self._has_index_on_name(Measurement._meta.db_table)


@pytest.mark.django_db
class TestDescriptionMaxLength:
    DESCRIPTION_CASES = [
        (ProjectDescriptionFactory, ProjectFactory),
        (DatasetDescriptionFactory, DatasetFactory),
        (SampleDescriptionFactory, RockSampleFactory),
        (
            MeasurementDescriptionFactory,
            lambda: ExampleMeasurementFactory(sample=RockSampleFactory()),
        ),
    ]

    @pytest.mark.parametrize("description_factory, related_factory", DESCRIPTION_CASES)
    def test_value_at_the_ceiling_is_valid(self, description_factory, related_factory):
        from fairdm.core.abstract import DESCRIPTION_MAX_LENGTH

        related = related_factory()
        description = description_factory.build(
            related=related, value="x" * DESCRIPTION_MAX_LENGTH
        )

        description.full_clean()

    @pytest.mark.parametrize("description_factory, related_factory", DESCRIPTION_CASES)
    def test_value_one_character_over_the_ceiling_is_rejected(
        self, description_factory, related_factory
    ):
        from django.core.exceptions import ValidationError

        from fairdm.core.abstract import DESCRIPTION_MAX_LENGTH

        related = related_factory()
        description = description_factory.build(
            related=related, value="x" * (DESCRIPTION_MAX_LENGTH + 1)
        )

        with pytest.raises(ValidationError) as excinfo:
            description.full_clean()

        assert "value" in excinfo.value.message_dict


@pytest.mark.django_db
class TestIdentifierAddress:
    @pytest.mark.parametrize(
        ("type_", "value", "address"),
        [
            (
                f"{IDENTIFIER_TYPES}/wikidata",
                "Q42",
                "https://www.wikidata.org/wiki/Q42",
            ),
            (
                f"{IDENTIFIER_TYPES}/crossref-funder-id",
                "10.13039/100000001",
                "https://doi.org/10.13039/100000001",
            ),
        ],
    )
    def test_a_type_with_a_resolver_gives_its_address(self, type_, value, address):
        identifier = ContributorIdentifierFactory(
            related=PersonFactory(), type_id=type_, value=value
        )

        assert identifier.get_absolute_url() == address

    def test_a_contributor_type_with_no_resolver_gives_no_address(self):
        identifier = ContributorIdentifierFactory(
            related=PersonFactory(),
            type_id=f"{IDENTIFIER_TYPES}/researcher-id",
            value="A-1234-2020",
        )

        assert identifier.get_absolute_url() is None

    def test_a_record_type_with_no_resolver_gives_no_address(self):
        identifier = ProjectIdentifierFactory(
            related=ProjectFactory(),
            type_id=f"{IDENTIFIER_TYPES}/grant-number",
            value="EAR-1234567",
        )

        assert identifier.get_absolute_url() is None
