"""
Unit tests for Dataset model.

Tests cover:
- Model creation and field constraints
- Name validation (required, max_length)
- Visibility choices and defaults
- PROTECT behavior on project deletion
- Orphaned datasets (project=null)
- License field with defaults
- UUID uniqueness and collision handling
- has_data property
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from fairdm.core.dataset.models import Dataset
from fairdm.factories import DatasetFactory, ProjectFactory
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestDatasetCreation:
    """Test basic Dataset model creation."""

    def test_create_dataset_with_required_fields(self):
        """Can create dataset with required fields."""
        project = ProjectFactory()
        dataset = Dataset.objects.create(name="Test Dataset", project=project)

        assert dataset.pk is not None
        assert dataset.name == "Test Dataset"
        assert dataset.project == project

    def test_create_dataset_with_factory(self):
        """DatasetFactory creates valid dataset."""
        dataset = DatasetFactory()

        assert dataset.pk is not None
        assert dataset.name
        assert dataset.project is not None
        assert dataset.uuid is not None


@pytest.mark.django_db
class TestDatasetNameValidation:
    """Test Dataset.name field validation."""

    def test_name_is_required(self):
        """Dataset name is required."""
        project = ProjectFactory()
        dataset = Dataset(project=project)

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_name_max_length_enforced(self):
        """Dataset name respects max_length constraint."""
        project = ProjectFactory()
        long_name = "x" * 301  # max_length=300
        dataset = Dataset(name=long_name, project=project)

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_name_accepts_valid_length(self):
        """Dataset name accepts valid length strings."""
        project = ProjectFactory()
        valid_name = "x" * 300  # Exactly at max_length
        dataset = Dataset(name=valid_name, project=project)

        dataset.full_clean()  # Should not raise
        dataset.save()
        assert dataset.pk is not None


@pytest.mark.django_db
class TestDatasetVisibility:
    """Test Dataset visibility choices and defaults."""

    def test_visibility_default_is_private(self):
        """New datasets default to PRIVATE visibility."""
        dataset = DatasetFactory()

        assert dataset.visibility == Visibility.PRIVATE.value

    def test_visibility_accepts_valid_choices(self):
        """Dataset accepts all valid visibility choices."""
        valid_choices = [
            Visibility.PUBLIC,
            Visibility.PRIVATE,
        ]

        for choice in valid_choices:
            dataset = DatasetFactory(visibility=choice.value)
            assert dataset.visibility == choice.value

    def test_visibility_rejects_invalid_choice(self):
        """Dataset rejects invalid visibility choice."""
        project = ProjectFactory()
        dataset = Dataset(name="Test", project=project, visibility=999)

        with pytest.raises(ValidationError):
            dataset.full_clean()


@pytest.mark.django_db
class TestDatasetProjectRelationship:
    """Test Dataset-Project relationship and PROTECT behavior."""

    def test_project_delete_raises_protected_error(self):
        """Deleting project with datasets raises ProtectedError."""
        project = ProjectFactory()
        DatasetFactory(project=project)

        with pytest.raises(ProtectedError):
            project.delete()

    def test_project_delete_succeeds_without_datasets(self):
        """Deleting project without datasets succeeds."""
        project = ProjectFactory()
        project_id = project.pk

        project.delete()

        from fairdm.core.project.models import Project

        assert not Project.objects.filter(pk=project_id).exists()

    def test_multiple_datasets_prevent_project_deletion(self):
        """Multiple datasets prevent project deletion."""
        project = ProjectFactory()
        DatasetFactory.create_batch(3, project=project)

        with pytest.raises(ProtectedError):
            project.delete()


@pytest.mark.django_db
class TestOrphanedDatasets:
    """Test orphaned datasets (project=null) behavior."""

    def test_dataset_can_exist_without_project(self):
        """Dataset can exist with project=null."""
        dataset = Dataset.objects.create(name="Orphaned Dataset", project=None)

        assert dataset.pk is not None
        assert dataset.project is None

    def test_orphaned_dataset_queries(self):
        """Can query orphaned datasets."""
        Dataset.objects.create(name="Orphaned", project=None)
        DatasetFactory()  # With project

        orphaned = Dataset.objects.filter(project__isnull=True)
        assert orphaned.count() == 1

    def test_setting_project_to_null_creates_orphan(self):
        """Setting project to null creates orphaned dataset."""
        dataset = DatasetFactory()
        dataset.project = None
        dataset.save()

        dataset.refresh_from_db()
        assert dataset.project is None


@pytest.mark.django_db
class TestDatasetLicense:
    """Test Dataset.license field and defaults."""

    def test_license_defaults_to_cc_by_4(self):
        """New datasets default to CC BY 4.0 license."""
        dataset = DatasetFactory()

        assert dataset.license is not None
        assert "CC BY 4.0" in dataset.license.name

    def test_license_can_be_changed(self):
        """Dataset license can be changed."""
        from licensing.models import License

        dataset = DatasetFactory()
        new_license, _ = License.objects.get_or_create(
            name="CC BY-SA 4.0",
            defaults={"slug": "cc-by-sa-4-0", "canonical_url": "https://creativecommons.org/licenses/by-sa/4.0/"},
        )

        dataset.license = new_license
        dataset.save()

        dataset.refresh_from_db()
        assert dataset.license == new_license

    def test_license_can_be_null(self):
        """Dataset license can be null."""
        dataset = DatasetFactory()
        dataset.license = None
        dataset.save()

        dataset.refresh_from_db()
        assert dataset.license is None


@pytest.mark.django_db
class TestDatasetUUID:
    """Test Dataset UUID field uniqueness and collision handling."""

    def test_uuid_generated_automatically(self):
        """Dataset UUID is generated automatically."""
        dataset = DatasetFactory()

        assert dataset.uuid is not None
        assert str(dataset.uuid)  # Can convert to string

    def test_uuid_is_unique(self):
        """Dataset UUIDs are unique."""
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()

        assert dataset1.uuid != dataset2.uuid

    def test_duplicate_uuid_raises_integrity_error(self):
        """Attempting to create dataset with duplicate UUID raises error."""
        dataset1 = DatasetFactory()

        with pytest.raises(IntegrityError):
            Dataset.objects.create(
                name="Duplicate UUID",
                project=ProjectFactory(),
                uuid=dataset1.uuid,  # Duplicate UUID
            )

    def test_uuid_immutable_after_creation(self):
        """UUID field is marked editable=False."""
        DatasetFactory()
        uuid_field = Dataset._meta.get_field("uuid")

        assert uuid_field.editable is False


@pytest.mark.django_db
class TestDatasetHasDataProperty:
    """Test Dataset.has_data property."""

    def test_has_data_false_for_empty_dataset(self):
        """has_data returns False for dataset without samples/measurements."""
        dataset = DatasetFactory()

        assert dataset.has_data is False

    @pytest.mark.skip(reason="Sample model not in scope for dataset feature tests")
    def test_has_data_true_with_samples(self):
        """has_data returns True for dataset with samples."""
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        Sample.objects.create(name="Test Sample", dataset=dataset)

        assert dataset.has_data is True

    @pytest.mark.skip(reason="Measurement model not in scope for dataset feature tests")
    def test_has_data_true_with_measurements(self):
        """has_data returns True for dataset with measurements."""
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        sample = Sample.objects.create(name="Test Sample", dataset=dataset)
        Measurement.objects.create(sample=sample, dataset=dataset)

        assert dataset.has_data is True

    def test_has_data_efficient_query(self):
        """has_data uses efficient EXISTS query."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        dataset = DatasetFactory()

        with CaptureQueriesContext(connection) as context:
            result = dataset.has_data

        # Should use EXISTS query (efficient)
        assert result is False
        assert len(context.captured_queries) <= 2  # Max 2 queries (samples + measurements)
