"""
Unit tests for DatasetDate model.

Tests cover:
- Date type vocabulary validation
- Required fields
- Relationship to Dataset
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from fairdm.core.dataset.models import DatasetDate
from fairdm.factories import DatasetFactory


@pytest.mark.django_db
class TestDatasetDateValidation:
    """Test DatasetDate model validation."""

    def test_create_date_with_valid_type(self):
        """Can create date with valid date_type."""
        dataset = DatasetFactory()
        dataset_date = DatasetDate.objects.create(related=dataset, type="Created", value="2024-01-15")

        assert dataset_date.pk is not None
        assert dataset_date.type == "Created"
        assert str(dataset_date.value) == "2024-01-15"
        assert dataset_date.related == dataset

    def test_date_type_vocabulary_validation(self):
        """date_type must be from predefined vocabulary."""
        dataset = DatasetFactory()
        dataset_date = DatasetDate(related=dataset, type="InvalidType", value="2024-01-15")

        with pytest.raises(ValidationError) as exc_info:
            dataset_date.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_date_types_accepted(self):
        """All valid date types from vocabulary are accepted."""
        from fairdm.core.dataset.models import Dataset

        dataset = DatasetFactory()

        # Test all types from Dataset.DATE_TYPES.choices
        for type_code, _type_label in Dataset.DATE_TYPES.choices:
            dataset_date = DatasetDate(related=dataset, type=type_code, value="2024-01-15")
            dataset_date.full_clean()  # Should not raise

    def test_date_field_required(self):
        """date field is required."""
        dataset = DatasetFactory()
        dataset_date = DatasetDate(
            related=dataset,
            type="Created",
            # Missing value
        )

        with pytest.raises(ValidationError) as exc_info:
            dataset_date.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        """Dataset relationship is required."""
        dataset_date = DatasetDate(
            type="Created",
            value="2024-01-15",
            # Missing related
        )

        with pytest.raises(ValidationError):
            dataset_date.full_clean()

    def test_unique_together_constraint(self):
        """Dataset can have only one date per date_type."""
        dataset = DatasetFactory()

        DatasetDate.objects.create(related=dataset, type="Created", value="2024-01-15")

        # Attempt duplicate
        with pytest.raises(IntegrityError):
            DatasetDate.objects.create(related=dataset, type="Created", value="2024-02-20")

    def test_multiple_date_types_allowed(self):
        """Dataset can have multiple dates of different types."""
        dataset = DatasetFactory()

        DatasetDate.objects.create(related=dataset, type="Created", value="2024-01-15")
        DatasetDate.objects.create(related=dataset, type="Submitted", value="2024-02-01")

        assert dataset.dates.count() == 2

    def test_cascade_delete_with_dataset(self):
        """Deleting dataset deletes associated dates."""
        dataset = DatasetFactory()
        DatasetDate.objects.create(related=dataset, type="Created", value="2024-01-15")

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetDate.objects.filter(related_id=dataset_id).exists()
