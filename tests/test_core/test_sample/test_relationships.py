"""Tests for Sample relationship functionality and provenance tracking.

Tests cover:
- SampleRelation creation with typed relationships
- Validation preventing self-reference and circular relationships
- Bidirectional relationship querying (children/parents)
- Complex hierarchies and provenance tracking
- Efficient querying of relationship trees
"""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from fairdm.core.sample.models import Sample, SampleRelation
from fairdm_demo.models import RockSample, WaterSample

pytestmark = pytest.mark.django_db


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
        assert SampleRelation.objects.filter(source=sample_b, target=sample_a).count() == 1
        assert rel1.type == "child_of"


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


class TestComplexSampleHierarchies:
    """Test complex multi-level sample hierarchies and provenance."""

    def test_multi_level_hierarchy(self, dataset):
        """Test creating and querying multi-level sample hierarchy (grandparent→parent→child)."""
        # Arrange: Create 3-level hierarchy
        grandparent = create_rock_sample("Grandparent Rock", dataset, rock_type="igneous")
        parent = create_rock_sample("Parent Section", dataset, rock_type="igneous")
        child = create_rock_sample("Child Thin Section", dataset, rock_type="igneous")

        # Create hierarchical relationships
        SampleRelation.objects.create(source=parent, target=grandparent, type="child_of")
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
            sample = create_rock_sample(f"Level {i} Sample", dataset, rock_type="igneous")
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
        children_queryset = Sample.objects.by_relationship(related_to=parent, relationship_type="child_of")

        # Assert: Both children are returned
        assert children_queryset.count() == 2
        assert child1 in children_queryset
        assert child2 in children_queryset
