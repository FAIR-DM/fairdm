import pytest
from django.test import TestCase

from fairdm.core.dataset.models import Dataset, DatasetDate, DatasetDescription
from fairdm.core.measurement.models import Measurement, MeasurementDate, MeasurementDescription
from fairdm.core.models import Project, Sample
from fairdm.core.project.models import ProjectDate, ProjectDescription
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.factories.core import (
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    MeasurementDateFactory,
    MeasurementDescriptionFactory,
    MeasurementFactory,
    ProjectDateFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    SampleDateFactory,
    SampleDescriptionFactory,
    SampleFactory,
)


class TestCoreFactoriesBasic(TestCase):
    """Test basic functionality of all core factories."""

    def test_project_factory_creates_instance(self):
        """Test ProjectFactory creates valid instances with relationships."""
        project = ProjectFactory(descriptions=2, dates=1)

        self.assertIsInstance(project, Project)
        self.assertIsNotNone(project.pk)
        self.assertIsNotNone(project.name)

        # Check that descriptions and dates are created
        descriptions = ProjectDescription.objects.filter(related=project)
        dates = ProjectDate.objects.filter(related=project)
        self.assertEqual(descriptions.count(), 2)
        self.assertEqual(dates.count(), 1)

    def test_dataset_factory_creates_instance(self):
        """Test DatasetFactory creates valid instances with relationships."""
        dataset = DatasetFactory(descriptions=2, dates=1)

        self.assertIsInstance(dataset, Dataset)
        self.assertIsNotNone(dataset.pk)
        self.assertIsNotNone(dataset.name)
        self.assertIsNotNone(dataset.project)

        # Check that descriptions and dates are created
        descriptions = DatasetDescription.objects.filter(related=dataset)
        dates = DatasetDate.objects.filter(related=dataset)
        self.assertEqual(descriptions.count(), 2)
        self.assertEqual(dates.count(), 1)

    def test_sample_factory_creates_instance(self):
        """Test SampleFactory creates valid instances with relationships."""
        sample = SampleFactory(descriptions=2, dates=1)

        self.assertIsInstance(sample, Sample)
        self.assertIsNotNone(sample.pk)
        self.assertIsNotNone(sample.name)
        self.assertIsNotNone(sample.dataset)

        # Check that descriptions and dates are created
        descriptions = SampleDescription.objects.filter(related=sample)
        dates = SampleDate.objects.filter(related=sample)
        self.assertEqual(descriptions.count(), 2)
        self.assertEqual(dates.count(), 1)

    def test_measurement_factory_creates_instance(self):
        """Test MeasurementFactory creates valid instances with relationships."""
        measurement = MeasurementFactory(descriptions=2, dates=1)

        self.assertIsInstance(measurement, Measurement)
        self.assertIsNotNone(measurement.pk)
        self.assertIsNotNone(measurement.name)
        self.assertIsNotNone(measurement.dataset)
        self.assertIsNotNone(measurement.sample)

        # Check that descriptions and dates are created
        descriptions = MeasurementDescription.objects.filter(related=measurement)
        dates = MeasurementDate.objects.filter(related=measurement)
        self.assertEqual(descriptions.count(), 2)
        self.assertEqual(dates.count(), 1)

    def test_description_factories_with_related_objects(self):
        """Test description factories work when provided with related objects."""
        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = SampleFactory()
        measurement = MeasurementFactory()

        # Test description factories
        project_desc = ProjectDescriptionFactory(related=project)
        dataset_desc = DatasetDescriptionFactory(related=dataset)
        sample_desc = SampleDescriptionFactory(related=sample)
        measurement_desc = MeasurementDescriptionFactory(related=measurement)

        self.assertEqual(project_desc.related, project)
        self.assertEqual(dataset_desc.related, dataset)
        self.assertEqual(sample_desc.related, sample)
        self.assertEqual(measurement_desc.related, measurement)

        # Check default types
        self.assertEqual(project_desc.type, "Abstract")
        self.assertEqual(dataset_desc.type, "Abstract")
        self.assertEqual(sample_desc.type, "Abstract")
        self.assertEqual(measurement_desc.type, "Abstract")

    def test_date_factories_with_related_objects(self):
        """Test date factories work when provided with related objects."""
        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = SampleFactory()
        measurement = MeasurementFactory()

        # Test date factories
        project_date = ProjectDateFactory(related=project)
        dataset_date = DatasetDateFactory(related=dataset)
        sample_date = SampleDateFactory(related=sample)
        measurement_date = MeasurementDateFactory(related=measurement)

        self.assertEqual(project_date.related, project)
        self.assertEqual(dataset_date.related, dataset)
        self.assertEqual(sample_date.related, sample)
        self.assertEqual(measurement_date.related, measurement)

        # Check default types
        self.assertEqual(project_date.type, "Created")
        self.assertEqual(dataset_date.type, "Created")
        self.assertEqual(sample_date.type, "Created")
        self.assertEqual(measurement_date.type, "Created")

    def test_factories_support_build_mode(self):
        """Test that all factories support build mode (without saving to database)."""
        project = ProjectFactory.build()
        dataset = DatasetFactory.build()
        sample = SampleFactory.build()
        measurement = MeasurementFactory.build()

        # Built instances should not have PKs
        self.assertIsNone(project.pk)
        self.assertIsNone(dataset.pk)
        self.assertIsNone(sample.pk)
        self.assertIsNone(measurement.pk)

        # But should have required fields
        self.assertIsNotNone(project.name)
        self.assertIsNotNone(dataset.name)
        self.assertIsNotNone(sample.name)
        self.assertIsNotNone(measurement.name)

    def test_factories_support_custom_parameters(self):
        """Test that factories accept custom parameters."""
        custom_project_name = "Custom Project"
        custom_dataset_name = "Custom Dataset"

        project = ProjectFactory(name=custom_project_name)
        dataset = DatasetFactory(name=custom_dataset_name, project=project)

        self.assertEqual(project.name, custom_project_name)
        self.assertEqual(dataset.name, custom_dataset_name)
        self.assertEqual(dataset.project, project)

    def test_factory_relationships_hierarchy(self):
        """Test that factories create proper relationships in hierarchy."""
        # Create a complete hierarchy
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)
        sample = SampleFactory(dataset=dataset)
        measurement = MeasurementFactory(dataset=dataset, sample=sample)

        # Verify relationships
        self.assertEqual(dataset.project, project)
        self.assertEqual(sample.dataset, dataset)
        self.assertEqual(measurement.dataset, dataset)
        self.assertEqual(measurement.sample, sample)

    def test_batch_creation_works(self):
        """Test that factories support batch creation."""
        projects = ProjectFactory.create_batch(3, descriptions=2, dates=1)
        datasets = DatasetFactory.create_batch(3, descriptions=2, dates=1)

        self.assertEqual(len(projects), 3)
        self.assertEqual(len(datasets), 3)

        # Check each has the expected descriptions and dates
        for project in projects:
            self.assertEqual(ProjectDescription.objects.filter(related=project).count(), 2)
            self.assertEqual(ProjectDate.objects.filter(related=project).count(), 1)

        for dataset in datasets:
            self.assertEqual(DatasetDescription.objects.filter(related=dataset).count(), 2)
            self.assertEqual(DatasetDate.objects.filter(related=dataset).count(), 1)

    def test_sample_factory_specific_features(self):
        """Test Sample-specific factory features."""
        sample = SampleFactory()

        self.assertIsNotNone(sample.local_id)
        self.assertTrue(sample.local_id.startswith("SAMPLE-"))
        self.assertEqual(sample.status, "unknown")
        self.assertIsNone(sample.location)  # Optional field

    def test_dataset_factory_license_handling(self):
        """Test Dataset factory license creation."""
        dataset = DatasetFactory()

        self.assertIsNotNone(dataset.license)
        self.assertEqual(dataset.license.name, "CC BY 4.0")

    def test_project_factory_funding_structure(self):
        """Test Project factory funding JSON field."""
        project = ProjectFactory()

        self.assertIsNotNone(project.funding)
        self.assertIn("agency", project.funding)
        self.assertIn("grant_number", project.funding)
        self.assertIn("amount", project.funding)

    @pytest.mark.django_db
    def test_factories_respect_database_constraints(self):
        """Test that factories respect database constraints."""
        # Create multiple objects to test uniqueness constraints
        projects = ProjectFactory.create_batch(3)
        datasets = DatasetFactory.create_batch(3)
        samples = SampleFactory.create_batch(3)
        measurements = MeasurementFactory.create_batch(3)

        # Verify all have unique PKs
        project_pks = [p.pk for p in projects]
        dataset_pks = [d.pk for d in datasets]
        sample_pks = [s.pk for s in samples]
        measurement_pks = [m.pk for m in measurements]

        self.assertEqual(len(set(project_pks)), 3)
        self.assertEqual(len(set(dataset_pks)), 3)
        self.assertEqual(len(set(sample_pks)), 3)
        self.assertEqual(len(set(measurement_pks)), 3)


