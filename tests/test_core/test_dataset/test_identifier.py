"""
Unit tests for DatasetIdentifier model.

Tests cover:
- Identifier type vocabulary validation
- DOI support via identifier_type='DOI'
- Required fields
- Relationship to Dataset
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from fairdm.core.dataset.models import Dataset, DatasetIdentifier
from fairdm.factories import DatasetFactory


@pytest.mark.django_db
class TestDatasetIdentifierValidation:
    """Test DatasetIdentifier model validation."""

    def test_create_identifier_with_valid_type(self):
        """Can create identifier with valid identifier_type."""
        dataset = DatasetFactory()
        identifier = DatasetIdentifier.objects.create(related=dataset, type="DOI", value="10.1000/xyz123")

        assert identifier.pk is not None
        assert identifier.identifier_type == "DOI"

    def test_identifier_type_vocabulary_validation(self):
        """identifier_type must be from predefined vocabulary."""
        dataset = DatasetFactory()
        identifier = DatasetIdentifier(related=dataset, type="InvalidType", value="some-identifier")

        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_identifier_types_accepted(self):
        """All valid identifier types from vocabulary are accepted."""
        dataset = DatasetFactory()

        # Test all types from Dataset.IDENTIFIER_TYPES
        for type_code, _type_label in Dataset.IDENTIFIER_TYPES:
            identifier = DatasetIdentifier(related=dataset, type=type_code, value=f"test-{type_code}")
            identifier.full_clean()  # Should not raise

    def test_identifier_field_required(self):
        """identifier field is required."""
        dataset = DatasetFactory()
        identifier = DatasetIdentifier(
            related=dataset,
            type="DOI",
            # Missing value
        )

        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        """Dataset relationship is required."""
        identifier = DatasetIdentifier(
            type="DOI",
            value="10.1000/xyz123",
            # Missing related
        )

        with pytest.raises(ValidationError):
            identifier.full_clean()


@pytest.mark.django_db
class TestDOISupport:
    """Test DOI support via DatasetIdentifier."""

    def test_create_doi_identifier(self):
        """Can create DOI identifier."""
        dataset = DatasetFactory()
        doi = DatasetIdentifier.objects.create(related=dataset, type="DOI", value="10.1000/xyz123")

        assert doi.identifier_type == "DOI"
        assert doi.identifier == "10.1000/xyz123"

    def test_query_datasets_with_doi(self):
        """Can query datasets that have DOI."""
        dataset_with_doi = DatasetFactory()
        DatasetIdentifier.objects.create(related=dataset_with_doi, type="DOI", value="10.1000/xyz123")

        dataset_without_doi = DatasetFactory()

        datasets_with_doi = Dataset.objects.filter(identifiers__type="DOI").distinct()

        assert dataset_with_doi in datasets_with_doi
        assert dataset_without_doi not in datasets_with_doi

    def test_multiple_identifiers_different_types(self):
        """Dataset can have multiple identifiers of different types."""
        dataset = DatasetFactory()

        DatasetIdentifier.objects.create(related=dataset, type="DOI", value="10.1000/xyz123")
        DatasetIdentifier.objects.create(related=dataset, type="ARK", value="ark:/12345/abc")

        assert dataset.identifiers.count() == 2

    def test_get_doi_helper(self):
        """Can retrieve DOI via query."""
        dataset = DatasetFactory()
        DatasetIdentifier.objects.create(related=dataset, type="DOI", value="10.1000/xyz123")

        doi = dataset.identifiers.filter(type="DOI").first()
        assert doi is not None
        assert doi.identifier == "10.1000/xyz123"

    def test_cascade_delete_with_dataset(self):
        """Deleting dataset deletes associated identifiers."""
        dataset = DatasetFactory()
        DatasetIdentifier.objects.create(related=dataset, type="DOI", value="10.1000/xyz123")

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetIdentifier.objects.filter(related_id=dataset_id).exists()

    def test_unique_together_constraint(self):
        """Dataset can have only one identifier per identifier_type."""
        dataset = DatasetFactory()

        DatasetIdentifier.objects.create(related=dataset, type="DOI", value="10.1000/xyz123")

        # Attempt duplicate identifier_type
        with pytest.raises(IntegrityError):
            DatasetIdentifier.objects.create(related=dataset, type="DOI", value="10.1000/different")
