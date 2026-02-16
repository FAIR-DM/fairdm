"""
Unit tests for DatasetLiteratureRelation intermediate model.

Tests cover:
- DataCite relationship type vocabulary validation
- Unique together constraint
- CASCADE behavior
- Valid relationship creation

NOTE: All tests deferred - literature app not yet complete.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Literature app not yet complete - deferred")


@pytest.mark.django_db
class TestDatasetLiteratureRelationValidation:
    """Test DatasetLiteratureRelation model validation."""

    def test_create_relation_with_valid_type(self):
        """Can create relationship with valid DataCite type."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        assert relation.pk is not None
        assert relation.relationship_type == "IsCitedBy"

    def test_relationship_type_vocabulary_validation(self):
        """relationship_type must be valid DataCite type."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation(dataset=dataset, literature_item=paper, relationship_type="InvalidType")

        with pytest.raises(ValidationError) as exc_info:
            relation.full_clean()

        assert "relationship_type" in exc_info.value.error_dict

    def test_all_datacite_types_accepted(self):
        """All DataCite relationship types are valid."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        for type_code, _type_label in DATACITE_RELATIONSHIP_TYPES:
            relation = DatasetLiteratureRelation(dataset=dataset, literature_item=paper, relationship_type=type_code)
            relation.full_clean()  # Should not raise

    def test_dataset_required(self):
        """Dataset is required."""
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation(
            literature_item=paper,
            relationship_type="IsCitedBy",
            # Missing dataset
        )

        with pytest.raises(ValidationError):
            relation.full_clean()

    def test_literature_item_required(self):
        """LiteratureItem is required."""
        dataset = DatasetFactory()

        relation = DatasetLiteratureRelation(
            dataset=dataset,
            relationship_type="IsCitedBy",
            # Missing literature_item
        )

        with pytest.raises(ValidationError):
            relation.full_clean()


@pytest.mark.django_db
class TestUniqueTogetherConstraint:
    """Test unique_together constraint."""

    def test_duplicate_relationship_raises_error(self):
        """Cannot create duplicate relationships of same type."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(dataset=dataset, literature_item=paper, relationship_type="IsCitedBy")

        with pytest.raises(IntegrityError):
            DatasetLiteratureRelation.objects.create(
                dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
            )

    def test_different_types_allowed(self):
        """Same dataset-paper can have multiple relationship types."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(dataset=dataset, literature_item=paper, relationship_type="IsCitedBy")
        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsDocumentedBy"
        )

        assert dataset.literature_relations.count() == 2


@pytest.mark.django_db
class TestCascadeBehavior:
    """Test CASCADE delete behavior."""

    def test_cascade_on_dataset_delete(self):
        """Deleting dataset deletes relationships."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(dataset=dataset, literature_item=paper, relationship_type="IsCitedBy")

        dataset.delete()

        assert DatasetLiteratureRelation.objects.count() == 0

    def test_cascade_on_literature_delete(self):
        """Deleting literature item deletes relationships."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(dataset=dataset, literature_item=paper, relationship_type="IsCitedBy")

        paper.delete()

        assert DatasetLiteratureRelation.objects.count() == 0


@pytest.mark.django_db
class TestQueryingRelationships:
    """Test querying relationships."""

    def test_query_by_relationship_type(self):
        """Can filter relationships by type."""
        dataset = DatasetFactory()
        paper1 = LiteratureItemFactory()
        paper2 = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(dataset=dataset, literature_item=paper1, relationship_type="IsCitedBy")
        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper2, relationship_type="IsDocumentedBy"
        )

        citing = dataset.related_literature.filter(dataset_relations__relationship_type="IsCitedBy")

        assert citing.count() == 1
        assert paper1 in citing

    def test_access_through_manytomany(self):
        """Can access literature through ManyToMany relationship."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(dataset=dataset, literature_item=paper, relationship_type="IsCitedBy")

        assert paper in dataset.related_literature.all()