class TestFactoryVocabularyValidation(TestCase):
    """Test that factories validate types against model VOCABULARY."""

    def test_project_factory_rejects_invalid_description_types(self):
        """Test ProjectFactory raises error for invalid description types."""
        with self.assertRaises(ValueError) as cm:
            ProjectFactory(descriptions=1, descriptions__types=["InvalidType"])

        self.assertIn("Invalid description types", str(cm.exception))
        self.assertIn("InvalidType", str(cm.exception))

    def test_project_factory_rejects_invalid_date_types(self):
        """Test ProjectFactory raises error for invalid date types."""
        with self.assertRaises(ValueError) as cm:
            ProjectFactory(dates=1, dates__types=["InvalidType"])

        self.assertIn("Invalid date types", str(cm.exception))
        self.assertIn("InvalidType", str(cm.exception))

    def test_dataset_factory_rejects_invalid_description_types(self):
        """Test DatasetFactory raises error for invalid description types."""
        with self.assertRaises(ValueError) as cm:
            DatasetFactory(descriptions=1, descriptions__types=["InvalidType"])

        self.assertIn("Invalid description types", str(cm.exception))

    def test_sample_factory_rejects_invalid_description_types(self):
        """Test SampleFactory raises error for invalid description types."""
        with self.assertRaises(ValueError) as cm:
            SampleFactory(descriptions=1, descriptions__types=["InvalidType"])

        self.assertIn("Invalid description types", str(cm.exception))

    def test_measurement_factory_rejects_invalid_description_types(self):
        """Test MeasurementFactory raises error for invalid description types."""
        with self.assertRaises(ValueError) as cm:
            MeasurementFactory(descriptions=1, descriptions__types=["InvalidType"])

        self.assertIn("Invalid description types", str(cm.exception))

    def test_factories_accept_valid_vocabulary_types(self):
        """Test factories accept all valid types from VOCABULARY."""
        # Test with valid types from vocabularies
        project = ProjectFactory(descriptions=2, descriptions__types=["Abstract", "Introduction"])
        dataset = DatasetFactory(descriptions=2, descriptions__types=["Abstract", "Methods"])

        self.assertEqual(ProjectDescription.objects.filter(related=project).count(), 2)
        self.assertEqual(DatasetDescription.objects.filter(related=dataset).count(), 2)

        # Verify the types were used
        desc_types = list(ProjectDescription.objects.filter(related=project).values_list("type", flat=True))
        self.assertIn("Abstract", desc_types)
        self.assertIn("Introduction", desc_types)

    def test_factories_use_vocabulary_defaults(self):
        """Test factories use defaults from model VOCABULARY when no types specified."""
        project = ProjectFactory(descriptions=2)

        # Should create 2 descriptions with first 2 types from VOCABULARY
        descriptions = ProjectDescription.objects.filter(related=project)
        self.assertEqual(descriptions.count(), 2)

        # Types should be from the model's VOCABULARY
        desc_types = list(descriptions.values_list("type", flat=True))
        vocab_values = ProjectDescription.VOCABULARY.values

        # The created types should be in the vocabulary
        for dtype in desc_types:
            self.assertIn(dtype, vocab_values)
