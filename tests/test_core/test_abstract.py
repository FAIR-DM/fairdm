"""Tests for GenericModel and its QuerySet ordering functionality (fairdm/core/abstract.py)."""

import pytest
from django.db import connection

from fairdm.core.dataset.models import DatasetDescription
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.factories import PersonFactory
from fairdm.factories.core import (
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
)


@pytest.mark.django_db
class TestGenericModelQuerySet:
    """Tests for GenericModelQuerySet.in_order() functionality."""

    def test_description_queryset_in_order(self):
        """Test that descriptions can be ordered using queryset.in_order()."""
        dataset = DatasetFactory.create()

        # Create descriptions in random order
        DatasetDescriptionFactory.create(
            related=dataset, type="Abstract", value="This is the abstract"
        )
        DatasetDescriptionFactory.create(
            related=dataset, type="Other", value="Some other info"
        )
        DatasetDescriptionFactory.create(
            related=dataset, type="Methods", value="The methods used"
        )
        DatasetDescriptionFactory.create(
            related=dataset, type="TechnicalInfo", value="Technical details"
        )

        # Order by vocabulary using the queryset method
        ordered = dataset.descriptions.in_order()

        # Verify order matches vocabulary
        expected_types = ["Abstract", "Methods", "TechnicalInfo", "Other"]
        actual_types = [d.type for d in ordered]

        assert actual_types == expected_types

    def test_date_queryset_in_order(self):
        """Test that dates can be ordered using queryset.in_order()."""
        dataset = DatasetFactory.create()

        # Create dates in random order
        DatasetDateFactory.create(
            related=dataset, type="CollectionEnd", value="2024-12-31"
        )
        DatasetDateFactory.create(
            related=dataset, type="CollectionStart", value="2024-01-01"
        )
        DatasetDateFactory.create(related=dataset, type="Available", value="2024-06-15")

        # Order by vocabulary using the queryset method
        ordered = dataset.dates.in_order()

        # Verify order matches vocabulary
        expected_types = ["Available", "CollectionStart", "CollectionEnd"]
        actual_types = [d.type for d in ordered]

        assert actual_types == expected_types

    def test_filtered_queryset_in_order(self):
        """Test ordering a filtered queryset."""
        dataset = DatasetFactory.create()

        # Create multiple descriptions
        DatasetDescriptionFactory.create(
            related=dataset, type="Abstract", value="Abstract 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset, type="Methods", value="Methods 1"
        )
        DatasetDescriptionFactory.create(related=dataset, type="Other", value="Other 1")
        DatasetDescriptionFactory.create(
            related=dataset, type="TechnicalInfo", value="Tech 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset, type="SeriesInformation", value="Series 1"
        )

        # Filter and order
        filtered = dataset.descriptions.filter(
            type__in=["Other", "Abstract", "Methods"]
        )
        ordered = filtered.in_order()

        # Should be Abstract, Methods, Other (in that vocabulary order)
        expected_types = ["Abstract", "Methods", "Other"]
        actual_types = [d.type for d in ordered]

        assert actual_types == expected_types
        assert len(ordered) == 3

    def test_manager_in_order(self):
        """Test using manager.in_order() directly."""
        # Create some descriptions across different datasets
        dataset1 = DatasetFactory.create()
        dataset2 = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset1, type="Other", value="Other 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset1, type="Abstract", value="Abstract 1"
        )
        DatasetDescriptionFactory.create(
            related=dataset2, type="Methods", value="Methods 1"
        )

        # Get all descriptions in vocabulary order
        all_ordered = DatasetDescription.objects.in_order()

        # Verify we have all items
        assert len(all_ordered) >= 3

        # Verify the ordering for the items we created
        # (there may be other items from previous tests, but ours should be ordered correctly)
        our_items = [
            d for d in all_ordered if d.value in ["Other 1", "Abstract 1", "Methods 1"]
        ]
        actual_types = [d.type for d in our_items]

        # They should appear in vocabulary order: Abstract, Methods, Other
        assert actual_types == ["Abstract", "Methods", "Other"]

    def test_empty_queryset_in_order(self):
        """Test that in_order() works with empty querysets."""
        dataset = DatasetFactory.create()

        # No descriptions created
        ordered = dataset.descriptions.in_order()

        assert ordered == []

    def test_single_item_queryset_in_order(self):
        """Test that in_order() works with a single item."""
        dataset = DatasetFactory.create()

        DatasetDescriptionFactory.create(
            related=dataset, type="Abstract", value="Only one"
        )

        ordered = dataset.descriptions.in_order()

        assert len(ordered) == 1
        assert ordered[0].type == "Abstract"

    def test_vocabulary_not_defined_raises_error(self):
        """Test that calling in_order() on a model without VOCABULARY raises ValueError."""
        from fairdm.core.abstract import GenericModel

        # Create a test model without VOCABULARY
        class TestModelWithoutVocab(GenericModel):
            class Meta:
                app_label = "test"

        # This should raise a ValueError
        with pytest.raises(ValueError, match="does not define a VOCABULARY attribute"):
            # We need to access through the queryset
            TestModelWithoutVocab.objects.in_order()

    def test_duplicate_type_raises_integrity_error(self):
        """Test that adding duplicate types for the same related object raises an IntegrityError."""
        from django.db import IntegrityError

        dataset = DatasetFactory.create()

        # Create first description
        DatasetDescriptionFactory.create(
            related=dataset, type="Abstract", value="First abstract"
        )

        # Try to create another description with the same type - should fail
        with pytest.raises(IntegrityError):
            DatasetDescriptionFactory.create(
                related=dataset, type="Abstract", value="Second abstract"
            )

    def test_duplicate_type_different_related_object_allowed(self):
        """Test that the same type can exist on different related objects."""
        dataset1 = DatasetFactory.create()
        dataset2 = DatasetFactory.create()

        # Create descriptions with same type on different datasets - should succeed
        desc1 = DatasetDescriptionFactory.create(
            related=dataset1, type="Abstract", value="First abstract"
        )
        desc2 = DatasetDescriptionFactory.create(
            related=dataset2, type="Abstract", value="Second abstract"
        )

        assert desc1.type == desc2.type
        assert desc1.related != desc2.related

    def test_different_types_same_related_object_allowed(self):
        """Test that different types can exist on the same related object."""
        dataset = DatasetFactory.create()

        # Create descriptions with different types - should succeed
        desc1 = DatasetDescriptionFactory.create(
            related=dataset, type="Abstract", value="Abstract text"
        )
        desc2 = DatasetDescriptionFactory.create(
            related=dataset, type="Methods", value="Methods text"
        )

        assert desc1.related == desc2.related
        assert desc1.type != desc2.type
        # Verify both exist in the database
        assert DatasetDescription.objects.filter(related=dataset).count() == 2


