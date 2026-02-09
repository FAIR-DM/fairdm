"""
Unit tests for DatasetDescription model.

Tests cover:
- Description type vocabulary validation
- Required fields
- Relationship to Dataset
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from fairdm.core.dataset.models import DatasetDescription
from fairdm.factories import DatasetFactory


@pytest.mark.django_db
class TestDatasetDescriptionValidation:
    """Test DatasetDescription model validation."""

    def test_create_description_with_valid_type(self):
        """Can create description with valid description_type."""
        dataset = DatasetFactory()
        description = DatasetDescription.objects.create(related=dataset, type="Abstract", value="This is an abstract")

        assert description.pk is not None
        assert description.description_type == "Abstract"

    def test_description_type_vocabulary_validation(self):
        """description_type must be from predefined vocabulary."""
        dataset = DatasetFactory()
        description = DatasetDescription(related=dataset, type="InvalidType", value="Test description")

        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_description_types_accepted(self):
        """All valid description types from vocabulary are accepted."""
        from fairdm.core.dataset.models import Dataset

        dataset = DatasetFactory()

        # Test all types from Dataset.DESCRIPTION_TYPES.choices
        for type_code, _type_label in Dataset.DESCRIPTION_TYPES.choices:
            description = DatasetDescription(related=dataset, type=type_code, value=f"Test {type_code}")
            description.full_clean()  # Should not raise

    def test_description_field_required(self):
        """description field is required."""
        dataset = DatasetFactory()
        description = DatasetDescription(
            related=dataset,
            type="Abstract",
            # Missing value
        )

        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        """Dataset relationship is required."""
        description = DatasetDescription(
            type="Abstract",
            value="Test",
            # Missing related
        )

        with pytest.raises(ValidationError):
            description.full_clean()

    def test_unique_together_constraint(self):
        """Dataset can have only one description per type (unique_together constraint)."""
        dataset = DatasetFactory()

        DatasetDescription.objects.create(related=dataset, type="Methods", value="Method 1")

        # Attempt to create duplicate description with same type should fail
        with pytest.raises(IntegrityError):
            DatasetDescription.objects.create(related=dataset, type="Methods", value="Method 2")

    def test_cascade_delete_with_dataset(self):
        """Deleting dataset deletes associated descriptions."""
        dataset = DatasetFactory()
        DatasetDescription.objects.create(related=dataset, type="Abstract", value="Test")

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetDescription.objects.filter(related_id=dataset_id).exists()