@pytest.mark.django_db
class TestAddContributor:
    """`BaseModel.add_contributor` is the entry point every core record type inherits,
    and the one the project and dataset creation views call.

    A contributor's credit on an object is one record carrying every role they hold for
    it, so crediting the same person a second time under a further role has to add that
    role to the record already there. Recording the credit again instead breaks the
    uniqueness the record type guarantees.
    """

    def test_second_credit_adds_its_role_to_the_first(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        first = dataset.add_contributor(person, with_roles=["DataCollector"])
        second = dataset.add_contributor(person, with_roles=["Researcher"])

        assert second.pk == first.pk
        assert {role.name for role in second.roles.all()} == {
            "DataCollector",
            "Researcher",
        }
        assert dataset.contributors.filter(contributor=person).count() == 1

    def test_a_repeated_role_is_not_recorded_twice(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        dataset.add_contributor(person, with_roles=["DataCollector"])
        contribution = dataset.add_contributor(person, with_roles=["DataCollector"])

        assert [role.name for role in contribution.roles.all()] == ["DataCollector"]

    def test_crediting_without_roles_leaves_existing_roles_alone(self):
        dataset = DatasetFactory.create()
        person = PersonFactory()

        dataset.add_contributor(person, with_roles=["DataCollector"])
        contribution = dataset.add_contributor(person)

        assert {role.name for role in contribution.roles.all()} == {"DataCollector"}


@pytest.mark.django_db
class TestNameIndex:
    """T010, SC-007: `BaseModel.name` carries a database index after
    migration.

    Asserted against `Sample`/`Measurement`'s own table - a concrete
    polymorphic child such as `RockSample` does not hold `name` in its own
    table at all, so introspecting it would fail for an unrelated reason.
    """

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
